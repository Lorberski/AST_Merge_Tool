import logging
import sys
import os

# --- Create Logs directory ---
os.makedirs("Logs", exist_ok=True)

# --- Define custom MERGE level ---
MERGE_LEVEL_NUM = 25  # between INFO(20) and WARNING(30)
logging.addLevelName(MERGE_LEVEL_NUM, "MERGE")


def merge(self, message, *args, **kwargs):
    if self.isEnabledFor(MERGE_LEVEL_NUM):
        self._log(MERGE_LEVEL_NUM, message, args, **kwargs)


# Add 'merge' method to all loggers
logging.Logger.merge = merge

# --- Create central logger ---
logger = logging.getLogger("merge_tool")
logger.setLevel(logging.DEBUG)  # capture all logs

# --- Avoid adding handlers multiple times ---
if not logger.handlers:
    # --- FileHandler: all logs, append mode, no filter ---
    file_handler = logging.FileHandler(os.path.join(
        "Logs", "merge_tool.log"), mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # alles ab DEBUG-Level
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # --- Console: only errors ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # --- FileHandler: only MERGE logs, append mode ---
    merge_file_handler = logging.FileHandler(os.path.join(
        "Logs", "merge_only.log"), mode="a", encoding="utf-8")
    # alle Logs, Filter sorgt für MERGE-only
    merge_file_handler.setLevel(logging.DEBUG)
    merge_file_handler.addFilter(
        lambda record: record.levelno == MERGE_LEVEL_NUM)
    merge_file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s")
    merge_file_handler.setFormatter(merge_file_formatter)
    logger.addHandler(merge_file_handler)
