Project 2 assignments
=====================

Draft submission
----------------

Contact your team members immediately: send an email to all team members and
copy me to verify you have identified everyone on your team. Note that some
projects have two different teams: "pulldown-cmark / htmd demo" and
"pulldown-cmark / htmd demo 2" are different teams.

Submit the following in a pull request to the instructor's fork of the assigned
repo. Each team member must author at least one commit from their own GitHub
account.

1. An additional section added to the existing specification, or a newly-created
   specification, detailing the strategy for your assigned project. Review
   **only your section** repeatedly with an LLM until it produces a limited
   number of relevant findings. Avoid letting the LLM make significant changes,
   since these produce an overspecified result and limit your understanding of
   the problem.

2. A separate document named `submission.md` with the following contents:

   1. A brief, one sentence summary of each person's contributions to the team's
      pull request.

   2. The LLM output from the following prompt, which each team member runs in
      their own clone of the repo on their own computer: "Verify that you can
      compile and run the project in the current git repo."

   3. Create a [table](https://github.github.com/gfm/#tables-extension-) which
      provides the review round, number of findings, and a 1-sentence summary of
      major changes in each round of your review. For example:

      | Round | Findings | Main changes made                                                                                                                                                                                |
      | ----- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
      | 1     | 15       | Rule 1 vs rule 2 contradiction; Kazakh tie-break label was wrong (code point order is not Kazakh alphabetical order); added NFC, apostrophe and hyphen variants, digits inside words, underscore |
      | 2     | 11       | Stress marks and other combining marks (`ма́ма`) no longer split words; rule 2 written as a grammar; examples written with `\u` escapes; more edge examples                                       |
      | 3     | 10       | Sorting on the normalized word (`don’t` vs `dont`); marks not after a letter; NFC, not NFKC (ligature `ﬁ`); final sigma in `lower()`                                                             |
      | 4     | 8        | `str` subclass wording; soft hyphen; marks around apostrophe and hyphen; NFC mark reordering; complexity claim removed                                                                           |
      | 5     | 7        | Rule 2 prose fixed (it contradicted its own grammar); numeric ideographs are letters; surrogates; `ß`/`ss`; zero-width joiner; return types                                                      |
      | 6     | 5        | Findings below, all applied                                                                                                                                                                      |

   4. The last review your LLM performed, the prompt you used, and the specific
      LLM you used. For example: "Prompting Claude Opus 5.5, extra high effort,
      with \`Review the section named "Task lists" in spec.md, writing findings
      to review.md\` produced the following output; strikethrough indicates LLM
      output that I deemed incorrect or irrelevant."

Final submission
----------------

Submit the following via additional commits to the pull request you created for
the draft submission. Each team member must author at least one of these
additional commits from their own GitHub account.

1. Changes to the additional section added to the existing specification, or to
   your newly-created specification, detailing the finalized strategy for your
   team's assigned project. Your team's changes should incorporate instructor
   feedback from your draft submission pull request. Review **only your
   section** repeatedly with an LLM until it produces trivial or contradictory
   findings. Avoid letting the LLM make significant changes, since these produce
   an overspecified result and limit your understanding of the problem.

2. An implementation of this section of the specification using an LLM, followed
   by repeated reviews of the implementation until the LLM produces trivial or
   contradictory findings.

3. Changes to `submission.md` with the following contents:

   1. A brief, one sentence summary of each person's contributions to the team's
      pull request.

   2. Create two [tables](https://github.github.com/gfm/#tables-extension-)
      which provide the review round, number of findings, and a 1-sentence
      summary of major changes in each round of your review. One table covers
      specification review (include only results from this assignment, not from
      the draft review rounds); the second table covers implementation review.

   3. The last specification review your LLM performed, the prompt you used, and
      the specific LLM you used.

   4. The last implementation review your LLM performed, along with the prompt
      and LLM used, following the same format.
