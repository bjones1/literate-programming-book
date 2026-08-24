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
# # `warmup_truncate.py` - a test harness for the string translation warmup exercise
#
# Warm-up: run one under-specified function against eight probes. To run it,
# click this tab and then click **Run** (or press `Ctrl + Enter`). The Run
# button executes whichever Python file you last had selected, so if you see
# output about a missing `solution.py`, you ran the wrong file.
#
# Every student wrote the same sentence. The fingerprint at the bottom shows how
# many different programs that sentence produced. Compare fingerprints across the
# room before anyone explains anything.
#
# ## Imports
# ### Standard library
from __future__ import annotations
import hashlib
import inspect
import sys
import unicodedata
from pathlib import Path

# ## Code
sys.path.insert(0, str(Path(__file__).parent))

try:
    from my_truncate import truncate
except ImportError as exc:  # noqa: BLE001
    raise SystemExit(
        f"Could not import truncate from my_truncate.py ({exc}).\n"
        "Paste the LLM's code there, and alias it if it has another name."
    ) from exc

ZWJ = "‍"
# One grapheme, seven code points, twenty-five bytes.
FAMILY = ZWJ.join(["\N{MAN}", "\N{WOMAN}", "\N{GIRL}", "\N{BOY}"])

PROBES: list[tuple[str, object, str]] = [
    (
        "short input",
        "Hello, world.",
        "Does a short string come back untouched, or get an ellipsis anyway?",
    ),
    (
        "exactly 100 chars",
        "x" * 100,
        "Is the limit inclusive? Truncated or untouched?",
    ),
    (
        "101 chars",
        "y" * 101,
        "Is the result 100, 101, or 103 characters? Does the ellipsis "
        "count toward the limit?",
    ),
    (
        "prose, cut mid-word",
        "The quick brown fox jumps over the lazy dog while the "
        "quick brown fox contemplates the nature of specification. " * 3,
        "Break mid-word, or back up to a word boundary?",
    ),
    (
        "whitespace at the cut",
        "z" * 96 + "     " + "trailing content here",
        "Is trailing whitespace stripped before the ellipsis is appended?",
    ),
    (
        "family emoji",
        FAMILY * 30,
        "Is a 'character' a byte, a code point, or a grapheme? Watch a "
        "four-person family become strangers.",
    ),
    ("empty string", "", "Empty out, or a lone ellipsis?"),
    ("None", None, "Crash, empty string, or passthrough?"),
]


def call(value):
    """Call the student's truncate with whatever signature it happens to have."""
    params = list(inspect.signature(truncate).parameters.values())
    unfilled = [p for p in params[1:] if p.default is inspect.Parameter.empty]
    positional = [
        p
        for p in unfilled
        if p.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    # An LLM that made the limit keyword-only would otherwise raise TypeError
    # here, and the student would read the harness's gap as their own mistake.
    keyword = {
        p.name: 100 for p in unfilled if p.kind is inspect.Parameter.KEYWORD_ONLY
    }
    return truncate(value, *(100 for _ in positional), **keyword)


def measure(result) -> str:
    if not isinstance(result, str):
        return f"type={type(result).__name__}"
    # Approximate grapheme clusters: a combining mark, a ZWJ, and whatever
    # follows a ZWJ all continue the cluster already in progress instead of
    # starting a new one. Rough, but enough to show that a four-person family
    # is one character rather than four.
    graphemes = 0
    previous = ""
    for ch in result:
        if unicodedata.combining(ch) or ch == ZWJ or previous == ZWJ:
            previous = ch
            continue
        graphemes += 1
        previous = ch
    return (
        f"{len(result):>4} code points, {len(result.encode('utf-8')):>4} bytes, "
        f"~{graphemes:>4} graphemes"
    )


def preview(result) -> str:
    if not isinstance(result, str):
        return repr(result)
    if len(result) <= 46:
        return repr(result)
    return repr(result[:24]) + " ... " + repr(result[-18:])


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    print()
    print("=" * 78)
    print("  WARM-UP: one sentence, eight questions you did not know you answered")
    print("=" * 78)

    digest = hashlib.sha256()

    for label, value, question in PROBES:
        print(f"\n-- {label} " + "-" * (72 - len(label)))
        print(f"   {question}")
        try:
            result = call(value)
        except Exception as exc:  # noqa: BLE001
            outcome = f"RAISED {type(exc).__name__}: {exc}"
            print(f"   result: {outcome}")
        else:
            outcome = f"{type(result).__name__}:{result!r}"
            print(f"   result: {preview(result)}")
            print(f"   size:   {measure(result)}")
        digest.update(outcome.encode("utf-8", "replace"))

    print()
    print("=" * 78)
    print(f"  FINGERPRINT: {digest.hexdigest()[:8]}")
    print("=" * 78)
    print(
        "\n  Compare with the person next to you. Same prompt, same model,\n"
        "  different program. Which of the eight answers did you intend,\n"
        "  and which did the model pick for you?\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
