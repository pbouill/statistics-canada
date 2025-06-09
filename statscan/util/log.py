from typing import Optional
import logging


def configure_logging(
    fmt: str = '%(asctime)s :: %(levelname)s :: %(name)s :: %(module)s.%(funcName)s:%(lineno)d - %(message)s',
    level: Optional[int | str] = None,
):
    if isinstance(level, str):
        level = logging.getLevelNamesMapping()[level.upper()]
    logging.basicConfig(format=fmt, level=level)