import pytest


def pytest_addoption(parser):
    parser.addoption("--local", action="store_true", help="run local only tests (marked with marker @local)")


def pytest_runtest_setup(item):
    print(f"Test: {item.name}")
    print(f"Keywords: {item.keywords}")
    print(f"Local option: {item.config.getoption('--local')}")
    if "local" in item.keywords and not item.config.getoption("--local"):
        pytest.skip("need --local option to run this test")
