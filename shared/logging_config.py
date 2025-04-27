import logging
import os
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(service_name: str):
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format_type = os.getenv("LOG_FORMAT", "JSON").upper()

    logger.remove()

    if log_format_type == "JSON":
        logger.add(
            sys.stdout,
            level=log_level,
            format="{message}",
            serialize=True,
            enqueue=True,
            backtrace=True,
            diagnose=False
        )
        logger.configure(extra={"service_name": service_name})
    else:
        logger.add(
            sys.stderr,
            level=log_level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                f"<cyan>{service_name: <15}</cyan> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
            ),
            colorize=True,
            enqueue=True,
            backtrace=True,
            diagnose=(log_level == "DEBUG")
        )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for name in logging.root.manager.loggerDict:
        current_logger = logging.getLogger(name)
        current_logger.handlers = [InterceptHandler()]
        current_logger.propagate = False

    logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Logging setup complete. Service: {service_name}, Level: {log_level}, Format: {log_format_type}")
