import logging

import os
logger = logging.getLogger(__name__)

# Log file output
logger.setLevel(logging.DEBUG)
logger.propagate = True
os.makedirs("Logs", exist_ok=True)
log_file_path = os.path.join("Logs", "merge_tool.log")
file_handler = logging.FileHandler(
    log_file_path, mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Custom log level
MERGE_LEVEL_NUM = 25
logging.addLevelName(MERGE_LEVEL_NUM, "MERGE")


def merge(self, message, *args, **kwargs):
    """Add .merge() method to logger."""
    if self.isEnabledFor(MERGE_LEVEL_NUM):
        self._log(MERGE_LEVEL_NUM, message, args, **kwargs)


logging.Logger.merge = merge


# Console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

console_formatter = logging.Formatter(
    "%(levelname)s: %(message)s"
)
console_handler.setFormatter(console_formatter)

logger.addHandler(console_handler)


def multiline_debug_log(multiline_string: str) -> None:
    for line in multiline_string.splitlines(keepends=False):
        logger.debug(line if line else "")
