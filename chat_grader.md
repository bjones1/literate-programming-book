Tools
===========

Python Implementation
---------------------

* For Python, use Poetry for package management.
* Add standard test/lint tools (see
  https://github.com/bjones1/CodeChat\_system/blob/master/CodeChat\_Server/tests/pre\_commit\_check.py
  and config files at
  https://github.com/bjones1/CodeChat\_system/tree/master/CodeChat\_Server).
* Use https://github.com/fastapi/typer for the CLI.



Chat grader
-----------

1. Given a date range, extract MS Teams chat history for a specific channel.
2. Convert this chat history into a CSV file with three columns: timestamp, user
   name, and HTML of the chat.
3. Given a set of *n* grading criteria, add an additional columns to the CSV:
   Fulfills grading criteria *n*. Each column should be a grade between 0% (for
   a chat that is unrelated to the grading criterion) and 100% (for a chat that
   completely fulfills that criterion).

Git homework grader
-------------------

Create a grading tool which grades the following homework assignment:

> In the [class](https://github.com/bjones1/literate-programming-fall-2024/) repository:
>
> 1. Create a branch whose name is your netid. Commit two files to it.
> 2. Merge someone else's branch into the main branch. The commit message must be: "<your netid>: merge branch with main".
> 3. Push all your changes to the repository.


A netid is the unique username assigned to every student. Do not keep a roster:
given a start and an end date, grade every netid the repository itself shows
working between them -- everyone who pushed a branch whose tip was committed in
that range, and everyone whose netid a merge made in that range names in its
message, which is the only trace of a student who merged without pushing a
branch of their own. Both dates are whole days, and both count in full. A netid
may also be named on the command line, for a student who left nothing behind at
all and would otherwise have no row.

The grading rubric is:

____/30 points -- Branch created with your netid. Commit hash: _________
____/30 points (15 points per file) -- Two files committed to this branch. Commit hash(es): _________, _________
____/40 points -- At least one merge commit exists with the correct commit message. Commit hash: _________

These lines are also the feedback text, so they stay short; the rules for
applying them follow. All branch names and commit messages are compared ignoring
case and surrounding whitespace.

1. *Branch.* A branch on the remote whose name is exactly the netid: `jit45`
   counts, `jit45-2` and `bensBranch` do not. Report the branch's tip commit.
   Without such a branch, this line and the next both score 0.
2. *Two files.* Files added by the student's own commits on that branch: the
   commits along the branch's own first parent, made this year, and written by
   the student -- who is taken to be the author of the branch's most recent
   ordinary commit, since a commit records a person's name rather than their
   netid. Work merged *in* arrives as a second parent and so does not count,
   and neither does the history the branch was cut from, which may well include
   a classmate's commit straight to `main`. "Not reachable from `main`" will
   not serve here: a student who merges their branch into `main`, as step 2
   asks them to, has put every one of their commits on `main`. Score 15 points
   per file, to a maximum of 30, no matter how many the branch adds. Report the
   hash of the commit which added each file, in the order added, so a single
   commit adding both files is reported twice. Files that are modified,
   renamed, or deleted do not count.
3. *Merge.* A commit with two or more parents, reachable from `main`, whose
   *first* message line is `<netid>: merge branch with main` -- only the first
   line, since Git appends its own body text to a merge message. The merge must
   bring in someone else's work, judged by the commits it adds to `main` --
   those its later parents reach and its first parent does not -- rather than by
   the branch it names. One such commit is the student's own only when their
   netid branch can reach it and no other student's netid branch can, so a
   classmate's branch which this student had already merged into their own is
   still the classmate's, whether the student then merges that branch into
   `main` or merges their own branch carrying it. Merging a branch which holds
   nothing but the student's own commits brings in nobody else's work and so
   earns nothing. Report the earliest qualifying commit.

The class repository carries branches and commits from previous years of this
course, and some netids recur between years; this is what the start date is for,
and it defaults to 2026-Aug-01. Nothing committed outside the date range counts,
toward a grade or toward being graded at all. Step 3 of the assignment earns no points of its own, since work
which was never pushed is invisible to the grader and so scores zero already.

The tool should output a simple CSV file with three columns: netid, grade, and
feedback. Write one row per netid found, in alphabetical order. The grade is the point total written as
a percentage, from `0%` to `100%`. The feedback is the three rubric lines, one
per line, with the underlines filled in with the points earned and with commit
hashes abbreviated to eight characters; a criterion which is not met earns 0
points and reads `not found` where its hashes would go. The feedback therefore
contains newlines, and must be quoted as RFC 4180 requires. One row, with its
feedback shown unquoted:

```
ewj55,100%,30/30 points -- Branch created with your netid. Commit hash: a01d9899
           30/30 points (15 points per file) -- Two files committed to this branch. Commit hash(es): a01d9899, a01d9899
           40/40 points -- At least one merge commit exists with the correct commit message. Commit hash: f6fd3bcc
```

Implement this as a second command in the `grader` package, following the
Python conventions above. The class repository is public, so no authentication
is needed: clone it once with `git clone --mirror` and answer every question
from that local clone rather than from the GitHub API, which keeps the run
reproducible and cheap across the repository's many branches. Write the CSV into
the `grader` directory, whose `.gitignore` entry already keeps `*.csv` --
here, student grades -- out of the repository.
