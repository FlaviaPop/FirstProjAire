"""Forms for the platform admin (Story 1.9): account create/change and parent-child links.

Forms check input shape and the account guards (patterns §7.3: nothing is saved when a rule
is broken); link rules come from the LinkParent use case so the admin and any later caller
apply exactly the same checks.
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar

from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm, UsernameField
from django.utils.translation import gettext_lazy as _

from application.accounts.link_parent import LinkParentCommand
from infrastructure import container
from infrastructure.persistence.accounts.models import (
    ADMIN_ROLE,
    ParentChildLinkModel,
    UserModel,
)
from infrastructure.web.common.errors import ERROR_MESSAGES

LAST_ADMIN = _("There must be at least one active administrator.")
STUDENT_HAS_LINKS = _("Remove this student's parent links before changing the role.")
# Owner decision 2026-10-22: the Parent guard has its own wording (7 messages in total).
PARENT_HAS_LINKS = _("Remove this parent's child links before changing the role.")
# Violations reported against one field; every other link violation is a form-level error.
FIELD_OF_VIOLATION = {"parent_not_parent_role": "parent", "student_not_student_role": "student"}
if TYPE_CHECKING:  # django-stubs generics; the runtime classes are not subscriptable
    CreationFormBase = UserCreationForm[UserModel]
    ChangeFormBase = UserChangeForm[UserModel]
    LinkFormBase = forms.ModelForm[ParentChildLinkModel]
else:
    CreationFormBase, ChangeFormBase, LinkFormBase = (
        UserCreationForm,
        UserChangeForm,
        forms.ModelForm,
    )
PLATFORM_FIELDS = ("username", "full_name", "date_of_birth", "role", "preferred_language")


def leaves_no_active_admin(removed_pks: Iterable[int]) -> bool:
    """True if no active Admin would remain once these accounts lose the Admin role/access."""
    remaining = UserModel.objects.filter(role=ADMIN_ROLE, is_active=True)
    return not remaining.exclude(pk__in=list(removed_pks)).exists()


def is_last_active_admin(user: UserModel) -> bool:
    return user.role == ADMIN_ROLE and user.is_active and leaves_no_active_admin([user.pk])


class PlatformUserCreationForm(CreationFormBase):
    """Add form: platform fields + the password twice, checked by AUTH_PASSWORD_VALIDATORS.

    Built on UserCreationForm, not AdminUserCreationForm, which adds `usable_password`: every
    pilot account signs in with a password the Admin hands over.
    """

    class Meta(UserCreationForm.Meta):
        model = UserModel
        fields = PLATFORM_FIELDS


class PlatformUserChangeForm(ChangeFormBase):
    """Change form; refuses changes that would lock everyone out or orphan parent links."""

    class Meta:
        model = UserModel
        fields = (*PLATFORM_FIELDS, "password", "is_active")
        field_classes: ClassVar[dict[str, type[forms.Field]]] = {"username": UsernameField}

    def clean(self) -> dict[str, Any]:
        data = super().clean() or {}
        # self.instance still holds the stored values here (_post_clean copies the new ones).
        stored = self.instance
        new_role, new_active = data.get("role", stored.role), data.get("is_active", True)
        if (new_role != ADMIN_ROLE or not new_active) and is_last_active_admin(stored):
            self.add_error(None, LAST_ADMIN)
        if new_role != stored.role:
            self._check_links_before_role_change(stored)
        return data

    def _check_links_before_role_change(self, stored: UserModel) -> None:
        if stored.role == "STUDENT" and stored.parent_links.exists():
            self.add_error("role", STUDENT_HAS_LINKS)
        if stored.role == "PARENT" and stored.child_links.exists():
            self.add_error("role", PARENT_HAS_LINKS)


class ParentChildLinkForm(LinkFormBase):
    """Pick a Parent/Guardian and a Student; the LinkParent use case decides if it's allowed."""

    # Set per request by ParentChildLinkAdmin.get_form (the session user, never POST data).
    actor_id: ClassVar[int]
    # Set when a concurrent request created the same link between validation and save.
    lost_race: ClassVar[bool] = False

    parent = forms.ModelChoiceField(
        UserModel.objects.filter(role="PARENT", is_active=True).order_by("username"),
        label=_("Parent/Guardian"),
        error_messages={"invalid_choice": ERROR_MESSAGES["parent_not_parent_role"]},
    )
    student = forms.ModelChoiceField(
        UserModel.objects.filter(role="STUDENT").order_by("username"),
        label=_("Student"),
        error_messages={"invalid_choice": ERROR_MESSAGES["student_not_student_role"]},
    )

    class Meta:
        model = ParentChildLinkModel
        fields = ("parent", "student")

    def clean(self) -> dict[str, Any]:
        data = super().clean() or {}
        if self.errors:
            return data
        if self.lost_race:
            self.add_error(None, str(ERROR_MESSAGES["link_exists"]))
            return data
        command = LinkParentCommand(data["parent"].pk, data["student"].pk, actor_id=self.actor_id)
        for violation in container.link_parent().validate(command):
            field = FIELD_OF_VIOLATION.get(violation.code)
            self.add_error(field, str(ERROR_MESSAGES[violation.code]))
        return data

    def _get_validation_exclusions(self) -> set[str]:
        # LinkParent reports duplicate and self links with the rule's own translated text;
        # Django's generic UniqueConstraint/CheckConstraint messages would only repeat it.
        # (A private ModelForm hook since Django 1.x; django-stubs doesn't declare it.)
        inherited: set[str] = super()._get_validation_exclusions()  # type: ignore[misc]
        return {*inherited, "parent", "student"}
