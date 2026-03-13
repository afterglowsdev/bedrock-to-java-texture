#!/usr/bin/env python3
"""Build Windows EXE via PyInstaller (includes vendor dependencies)."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEP = ";" if platform.system().lower().startswith("win") else ":"


def main() -> None:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name",
        "bedrock_to_java_converter",
        f"--add-data=vendor{SEP}vendor",
        "convert_mcpack_gui.py",
    ]
    subprocess.check_call(cmd, cwd=ROOT)


if __name__ == "__main__":
    main()
