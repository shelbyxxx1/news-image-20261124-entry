"""Entrypoint: place the committed front page at the grader's output path.

The grader runs a bare Python 3.13 image with no third-party packages, so
this file sticks to the standard library. It copies the entry.png that ships
in this repository into the output directory and nothing else.
"""

import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "entry.png"


def output_dir():
    """The grader's output mount, or /output when nothing names another."""
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")


def main():
    target_dir = output_dir()
    # The output directory is a mount point on the grader: create it when it
    # is missing, but never remove or replace the directory itself.
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "entry.png"
    shutil.copyfile(SOURCE, target)
    print(f"entry.png -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
