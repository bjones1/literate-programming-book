#!/usr/bin/env python3
# ****************************************************************************************
# |docname| - Run a series of checks that should all pass before submitting a pull request
# ****************************************************************************************
# In a perfect world, these would also pass before every commit.
#
# Run this from the directory containing ``pyproject.toml``::
#
#   uv run python tests/pre_commit_check.py
#
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
import os.path
import sys

# Third-party imports
# -------------------
# None.
#
# Local application imports
# -------------------------
sys.path.insert(0, os.path.dirname(__file__))
from ci_utils import pushd, xqt  # noqa: E402


# Checks
# ======
def checks() -> None:
    # Every check runs from the project root, which is where ``pyproject.toml``
    # and the tool configuration files live.
    with pushd(os.path.join(os.path.dirname(__file__), "..")):
        xqt(
            "ruff format --check .",
            "ruff check .",
            "ty check",
            "pytest",
        )


if __name__ == "__main__":
    checks()
