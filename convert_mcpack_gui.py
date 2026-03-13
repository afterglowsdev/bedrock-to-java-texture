#!/usr/bin/env python3
"""GUI entrypoint for Bedrock -> Java converter."""

from convert_mcpack import run_gui, setup_logging


def main() -> None:
    setup_logging(False)
    run_gui()


if __name__ == "__main__":
    main()
