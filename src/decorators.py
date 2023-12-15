import math
import time


def timeit(func):
    """
    Decorator function to time a function.

    :param func:
    :return:
    """
    def timeit_wrapper(*args, **kwargs):
        self = args[0]
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = str(str(time.perf_counter() - start) + '000')[:6]
        self.log.info(
            f"Time taken: {end} seconds to run {self.__class__.__name__}.{func.__name__}",
            extra={'custom_funcName': func.__name__}
        )
        return result
    return timeit_wrapper


def log_args(func):
    """
    Decorator function to log the arguments of a function. One log row per argument. If the arguments are too long, they
    will be truncated.

    :param func:
    :return:
    """
    def logargs_wrapper(*args, **kwargs):
        self = args[0]
        for arg in args[1:]:
            arg = str(arg)[:100]
            self.log.trace(f"Argument: {arg}", extra={'custom_funcName': func.__name__})
        for key, value in kwargs.items():
            value = str(value)[:100]
            self.log.trace(f"Argument: {key}={value}", extra={'custom_funcName': func.__name__})
        return func(*args, **kwargs)
    return logargs_wrapper