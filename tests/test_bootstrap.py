"""Smoke checks that do not require a running database."""

from django.core.checks import run_checks


def test_django_system_checks():
    assert run_checks() == []


def test_unconfigured_route_returns_404(client, settings):
    settings.DEBUG = False
    response = client.get("/not-configured/")
    assert response.status_code == 404
