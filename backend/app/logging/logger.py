import logging
import os
import sys

from pythonjsonlogger import jsonlogger


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured application logs.
    """

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record["timestamp"] = self.formatTime(
            record,
            self.datefmt,
        )

        log_record["level"] = record.levelname

        log_record["logger"] = record.name


handler = logging.StreamHandler(sys.stdout)

formatter = CustomJsonFormatter()

handler.setFormatter(formatter)

logger = logging.getLogger("enterprise-ai")

logger.handlers.clear()

logger.addHandler(handler)

logger.setLevel(LOG_LEVEL)

logger.propagate = False