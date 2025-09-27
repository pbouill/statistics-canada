# Custom decorator for refactor-safe WDS method mocking
from typing import Any, Callable
from unittest.mock import patch
import pytest


def mock_method(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that patches methods using method references for refactor-safety.

    Automatically applies @pytest.mark.mock marker for consistent test categorization.

    Args:
        method: The actual method reference (e.g., WDSRequests.get_code_sets)

    Returns:
        A decorated function with both patch and pytest.mark.mock applied

    Usage:
        @mock_method(WDSRequests.get_code_sets)
        @pytest.mark.asyncio
        async def test_something(self, mock_get_code_sets, ...):
    """
    target = f"{method.__module__}.{method.__qualname__}"

    def decorator(func):
        # Apply the patch decorator
        patched_func = patch(target)(func)
        # Apply the mock marker
        marked_func = pytest.mark.mock(patched_func)
        return marked_func

    return decorator
