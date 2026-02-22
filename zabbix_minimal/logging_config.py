import logging
import sys


def setup_logging(level=logging.INFO, log_to_file=True):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    """ Console handler """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    """ File handler (optional) """
    if log_to_file:
        file_handler = logging.FileHandler("zabbix.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)