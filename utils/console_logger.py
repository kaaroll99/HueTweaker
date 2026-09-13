import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

import discord
from colorlog import ColoredFormatter


class PlainFormatter(logging.Formatter):
    """Ignores the traceback cached on the record by the colored console formatter."""

    def format(self, record: logging.LogRecord) -> str:
        record = logging.makeLogRecord(record.__dict__)
        record.exc_text = None
        return super().format(record)


MISSING_PERMISSIONS_CODE = 50013
ROUTINE_MESSAGE_PREFIXES = ('Attempting a reconnect for shard ID',)


def _is_missing_permissions(value) -> bool:
    return isinstance(value, discord.Forbidden) and value.code == MISSING_PERMISSIONS_CODE


def _is_routine_error(record: logging.LogRecord) -> bool:
    """Expected failures (Missing Permissions, shard reconnects) that shouldn't be reported as errors."""
    if record.exc_info and _is_missing_permissions(record.exc_info[1]):
        return True
    args = record.args if isinstance(record.args, tuple) else (record.args,)
    if any(_is_missing_permissions(arg) for arg in args):
        return True
    message = str(record.msg)
    if message.startswith(ROUTINE_MESSAGE_PREFIXES):
        return True
    try:
        return f"error code: {MISSING_PERMISSIONS_CODE}" in record.getMessage() or "Missing Permissions" in record.getMessage()
    except Exception:
        return False


def install_downgrade_factory() -> None:
    """Create ERROR/CRITICAL records for routine failures as WARNING, for every logger and handler."""
    base_factory = logging.getLogRecordFactory()
    if getattr(base_factory, "_downgrades_routine_errors", False):
        return

    def factory(*args, **kwargs) -> logging.LogRecord:
        record = base_factory(*args, **kwargs)
        if isinstance(record.levelno, int) and record.levelno >= logging.ERROR and _is_routine_error(record):
            record.levelno = logging.WARNING
            record.levelname = logging.getLevelName(logging.WARNING)
        return record

    factory._downgrades_routine_errors = True
    logging.setLogRecordFactory(factory)


class ErrorFileHandler(logging.Handler):
    """Writes every ERROR record (with its traceback) to its own file."""

    def __init__(self, directory: str):
        super().__init__(level=logging.ERROR)
        self.directory = directory
        self.addFilter(lambda record: record.levelno == logging.ERROR)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            text = self.format(record)
            stamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d_%H-%M-%S-%f")
            base = f"{stamp}_{record.name}"
            counter = 0
            while True:
                suffix = f"_{counter}" if counter else ""
                path = os.path.join(self.directory, f"{base}{suffix}.log")
                try:
                    with open(path, "x", encoding="utf-8") as f:
                        f.write(text + "\n")
                    break
                except FileExistsError:
                    counter += 1
        except Exception:
            self.handleError(record)


def setup_logger():
    log_dir = 'logs'
    history_dir = os.path.join(log_dir, 'history')
    errors_dir = os.path.join(log_dir, 'errors')
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)
    os.makedirs(errors_dir, exist_ok=True)

    logger_setup = logging.getLogger()

    if not logger_setup.handlers:
        logger_setup.setLevel(logging.INFO)

        color_formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(log_color)s%(levelname)s%(reset)s - %(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'blue',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(color_formatter)
        logger_setup.addHandler(console_handler)

        file_formatter = PlainFormatter(
            (
                "%(asctime)sZ %(levelname)s %(name)s [pid=%(process)d tid=%(thread)d] %(module)s:%(lineno)d - %(message)s"
            )
        )
        file_path = os.path.join(log_dir, 'app.log')
        file_handler = TimedRotatingFileHandler(
            file_path,
            when="midnight",
            backupCount=7,
            encoding='utf-8',
            utc=False,
        )

        base_name = os.path.basename(file_path)
        root, ext = os.path.splitext(base_name)

        def namer(default_name: str) -> str:
            date_part = default_name.split(base_name + '.', 1)[-1]
            return os.path.join(history_dir, f"{date_part}{ext}")

        def rotator(source: str, dest: str) -> None:
            os.replace(source, dest)

        file_handler.namer = namer
        file_handler.rotator = rotator
        file_handler.setFormatter(file_formatter)
        logger_setup.addHandler(file_handler)

        error_handler = ErrorFileHandler(errors_dir)
        error_handler.setFormatter(file_formatter)
        logger_setup.addHandler(error_handler)

    install_downgrade_factory()

    return logger_setup
