"""Get logger instance and logging functions."""

import datetime
from logging import INFO, FileHandler, Formatter, Logger, StreamHandler, getLogger
from pathlib import Path
from traceback import print_exc


def logger_instance() -> Logger:
    """Get logger instance.

    Returns:
        Logger: Logger instance.
    """
    logger = getLogger(name=None)
    logger.setLevel(level=INFO)

    if not logger.hasHandlers():
        format_txt = "%(levelname)-9s | %(asctime)s | %(filename)s:l.%(lineno)d:%(module)s:%(funcName)s | %(message)s"
        st_handler = StreamHandler(stream=None)
        st_handler.setLevel(INFO)
        st_handler.setFormatter(Formatter(format_txt))
        logger.addHandler(st_handler)

        log_path = Path(__file__).resolve().parent / "log_file.log"
        log_path.touch(exist_ok=True)
        fl_handler = FileHandler(
            filename=log_path, mode="a", encoding="utf-8", delay=False, errors=None
        )
        fl_handler.setLevel(INFO)
        fl_handler.setFormatter(Formatter(format_txt))

        # add handler
        logger.addHandler(fl_handler)

        logger.debug(msg="called logger_instance")
    return logger


def save_traceback() -> None:
    """Save traceback texts."""
    print_exc()
    with (Path(__file__).resolve().parent / "log_print_exc.log").open(mode="a") as f:
        print(f"{datetime.datetime.now()}", file=f)
        print_exc(limit=None, file=f)
        print("", file=f)
