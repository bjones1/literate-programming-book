Contact your team members immediately: send an email to all team members and
copy me to verify you have identified everyone on your team. Note that some
projects have two different teams: "pulldown-cmark / htmd demo" and
"pulldown-cmark / htmd demo 2" are different teams.

Submit a pull request to the instructor's fork of the assigned repo with an
additional section added to the existing specification, or a newly-created
specification, detailing the strategy for your assigned project. Review **only
your section** repeatedly with an LLM until it produces a limited number of
relevant findings. Avoid letting the LLM make significant changes, since these
are often too wordy. Turn the following in:

1. The LLM output from the following prompt: "Verify that you can compile and
   run the project in the current git repo."

2. Create a [table](https://github.github.com/gfm/#tables-extension-) which
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

3. Attach the last review your LLM performed, the prompt you used, and the
   specific LLM you used. For example: "Prompting Claude 5.5 Opus, extra high
   effort, with \`Review the section named "Task lists" in spec.md\` produced
   the following output; strikethrough indicates LLM output that I deemed
   incorrect or irrelevant."
