MSU class notes
===============

Week 5
------

### Wednesday, 2026-Sep-23

1. [Homework](https://canvas.msstate.edu/courses/186065/assignments) - due
   Sunday!
2. Dev notes -- [pnpm issue triage](https://github.com/pnpm/pnpm/issues).
3. Enable Capture when using the CodeChat Editor.
6. Spec design for
   [git-hint](https://github.com/bjones1/literate-programming-fall-2024), on the
   `git-tool` branch.

### Monday, 2026-Sep-21

1. [Homework](https://canvas.msstate.edu/courses/186065/assignments) - due
   Sunday!
2. Dev notes -- [htmd](https://github.com/letmutex/htmd) project.
3. Enable Capture when using the CodeChat Editor.
4. Discussion -- what is the appropriate use of AI when developing open-source
   software?
   1. Not allowed --
      [Zig](https://ziglang.org/code-of-conduct/#strict-no-llm-no-ai-policy)
   2. Human review --
      [LLVM](https://discourse.llvm.org/t/rfc-llvm-ai-tool-policy-human-in-the-loop/89159#p-355841-llvm-ai-tool-use-policy-1)
      (require human review)
   3. Higher standard - Rust
      ([explanation](https://blog.rust-lang.org/inside-rust/2026/08/05/rust-langrust-is-adopting-an-llm-policy/)),
      ([policy](https://forge.rust-lang.org/policies/llm-usage.html))
   4. Just a tool --
      [Linux](https://lore.kernel.org/linux-media/CAHk-=wi4zC+Ze8e+p3tMv8TtG_80KzsZ1syL9anBtmEh5Z40vg@mail.gmail.com/)
5. CodeChat Editor [manual](course_materials/CodeChat-Editor-manual.md). To
   create a CodeChat Editor project, simply add a `toc.md`.
6. Spec design for
   [git-hint](https://github.com/bjones1/literate-programming-fall-2024), on the
   `git-tool` branch.
   1. Brainstorm several hints in each category.
   2. Generalize these to principles.
   3. Develop an overall architecture.
   4. Derive a detailed specification.
   5. Include test cases to explore corner cases.

Week 4
------

### Friday, 2026-Sep-18

1. [Homework](https://canvas.msstate.edu/courses/186065/assignments) - due
   Sunday! See the
   [pull requests](https://github.com/bjones1/literate-programming-github-fall-2026/pulls)
   (PRs).
2. Enable Capture when using the CodeChat Editor.
3. Git tracks files, not directories.
4. Install the
   [VSCode Live Share](https://marketplace.visualstudio.com/items?itemName=MS-vsliveshare.vsliveshare)
   extension.
5. CodeChat Editor [manual](course_materials/CodeChat-Editor-manual.md).
6. Spec design for
   [git-hint](https://github.com/bjones1/literate-programming-fall-2024), on the
   `git-tool` branch.

### Wednesday, 2026-Sep-16

> LLMs are excellent instruments and unreliable diagnosticians. Use them for the
> instrument work — writing the utility, running the sweep, formatting the
> analysis — and keep the diagnostic judgment for yourself. -- Evan Chan,
> [Making io\_uring Actually Fast: I/O Threads, Chunking, and the Memory Story Nobody Talks About](https://www.conviva.ai/resource/making-io_uring-actually-fast-i-o-threads-chunking-and-the-memory-story-nobody-talks-about/);
> see section "Debugging with an LLM in the loop."

1. [Homework](https://canvas.msstate.edu/courses/186065/assignments) - due
   Sunday!
2. Enable Capture when using the CodeChat Editor.
3. Creating simple utilities. See the
   [class repo](https://github.com/bjones1/literate-programming-fall-2024).
   Ideas:
   1. Tetris, maybe with Git
   2. Pong, with ?
   3. Hints utility for CLI Git
      1. If files are changes, wait bit, then pop up a note: need to stage?
      2. Have highlighted/hyperlinked items with links to definitions. Hover
         summary, click for deep info.
   4. Game day parking, game day tailgating? Open spots, where people are, etc.
4. Creating a new CodeChat Editor project.

#### In-class exercises

1. Ideas for projects.

### Monday, 2026-Sep-14

1. [Homework](https://canvas.msstate.edu/courses/186065/assignments) - due
   Sunday!
2. Ensure you're running the
   [latest version of the CodeChat Editor](https://github.com/bjones1/CodeChat_Editor/releases).
3. Become familiar with [CommonMark](https://commonmark.org/help/), which is
   used by the CodeChat Editor to format comments. The CodeChat Editor also
   supports many
   [GitHub extensions](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
   to CommonMark.
4. Fast enterprises.
5. Exercises using GitHub: browse to
   [https://github.com/bjones1/literate-programming-github-fall-2026](https://github.com/bjones1/literate-programming-github-fall-2026).

#### In-class exercises

1. Browse to
   [https://github.com/bjones1/literate-programming-github-fall-2026](https://github.com/bjones1/literate-programming-github-fall-2026).
2. Paste an image of a failed push to the
   [https://github.com/bjones1/literate-programming-github-fall-2026](https://github.com/bjones1/literate-programming-github-fall-2026)
   in the chat.
3. Show a screenshot of `git remote -v`.
4. Send a PR with an example commit to the same repo. Your PR must be titled
   `<your netid>: in-class exercise`.

Week 3
------

### Friday, 2026-Sep-11

1. [AI Efficiency Could Cost Us the Next Generation of Experts](https://spectrum.ieee.org/ai-engineer-skills)
2. [OpenAI – Hugging Face Incident Technical Report](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf)
3. [Homework](https://canvas.msstate.edu/courses/186065/assignments) - due
   Sunday!
4. Using LLMs with Git.
5. Review of Git and the VSCode Git GUI.

#### In-class exercises

1. Longest-running LLM query?

### Wednesday, 2026-Sep-09

> "Technology and coding are always evolving, so the implementation is not
> nearly as important as the reasoning behind it." - Justin Gray

1. [AI coding article](https://spectrum.ieee.org/ai-code-review-software-engineers) -
   spec writing is central. See "AI Agents in Code Review Workflows" section.
2. Homework is graded.
3. [Homework](https://canvas.msstate.edu/courses/186065/assignments) - due
   Sunday!
4. Be concise; LLMs aren't by default.
5. [Introduction to Git](git_intro.md) and GitHub.

#### In-class exercises

1. Paste an image of the e-book repo, showing today's commits, in the Teams
   chat.
2. Paste an image from the e-book repo in the chat of:
   1. A change to a file in a commit.
   2. A file in a commit.
   3. A commit.
   4. A local branch (create if necessary).
   5. A remote branch.
   6. The Changes part of the VSCode Git GUI, showing a changed file and a
      staged file.

Week 2
------

### Friday, 2026-Sep-04

1. Start using Capture! Follow the
   [setup guide](course_materials/capture-token-setup-guide.html) then message
   me on Teams.
2. The origins of literate programming: (TODO: add a summary image for each)
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
   4. The CodeChat family. Markup in comments.
3. [Introduction to Git](git_intro.md).

### Wednesday, 2026-Sep-02

> The idea is that you do not document programs (after the fact), but write
> documents that contain the programs. —John Max Skaller

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

### Monday, 2026-Aug-31

1. [Resources](README.md)

2. Questions? [Schedule a meeting](https://bjones.youcanbook.me).

3. [Homework](https://canvas.msstate.edu/courses/186065/assignments) - due
   Sunday!

4. Updated class schedule (see table of contents).

5. Quote:

   > "The model's job is to produce something plausible. Your job is to make
   > sure only one thing is plausible." -- Claude

6. Writing must be specific.

7. Always employ LLM review (code, specs, etc.).

8. Keep specs close to code (literate programming, using the CodeChat Editor).

9. Drive LLMs from specs in code/docs, not from prompts.

10. Ensure cognitive engagement.

11. Today's topic: the [origins of literate programming](origins.md).

Week 1
------

### Friday, 2026-Aug-28

1. CodeChat Editor Capture
2. Today's topic: write tests.
