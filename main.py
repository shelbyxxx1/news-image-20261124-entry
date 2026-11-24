"""Copy the committed entry.png into the configured output directory.

Standard library only: the grader runs a bare Python image, so this
entrypoint imports nothing beyond os, shutil and pathlib.
"""

import os
import shutil
from pathlib import Path


def main() -> int:
    out = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    # Never remove or replace the output directory itself: on the grader
    # it is a mount point. Only create it when it is missing.
    os.makedirs(out, exist_ok=True)
    src = Path(__file__).resolve().parent / "entry.png"
    dest = Path(out) / "entry.png"
    shutil.copyfile(src, dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
