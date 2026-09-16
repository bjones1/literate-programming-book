# ***********************************************
# |docname| - Utilities for running build commands
# ***********************************************
# A trimmed copy of ``ci_utils.py`` from the `CodeChat System
# <https://github.com/bjones1/CodeChat_system/blob/master/CodeChat_Server/tests/ci_utils.py>`_,
# carrying only what `pre_commit_check.py` needs.
#
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# .. _PEP 8: https://peps.python.org/pep-0008/#imports
#
# Standard library
# ----------------
import os
import os.path
import subprocess
import sys
from typing import Any, List, Literal, Union

# Platform detection
# ==================
is_win = sys.platform == "win32"
is_linux = sys.platform.startswith("linux")
is_darwin = sys.platform == "darwin"
is_64bits = sys.maxsize > 2**32


# Utilities
# =========
def flush_print(*args: Any, **kwargs: Any) -> None:
    print(*args, **kwargs)
    # Flush both buffers, just in case there's something in ``stdout``.
    sys.stdout.flush()
    sys.stderr.flush()


def xqt(
    *cmds: str, **kwargs: Any
) -> Union[subprocess.CompletedProcess, List[subprocess.CompletedProcess]]:
    # eXecute each command in a shell, raising on the first failure.
    ret = []
    for _ in cmds:
        flush_print(_)
        executable = "/bin/bash" if is_linux or is_darwin else None
        try:
            cp = subprocess.run(
                _, shell=True, executable=executable, check=True, **kwargs  # type: ignore
            )
        except subprocess.CalledProcessError as e:
            flush_print(
                "Subprocess output:\n{}\n{}".format(e.stderr or "", e.stdout or "")
            )
            raise
        ret.append(cp)

    return ret[0] if len(ret) == 1 else ret


class pushd:
    # A context manager that changes to ``path``, then back again on exit.
    def __init__(
        self,
        path: str,
    ):
        self.path = path

    def __enter__(self) -> None:
        flush_print("pushd {}".format(self.path))
        self.cwd = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, type_: Any, value: Any, traceback: Any) -> Literal[False]:
        flush_print("popd - returning to {}.".format(self.cwd))
        os.chdir(self.cwd)
        return False
