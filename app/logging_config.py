import logging
import sys


def configure_logging(*, debug: bool = False) -> None:
    """Configure application-wide console logging."""

    log_level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    logging.getLogger("aiogram").setLevel(logging.DEBUG if debug else logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if debug else logging.WARNING,
    )
