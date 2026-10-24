# <span id="cc--AgC5ADOps">Guidelines for LLM-based software development</span>

LLM use
-------

1. Keep prompts short: "Review this specification" or "Implement this
   specification."

2. Start a new session when providing a prompt of this type; this helps avoid
   [context rot](https://www.salesforce.com/artificial-intelligence/ai-context/context-rot/).

3. Avoid long conversations with the LLM. This reduces reproducibility (see
   item 11) and leads
   to [context rot](https://www.salesforce.com/artificial-intelligence/ai-context/context-rot/).

4. Repeatedly review your specification using an LLM until reviews produce
   trivial or contradictory items. After each review, revise the specification
   manually. Per item 2, always begin a new session with each review.

5. Be concise. In general, allowing LLMs to perform significant revisions
   produces a bloated, overspecified result. Review and manually edit any
   LLM-based edits to your specification.

6. Ask the LLM to focus on short sections of a specification when reviewing or
   implementing: "Review the section titled 'Task lists' of spec.md". Asking for
   a review/implementation of one section produces better results.

7. Provide context for LLMs: Avoid web use of LLMs for software development.
   Instead, use an IDE plugin, or the desktop/CLI app run from your project's
   root folder, so the LLM can see all project files.

8. After an LLM implementation, repeatedly ask the LLM to review its work,
   starting a new session with each repetition. Study the issues raised to see
   if the spec needs revision, or if these issues are relevant only to the
   implementation.

9. Use a paid, high-quality model at high effort levels when possible. The
   quality difference between low-quality and high-quality models is large and
   directly impacts review quality.

10. To keep track of which issues you've resolved in the long list of issues
    produced by the LLM, either:

    1. Instruct the LLM to place the resulting view in a Markdown-formatted file
       named (for example) `review.md`.
    2. Take the text of an LLM review and copy it. Create a new, empty file
       called `review.md`, open it in the CodeChat Editor, then paste the review
       into the CodeChat Editor Client (the rendered, editable view of the
       file).

    As you address each point in the review, delete it in the Client or format
    it using strikethrough to keep track of which issues remain.

11. If an implementation is unsatisfactory, or you made large changes to the
    spec that produced a code mess, simply throw away the code and have the LLM
    regenerate it from your spec.

12. Develop an `AGENTS.md` file for each project to enforce project development
    guidelines. For an example, see the CodeChat Editor's
    [`CLAUDE.md`](https://github.com/bjones1/CodeChat_Editor/blob/main/CLAUDE.md)
    (Claude's name for this file).

13. Ask the LLM about portions of the code that you don't understand. Make sure
    the overall flow of what the LLM implemented makes sense.

Security
--------

Be careful what information you disclose to LLMs:

1. Don't put sensitive or confidential information into prompts or files your
   LLM reads.
2. Ask the LLM to review only information yor trust; see
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
   add a line such as "Co-Authored-By: \<model name>
   \<noreply@llm-company-address.com>" to your commits, pull requests, comments,
   etc.
5. Ask the LLM to commit changes after it makes edits. It usually writes a
   helpful commit message.
6. Ask the LLM to resolve merge or rebase conflicts.
7. If a series of LLM interactions produces a large number of changes, ask the
   LLM to split the changes into a series of commits.

Specification design
--------------------

1. Record your ideas in a specification or set of design requirements, formatted
   in Markdown.
2. When composing the specification, consider: What is the purpose of this code?
   How can it best be expressed or explained?
3. Use pseudocode, block diagrams, flowcharts, truth tables, etc. to visually
   capture your idea. See [futher](#cc-M8IRskMnku) [guidelines](#cc-zoUcUJXRmm).
4. Write down the expected inputs, expected outputs, and record an approach to
   produce the desired outputs from the provided inputs.
5. Anticipate any corner cases or problems your approach must correctly handle.
6. Include links to relevant specifications, documentation, and ideas.
7. Update the approach you sketched out as you learn what works (and doesn't)
   through the implementation process.
8. Add additional explanation for any pieces of code that took significant
   development or debug time, or which contain difficult-to-understand code.
9. The purpose of writing a specification is not to eliminate LLM review issues,
   but to come to a deeper understading of the problem you're solving. Take time
   to step back, think about the overall approach, re-read the specification,
   and find unique solutions. Don't simply rely on LLM review.
10. If the code becomes long or complex, re-consider your approach: would
    dropping features or relaxing constraints help simplify the resulting
    implementation?
11. Define data structures as part of the design. For example, the CodeChat
    Editor's
    [cache design](https://github.com/bjones1/CodeChat_Editor/blob/main/server/src/processing/cache.rs)
    is heavily structured by this approach.
12. Where possible, avoid OS-specific and language-specific details in a
    specification. When necessary, place this in an implementation section.
13. Additional resources:
    [A practical guide to writing technical specs](https://stackoverflow.blog/2020/04/06/a-practical-guide-to-writing-technical-specs/).

Testing
-------

1. Create tables that describe the input and expected output to define a series
   of test cases.
2. Think carefully when creating test cases; this is an important form of
   design. What valid input could cause the implementation to produce incorrect
   output?
3. Verify that when the LLM implements a specification, it also implements test
   defined in the spec; verify that it runs existing tests before completing an
   implementation.

CodeChat Editor guidelines
--------------------------

1. Employ CodeChat Editor project features:
   1. Create a project by placing a `toc.md` at the root of the project.
   2. For each file, add a unique ID to the level-1 heading for that file:
      <br>`# <span id=*>Cache design</span>`<br>When you edit this heading in
      the Client, it replaces the `*` with a generated unique ID.
   3. In the table of contents (`toc.md`), add an `<xref ref=unique_id></xref>`
      to refer to this file by its level-1 heading (the file's title).
   4. When the LLM implements code, instruct it to place a fragment for each
      addition, connecting this back to the spec with a gather in a subheading.
      See the CodeChat Editor's
      [`CLAUDE.md`](https://github.com/bjones1/CodeChat_Editor/blob/main/CLAUDE.md)
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
5. Include hyperlinks to relevant specifications, API documentation, etc. This
   improves LLM reasoning and context.
6. Use headings to appropriately organize the contents. Near the top of the
   file, include a single level-1 heading, providing the title of the file; per
   the HTML spec, there should be
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
   [VS Code](https://stackoverflow.com/a/53663494/16038919)
6. Use a spell checker:
   [VS Code](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)
7. On a big monitor, place your IDE side by side with the CodeChat Editor.
