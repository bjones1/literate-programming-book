#!/usr/bin/env python3
# Copyright (C) 2026 Bryan A. Jones.
#
# This file is part of the literate programming book.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see
# [http://www.gnu.org/licenses/](http://www.gnu.org/licenses/).
#
# `git_homework.py` -- grade the Git branch-and-merge homework
# ============================================================
#
# This implements the "Git homework grader" section of `chat_grader.md`: given
# a range of dates, find every userid which worked in the class repository
# during it and decide, for each, whether the student
#
# 1.  created a branch named after their userid,
# 2.  committed two files to it, and
# 3.  merged someone else's branch into `main` with the required commit
#     message,
#
# then write one CSV row per student holding the grade and the filled-in
# rubric, which is the feedback. There is no roster: the students are whoever
# the repository says they are between those dates, so grading a term takes its
# dates and nothing else. The dates decide only who is graded, not what they
# score: once found, a student is graded on everything they pushed.
#
# Every question is answered from a mirror clone of the class repository, made
# once and thereafter kept current, so a run costs one network round trip no
# matter how many students are graded. The class repository is public, so no
# authentication is involved.
"""Grade the Git branch-and-merge homework from the class repository.

See README.md in this directory for setup and usage.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from itertools import takewhile
from pathlib import Path
from typing import Annotated, Optional, Sequence

try:
    import typer
except ModuleNotFoundError as exc:  # pragma: no cover - setup guidance only.
    sys.exit(
        f"Missing dependency {exc.name!r}. Install this project's dependencies "
        "first:\n    uv sync"
    )


# Configuration
# -------------
#
# The repository the homework is done in.
DEFAULT_REPO = "https://github.com/bjones1/literate-programming-git-2026"

# The window of time which decides who is graded has no default start: a term
# is graded by naming it. Its last day, inclusive, may be left empty, meaning
# the window has no end: grade everyone who worked since the start date.
DEFAULT_UNTIL = ""

# One day. `--until` names a whole day, which counts in full; the window
# compares against the instant that day ends.
DAY = timedelta(days=1)

# The rubric. These three lines are both the scoring and, with their blanks
# filled in, the feedback a student reads, so they are kept short; the rules
# for applying them live in the functions below.
RUBRIC = (
    "{points}/30 points -- Branch created with your userid. Commit hash: {hashes}",
    "{points}/30 points (15 points per file) -- Two files committed to this "
    "branch. Commit hash(es): {hashes}",
    "{points}/40 points -- At least one merge commit exists with the correct "
    "commit message. Commit hash: {hashes}",
)

# The merge message the third rubric line asks for. It is matched against what
# a student wrote, and read backwards to recover the userid which wrote it.
MERGE_SUBJECT = "{userid}: merge branch with main"

# Branch names which belong to the repository rather than to a student. No
# userid is read from one.
MAIN_NAMES = ("main", "master")

# How many blanks each rubric line has to fill, and what each line is worth.
BLANKS = (1, 2, 1)
BRANCH_POINTS = 30
MERGE_POINTS = 40

# The second rubric line is scored per file, up to two files.
PER_FILE = 15
FILES_WANTED = 2

# What a blank reads when the work it names was not found.
MISSING = "not found"

# Commit hashes are abbreviated to this many characters in the feedback: long
# enough to be unambiguous in a class repository, short enough to retype.
SHORT = 8

# Separates the commits of a `git log` whose output is otherwise line-based,
# and the fields within one such commit. Both are ASCII separators which cannot
# appear in a path or a commit message written by a person.
RECORD = "\x1e"
FIELD = "\x1f"


# Running git
# -----------
def _git(*args: str, verbose: bool = False) -> str:
    """Run git, returning its standard output and stopping the run if it
    fails."""
    if verbose:
        print("  git " + " ".join(args), file=sys.stderr)
    try:
        result = subprocess.run(
            ["git", *args], capture_output=True, text=True, encoding="utf-8"
        )
    except FileNotFoundError:  # pragma: no cover - depends on the machine.
        sys.exit("git is not on the PATH. Install it, then run this again.")
    if result.returncode:
        sys.exit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


class Repo:
    """One mirror clone of the class repository, and the handful of questions
    the rubric asks of it. A mirror clone holds every branch under
    ``refs/heads``, which is exactly what the rubric asks about, so every
    answer below is computed locally."""

    def __init__(self, git_dir: Path, verbose: bool = False) -> None:
        self.git_dir = git_dir
        self.verbose = verbose

    def out(self, *args: str) -> str:
        """The standard output of a git command run against this clone."""
        return _git("--git-dir", str(self.git_dir), *args, verbose=self.verbose)

    def _status(self, *args: str) -> int:
        """The exit status of a git command run against this clone. Used for
        the questions git answers by succeeding or failing rather than by
        printing."""
        return subprocess.run(
            ["git", "--git-dir", str(self.git_dir), *args],
            capture_output=True,
            text=True,
        ).returncode

    def has_ref(self, ref: str) -> bool:
        """Does this reference exist?"""
        return self._status("rev-parse", "--verify", "-q", ref) == 0

    def reaches(self, tip: str, commit: str) -> bool:
        """Can `tip` reach `commit`?"""
        status = self._status("merge-base", "--is-ancestor", commit, tip)
        if status > 1:  # pragma: no cover - a malformed repository.
            sys.exit(f"git merge-base --is-ancestor {commit} {tip} failed.")
        return status == 0

    def commits(self, *args: str) -> set[str]:
        """The commits a ``git rev-list`` selects, as a set of hashes."""
        return set(self.out("rev-list", *args).split())


def mirror(url: str, path: Path, verbose: bool = False) -> Repo:
    """Clone the class repository, or bring an existing clone up to date, and
    return it. Keeping the clone between runs turns every later run into a
    single fetch."""
    if (path / "HEAD").exists():
        _git("--git-dir", str(path), "remote", "update", "--prune", verbose=verbose)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        _git("clone", "--mirror", url, str(path), verbose=verbose)
    return Repo(path, verbose)


# Reading the repository
# ----------------------
@dataclass(frozen=True)
class Window:
    """The stretch of time which decides who is graded: from `start`,
    inclusive, to `end`, exclusive, or with no end at all when `end` is
    `None`.

    Since the userids are read from the repository rather than from a roster,
    the window is what says who they are: everyone with a branch tip or a
    rubric merge inside it. It says nothing about what they score -- a student,
    once found, is graded on everything they pushed -- save that the year it
    opens in is the year whose commits count as theirs.
    """

    start: datetime
    end: Optional[datetime] = None

    def holds(self, when: datetime) -> bool:
        """Does this instant fall inside the window?"""
        return self.start <= when and (self.end is None or when < self.end)

    def describe(self) -> str:
        """The window as a person reads it, for the messages on stderr."""
        start = self.start.date().isoformat()
        if self.end is None:
            return f"since {start}"
        # The end is exclusive, so the last day which counts is the day before.
        return f"from {start} through {(self.end - DAY).date().isoformat()}"


@dataclass(frozen=True)
class Branch:
    """A branch, and when its tip was committed."""

    name: str
    tip: str
    when: datetime


@dataclass(frozen=True)
class Merge:
    """A merge commit reachable from `main`."""

    hash: str
    when: datetime
    parents: tuple[str, ...]
    subject: str


@dataclass(frozen=True)
class Commit:
    """A commit on a student's branch. `author` is the address it was written
    from, folded for comparison, and `merge` says whether it brought another
    branch in."""

    hash: str
    when: datetime
    author: str
    merge: bool


def parse_time(value: str) -> datetime:
    """Parse one of git's ``iso-strict`` timestamps into an aware instant."""
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def main_branch(repo: Repo) -> str:
    """The name of the repository's main branch."""
    for name in MAIN_NAMES:
        if repo.has_ref(f"refs/heads/{name}"):
            return name
    sys.exit("This repository has neither a 'main' nor a 'master' branch.")


def branches(repo: Repo) -> list[Branch]:
    """Every branch in the repository."""
    fmt = f"%(refname:short){FIELD}%(objectname){FIELD}%(committerdate:iso-strict)"
    found = []
    for line in repo.out("for-each-ref", f"--format={fmt}", "refs/heads").splitlines():
        if not line.strip():
            continue
        name, tip, when = line.split(FIELD)
        found.append(Branch(name, tip, parse_time(when)))
    return found


def merges(repo: Repo, main: str) -> list[Merge]:
    """Every merge commit reachable from `main`, oldest first."""
    # ``-z`` separates commits with NULs, which is what makes it safe to ask
    # for the whole message body: the rubric matches on the message's first
    # line, and only ``%B`` reports a message unmangled -- ``%s`` runs a
    # multi-line subject together into one.
    fmt = f"%H{FIELD}%cI{FIELD}%P{FIELD}%B"
    found = []
    for record in repo.out("log", "--merges", "-z", f"--format={fmt}", main).split(
        "\0"
    ):
        if not record.strip():
            continue
        hash_, when, parents, body = record.split(FIELD, 3)
        lines = body.splitlines()
        found.append(
            Merge(hash_, parse_time(when), tuple(parents.split()), lines[0].strip())
        )
    found.reverse()
    return found


def branch_commits(repo: Repo, branch: Branch) -> list[Commit]:
    """The commits along `branch`'s first parent, newest first.

    A student's own commits, and the merges they make, lie along their
    branch's first parent; work they merge *in* -- a classmate's branch, or
    `main` -- arrives as a second parent, and so does not appear here."""
    fmt = f"%H{FIELD}%cI{FIELD}%P{FIELD}%ae{FIELD}%an"
    found = []
    for line in repo.out(
        "log", "--first-parent", f"--format={fmt}", branch.name
    ).splitlines():
        if not line.strip():
            continue
        hash_, when, parents, email, name = line.split(FIELD)
        found.append(
            Commit(
                hash_,
                parse_time(when),
                (email or name).casefold(),
                len(parents.split()) > 1,
            )
        )
    return found


def own_commits(repo: Repo, branch: Branch, year: int) -> set[str]:
    """The commits on `branch` which are this student's own work, made in
    `year` or since.

    Neither "the commits `main` cannot reach" nor "the commits not on `main`'s
    first-parent chain" will do here. A student who has merged their branch
    into `main` -- which the assignment asks them to do -- has put every one of
    their commits on `main`; and a student who merged *from* their branch
    rather than from `main` leaves `main`'s first parent pointing at their own
    work, which drags the whole class's commits off that chain.

    So take the commits along this branch's first parent which were made this
    year and which the student wrote. Who that is comes from the branch
    itself -- the author of its most recent ordinary commit -- since a commit
    records a person's name and address rather than their userid. The history
    a branch starts from is then someone else's by construction, whether it
    belongs to the instructor, to last year's class, or to the classmate who
    happened to commit to `main` just before this branch was cut.
    """
    # Stop at the first commit made before this year rather than skipping over
    # it: what lies beyond is the history this branch was cut from, and a
    # branch left over from a previous year reaches it immediately.
    recent = list(
        takewhile(lambda commit: commit.when.year >= year, branch_commits(repo, branch))
    )
    student = next((commit.author for commit in recent if not commit.merge), None)
    if student is None:
        return set()
    return {commit.hash for commit in recent if commit.author == student}


def files_added(repo: Repo, commits: set[str]) -> list[tuple[str, str]]:
    """The files these commits add, oldest first, as ``(path, commit hash)``
    pairs.

    A path counts once, at the commit which first added it, so deleting and
    re-adding a file does not earn the points twice. Modified, renamed, and
    deleted files do not count at all.
    """
    if not commits:
        return []
    # ``--no-walk`` restricts the listing to exactly these commits rather than
    # to their history; sorted and reversed, they arrive oldest first, which is
    # the order the rubric's blanks are filled in.
    text = repo.out(
        "log",
        "--no-walk=sorted",
        "--reverse",
        "--diff-filter=A",
        "--name-only",
        f"--format={RECORD}%H",
        *sorted(commits),
    )

    added: dict[str, str] = {}
    for record in text.split(RECORD):
        if not record.strip():
            continue
        hash_, *paths = record.splitlines()
        for path in paths:
            if path.strip():
                added.setdefault(path, hash_)
    return list(added.items())


# Grading
# -------
@dataclass(frozen=True)
class Grade:
    """One student's row of the output CSV."""

    userid: str
    grade: str
    feedback: str


def fill(points: Sequence[int], hashes: Sequence[Sequence[str]]) -> str:
    """Fill in the rubric's blanks: the points earned on each line, and the
    commit hashes which earned them. A blank with no hash to show reads
    `MISSING`, so the feedback has the same shape whether or not the work was
    found."""
    lines = []
    for line, earned, found, blanks in zip(RUBRIC, points, hashes, BLANKS):
        shown = [h[:SHORT] for h in found] + [MISSING] * (blanks - len(found))
        lines.append(line.format(points=earned, hashes=", ".join(shown)))
    return "\n".join(lines)


def find_branch(all_branches: Sequence[Branch], userid: str) -> Optional[Branch]:
    """The student's homework branch: one named exactly their userid, ignoring
    case. ``jit45`` counts; ``jit45-2`` and ``bensBranch`` do not. When it was
    pushed does not matter, since the window decides only who is graded."""
    for branch in all_branches:
        if branch.name.casefold() == userid.casefold():
            return branch
    return None


def is_own_work(
    repo: Repo, commit: str, own: Optional[Branch], others: Sequence[Branch]
) -> bool:
    """Is `commit` this student's own work rather than a classmate's?

    Decided by reachability rather than by authorship, since a commit records
    a person's name and not their userid. The commit is the student's own only
    when their userid branch can reach it and no other student's userid branch
    can: a classmate's branch which this student has already merged into their
    own is still the classmate's.
    """
    if own is None or not repo.reaches(own.tip, commit):
        return False
    return not any(repo.reaches(other.tip, commit) for other in others)


def find_merge(
    repo: Repo,
    userid: str,
    all_merges: Sequence[Merge],
    own: Optional[Branch],
    others: Sequence[Branch],
) -> Optional[Merge]:
    """The earliest merge commit which satisfies the third rubric line: a merge
    reachable from `main` whose message's first line is ``<userid>: merge
    branch with main`` ignoring case and surrounding whitespace, and which
    brings in work that is not the student's own. When it was made does not
    matter, since the window decides only who is graded."""
    wanted = MERGE_SUBJECT.format(userid=userid).casefold()
    for merge in all_merges:
        if merge.subject.casefold() != wanted:
            continue
        # Parent one is `main` as it stood; the rest are what the merge
        # brought in. What matters is the work which arrives, not the branch
        # which was named: a student who merges a classmate's branch into
        # their own and then merges *that* into `main` has still brought the
        # classmate's work in, even though the incoming parent is their own
        # branch tip. So ask after the commits the merge adds to `main` rather
        # than after its parents. One commit of someone else's is enough.
        brought_in = repo.commits(*merge.parents[1:], "--not", merge.parents[0])
        if any(not is_own_work(repo, commit, own, others) for commit in brought_in):
            return merge
    return None


def userid_of(subject: str) -> Optional[str]:
    """The userid a merge's message names, or `None` if that message is not the
    one the rubric asks for.

    Read so that a student who merged but never pushed a branch is still
    graded: without this they would have no row at all, since every other trace
    of them is a branch name. Anything but a single word before the colon is
    somebody's ordinary merge message rather than a userid.
    """
    tail = MERGE_SUBJECT.format(userid="")
    if not subject.casefold().endswith(tail.casefold()):
        return None
    userid = subject[: len(subject) - len(tail)].strip()
    return userid if userid.split() == [userid] else None


def roster(
    all_branches: Sequence[Branch],
    all_merges: Sequence[Merge],
    window: Window,
    extra: Sequence[str] = (),
) -> list[str]:
    """Every userid to grade, in alphabetical order.

    A student is whoever left work in the window: a branch whose tip was
    committed inside it, or a rubric merge made inside it, which names its
    userid in so many words. That is the whole roster -- the repository's own
    branches aside -- so a term is graded by naming its dates, and a student
    who was added to the class late or dropped it needs no editing here.

    `extra` names userids by hand, for a student who left nothing at all behind
    -- or nothing inside the window -- and would otherwise have no row to
    grade.

    Userids are matched ignoring case throughout, so a userid spelled two ways
    is one student, reported under the spelling met first.
    """
    found: dict[str, str] = {}
    for branch in all_branches:
        if branch.name.casefold() not in MAIN_NAMES and window.holds(branch.when):
            found.setdefault(branch.name.casefold(), branch.name)
    for merge in all_merges:
        userid = userid_of(merge.subject) if window.holds(merge.when) else None
        if userid:
            found.setdefault(userid.casefold(), userid)
    for userid in extra:
        found.setdefault(userid.casefold(), userid)
    return [found[key] for key in sorted(found)]


def grade_one(
    repo: Repo,
    userid: str,
    all_branches: Sequence[Branch],
    all_merges: Sequence[Merge],
    year: int,
) -> Grade:
    """Apply all three rubric lines to one student, counting only commits made
    in `year` or since as their own files."""
    own = find_branch(all_branches, userid)
    # Every classmate's branch, which is what tells this student's work from
    # theirs: every branch but this student's own and the repository's. Nothing
    # says which branch names are userids, so each is taken to be one -- just
    # as `roster` takes it -- and the window has no say, since a classmate who
    # pushed before it opened is a classmate still.
    others = [
        branch
        for branch in all_branches
        if branch.name.casefold() not in (userid.casefold(), *MAIN_NAMES)
    ]

    # 1. The branch. Its tip is the hash reported, since git has no commit
    # which "creates" a branch.
    branch_hashes = [own.tip] if own else []

    # 2. The files. Without a branch, there is nothing to look at.
    files = []
    if own:
        files = files_added(repo, own_commits(repo, own, year))[:FILES_WANTED]
    file_hashes = [hash_ for _, hash_ in files]

    # 3. The merge.
    merge = find_merge(repo, userid, all_merges, own, others)
    merge_hashes = [merge.hash] if merge else []

    points = [
        BRANCH_POINTS if own else 0,
        PER_FILE * len(files),
        MERGE_POINTS if merge else 0,
    ]
    hashes = [branch_hashes, file_hashes, merge_hashes]
    return Grade(userid, f"{sum(points)}%", fill(points, hashes))


def grade_all(repo: Repo, window: Window, extra: Sequence[str] = ()) -> list[Grade]:
    """Grade everyone the repository shows working in the window, plus anyone
    named in `extra`, in alphabetical order.

    The window chooses the rows and nothing more: each student is graded on
    everything they pushed, wherever it falls. The one date the rubric asks
    after is the year, since only commits made this year are a student's own
    files -- and this year is the one the window opens in, so that grading a
    term gives the same answer whenever it is run."""
    main = main_branch(repo)
    all_branches = branches(repo)
    all_merges = merges(repo, main)
    userids = roster(all_branches, all_merges, window, extra)
    year = window.start.year
    return [
        grade_one(repo, userid, all_branches, all_merges, year) for userid in userids
    ]


# Output
# ------
def write_csv(path: Path, grades: Sequence[Grade]) -> None:
    """Write the three-column CSV: userid, grade, and feedback. The feedback
    holds the three rubric lines, so it spans three lines of its own, and the
    csv module quotes it as RFC 4180 requires."""
    # ``utf-8-sig`` so that Excel recognizes the encoding on a double-click,
    # and ``newline=""`` so that the csv module controls line endings itself.
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["userid", "grade", "feedback"])
        for row in grades:
            writer.writerow([row.userid, row.grade, row.feedback])


# Command line
# ------------
def read_date(value: str, option: str) -> datetime:
    """Read one end of the window from the command line, in UTC, or fail with
    the option named."""
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        raise typer.BadParameter(
            f"Cannot read {value!r} as a date. Use YYYY-MM-DD.", param_hint=option
        ) from None


# One Typer command, collapsed to a bare command line because the app defines
# only one. `Annotated` carries each option's help text next to its type, so
# the signature is the whole interface.
app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command(
    epilog="""Example: git-grade --since 2026-10-01 --out grades.csv -- which
clones the class repository, grades everyone who worked in it since that date,
and writes a CSV of userid, grade, and feedback."""
)
def grade(
    # Required, so it comes first: a parameter with no default cannot follow
    # one with a default.
    since: Annotated[
        str,
        typer.Option(
            help="Grade everyone who worked on or after this date, YYYY-MM-DD. "
            "Required. Only commits made in its year or later count as a "
            "student's own files."
        ),
    ],
    until: Annotated[
        str,
        typer.Option(
            help="Grade everyone who worked on or before this date, YYYY-MM-DD, "
            "a whole day which counts in full. Empty means no end date."
        ),
    ] = DEFAULT_UNTIL,
    repo: Annotated[
        str, typer.Option(help="Class repository to grade: a URL or a path.")
    ] = DEFAULT_REPO,
    userids: Annotated[
        str,
        typer.Option(
            help="Userids to grade in addition to those found in the "
            "repository, comma-separated. Use this for a student who left "
            "nothing between the dates and would otherwise have no row."
        ),
    ] = "",
    out: Annotated[Path, typer.Option(help="Where to write the CSV.")] = Path(
        "grades.csv"
    ),
    cache: Annotated[
        Path, typer.Option(help="Where to keep the mirror clone between runs.")
    ] = Path(".grader-cache"),
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Report progress on stderr.")
    ] = False,
) -> None:
    """Grade the Git branch-and-merge homework in the class repository.

    Who is graded comes from the repository itself: every userid which pushed a
    branch or made a merge between --since and --until. What they score does
    not: each is graded on everything they pushed.
    """
    # Validate the options against each other before cloning, so that a typo
    # costs nothing. `BadParameter` names the offending option and prints the
    # usage line, which a bare message would not.
    extra = [userid.strip() for userid in userids.split(",") if userid.strip()]
    repeated = sorted({userid for userid in extra if extra.count(userid) > 1})
    if repeated:
        raise typer.BadParameter(
            f"Repeated userid(s): {', '.join(repeated)}.", param_hint="--userids"
        )
    start = read_date(since, "--since")
    # The day `--until` names counts in full, so the window ends when it does.
    end = read_date(until, "--until") + DAY if until.strip() else None
    if end is not None and end <= start:
        raise typer.BadParameter(
            f"{until} falls before --since ({since}).", param_hint="--until"
        )
    window = Window(start, end)

    name = repo.rstrip("/\\").replace("\\", "/").split("/")[-1].removesuffix(".git")
    clone = mirror(repo, cache / f"{name}.git", verbose)

    grades = grade_all(clone, window, extra)
    if not grades:
        sys.exit(f"Nobody worked in {repo} {window.describe()}.")
    write_csv(out, grades)

    typer.echo(
        f"Graded {len(grades)} student(s) in {repo} {window.describe()}:", err=True
    )
    # A userid is an e-mail address's local part, which can run long, so the
    # column is as wide as the longest of them.
    width = max(len(row.userid) for row in grades)
    for row in grades:
        typer.echo(f"  {row.userid:<{width}} {row.grade:>4}", err=True)
    typer.echo(f"  {out}", err=True)


def main() -> None:
    """The ``git-grade`` console script."""
    app()


if __name__ == "__main__":
    main()
