# Custom decorator for refactor-safe WDS method mocking
from collections.abc import Callable
from typing import Any
from unittest.mock import patch


def mock_method(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that patches methods using method references for refactor-safety.

    Args:
        method: The actual method reference (e.g., WDSRequests.get_code_sets)

    Returns:
        A decorated function with the patch applied

    Usage:
        @mock_method(WDSRequests.get_code_sets)
        @pytest.mark.asyncio
        async def test_something(self, mock_get_code_sets, ...):

    """
    target = f"{method.__module__}.{method.__qualname__}"

    def decorator(func):
        # Apply the patch decorator
        return patch(target)(func)

    return decorator
