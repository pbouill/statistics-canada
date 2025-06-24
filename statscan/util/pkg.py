from typing import Optional, Iterable, Any, TypeVar
import importlib
import pkgutil
import inspect
import logging

logger = logging.getLogger(__name__)

_T = TypeVar('_T')


def get_subpkg_subcls(
    cls: type[_T], 
    cls_test_methods: Optional[Iterable[tuple[str, Any]]] = None,
    exclude_missing_test: bool = False,
) -> dict[str, type[_T]]:
    """
    Get all subclasses of a given class in the same package as the caller module.
    Args:
        cls: The class to find subclasses of.
        cls_test_methods: A list of tuples containing method names and their expected return values.
        exclude_missing_test: If True, exclude subclasses that do not have the specified test methods.
    Returns:
        A dictionary with the names of the subclasses as keys and the subclass types as values.
    """
    subcls: dict[str, type[_T]] = {}
    excluded = set()

    if (frame := inspect.currentframe()) is None:
        raise RuntimeError('Cannot determine current frame in call stack.')
    if (caller_frame := frame.f_back) is None:
        raise RuntimeError('Cannot determine caller frame in call stack.')  
    if (caller_module := inspect.getmodule(caller_frame)) is None:
        raise RuntimeError('Cannot determine caller module in call stack.')

    caller_module_name = caller_module.__name__
    logger.debug(f'finding subclasses of {cls.__name__} in {caller_module_name} using {cls_test_methods=}')
    
    for module_info in pkgutil.iter_modules(caller_module.__path__):
        module_name = module_info.name
        logger.debug(f'[{caller_module_name}] checking module {module_name} for subclasses of {cls.__name__}')
        module = importlib.import_module(f'.{module_name}', package=caller_module.__name__)

        for name, obj in inspect.getmembers(module, predicate=inspect.isclass):
            
            if obj.__module__ != module.__name__:
                logger.debug(f'[{caller_module_name}] {name} ({obj}) is not in module {module_name} ({obj.__module__}). Skipping...')
                continue
            else:
                logger.debug(f'[{caller_module_name}] checking {name} ({obj}) for subclass of {cls.__name__}')
            if obj in excluded:
                logger.debug(f'[{caller_module_name}] {name} ({obj}) is in excluded set. Skipping...')
                continue
            if obj in subcls.values():
                logger.debug(f'[{caller_module_name}] {name} ({obj}) is already included in subcls. Skipping...')
                continue
            if issubclass(obj, cls) and (obj is not cls):
                if cls_test_methods is not None:
                    for mn, target_value in cls_test_methods:
                        if (m := getattr(obj, mn, None)) is None:
                            logger.warning(f'[{caller_module_name}] {obj.__name__} ({cls.__name__} subclass) does not have method {mn}.')
                            if exclude_missing_test:
                                excluded.add(obj)
                                break
                            else:
                                logger.debug(f'[{caller_module_name}] {obj.__name__} ({cls.__name__} subclass) method {mn} is missing, but not excluding due to exclude_missing_test=False.')
                                continue
                        elif not callable(m):
                            logger.warning(f'[{caller_module_name}] {obj.__name__} ({cls.__name__} subclass) method {mn} is not callable. Excluding...')
                            excluded.add(obj)
                            break
                        elif len(params := inspect.signature(m).parameters) > 0:
                            logger.warning(f'[{caller_module_name}] {obj.__name__} ({cls.__name__} subclass) method {mn} has parameters {params}. Excluding...')
                            excluded.add(obj)
                            break
                        elif (test_value := m()) != target_value:
                            logger.warning(f'[{caller_module_name}] {obj.__name__} ({cls.__name__} subclass) method ".{mn}()" did not pass test ({test_value} != {target_value}). Excluding...')
                            excluded.add(obj)
                            break
                if obj in excluded:
                    logger.debug(f'[{caller_module_name}] {obj.__name__} ({cls.__name__} subclass) excluded due to test failure.')
                    continue
                if name in subcls:
                    logger.warning(f'[{caller_module_name}] {name} ({obj}) already exists in subcls. Skipping...')
                    continue
                logger.debug(f'[{caller_module_name}] including {obj} ({cls.__name__} subclass)')
                subcls[name] = obj
            

    return subcls