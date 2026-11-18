Tools
=====

Python Implementation
---------------------

* For Python, use uv for package management.
* Add standard test/lint tools (see
  [https://github.com/bjones1/CodeChat_system/blob/master/CodeChat_Server/tests/pre_commit_check.py](https://github.com/bjones1/CodeChat_system/blob/master/CodeChat_Server/tests/pre_commit_check.py)
  and config files at
  [https://github.com/bjones1/CodeChat_system/tree/master/CodeChat_Server](https://github.com/bjones1/CodeChat_system/tree/master/CodeChat_Server)).
* Use [https://github.com/fastapi/typer](https://github.com/fastapi/typer) for
  the CLI.

Download team info
------------------
Some copy and paste, some fill in the blanks.

```PowerShell
# One-time installs.
Install-Module MicrosoftTeams -Scope CurrentUser
Install-Module Microsoft.Graph.Authentication, Microsoft.Graph.Users, Microsoft.Graph.Groups -Scope CurrentUser

# Authenticate.
Connect-MicrosoftTeams
Connect-MgGraph -Scopes "User.ReadBasic.All"

# Find the team's GroupId. Use this in the next step.
Get-Team -DisplayName "<Your team name>"

# Download data.
$groupId = "<groupId here>"
Get-TeamUser -GroupId $groupId | ForEach-Object {
    Get-MgUser -UserId $_.User -Property DisplayName,GivenName,Surname,Mail,UserPrincipalName
} | Select-Object DisplayName, GivenName, Surname, Mail, UserPrincipalName |
    Export-Csv team_members_names.csv -Encoding utf8BOM
```

This still needs some processing, since KBTU has Family Name then Given name in their downloads, and the Russian version includes a patronymic.

I need more permission to be allowed to upload grades. But KBTU might give that to me.

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

> Your userid is your KBTU e-mail address without the @kbtu.kz suffix. For
> example, my e-mail address is b.jones@kbtu.kz so my userid is b.jones.
>
> In the
> [class repository](https://github.com/bjones1/literate-programming-git-2026):
>
> 1. Create a branch whose name is your userid. Commit two new files to it.
> 2. Merge someone else's branch into the main branch. The commit message must
>    be: "\<your userid>: merge branch with main".
> 3. Push all your changes to the repository.

A userid is the unique username assigned to every student. Do not keep a roster:
given a start and an end date, grade every userid the repository itself shows
working between them -- everyone who pushed a branch whose tip was committed in
that range, and everyone whose userid a merge made in that range names in its
message, which is the only trace of a student who merged without pushing a
branch of their own. Both dates are whole days, and both count in full. A userid
may also be named on the command line, for a student who left nothing behind at
all and would otherwise have no row.

The grading rubric is:

30 points -- Branch created with your userid.
30 points (15 points per file) -- Two files committed to this branch.
40 points -- At least one merge commit exists with
the correct commit message.

These lines are also the feedback text, so they stay short; the rules for
applying them follow. All branch names and commit messages are compared ignoring
case and surrounding whitespace.

1. *Branch.* A branch on the remote whose name is exactly the userid: `jit45`
   counts, `jit45-2` and `bensBranch` do not. Report the branch's tip commit.
   Without such a branch, this line and the next both score 0.
2. *Two files.* Files added by the student's own commits on that branch: the
   commits along the branch's own first parent, made this year, and written by
   the student -- who is taken to be the author of the branch's most recent
   ordinary commit, since a commit records a person's name rather than their
   userid. Work merged *in* arrives as a second parent and so does not count,
   and neither does the history the branch was cut from, which may well include
   a classmate's commit straight to `main`. "Not reachable from `main`" will not
   serve here: a student who merges their branch into `main`, as step 2 asks
   them to, has put every one of their commits on `main`. Score 15 points per
   file, to a maximum of 30, no matter how many the branch adds. Report the hash
   of the commit which added each file, in the order added, so a single commit
   adding both files is reported twice. Files that are modified, renamed, or
   deleted do not count.
3. *Merge.* A commit with two or more parents, reachable from `main`, whose
   *first* message line is `<userid>: merge branch with main` -- only the first
   line, since Git appends its own body text to a merge message. The merge must
   bring in someone else's work, judged by the commits it adds to `main` --
   those its later parents reach and its first parent does not -- rather than by
   the branch it names. One such commit is the student's own only when their
   userid branch can reach it and no other student's userid branch can, so a
   classmate's branch which this student had already merged into their own is
   still the classmate's, whether the student then merges that branch into
   `main` or merges their own branch carrying it. Merging a branch which holds
   nothing but the student's own commits brings in nobody else's work and so
   earns nothing. Report the earliest qualifying commit.

The tool should output a simple CSV file with three columns: userid, grade, and
feedback. Write one row per userid found, in alphabetical order. The grade is
the point total written as a percentage, from `0%` to `100%`. The feedback is
the three rubric lines, one per line, with the underlines filled in with the
points earned and with commit hashes abbreviated to eight characters; a
criterion which is not met earns 0 points and reads `not found` where its hashes
would go. The feedback therefore contains newlines, and must be quoted as RFC
4180 requires. One row, with its feedback shown unquoted:

```
ewj55,100%,30/30 points -- Branch created with your userid. Commit hash: a01d9899
           30/30 points (15 points per file) -- Two files committed to this branch. Commit hash(es): a01d9899, a01d9899
           40/40 points -- At least one merge commit exists with the correct commit message. Commit hash: f6fd3bcc
```

Implement this as a second command in the `grader` package, following the Python
conventions above. The class repository is public, so no authentication is
needed: clone it once with `git clone --mirror` and answer every question from
that local clone rather than from the GitHub API, which keeps the run
reproducible and cheap across the repository's many branches. Write the CSV into
the `grader` directory, whose `.gitignore` entry already keeps `*.csv` -- here,
student grades -- out of the repository.
