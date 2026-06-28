import pytest

from src.core.registry import timer_registry


@pytest.fixture(autouse=True)
def isolated_registry():
    """Reset the timer registry before and after every test."""
    timer_registry.reset()
    yield
    timer_registry.reset()
