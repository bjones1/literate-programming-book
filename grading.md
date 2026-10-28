Students submitted the following homework assignment:

> Your userid is your KBTU e-mail address without the `@kbtu.kz` suffix. For
> example, my e-mail address is `b.jones@kbtu.kz` so my userid is `b.jones`.
>
> In this assignment, you must:
>
> 1. Fork and clone the
>    [assignment's repository](https://github.com/bjones1/literate-programming-github-2026);
>    the upstream remote should be the assignment repository, while the origin
>    remote should be your fork. See the e-book Introduction to Git and GitHub
>    page for additional details on working with GitHub.
> 2. Add a commit in a directory named by your userid: for me, the directory
>    name would be `b.jones`. The contents of your commit should contain two
>    files in this directory:
>    1. `spec.md`, your specification for the
>       [Top words problem](https://github.com/bjones1/literate-programming-book/blob/main/exercises/top-words.md)
>       from the e-book.
>    2. `llm-review.md`, a output of an LLM review showing the last review your
>       LLM performed, the prompt you used, and the specific LLM you used. For
>       example: "Prompting Claude 5.5 Opus, extra high effort, with `Review
>       spec.md` produced the following output; strikethrough indicates LLM
>       output that I deemed incorrect or irrelevant."
> 3. Send a pull request (PR) with this commit by 11:59 PM on Wednesday, Oct
>    21st.
> 4. Respond to the provided feedback by adding a commit which addresses the
>    problems found. Push this commit, which adds it to your PR.
>
> You will receive credit for this assignment only when your PR is merged.

Most students have submitted the initial PR to
https://github.com/bjones1/literate-programming-github-2026, and I (GitHub user
`bjones1`) have responded to each with a "Request changes" review. Use `gh` to
read the PRs.

Grade a PR only if at least one commit follows the commit that my latest
"Request changes" review was made on (the review's `commit_id`). Include merged
PRs. Ignore CodeRabbit's reviews and comments.

My feedback is the whole body of that latest review. This includes any LLM review
pasted into it, and anything it points to: for example, "the issues identified by
your LLM review" means the `llm-review.md` at the reviewed commit. Split the
feedback into separate required changes. For each one, compare the PR at the
reviewed commit with its current head. A change counts as made if the student
made it, or if they gave a reason for rejecting it (strikethrough in
`llm-review.md` counts as a reason). A new `llm-review.md` counts only if it
reviews the current `spec.md`, names the prompt and the LLM, and shows no
significant open issues.

Rate each PR:

* No: none of the required changes were made.
* Some: fewer than half were made.
* Most: at least half, but not all, were made.
* All: every required change was made.

Output a Markdown table with one row per graded PR, sorted by PR number, with
these columns:

- PR #
- Userid: the name of the directory holding the student's files, or "(none)"
  followed by their GitHub login if the files aren't in a directory.
- Rating (no/some/most/all)
- Notes: the required changes that were not made.

After the table, list each PR you skipped and why.