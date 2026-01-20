import logging

import os
logger = logging.getLogger(__name__)

# Log file output
logger.setLevel(logging.DEBUG)
logger.propagate = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "Logs")
os.makedirs(LOG_DIR, exist_ok=True)

# --- Debug + alles ---
debug_log_path = os.path.join(LOG_DIR, "merge_tool.log")
debug_handler = logging.FileHandler(debug_log_path, mode="a", encoding="utf-8")
debug_handler.setLevel(logging.DEBUG)

# --- Info-only Log ---
info_log_path = os.path.join(LOG_DIR, "only_info_merge_tool.log")
info_handler = logging.FileHandler(info_log_path, mode="a", encoding="utf-8")
info_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
debug_handler.setFormatter(formatter)
info_handler.setFormatter(formatter)

logger.addHandler(debug_handler)
logger.addHandler(info_handler)

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
