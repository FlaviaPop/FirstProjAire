from domain.accounts.roles import Role
from infrastructure.persistence.accounts.models import ROLE_CHOICES


def test_persisted_role_choices_equal_domain_roles():
    assert [value for value, _label in ROLE_CHOICES] == [role.value for role in Role]
