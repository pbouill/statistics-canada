"""Utility functions for dynamic subclass discovery and package inspection.

This module provides helpers to find all subclasses of a given class within the caller's
package, with optional method-based filtering and exclusion logic. Used for dynamic
model and enum management.
"""
import importlib
import inspect
import logging
import pkgutil
from collections.abc import Generator, Iterable
from pathlib import Path
from types import ModuleType
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

class TestMethodError(Exception):
    """Base exception for subclass testing errors."""

    pass


class MethodDNError(TestMethodError):
    """The subclass does not implement the required method."""

    pass


class MethodSignatureError(TestMethodError):
    """The subclass method has an unexpected signature."""

    pass


class MethodValueError(TestMethodError):
    """The subclass method does not return the expected value."""

    pass


def test_class_method(
    cls: type,
    method_name: str,
    target_value: Any,
    ignore_missing_test: bool = False,
) -> None:
    """Execute a test on a class by method name.

    This function checks if the specified class has a method with the given name,
    verifies that it is callable, takes no parameters, and returns the expected value.

    Args:
        cls: The class to test.
        method_name: The name of the method to check.
        target_value: The expected return value of the method.
        ignore_missing_test: If True, do not raise an error if the method is missing.

    """
    if (m := getattr(cls, method_name, None)) is None:
        if ignore_missing_test:
            return
        raise MethodDNError(
            f"{cls.__name__} does not have method {method_name}."
        )
    if not callable(m):
        raise MethodSignatureError(
            f"{cls.__name__}.{method_name} is not callable."
        )
    if len(params := inspect.signature(m).parameters) > 0:
        raise MethodSignatureError(
            f"{cls.__name__}.{method_name} has parameters {params}."
        )
    if (test_value := m()) != target_value:
        raise MethodValueError(
            f"{cls.__name__}.{method_name} returned {test_value}, "
            f"expected {target_value}."
        )


def subcls_in_module[T](
    cls: type[T],
    module: ModuleType,
 ) -> Generator[tuple[str, type[T]]]:
    """Find all subclasses of a given class in a specified module.

    This function inspects the provided module for classes that are subclasses
    of the specified class, excluding the class itself. It yields tuples of
    subclass names and their corresponding class types.

    Args:
        cls: The base class to find subclasses of.
        module: The module to inspect for subclasses.

    Yields:
        Tuples of (subclass name, subclass type).

    """
    logger.debug(
        f"Checking module {module.__name__} for subclasses of {cls.__name__}"
    )
    for name, mod_cls in inspect.getmembers(module, predicate=inspect.isclass):
        if mod_cls.__module__ != module.__name__:
            logger.debug(
                f"[{module.__name__}] {name} ({mod_cls}) is not in "
                f"module {module.__name__} ({mod_cls.__module__}). Skipping..."
            )
            continue
        if not issubclass(mod_cls, cls) or (mod_cls is cls):
            logger.debug(
                f"[{module.__name__}] {name} ({mod_cls}) is not a "
                f"subclass of {cls.__name__} or is the same class. Skipping..."
            )
            continue

        yield name, mod_cls


def module_from_path(path: Path) -> ModuleType:
    """Import a module from a given file path.

    Args:
        path: The file path to the module.

    Returns:
        The imported module.

    """
    if path.is_file():
        path = path.parent
    if not path.is_dir():
        raise ValueError(f"Provided path {path} is not a directory.")
    module = importlib.import_module(path.as_posix().replace("/", "."))
    return module

def path_from_module(module: ModuleType) -> Path:
    """Get the file path of a given module.

    Args:
        module: The module to get the path for.

    Returns:
        The file path of the module.

    Raises:
        ValueError: If the module does not have a __file__ attribute.

    """
    try:
        path = Path(module.__path__[0])
    except AttributeError as ae:
        if module.__file__ is None:
            raise AttributeError(
                f"Module {module.__name__} does not have a __file__ attribute."
            ) from ae
        path =  Path(module.__file__)
        if path.is_file():
            path = path.parent
    return path


def module_from_caller(frame_level: int = 1) -> ModuleType:
    """Get the module from the caller's frame.

    This function inspects the call stack to find the module of the caller
    at the specified frame level.

    Args:
        frame_level: The number of frames to go back in the call stack.

    Returns:
        The caller's module.

    """
    if not (frame := inspect.currentframe()):
        raise RuntimeError("Cannot determine current frame in call stack.")
    for i in range(frame_level):
        if (frame := frame.f_back) is None:
            raise RuntimeError(f"Cannot determine frame in call stack at level {i}.")
    if (module := inspect.getmodule(frame)) is None:
        raise RuntimeError("Cannot determine caller module in call stack.")
    return module


def get_submodule_subcls[T](
    cls: type[T],
    module_path: Path | None = None,
    cls_test_methods: Iterable[tuple[str, Any]] | None = None,
    ignore_missing_test: bool = False,
) -> dict[str, type[T]]:
    """Get all subclasses of a given class.

    This function searches for subclasses of the specified class within the
    caller's package or a specified module path. It can also filter subclasses based
    on the presence and return values of specified class methods.

    Args:
        cls: The base class to find subclasses of.
        module_path: Optional path to the module/package to search. If None, uses the
            caller's package.
        cls_test_methods: Optional iterable of (method_name, expected_value) tuples
            to test on each subclass. Only subclasses passing all tests are included.
        ignore_missing_test: If True, subclasses missing a test method are included.

    Returns:
        A dictionary mapping subclass names to subclass types.

    """
    subcls: dict[str, type[T]] = {}
    excluded = set()

    if module_path:
        module = module_from_path(path=module_path)
    else:
        module = module_from_caller(frame_level=2)

    logger.debug(
        f"finding subclasses of {cls.__name__} in {module_path} "
        f"using {cls_test_methods=}"
    )

    for submod_info in pkgutil.iter_modules(module.__path__):
        submod_name = submod_info.name
        submod = importlib.import_module(
            f".{submod_name}", package=module.__name__
        )
        for name, mod_cls in subcls_in_module(cls=cls, module=submod):
            logger.debug(f"[{submod_name}] Found subclass {name} ({mod_cls})")
            if cls_test_methods is not None:
                for mn, target_value in cls_test_methods:
                    try:
                        test_class_method(
                            cls=mod_cls,
                            method_name=mn,
                            target_value=target_value,
                            ignore_missing_test=ignore_missing_test,
                        )
                    except TestMethodError as e:
                            excluded.add(mod_cls)
                            logger.debug(f"[{submod_name}] {e}. Excluding...")
                            break
            if mod_cls not in excluded:
                if name not in subcls:
                    logger.debug(
                        f"[{submod_name}] including {mod_cls} "
                        f"({cls.__name__} subclass)"
                    )
                    subcls[name] = mod_cls
            else:
                logger.warning(
                    f"[{submod_name}] {name} ({mod_cls}) "
                    f"already exists in subcls. Skipping..."
                )

    return subcls
