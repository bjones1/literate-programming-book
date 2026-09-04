Class notes
===========

Friday, 2026-Sep-04
-------------------

1. Start using Capture! Follow the
   [setup guide](course_materials/capture-token-setup-guide.html) then message
   me on Teams.
2. The origins of literate programming:
   1. Knuth introduced the idea of writing for a person. Literate source code is
      ordered topically; weave typesets it as HTML/PDF, while while reorders it
      to conform to compiler requirements. Used TeX along with somewhat cryptic
      markup. Spawned many follow-up tools; rarely adopted.
   2. Documentation generators provide markup in comments, allowing
      documentation to be interleaved with source. The resulting HTML is
      produced by reordering the source tree. These only generate API
      documentation; they cannot be used to describe the inner workings of a
      program. Widely adopted.
   3. Computational notebooks (literate computing) mix blocks of code with
      blocks of formatted documentation. Each code block can be independently
      executed. These cannot be used to write larger programs; code blocks
      cannot be interrupted with documentation between statements. Widely
      adopted.
   4. The CodeChat family. Markup in comments
3. [Introduction to Git](git_intro.md).


Wednesday, 2026-Sep-02
----------------------

> The idea is that you do not document programs (after the fact), but write
> documents that contain the programs.

1. Questions? [Schedule a meeting](https://bjones.youcanbook.me).

2. [Homework](https://canvas.msstate.edu/courses/186065/assignments) - due
   Sunday!

3. CodeChat Editor update -- verify you have v0.2.2!

   ![Screenshot of Visual Studio Code with the Extensions panel open and the CodeChat Editor extension selected, which shows the currently installed version in the lower left-hand corner](course_materials/CodeChat_Editor_v0.2.2.png)

4. Start using Capture! Follow the
   [setup guide](course_materials/capture-token-setup-guide.html) then message
   me on Teams.

5. Field notes -
   [htmd](https://github.com/letmutex/htmd/pulls?q=is%3Apr+is%3Aclosed),
   review/implementation in htmd.

6. Today's topic: the [origins of literate programming](origins.md).

Monday, 2026-Aug-31
-------------------

1. [Resources](README.md)
2. Questions? [Schedule a meeting](https://bjones.youcanbook.me).
3. [Homework](https://canvas.msstate.edu/courses/186065/assignments) - due
   Sunday!
4. Updated class schedule (see table of contents).
5. Quote:
   > "The model's job is to produce something plausible. Your job is to make
   > sure only one thing is plausible."
6. Writing must be specific.
7. Always employ LLM review (code, specs, etc.).
8. Keep specs close to code (literate programming, using the CodeChat Editor).
9. Drive LLMs from specs in code/docs, not from prompts.
10. Ensure cognitive engagement.
11. Today's topic: the [origins of literate programming](origins.md).

Friday, 2026-Aug-28
-------------------

1. CodeChat Editor Capture
2. Today's topic: write tests.
