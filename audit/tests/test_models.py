from audit.models import AuditLog


def test_details_default_is_independent():
    first = AuditLog()
    second = AuditLog()
    first.details["message"] = "test"
    assert second.details == {}
