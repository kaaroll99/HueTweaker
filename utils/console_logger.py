import logging
import os
from logging.handlers import TimedRotatingFileHandler

from colorlog import ColoredFormatter


def setup_logger():
    log_dir = 'logs'
    history_dir = os.path.join(log_dir, 'history')
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)

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

        file_formatter = logging.Formatter(
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

    return logger_setup
