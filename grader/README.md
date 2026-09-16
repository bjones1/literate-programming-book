Grading tools
=============

Two commands, both specified by [chat\_grader.md](../chat_grader.md):

* `teams-export` pulls one Microsoft Teams channel's chat history over a date
  range, and
* `git-grade` grades the Git branch-and-merge homework in the class
  repository.

Setup
-----

```console
$ poetry install
```

That creates `.venv/` in this directory (see [poetry.toml](poetry.toml)) and
installs both the runtime dependencies and the check tools.

Exporting Teams chats
---------------------

`grader/teams_export.py` implements steps 1 and 2 of the chat grader: given a
date range, it pulls one Microsoft Teams channel's history and writes

* `chats.json` — the raw Microsoft Graph record of every message, so nothing is
  lost before grading, and
* `chats.csv` — three columns, `timestamp`, `user`, `html`, which step 3 appends
  its grading-criterion columns to.

No Azure app registration is needed. The exporter signs in *as you* using the
OAuth device code flow against Microsoft's own pre-registered "Microsoft Graph
Command Line Tools" client, so it can read exactly the channels you can already
read in Teams — no more.

Installing the project provides a `teams-export` command (note that the backtick
escapes newlines in PowerShell; use `\` in MacOS/Linux):

```console
PS> poetry run teams-export `
    --team "CSDA 5101 - Advanced Software Paradigms - 2026 Fall" `
    --channel General --start 2026-09-06 --end 2026-09-13 `
    --out fall2026-week2
```

The first run prints a code and a URL; open the URL, enter the code, and sign in
with your university account. The sign-in is cached in
`%USERPROFILE%\.teams_export_token.json`, so later runs are silent. Delete that
file to sign out.

`--start` and `--end` are both inclusive whole local days. To slice more finely,
pass a full timestamp instead: `--end 2026-09-14T09:30`.

### Options worth knowing

Run `poetry run teams-export -h` for the full list; the command line is
[Typer](https://typer.tiangolo.com/), built from the annotations on `export` in
[teams\_export.py](grader/teams_export.py), so the help text and the
signature cannot drift apart.

| Option                 | Effect                                                                                                                 |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `--tz America/Chicago` | Read the dates, and write the CSV timestamps, in this time zone. Defaults to your machine's.                           |
| `--no-replies`         | Export only top-level posts. The default, `--replies`, gives each threaded reply a row of its own.                     |
| `--include-system`     | Include "X joined the team" event messages, normally filtered out.                                                     |
| `--include-deleted`    | Include deleted messages, whose bodies are usually empty anyway.                                                       |
| `-v`                   | Report paging progress and throttling on stderr.                                                                       |
| `--tenant`             | Sign in to a specific tenant rather than `organizations`. Use your tenant ID or domain if you belong to more than one. |

Bad options are caught before sign-in, so a typo costs nothing, and they exit 2
with the offending option named:

```console
$ poetry run teams-export --team ... --start 2026-09-14 --end 2026-09-01
Invalid value for --end: 2026-09-01 falls before --start (2026-09-14).
```

`--team` and `--channel` accept either a display name or an ID. Names are
matched exactly first, then case-insensitively, then as a substring; anything
ambiguous or unmatched fails with the list of what is actually available, rather
than guessing at which section you meant.

Grading Git homework
--------------------

`git-grade` grades the assignment specified in
[chat\_grader.md](../chat_grader.md): a branch named for your netid, two files
committed to it, and a merge of someone else's branch into `main` carrying the
message `<your netid>: merge branch with main`. It needs no sign-in — the class
repository is public, and the tool clones it itself.

```console
PS> poetry run git-grade --out grades.csv
```

That writes one row per student — `netid`, `grade`, and `feedback`, the feedback
being the rubric's three lines with their blanks filled in — and prints each
grade on stderr as it goes. One row, with its feedback shown unquoted:

```
ewj55,100%,30/30 points -- Branch created with your netid. Commit hash: a01d9899
           30/30 points (15 points per file) -- Two files committed to this branch. Commit hash(es): a01d9899, a01d9899
           40/40 points -- At least one merge commit exists with the correct commit message. Commit hash: f6fd3bcc
```

The feedback spans three lines, so the CSV quotes it as RFC 4180 requires;
Excel, Canvas, and Python's `csv` module all read it back as one field.

### Who gets graded

There is no roster to keep. The students are whoever the repository shows
working between `--since` and `--until`: everyone who pushed a branch whose
last commit falls in that window, plus everyone a merge in it names in its
`<netid>: merge branch with main` message, which is the only trace of a student
who merged without ever pushing a branch of their own. Rows come out in
alphabetical order.

So a term is graded by naming its dates, and a student who joined the class
late or dropped it needs no editing anywhere:

```console
PS> poetry run git-grade --since 2026-08-01 --until 2026-12-15 --out grades.csv
```

Two things follow from reading the roster out of the repository rather than
being told it.

*A branch which is not a netid still gets a row.* Nothing in a class repository
says which branch names are netids, so `jit45-2`, `my-branch`, and the
instructor's own branch are all graded as if they were students. Delete those
rows; that is cheaper than maintaining a roster, and it is how you notice a
student who pushed a branch under the wrong name.

*A student who left nothing behind has no row*, since there is nothing to find
them by. Name them with `--netids` to grade them anyway — they score 0%, with
the rubric explaining why:

```console
PS> poetry run git-grade --netids dbg103,drj228 --out grades.csv
```

### Options worth knowing

Run `poetry run git-grade -h` for the full list.

| Option      | Effect                                                                                                      |
| ----------- | ----------------------------------------------------------------------------------------------------------- |
| `--repo`    | What to grade. Defaults to the class repository; a local path works too, which is how the tests drive it.   |
| `--since`   | Grade work committed on or after this date. Defaults to `2026-08-01`, which keeps previous years out.        |
| `--until`   | Grade work committed on or before this date, a whole day which counts in full. Defaults to no end date.      |
| `--netids`  | Netids to grade *in addition to* those found, comma-separated. For students who left nothing behind.         |
| `--out`     | Where to write the CSV. Defaults to `grades.csv`.                                                           |
| `--cache`   | Where the mirror clone lives between runs. Defaults to `.grader-cache`.                                     |
| `-v`        | Print each git command as it runs.                                                                          |

Both dates are whole days in UTC, and both ends are checked before the clone, so
a window which runs backwards costs nothing:

```console
$ poetry run git-grade --since 2026-09-14 --until 2026-09-01
Invalid value for --until: 2026-09-01 falls before --since (2026-09-14).
```

The clone is a mirror, made once and thereafter fetched into, so a run costs one
round trip however many students are graded. Delete `--cache` to start over.

### How the rubric is decided

Each line of the rubric needs a rule, and two of the three are less obvious than
they look.

*The branch* must be named exactly the netid, ignoring case, and its tip must
fall inside the window: `jit45` counts toward `jit45`, `jit45-2` does not. The
hash reported is the branch tip, since git has no commit which "creates" a
branch.

*The two files* are the ones added by the student's own commits: those along
their branch's own first parent, made since `--since`, and written by whoever
wrote the branch's most recent ordinary commit. Each of those conditions earns
its keep against the real repository. "Files not reachable from `main`" would
score zero for every student who did step 2, since merging your branch into
`main` puts your commits there. Taking the whole branch would credit a student
with the classmate's branch they merged in. Skipping the author check would
credit them with whatever their classmates committed straight to `main` before
their branch was cut. Files that are modified, renamed, or deleted do not count
— only files added — so a student who edits an existing file scores nothing on
this line.

*The merge* must be a merge commit reachable from `main` whose message's first
line, ignoring case and surrounding whitespace, is `<netid>: merge branch with
main`, and which brings in someone else's work. Who a merge belongs to comes
from that message rather than from its author, since a commit records a person's
name and not their netid. "Someone else's" is decided by reachability, and by
the commits the merge puts on `main` rather than by the branch it names: a
commit is the student's own only when their branch can reach it and no other
student's branch can. So a classmate's branch which this student had already
merged into their own still counts as the classmate's, whether the student then
merges that branch into `main` or merges their own branch carrying it. A merge
of a branch holding nothing but the student's own commits earns nothing.

Checks
------

Before submitting a pull request, run every check at once:

```console
$ poetry run python tests/pre_commit_check.py
```

That is black, flake8, mypy, and pytest, configured as in
[CodeChat\_Server](https://github.com/bjones1/CodeChat_system/tree/master/CodeChat_Server)
— see [pyproject.toml](pyproject.toml) (black and pytest), [.flake8](.flake8),
and [mypy.ini](mypy.ini). Run them individually as `poetry run black .`, `poetry
run flake8`, `poetry run mypy`, `poetry run pytest`.

The tests are entirely offline. For the exporter: timestamp and date-range
handling, name resolution, thread flattening against a stubbed Graph client,
both output formats, and the command line itself through Typer's `CliRunner` —
its three cases all fail during option validation, which happens before sign-in,
so they never reach the network. For the homework grader, there is no stub at
all: the tests build a small class repository with git itself — one branch per
student, a bystander's commit straight to `main`, a branch left over from last
year, a student known only by the merge they made, and the merges the students
made — then grade it and check the rubric against real commits. Each of the
judgment calls described above has a student in that repository whose grade
depends on it, and the roster the tests check is the one the tool reads back out
of that repository. For coverage, configured by
[.coveragerc](.coveragerc):

```console
$ poetry run coverage run -m pytest
$ poetry run coverage combine
$ poetry run coverage report
```

The gap in coverage is deliberate: sign-in, the Graph HTTP client, and the body
of `export` past validation all require a live tenant, so they are exercised by
running the tool rather than by the test suite. The homework grader has no such
gap — it needs nothing but git.

Notes and limits
----------------

* **Permissions.** The first sign-in asks you to consent to
  `ChannelMessage.Read.All`. Some tenants disable user consent, in which case an
  administrator must grant it once for the Graph CLI client, or you must
  register your own public client and pass `--client-id`.
* **Private and shared channels** live on different Graph endpoints than
  standard channels. This script handles standard channels; a private channel
  will fail at the message listing step.
* **Whole-channel paging.** Graph orders channel messages by *last modified*
  time and offers no server-side date filter here, so the script pages the whole
  channel and filters locally. That is always correct, and fast enough for a
  class channel, but it does mean the run time grows with the channel's total
  history rather than with the date range.
* **Inline images and attachments** are referenced by the body HTML but are not
  downloaded. The URLs require authentication, so the HTML column renders text
  and formatting, not pictures.
* **Who wrote a commit** is how the grader tells a student's work from a
  classmate's, and it reads the author's address to do it. A student who commits
  from two different addresses — a laptop and the GitHub web editor, say — will
  be credited only with the commits written from the address their branch tip
  carries. Check any grade which looks low before sending it out.
* **Unpushed work is invisible.** Step 3 of the assignment carries no points of
  its own for exactly this reason: what was never pushed cannot be graded, and
  so scores zero on every line. It is also why a student who pushed nothing has
  no row at all until `--netids` names them.
* **A branch is placed by its tip.** A student whose branch was last committed
  to outside the window is neither graded nor found, even if the commits behind
  that tip fall inside it. Widen the window rather than narrowing it if a grade
  or a student goes missing.
* **Student data.** Exports contain student names and everything they wrote, and
  `grades.csv` contains grades. The repository's `.gitignore` keeps `.csv` and
  `.json` files, and the mirror clone, out of git; keep it that way.
