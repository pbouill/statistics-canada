# Custom decorator for refactor-safe WDS method mocking
from typing import Any, Callable
from unittest.mock import patch


def mock_method(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that patches methods using method references for refactor-safety.

    Args:
        method: The actual method reference (e.g., WDSRequests.get_code_sets)

    Returns:
        A patch decorator configured with the fully qualified method name

    Usage:
        @mock_method(WDSRequests.get_code_sets)
        @pytest.mark.asyncio
        async def test_something(self, mock_method: AsyncMock, ...):
    """
    target = f"{method.__module__}.{method.__qualname__}"
    return patch(target)