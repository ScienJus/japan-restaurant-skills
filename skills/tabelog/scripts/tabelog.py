#!/usr/bin/env python3
"""Source-tree launcher. Installed entry point: tabelog."""
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Python >=3.10 required; install Python 3.12+ and run pip install -e . in a venv.")

try:
    from client.cli import main
except ModuleNotFoundError as error:
    raise SystemExit(f"Missing dependency {error.name}; install this project: python -m pip install -e .") from None

raise SystemExit(main())
