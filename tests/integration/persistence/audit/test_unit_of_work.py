import pytest

from infrastructure.persistence.audit.models import AuditLogModel
from infrastructure.persistence.audit.repositories import DjangoAuditPort
from infrastructure.persistence.common.unit_of_work import DjangoUnitOfWork
from tests.fakes import FixedClock

# The UoW runs inside the per-test transaction (as a savepoint). transaction=True isn't
# usable here: its teardown flush DELETEs audit_log, which the append-only triggers forbid.
pytestmark = pytest.mark.django_db


def _audit_then_fail():
    with DjangoUnitOfWork():
        DjangoAuditPort(FixedClock()).record("auth.login", actor_username="ana")
        raise RuntimeError("business rule failed after the audit write")


def test_unit_of_work_commits_on_clean_exit():
    with DjangoUnitOfWork():
        DjangoAuditPort(FixedClock()).record("auth.login", actor_username="ana")

    assert AuditLogModel.objects.count() == 1


def test_unit_of_work_rolls_back_and_reraises_on_error():
    with pytest.raises(RuntimeError, match="business rule failed"):
        _audit_then_fail()

    assert AuditLogModel.objects.count() == 0
