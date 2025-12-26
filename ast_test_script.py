#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
from log_config import logger


def run_test(test_folder):
    test_folder = Path(test_folder)

    base_file = test_folder / "base.py"
    local_file = test_folder / "local.py"
    remote_file = test_folder / "remote.py"
    merged_file = test_folder / "merged_output.py"

    # Check that all required files exist
    for f in [base_file, local_file, remote_file]:
        if not f.exists():
            logger.error(f"Missing file: {f}")
            return False

    # Call the merge tool
    cmd = [
        "python3",
        "ast_merge_tool.py",
        str(base_file),
        str(local_file),
        str(remote_file),
        str(merged_file)
    ]

    logger.info(f"--- Running test with: {test_folder.name} ---")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("[FAIL] Merge tool returned an error")
        return False

    logger.info(f"[OK] Merged file created: {merged_file}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.error("Usage: python ast_test_script.py <test_folder>")

        sys.exit(1)
    test_folder = sys.argv[1]
    success = run_test(test_folder)

    if not success:
        sys.exit(1)
