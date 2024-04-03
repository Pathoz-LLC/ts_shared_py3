import logging
from logging import getLogger, Logger


class _PrintHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        print(msg)


def createLogger(name: str, *, level: int = logging.INFO) -> Logger:

    # Configure the logger
    log: Logger = getLogger(name)
    log.setLevel(logging.INFO)

    # Create and add the custom handler
    print_handler = _PrintHandler()
    print_handler.setLevel(level)
    log.addHandler(print_handler)

    # Optionally, set a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    print_handler.setFormatter(formatter)

    return log
