"""Make audit_log append-only in the database itself (Story 1.8 review v1 ISS-002).

The Python guards in models.py cover `AuditLogModel.objects`; these triggers also cover
`_base_manager`, raw SQL and dbshell. The only permitted UPDATE is the one Django's deletion
collector issues when an account is deleted: actor_id → NULL with every other column unchanged.
A future retention job (DevOps) must drop and re-create these triggers explicitly.
"""

from django.db import migrations

_COLUMNS_UNCHANGED = " AND ".join(
    f"NEW.{column} IS OLD.{column}"
    for column in (
        "id",
        "actor_username",
        "action",
        "target_type",
        "target_id",
        "metadata",
        "ip_address",
        "created_at",
    )
)

CREATE_TRIGGERS = (
    """
    CREATE TRIGGER audit_log_append_only_delete
    BEFORE DELETE ON audit_log
    BEGIN
        SELECT RAISE(ABORT, 'audit_log is append-only');
    END;
    """,
    f"""
    CREATE TRIGGER audit_log_append_only_update
    BEFORE UPDATE ON audit_log
    WHEN NOT (OLD.actor_id IS NOT NULL AND NEW.actor_id IS NULL AND {_COLUMNS_UNCHANGED})
    BEGIN
        SELECT RAISE(ABORT, 'audit_log is append-only');
    END;
    """,
)
DROP_TRIGGERS = (
    "DROP TRIGGER IF EXISTS audit_log_append_only_update;",
    "DROP TRIGGER IF EXISTS audit_log_append_only_delete;",
)


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]

    operations = [migrations.RunSQL(sql=CREATE_TRIGGERS, reverse_sql=DROP_TRIGGERS)]
