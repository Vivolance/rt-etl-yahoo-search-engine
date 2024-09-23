import logging


def setup_logger(logger: logging.Logger) -> None:
    formatter: logging.Formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    handler: logging.Handler = logging.FileHandler("logs.txt")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
