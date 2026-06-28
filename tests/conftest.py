import pytest

from src.core.registry import timer_registry


@pytest.fixture(autouse=True)
def isolated_registry():
    timer_registry.reset()
    yield
    timer_registry.reset()
