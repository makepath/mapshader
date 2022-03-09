import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runlarge", action="store_true", default=False, help="run large tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "large: mark test as large")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runlarge"):
        skip_large = pytest.mark.skip(reason="use --runlarge option to run")
        for item in items:
            if "large" in item.keywords:
                item.add_marker(skip_large)
