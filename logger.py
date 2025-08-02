import logging
import sys


def get_logger(name: str = "shiftwise"):
    logger = logging.getLogger(name)

    if not logger.handlers:  # Prevent duplicate handlers if called multiple times
        logger.setLevel(logging.DEBUG)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Log Format
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger
