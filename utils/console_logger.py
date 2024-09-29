import logging
import os
from logging.handlers import TimedRotatingFileHandler
from colorlog import ColoredFormatter

def setup_logger():
    os.makedirs('logs', exist_ok=True)

    logger_setup = logging.getLogger()

    if not logger_setup.handlers:
        logger_setup.setLevel(logging.INFO)

        # Kolorowy formatter dla konsoli, tylko dla levelname
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

        # Zwykły formatter dla plików
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(color_formatter)
        logger_setup.addHandler(console_handler)

        latest_handler = logging.FileHandler('logs/latest.log', mode='w', encoding='utf-8')
        latest_handler.setFormatter(file_formatter)
        logger_setup.addHandler(latest_handler)

        daily_handler = TimedRotatingFileHandler(
            'logs/latest.log',
            when="midnight",
            backupCount=7,
            encoding='utf-8'
        )
        daily_handler.setFormatter(file_formatter)
        daily_handler.namer = lambda name: name.replace("latest.log.", "") + ".log"
        logger_setup.addHandler(daily_handler)

    return logger_setup