import pytest

from audit.models import AuditLog

pytestmark = [pytest.mark.postgres, pytest.mark.django_db]


def test_system_audit_log():
    log = AuditLog.objects.create(
        action="test", object_type="Room", object_id="1", result="success"
    )
    log.refresh_from_db()
    assert log.user is None
    assert log.details == {}
    assert log.created_at is not None
