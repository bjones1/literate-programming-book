# ***********************************************
# |docname| - Offline tests for `git_homework.py`
# ***********************************************
# These build a small class repository with git itself -- one branch per
# student, and the merges they made -- then grade it, so the rubric is checked
# against real commits rather than against a stub. Nothing here touches the
# network. Run them with ``poetry run pytest``.
#
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
import csv
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

# Third-party imports
# -------------------
import pytest
from typer.testing import CliRunner, Result

# Local application imports
# -------------------------
from grader import git_homework as gh

# Fixtures and helpers
# ====================
#
# The window the fixture repository is graded over, which is also what
# separates this year's work from the previous year's. There is no roster: the
# netids come out of the repository. `EXTRA` names the two students who left
# nothing inside the window and so would otherwise have no row -- one who did
# nothing at all, and one whose only branch is last year's.
FLOOR = datetime(2026, 8, 1, tzinfo=timezone.utc)
WINDOW = gh.Window(FLOOR)
EXTRA = ["delta4", "old5"]

# Who the fixture repository shows working inside that window, alphabetically:
# a branch tip apiece, save for `iota8`, who merged without pushing a branch.
FOUND = [
    "alpha1",
    "alpha1-2",
    "beta2",
    "eps6",
    "eta7",
    "gamma3",
    "iota8",
    "zeta7",
]


def _git(
    cwd: Path, *args: str, when: Optional[str] = None, who: str = "instructor"
) -> str:
    # Run git in a repository under construction, as `who`. The global and
    # system configuration files are pointed at a path which does not exist, so
    # that whoever runs the tests cannot change their outcome -- commit
    # signing, in particular, would otherwise stop the fixture dead.
    env = dict(os.environ)
    nowhere = str(cwd / "no-such-config")
    env.update(
        {
            "GIT_CONFIG_GLOBAL": nowhere,
            "GIT_CONFIG_SYSTEM": nowhere,
            "GIT_AUTHOR_NAME": who.title(),
            "GIT_AUTHOR_EMAIL": f"{who}@example.com",
            # The committer is somebody else throughout, deliberately: the
            # rubric asks who *wrote* a commit, and a merge made on GitHub is
            # committed by GitHub.
            "GIT_COMMITTER_NAME": "Classroom",
            "GIT_COMMITTER_EMAIL": "classroom@example.com",
        }
    )
    if when:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    done = subprocess.run(
        ["git", *args], cwd=cwd, env=env, capture_output=True, text=True
    )
    assert done.returncode == 0, f"git {' '.join(args)}:\n{done.stderr}"
    return done.stdout


def _commit(cwd: Path, who: str, when: str, message: str, *files: str) -> None:
    # Add each named file, then commit them as one change.
    for name in files:
        (cwd / name).write_text(f"{name}\n", encoding="utf-8")
    _git(cwd, "add", "-A")
    _git(cwd, "commit", "-m", message, when=when, who=who)


def _branch(cwd: Path, name: str, start: str = "main") -> None:
    _git(cwd, "checkout", "-q", "-b", name, start)


def _merge(cwd: Path, who: str, into: str, what: str, when: str, message: str) -> None:
    # Always a real merge commit, so that the rubric has something to find.
    _git(cwd, "checkout", "-q", into)
    _git(cwd, "merge", "-q", "--no-ff", what, "-m", message, when=when, who=who)


def _build(root: Path) -> Path:
    """Build the class repository the tests grade.

    Each student exercises one corner of the rubric:

    -   `alpha1` does the assignment exactly.
    -   `beta2` commits the two files in two commits, and writes the merge
        message wrong.
    -   `gamma3` commits one file, and merges their *own* branch into main.
    -   `delta4` does nothing at all.
    -   `old5` has a branch, but from the previous year.
    -   `eps6` merges a classmate's branch into their own branch before
        merging it into main -- which must still count as the classmate's
        work, not as `eps6`'s own.
    -   `eta7` does the same, but merges *their own branch* into main rather
        than the classmate's, which still carries the classmate's work onto
        main and so must still count.
    -   `iota8` never pushes a branch, and is known only by the merge they
        made, which is where that netid has to be read from.

    Every branch is cut from a commit `rsz12` made straight to `main`, as
    happens in a class repository, so no student may be credited with the file
    it adds.
    """
    source = root / "class"
    source.mkdir()
    _git(source, "init", "-q", "-b", "main", ".")
    _commit(source, "instructor", "2026-08-05T00:00:00+00:00", "start", "README.md")
    _commit(source, "rsz12", "2026-08-20T00:00:00+00:00", "test commit", "r.txt")

    # A previous year's branch, whose netid happens to recur on this roster.
    _branch(source, "old5")
    _commit(source, "old5", "2024-10-01T00:00:00+00:00", "last year", "x.txt", "y.txt")

    _branch(source, "alpha1")
    _commit(
        source,
        "alpha1",
        "2026-09-01T00:00:00+00:00",
        "alpha1: two files",
        "a1.txt",
        "a2.txt",
    )

    # A branch which merely starts with a netid, which the rubric does not
    # accept in place of the netid itself.
    _branch(source, "alpha1-2")
    _commit(source, "alpha1", "2026-09-01T12:00:00+00:00", "a third file", "a3.txt")

    _branch(source, "beta2")
    _commit(source, "beta2", "2026-09-02T00:00:00+00:00", "beta2: first file", "b1.txt")
    _commit(
        source, "beta2", "2026-09-03T00:00:00+00:00", "beta2: second file", "b2.txt"
    )

    _branch(source, "gamma3")
    _commit(source, "gamma3", "2026-09-04T00:00:00+00:00", "gamma3: one file", "g1.txt")

    _branch(source, "eps6")
    _commit(
        source,
        "eps6",
        "2026-09-05T00:00:00+00:00",
        "eps6: two files",
        "e1.txt",
        "e2.txt",
    )

    _branch(source, "eta7")
    _commit(
        source,
        "eta7",
        "2026-09-05T06:00:00+00:00",
        "eta7: two files",
        "h1.txt",
        "h2.txt",
    )

    # A branch belonging to nobody on the roster, merged in below.
    _branch(source, "zeta7")
    _commit(source, "zeta7", "2026-09-05T12:00:00+00:00", "zeta7: a file", "z.txt")

    # alpha1 merges a classmate's branch into main, as asked.
    _merge(
        source,
        "alpha1",
        "main",
        "beta2",
        "2026-09-06T00:00:00+00:00",
        "alpha1: merge branch with main",
    )
    # gamma3 merges their own branch, which the assignment does not ask for.
    _merge(
        source,
        "gamma3",
        "main",
        "gamma3",
        "2026-09-07T00:00:00+00:00",
        "gamma3: merge branch with main",
    )
    # eps6 first merges alpha1's branch into their own...
    _merge(
        source,
        "eps6",
        "eps6",
        "alpha1",
        "2026-09-08T00:00:00+00:00",
        "eps6: catching up with alpha1",
    )
    # ...and then merges it into main, in the required words but not the
    # required capitalization.
    _merge(
        source,
        "eps6",
        "main",
        "alpha1",
        "2026-09-09T00:00:00+00:00",
        "eps6: MERGE Branch With Main",
    )
    # beta2's merge says the wrong thing.
    _merge(
        source,
        "beta2",
        "main",
        "zeta7",
        "2026-09-10T00:00:00+00:00",
        "beta2: merged branch with main",
    )
    # eta7 merges a classmate's branch into their own, as eps6 did...
    _merge(
        source,
        "eta7",
        "eta7",
        "eps6",
        "2026-09-11T00:00:00+00:00",
        "eta7: catching up with eps6",
    )
    # ...but then merges their own branch into main, rather than the
    # classmate's. eps6's work arrives on main all the same.
    _merge(
        source,
        "eta7",
        "main",
        "eta7",
        "2026-09-12T00:00:00+00:00",
        "eta7: merge branch with main",
    )
    # iota8 has no branch at all: this merge is the only trace of them.
    _merge(
        source,
        "iota8",
        "main",
        "alpha1-2",
        "2026-09-13T00:00:00+00:00",
        "iota8: merge branch with main",
    )
    _git(source, "checkout", "-q", "main")
    return source


@pytest.fixture(scope="module")
def source(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _build(tmp_path_factory.mktemp("source"))


@pytest.fixture(scope="module")
def repo(source: Path, tmp_path_factory: pytest.TempPathFactory) -> gh.Repo:
    # Clone the fixture repository exactly as a real run clones the class
    # repository -- from a path rather than a URL, which git treats the same.
    return gh.mirror(str(source), tmp_path_factory.mktemp("cache") / "class.git")


@pytest.fixture(scope="module")
def grades(repo: gh.Repo) -> Dict[str, gh.Grade]:
    return {row.netid: row for row in gh.grade_all(repo, WINDOW, EXTRA)}


def _hash(repo: gh.Repo, rev: str) -> str:
    return repo.out("rev-parse", rev).strip()[: gh.SHORT]


def _merge_hash(repo: gh.Repo, netid: str) -> str:
    # The short hash of this student's rubric merge, found by its message
    # rather than by its position on `main`: every merge made after it moves
    # that position, and the fixture makes more of them.
    wanted = gh.MERGE_SUBJECT.format(netid=netid).casefold()
    found = [m for m in gh.merges(repo, "main") if m.subject.casefold() == wanted]
    assert len(found) == 1, f"{netid}: {len(found)} merges"
    return found[0].hash[: gh.SHORT]


def _lines(grade: gh.Grade) -> List[str]:
    return grade.feedback.splitlines()


# Reading the repository
# ======================
def test_main_branch(repo: gh.Repo) -> None:
    assert gh.main_branch(repo) == "main"


def test_branches_are_found_with_their_tips(repo: gh.Repo) -> None:
    found = {branch.name: branch for branch in gh.branches(repo)}
    assert "alpha1" in found and "zeta7" in found
    assert found["alpha1"].tip == repo.out("rev-parse", "alpha1").strip()
    # The previous year's branch is dated in the previous year.
    assert found["old5"].when < FLOOR


def test_merges_are_oldest_first_with_first_lines(repo: gh.Repo) -> None:
    found = gh.merges(repo, "main")
    # Every merge `main` can reach, oldest first -- which includes the ones
    # made on a branch, once that branch is merged into `main`.
    assert [merge.subject for merge in found] == [
        "alpha1: merge branch with main",
        "gamma3: merge branch with main",
        "eps6: catching up with alpha1",
        "eps6: MERGE Branch With Main",
        "beta2: merged branch with main",
        "eta7: catching up with eps6",
        "eta7: merge branch with main",
        "iota8: merge branch with main",
    ]
    # Every one of them is a merge, so every one has a second parent.
    assert all(len(merge.parents) >= 2 for merge in found)


def test_find_branch_wants_the_netid_exactly(repo: gh.Repo) -> None:
    all_branches = gh.branches(repo)
    # `alpha1-2` starts with the netid, but is not the netid.
    found = gh.find_branch(all_branches, "alpha1", WINDOW)
    assert found is not None and found.name == "alpha1"
    # Case does not matter...
    assert gh.find_branch(all_branches, "ALPHA1", WINDOW) is not None
    # ...but the window does, and a student with no branch has none.
    assert gh.find_branch(all_branches, "old5", WINDOW) is None
    assert gh.find_branch(all_branches, "delta4", WINDOW) is None


def test_own_commits_are_the_students_own(repo: gh.Repo) -> None:
    all_branches = gh.branches(repo)
    branch = gh.find_branch(all_branches, "eps6", WINDOW)
    assert branch is not None
    # eps6 wrote one commit and one merge; what they merged in -- alpha1's
    # commit -- and what they branched from are somebody else's.
    mine = gh.own_commits(repo, branch, WINDOW)
    assert mine == {_full(repo, "eps6"), _full(repo, "eps6~1")}
    assert _full(repo, "alpha1") not in mine


def _full(repo: gh.Repo, rev: str) -> str:
    return repo.out("rev-parse", rev).strip()


# The rubric, line by line
# ========================
def test_the_assignment_done_exactly(grades: Dict[str, gh.Grade]) -> None:
    alpha1 = grades["alpha1"]
    assert alpha1.grade == "100%"
    first, second, third = _lines(alpha1)
    assert first.startswith("30/30 points -- Branch created with your netid.")
    assert second.startswith("30/30 points (15 points per file)")
    assert third.startswith("40/40 points")
    assert gh.MISSING not in alpha1.feedback


def test_a_bystanders_commit_is_not_credited(
    repo: gh.Repo, grades: Dict[str, gh.Grade]
) -> None:
    # Every branch here is cut from `rsz12`'s commit, which adds a file of its
    # own. Both of alpha1's blanks name alpha1's one commit, not that one.
    theirs = _hash(repo, "alpha1")
    assert _lines(grades["alpha1"])[1].endswith(f"Commit hash(es): {theirs}, {theirs}")
    assert _hash(repo, "alpha1~1") not in grades["alpha1"].feedback


def test_two_files_may_arrive_in_two_commits(
    repo: gh.Repo, grades: Dict[str, gh.Grade]
) -> None:
    beta2 = grades["beta2"]
    # Two files, so full marks on that line, and the two commits which added
    # them are reported oldest first.
    assert _lines(beta2)[1].endswith(
        f"Commit hash(es): {_hash(repo, 'beta2~1')}, {_hash(repo, 'beta2')}"
    )
    # The merge message says "merged", not "merge", so the merge line fails --
    # and this student's branch *is* on main, which must not be mistaken for
    # the files having been committed somewhere else.
    assert beta2.grade == "60%"
    assert _lines(beta2)[2] == (
        "0/40 points -- At least one merge commit exists with the correct "
        "commit message. Commit hash: not found"
    )


def test_one_file_earns_half_that_line(grades: Dict[str, gh.Grade]) -> None:
    gamma3 = grades["gamma3"]
    # One file committed, and a merge of the student's own branch, which the
    # assignment does not ask for.
    assert gamma3.grade == "45%"
    assert _lines(gamma3)[1].endswith(f", {gh.MISSING}")
    assert _lines(gamma3)[2].startswith("0/40 points")


def test_a_classmates_branch_stays_the_classmates(
    repo: gh.Repo, grades: Dict[str, gh.Grade]
) -> None:
    # eps6 merged alpha1's branch into their own before merging it into main.
    # That must still count as someone else's work...
    eps6 = grades["eps6"]
    assert eps6.grade == "100%"
    assert _lines(eps6)[2].endswith(f"Commit hash: {_merge_hash(repo, 'eps6')}")
    # ...and alpha1's two files, which are now reachable from eps6's branch,
    # must not be credited to eps6 on top of their own two.
    assert _lines(eps6)[1].startswith("30/30 points")
    assert f"Commit hash(es): {_hash(repo, 'eps6~1')}," in _lines(eps6)[1]


def test_a_classmates_work_counts_however_it_arrives(
    repo: gh.Repo, grades: Dict[str, gh.Grade]
) -> None:
    # eta7 merged eps6's branch into their own, then merged *their own branch*
    # into main. The incoming parent is therefore eta7's own branch tip, which
    # no classmate's branch can reach...
    eta7 = grades["eta7"]
    assert _full(repo, f"{_merge_hash(repo, 'eta7')}^2") == _full(repo, "eta7")
    # ...but eps6's commits are among those the merge puts on main, so it
    # brings in someone else's work and the line scores.
    assert eta7.grade == "100%"
    assert _lines(eta7)[2].endswith(f"Commit hash: {_merge_hash(repo, 'eta7')}")
    # eps6's files rode along, and must not be credited to eta7 on top of the
    # two of their own.
    theirs = _hash(repo, "eta7~1")
    assert _lines(eta7)[1].endswith(f"Commit hash(es): {theirs}, {theirs}")


def test_nothing_at_all(grades: Dict[str, gh.Grade]) -> None:
    delta4 = grades["delta4"]
    assert delta4.grade == "0%"
    assert delta4.feedback.count(gh.MISSING) == 4  # One per blank in the rubric.
    assert _lines(delta4)[0].startswith("0/30 points")


def test_last_years_work_does_not_count(
    repo: gh.Repo, grades: Dict[str, gh.Grade]
) -> None:
    # `old5` has a branch named for the netid, with two files on it, but both
    # it and they are from the previous year -- and the commit the branch was
    # cut from is this year's, but is somebody else's.
    assert grades["old5"].grade == "0%"
    assert gh.MISSING in _lines(grades["old5"])[0]
    assert _hash(repo, "old5~1") not in grades["old5"].feedback


def test_the_roster_comes_out_of_the_repository(repo: gh.Repo) -> None:
    found = gh.roster(gh.branches(repo), gh.merges(repo, "main"), WINDOW)
    # Every branch pushed inside the window, and the netid iota8's merge names,
    # in alphabetical order -- but not `main`, and not last year's `old5`.
    assert found == FOUND
    # `alpha1-2` is nobody's netid, but nothing in the repository says so: an
    # extra row is the price of not keeping a roster, and is easily deleted.
    assert "alpha1-2" in found


def test_extra_netids_are_graded_alongside_what_is_found(repo: gh.Repo) -> None:
    # A student with nothing inside the window has no trace to be found by, so
    # naming them is the only way they get a row.
    graded = [row.netid for row in gh.grade_all(repo, WINDOW, EXTRA)]
    assert graded == sorted(FOUND + EXTRA)


def test_the_window_shuts_at_both_ends(repo: gh.Repo) -> None:
    # A window which closes before the later branches were pushed reports only
    # the students who had finished by then.
    early = gh.Window(FLOOR, datetime(2026, 9, 4, tzinfo=timezone.utc))
    assert gh.roster(gh.branches(repo), gh.merges(repo, "main"), early) == [
        "alpha1",
        "alpha1-2",
        "beta2",
    ]
    # Every merge in this repository was made later, so no netid is read from
    # one, and the merge line scores nothing for anybody.
    assert all(
        _lines(row)[2].startswith("0/40 points") for row in gh.grade_all(repo, early)
    )


def test_a_merge_names_the_netid_which_made_it(repo: gh.Repo) -> None:
    # The netid a rubric merge names, which is all the tool knows of a student
    # who never pushed a branch.
    assert gh.netid_of("iota8: merge branch with main") == "iota8"
    # Nearly right still names a student: they get a row, and the merge line
    # tells them it scored nothing, which no row at all would not.
    assert gh.netid_of("  iota8 : MERGE Branch With Main") == "iota8"
    assert gh.netid_of("iota8: merged branch with main") is None
    assert gh.netid_of("eps6: catching up with alpha1") is None
    # A message with no netid in front of it names nobody.
    assert gh.netid_of(": merge branch with main") is None
    assert gh.netid_of("Fixed the build: merge branch with main") is None


def test_a_merge_alone_earns_its_line(grades: Dict[str, gh.Grade]) -> None:
    # iota8 pushed no branch, so the first two lines find nothing, but the
    # merge they made brought in somebody else's work.
    iota8 = grades["iota8"]
    assert iota8.grade == "40%"
    assert _lines(iota8)[0].startswith("0/30 points")
    assert _lines(iota8)[2].startswith("40/40 points")


def test_a_window_describes_itself() -> None:
    # What the run reports on stderr. The end date is exclusive inside, but is
    # reported as the whole day the user asked for.
    assert gh.Window(FLOOR).describe() == "since 2026-08-01"
    end = datetime(2026, 9, 15, tzinfo=timezone.utc) + gh.DAY
    assert gh.Window(FLOOR, end).describe() == "from 2026-08-01 through 2026-09-15"


# Feedback and output
# ===================
def test_fill_pads_every_blank() -> None:
    feedback = gh.fill([30, 15, 0], [["a" * 40], ["b" * 40], []])
    first, second, third = feedback.splitlines()
    assert first.endswith(f"Commit hash: {'a' * gh.SHORT}")
    # The second line has two blanks, so an unearned one still shows.
    assert second.endswith(f"Commit hash(es): {'b' * gh.SHORT}, {gh.MISSING}")
    assert third.startswith("0/40 points")


def test_csv_round_trips_multi_line_feedback(tmp_path: Path) -> None:
    rows = [gh.Grade("alpha1", "100%", "one\ntwo\nthree"), gh.Grade("beta2", "0%", "x")]
    path = tmp_path / "grades.csv"
    gh.write_csv(path, rows)

    with path.open(encoding="utf-8-sig", newline="") as handle:
        read = list(csv.reader(handle))
    assert read[0] == ["netid", "grade", "feedback"]
    assert read[1] == ["alpha1", "100%", "one\ntwo\nthree"]
    assert len(read) == 3
    # The feedback is quoted, per RFC 4180, rather than breaking the row.
    assert '"one\ntwo\nthree"' in path.read_text(encoding="utf-8-sig")


# The command line
# ================
runner = CliRunner()


def _invoke(args: Sequence[str]) -> Result:
    return runner.invoke(gh.app, list(args))


def _rows(path: Path) -> List[List[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def test_cli_grades_everyone_it_finds(source: Path, tmp_path: Path) -> None:
    out = tmp_path / "grades.csv"
    result = _invoke(
        [
            "--repo",
            str(source),
            "--since",
            "2026-08-01",
            "--netids",
            "delta4, old5",
            "--out",
            str(out),
            "--cache",
            str(tmp_path / "cache"),
        ]
    )
    assert result.exit_code == 0, result.output
    read = _rows(out)
    # One row per netid the repository shows, plus the two named by hand.
    assert [row[0] for row in read] == ["netid"] + sorted(FOUND + EXTRA)
    graded = {row[0]: row[1] for row in read[1:]}
    assert graded["alpha1"] == "100%" and graded["delta4"] == "0%"


def test_cli_dates_decide_who_is_graded(source: Path, tmp_path: Path) -> None:
    out = tmp_path / "grades.csv"
    result = _invoke(
        [
            "--repo",
            str(source),
            "--since",
            "2026-08-01",
            "--until",
            "2026-09-01",
            "--out",
            str(out),
            "--cache",
            str(tmp_path / "cache"),
        ]
    )
    assert result.exit_code == 0, result.output
    # `--until` names a whole day, so alpha1-2's branch, pushed at noon on it,
    # is inside the window and beta2's, pushed two days later, is not.
    assert [row[0] for row in _rows(out)] == ["netid", "alpha1", "alpha1-2"]
    assert "from 2026-08-01 through 2026-09-01" in result.output


def test_cli_reports_an_empty_window(source: Path, tmp_path: Path) -> None:
    # Nobody worked in this repository in 2020, so there is nothing to write.
    out = tmp_path / "grades.csv"
    result = _invoke(
        [
            "--repo",
            str(source),
            "--since",
            "2020-01-01",
            "--until",
            "2020-01-02",
            "--out",
            str(out),
            "--cache",
            str(tmp_path / "cache"),
        ]
    )
    assert result.exit_code == 1
    assert not out.exists()


def test_cli_reuses_its_clone(source: Path, tmp_path: Path) -> None:
    # The second run fetches into the clone the first run made, rather than
    # failing because the directory is already there.
    cache = tmp_path / "cache"
    for _ in range(2):
        result = _invoke(
            [
                "--repo",
                str(source),
                "--netids",
                "alpha1",
                "--out",
                str(tmp_path / "grades.csv"),
                "--cache",
                str(cache),
            ]
        )
        assert result.exit_code == 0, result.output
    assert (cache / "class.git" / "HEAD").exists()


@pytest.mark.parametrize(
    "option,value,expected",
    [
        ("--netids", "alpha1,alpha1", "Repeated netid"),
        ("--since", "last August", "Cannot read"),
        ("--until", "next Friday", "Cannot read"),
    ],
)
def test_cli_rejects_bad_options_before_cloning(
    option: str, value: str, expected: str, tmp_path: Path
) -> None:
    # Validation happens before the clone, so these never touch a repository.
    result = _invoke([option, value, "--repo", str(tmp_path / "nowhere")])
    assert result.exit_code == 2
    assert expected in result.output


def test_cli_rejects_a_window_which_runs_backwards(tmp_path: Path) -> None:
    result = _invoke(
        [
            "--since",
            "2026-09-14",
            "--until",
            "2026-09-01",
            "--repo",
            str(tmp_path / "nowhere"),
        ]
    )
    assert result.exit_code == 2
    assert "falls before --since" in result.output
