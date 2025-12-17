import logging
import sys
import os

# --- Create Logs directory ---
os.makedirs("Logs", exist_ok=True)

# --- Define custom MERGE level ---
MERGE_LEVEL_NUM = 25  # between INFO(20) and WARNING(30)
logging.addLevelName(MERGE_LEVEL_NUM, "MERGE")


def merge(self, message, *args, **kwargs):
    """Add .merge() method to logger."""
    if self.isEnabledFor(MERGE_LEVEL_NUM):
        self._log(MERGE_LEVEL_NUM, message, args, **kwargs)


logging.Logger.merge = merge

# --- Create central logger ---
logger = logging.getLogger("merge_tool")
logger.setLevel(logging.DEBUG)  # capture all logs

# --- Remove any existing handlers to prevent duplicates ---
if logger.hasHandlers():
    logger.handlers.clear()

# --- Single FileHandler for all logs ---
log_file_path = os.path.join("Logs", "merge_tool.log")
file_handler = logging.FileHandler(
    log_file_path, mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)  # capture all levels
file_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# --- ConsoleHandler for live ERROR/MERGE logs ---
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.ERROR)  # only ERROR and above to console
console_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)
