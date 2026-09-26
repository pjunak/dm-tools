"""Release closed Tk test objects before another test starts a worker."""

import gc
from collections.abc import Generator

import pytest


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item) -> Generator[None, bool | None, bool | None]:
    try:
        return (yield)
    finally:
        if item.path.stem.endswith(("_ui", "_workbench")):
            # Fixture teardown alone is too early: pytest still owns funcargs.
            # Once the protocol returns those references are released. Collect
            # on this UI thread so a later worker cannot finalize old Tk vars
            # against a destroyed interpreter while root.update() drives tests.
            gc.collect()
