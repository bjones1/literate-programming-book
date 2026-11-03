<h1 id="cc--AgC5ADOps">
  Guidelines for specification-driven design using LLMs
</h1>

The purpose of writing a specification is to come to a deeper understanding of
the problem you're solving. Take time to step back, think about the overall
approach, re-read the specification, and find creative solutions. The
specification is the LLM's primary input; a well-written specification is the
foundation for a good implementation.

Specification design
--------------------

1. Record your ideas in a specification or set of design requirements, formatted
   in Markdown.
2. Be concise; use only the minimum of prose needed to fully define the desired
   behavior.
3. When composing the specification, consider: What is the purpose of this code?
   How can it best be expressed or explained?
4. Use pseudocode, block diagrams, flowcharts, truth tables, etc. to visually
   capture your idea. See guidelines on [diagrams](#cc-M8IRskMnku) and on
   [equations and tables](#cc-zoUcUJXRmm).
5. Write down the expected inputs, expected outputs, and record an approach to
   produce the desired outputs from the provided inputs.
6. Anticipate any corner cases or problems your approach must correctly handle.
7. Include hyperlinks to relevant specifications, API documentation, etc. This
   improves LLM reasoning and context.
8. If the code becomes long or complex, re-consider your approach: would
   dropping features or relaxing constraints help simplify the resulting
   implementation?
9. Define data structures as part of the design. For example, the CodeChat
   Editor's
   [cache design](https://github.com/bjones1/CodeChat_Editor/blob/main/server/src/processing/cache.rs)
   is heavily structured by this approach.
10. Where possible, avoid OS-specific and language-specific details in a
    specification. When necessary, place these in an implementation section.

Additional resources:

* [A practical guide to writing technical specs](https://stackoverflow.blog/2020/04/06/a-practical-guide-to-writing-technical-specs/).

LLM use
-------

### Setup

1. Provide context for LLMs: Avoid browser-based chat interfaces for software
   development. Instead, use an IDE plugin, or the desktop/CLI app run from your
   project's root folder, so the LLM can see all project files, compile and run
   tests, etc.
2. <a id="cc-Rk4wTz8NqB"></a>Install the relevant compiler and tools. LLMs need
   to run tests, throwaway probes, etc. Use a short prompt: "Verify that you can
   build the project in the current git repo and run its tests."
3. Use a paid, high-quality model at high effort levels when possible. The
   quality difference between low-quality and high-quality models is large and
   directly impacts review and implementation quality.
4. Develop an `AGENTS.md` file for each project to enforce project development
   guidelines. For an example, see the CodeChat Editor's
   [`AGENTS.md`](https://github.com/bjones1/CodeChat_Editor/blob/main/AGENTS.md).

### Prompting

1. Keep prompts short: "Review this specification to review.md" or "Implement
   this specification; write comments to review.md." Complexity belongs in the
   specification, not the prompt. See also
   [Iterative review item 4](#cc-jaEUDjWPbS).
2. <a id="cc-Eulg3z82r1"></a> Start a new session for each review or
   implementation; long conversations reduce reproducibility (see
   [Iterative implementation item 2](#cc-0VeK0e9v8J)) and cause
   [context rot](https://www.trychroma.com/research/context-rot). Short
   follow-ups to that work, such as questions about the code or a request to
   commit it, can stay in the same session.
3. Verify APIs, links, and citations suggested by the LLM to avoid hallucinated
   references.

### Iterative review

1. Repeatedly review your specification using an LLM until reviews produce
   trivial or contradictory items. After each review, revise the specification
   manually. Per [Prompting item 2](#cc-Eulg3z82r1), always begin a new session
   with each review.

2. Avoid large LLM edits; in general, allowing LLMs to perform significant
   revisions produces a bloated, overspecified result. Review and manually edit
   any LLM-based edits to your specification.

3. Ask the LLM to focus on short sections of a specification when reviewing or
   implementing: "Review the section titled 'Task lists' of spec.md to
   review.md."

4. <a id="cc-jaEUDjWPbS"></a>To keep track of which issues you've resolved in
   the long list of issues produced by the LLM, either:

   1. Instruct the LLM to place the resulting review in a Markdown-formatted
      file named (for example) `review.md`; add this to `.gitignore`, so the LLM
      doesn't later consider this part of the files to process.
   2. Take the text of an LLM review and copy it. Create a new, empty file
      called `review.md` outside your project, open it in the CodeChat Editor,
      then paste the review into the CodeChat Editor Client (the rendered,
      editable view of the file).

   As you address each point in the review, delete it or format it using
   strikethrough to keep track of which issues remain.

### Iterative implementation

1. After an LLM implementation, repeatedly ask the LLM to review its work,
   starting a new session with each repetition, until reviews produce trivial or
   contradictory items. Study the issues raised to see if the spec needs
   revision, or if these issues are relevant only to the implementation.

2. <a id="cc-0VeK0e9v8J"></a>If an implementation is unsatisfactory, or you made
   large changes to the spec that produced a code mess, simply throw away the
   code and have the LLM regenerate it from your spec.

3. Ask the LLM about portions of the code that you don't understand. Make sure
   the overall flow of what the LLM implemented makes sense.

4. Update the approach in your spec as you learn what works (and doesn't work)
   through the implementation process.

5. Explain any code that took significant development or debugging time, or that
   is difficult to understand.

Security
--------

Be careful what information you disclose or provide to LLMs:

1. Don't put sensitive or confidential information into prompts or files your
   LLM reads. LLM agents usually have access to all files in your project.
2. Don't let an agent with access to private data and network/tool access
   process untrusted content (web pages, issues, emails); see
   [Simon Willison: The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/).

Git
---

1. Refer to files by their git state: "Review the changed/staged files."
2. Refer to changes across multiple files: "Implement the staged changes to the
   spec." This focuses the LLM on the changed lines, rather than on the entire
   file (often what you want).
3. Before letting an LLM edit your spec, stage your own edits. The LLM's changes
   then appear as the only unstaged diff, so you can review, refine, or discard
   just those changes.
4. When the LLM contributes to your code or spec, acknowledge it; for example,
   add a line such as `Co-Authored-By: <model name>
   <noreply@llm-company-address.com>` to your commits, pull requests, issue
   comments, etc.
5. Ask the LLM to commit changes after finishing an iterative implementation. It
   writes a helpful commit message; review the message before the actual commit.
6. Ask the LLM to resolve merge or rebase conflicts. Review the results; LLMs
   can drop part of a conflict as a "resolution."
7. If a series of LLM interactions produces a large number of changes, ask the
   LLM to split the changes into a series of commits.

Testing
-------

1. Create tables that describe the input and expected output to define a series
   of test cases.
2. Think carefully when creating test cases; this is an important form of
   design. What valid input could cause the implementation to produce incorrect
   output?
3. Verify that when the LLM implements a specification, it also implements tests
   defined in the spec; verify that it runs existing tests before completing an
   implementation (see [Setup item 2](#cc-Rk4wTz8NqB)).
4. Ensure that the LLM didn't weaken, skip, or rewrite tests to make them pass.
   Run the tests yourself after the LLM reports success; LLMs sometimes claim
   tests pass without running them, or after running only some of them.

[CodeChat Editor](https://github.com/bjones1/CodeChat_Editor#welcome-to-the-codechat-editor)
guidelines
--------------------------------------------------------------------------------------------

1. Employ CodeChat Editor project features:
   1. Create a project by placing a `toc.md` at the root of the project.
   2. For each file, add a unique ID to the level-1 heading for that file:
      <br>`<h1 id=*>Cache design</h1>`<br>When you edit this heading in the
      Client, it replaces the `*` with a generated unique ID.
   3. In the table of contents (`toc.md`), add an `<xref ref=unique_id></xref>`
      to refer to this file by its level-1 heading (the file's title).
   4. When the LLM implements code, instruct it to place a fragment for each
      addition, connecting this back to the spec with a gather in a subheading.
      See the CodeChat Editor's
      [`AGENTS.md`](https://github.com/bjones1/CodeChat_Editor/blob/main/AGENTS.md)
      file. See the
      [CodeChat Editor user guide, Gathering fragments section](https://github.com/bjones1/CodeChat_Editor/blob/main/README.md#gathering-fragments);
      this is best viewed in the CodeChat Editor, where cross-references and
      gather elements render.
2. Place long specification documents in a separate file beside the related code
   file, rather than in the code files. See
   [`cache-spec.md`](https://github.com/bjones1/CodeChat_Editor/blob/main/server/src/processing/cache-spec.md)
   and
   [`cache.rs`](https://github.com/bjones1/CodeChat_Editor/blob/main/server/src/processing/cache.rs).
3. <a id="cc-M8IRskMnku"></a>Use diagrams, flowcharts, state machines, etc. as
   necessary to explain your design. The CodeChat Editor supports Mermaid and
   Graphviz diagrams natively; PlantUML diagrams are easy to paste in;
   [draw.io](https://draw.io/) diagrams can be included as images. See the
   [CodeChat Editor user guide, Diagrams section](https://github.com/bjones1/CodeChat_Editor/blob/main/README.md#diagrams).
4. <a id="cc-zoUcUJXRmm"></a>Use
   [equations](https://github.com/bjones1/CodeChat_Editor/blob/main/README.md#mathematics)
   and
   [tables](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-tables)
   where appropriate to specify a design.
5. Use headings to appropriately organize the contents. Near the top of the
   file, include a single level-1 heading, providing the title of the file; per
   MDN HTML recommendations, there should be
   [only one level-1 heading](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/Heading_Elements#avoid_using_multiple_h1_elements_on_one_page).
   For source files, include the file name at the beginning of the title, in a
   monospaced font. Following the title, include additional heading levels;
   [don't skip levels](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/Heading_Elements#navigation),
   e.g., by placing a level-3 heading immediately following a level-1 heading.
   Use headings to provide a natural outline of your program.

Editor configuration
--------------------

Properly configuring the text editor used with the CodeChat Editor significantly
improves the authoring process. Recommended settings:

1. Enable word wrap:
   [VS Code](https://code.visualstudio.com/docs/editing/codebasics#_how-do-i-turn-on-word-wrap)
2. Use spaces, not tabs, for indentation:
   [VS Code](https://code.visualstudio.com/docs/editing/codebasics#_indentation)
3. Enable auto-save:
   [VS Code](https://code.visualstudio.com/docs/editing/codebasics#_save-auto-save)
4. Enable auto-reload (enabled by default in VS Code)
5. On save, remove trailing whitespace:
   [VS Code](https://stackoverflow.com/a/53663494/16038919). Note that two
   trailing spaces indicate a hard line break in Markdown, which
   trailing-whitespace removal would delete. Always write hard line breaks in
   Markdown as `<br>`.
6. Use a spell checker:
   [VS Code](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)
7. On a big monitor, place your IDE side by side with the CodeChat Editor.
