import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--postgres",
        action="store_true",
        default=False,
        help="Run integration tests against the configured PostgreSQL test database.",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--postgres"):
        return
    skip = pytest.mark.skip(reason="Requires PostgreSQL; run pytest --postgres")
    for item in items:
        if item.get_closest_marker("postgres"):
            item.add_marker(skip)
