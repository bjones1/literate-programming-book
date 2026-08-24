# Copyright (C) 2026 Bryan A. Jones.
#
# This file is part of the Literate Programming Book.
#
# The Literate Programming Book is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# The Literate Programming Book is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a [copy](../../LICENSE.md) of the GNU General Public
# License along with the Literate Programming Book. If not,
# see [https://www.gnu.org/licenses/](https://www.gnu.org/licenses/).
#
# # `run_tests.py` - run every pytest file in this folder
#
# Python Online has no command line for you to type `pytest` into, so this file
# is the command line. Click this tab, then click **Run** (or press
# `Ctrl + Enter`). The Run button executes whichever Python file you last had
# **selected**, so if you see output from a different exercise, you ran the
# wrong file.
#
# It hands this folder to pytest and lets pytest discover what to run, so there
# is nothing to edit here when a new test file arrives.
#
# If the run feels slow, it is not your tests. Importing pytest pulls in a bit
# over two hundred modules before a single assertion runs, and a browser IDE
# reads those off a network-backed disk. Set `TIMING = True` below to see the
# split between startup and your actual tests.
#
# ## Imports
# ### Standard library
from __future__ import annotations
import os
import sys
import time
from pathlib import Path

# ## Configuration
#
# Flip `VERBOSE` to `True` when you want one line per test — which case failed,
# by name — rather than just a row of dots and a score.
VERBOSE = False

# Flip `TIMING` to `True` to print how long the import, the collection, and the
# tests each took. Useful exactly once, to confirm that the wait is startup
# rather than anything you wrote.
TIMING = False

# ## Code
#
# `Path(__file__).parent` rather than `os.getcwd()`: the web IDE does not
# promise which directory it launches you from, but it does put this file next
# to the tests.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def main() -> int:
    # The probes print emoji. A console that cannot encode them should show a
    # replacement character, not kill the run with a UnicodeEncodeError.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    # Read before pytest builds its plugin manager: without it, pytest walks the
    # metadata of every installed distribution looking for `pytest11` entry
    # points and imports each plugin it finds. Nothing here needs a plugin, and
    # on a slow filesystem that scan is pure wait.
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    started = time.perf_counter()
    try:
        import pytest
    except ImportError:
        print(
            "\n"
            + "=" * 70
            + "\npytest is not installed in this project.\n"
            "Open the PACKAGES panel in the left sidebar, search for `pytest`,\n"
            "and click Install. Packages are per-project, so you do this once.\n"
            + "=" * 70
            + "\n"
        )
        return 1

    # pytest resolves `conftest.py`, its rootdir, and any relative path it
    # prints against the working directory, so move there first and then let it
    # discover the tests itself.
    os.chdir(HERE)
    # `no:cacheprovider` keeps pytest from writing a `.pytest_cache` folder into
    # your project tree, which the Explorer would then show you forever.
    args = [str(HERE), "-p", "no:cacheprovider"]
    args += ["-v"] if VERBOSE else ["-q", "--no-header", "--tb=short"]

    imported = time.perf_counter()
    code = pytest.main(args)
    finished = time.perf_counter()

    if TIMING:
        print()
        print(f"import pytest:  {imported - started:5.2f}s")
        print(f"collect + run: {finished - imported:5.2f}s")
        print(
            "The `in Ns` figure in pytest's own summary line above is what"
            " your tests alone cost."
        )
        print()

    if code == pytest.ExitCode.NO_TESTS_COLLECTED:
        print(
            "\n"
            + "=" * 70
            + f"\nNo tests found in {HERE.name}/.\n"
            "pytest collects files named `test_*.py` or `*_test.py`, and inside\n"
            "them, functions named `test_*`. Check the EXPLORER panel: the\n"
            "starter files may not have finished importing.\n"
            + "=" * 70
            + "\n"
        )
    elif code != pytest.ExitCode.OK and not VERBOSE:
        print(
            "\nSet VERBOSE = True at the top of this file and run it again to\n"
            "see which named case each failure belongs to.\n"
        )
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
