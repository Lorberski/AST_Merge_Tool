#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path


def run_test(test_folder):
    test_folder = Path(test_folder)

    base_file = test_folder / "base.py"
    local_file = test_folder / "local.py"
    remote_file = test_folder / "remote.py"
    merged_file = test_folder / "merged_output.py"

    # Check that all required files exist
    for f in [base_file, local_file, remote_file]:
        if not f.exists():
            print(f"[ERROR] Missing file: {f}")
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

    print(f"Running test in {test_folder.name}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    print(result.stdout)
    if result.returncode != 0:
        print("[FAIL] Merge tool returned an error")
        print(result.stderr)
        return False

    print(f"[OK] Merged file created: {merged_file}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ast_test_script.py <test_folder>")
        sys.exit(1)

    test_folder = sys.argv[1]
    success = run_test(test_folder)

    if not success:
        sys.exit(1)
