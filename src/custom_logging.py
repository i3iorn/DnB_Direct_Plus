import logging
import logging.config
from pathlib import Path


def add_log_levels():
    new_levels = {
        'TRACE': 5,
        'VERBOSE': 15,
        'IMPORTANT': 25
    }

    def log_func(self, message, *args, **kwargs):
        if self.isEnabledFor(new_levels.get(message.upper(), 0)):
            self._log(new_levels.get(message.upper(), 0), message, args, **kwargs)

    for level, value in new_levels.items():
        logging.addLevelName(value, level)
        setattr(logging.Logger, level.lower(), log_func)
        setattr(logging.LoggerAdapter, level.lower(), log_func)


def logging_setup():
    add_log_levels()
    logging.config.dictConfig(dictconfig)

class CustomFormatter(logging.Formatter):
    COLORS = {
        'TRACE': '\033[90m',    # Gray
        'DEBUG': '\033[94m',    # Blue
        'VERBOSE': '\033[96m',  # Cyan
        'INFO': '\033[92m',     # Green
        'IMPORTANT': '\033[93m',  # Yellow
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m'  # Magenta
    }

    RESET_COLOR = '\033[0m'  # Reset color to default

    def __init__(self, fmt=None, datefmt=None, style='%'):
        if fmt is None:
            fmt = '%(asctime)s - %(name)25s - %(funcName)25s - %(message)s'
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        # Check if a custom funcName is provided in the log record
        custom_funcName = getattr(record, 'custom_funcName', None)

        # Use custom_funcName if provided, otherwise use the default funcName
        record.funcName = custom_funcName or record.funcName

        log_message = super().format(record)
        level_name = record.levelname

        if level_name in self.COLORS:
            colored_message = f"{self.COLORS[level_name]}{log_message}{self.RESET_COLOR}"
            return colored_message
        else:
            return log_message


class CustomHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()


class CustomLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)
        self.info("Initializing custom logger ({}).".format(name))


dictconfig = {
    "version": 1,
    "disable_existing_loggers": "True",
    "formatters": {
        'custom_formatter': {
                '()': 'src.custom_logging.CustomFormatter',
            },
    },
    "handlers": {
        "console": {
            "level": "TRACE",
            'class': 'src.custom_logging.CustomHandler',
            'formatter': 'custom_formatter'
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "custom_formatter",
            "filename": f"{Path(__file__).parent.parent}/logs/application.log",
            "backupCount": 1,
            "maxBytes": 1048576,
            "encoding": "UTF8"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "TRACE",
            "propagate": 0
        },
        "src.direct_plus": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": 0
        },
        "src.session": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": 0
        },
        "src.request": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": 0
        },
        "urllib3.connectionpool": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": 0
        },
    }
}



