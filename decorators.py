import functools
import time
from typing import Callable


def timed(func: Callable) -> Callable:

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  ⏱  {func.__name__} completed in {elapsed:.3f}s")
        return result

    return wrapper


def validate_log_level(func: Callable) -> Callable:
    from models import LOG_LEVELS

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        level = kwargs.get("level")
        if level is not None and level.upper() not in LOG_LEVELS:
            raise ValueError(
                f"Unknown log level '{level}'. Valid levels: {', '.join(LOG_LEVELS)}"
            )
        return func(*args, **kwargs)

    return wrapper


def log_call(func: Callable) -> Callable:

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"  → calling {func.__name__}")
        return func(*args, **kwargs)

    return wrapper