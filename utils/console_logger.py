import logging
import os
from logging.handlers import TimedRotatingFileHandler


def setup_logger():
    os.makedirs('logs', exist_ok=True)

    logger_setup = logging.getLogger()
    logger_setup.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger_setup.addHandler(console_handler)

    latest_handler = logging.FileHandler('logs/latest.log', mode='w', encoding='utf-8')
    latest_handler.setFormatter(formatter)
    logger_setup.addHandler(latest_handler)

    daily_handler = TimedRotatingFileHandler(
        'logs/daily.log',
        when="midnight",
        backupCount=7,
        encoding='utf-8'
    )
    daily_handler.setFormatter(formatter)
    daily_handler.namer = lambda name: name.replace("daily.log.", "") + ".log"
    logger_setup.addHandler(daily_handler)

    return logger_setup
