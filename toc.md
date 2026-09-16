1. Week 0: [Introduction](README.md)
   1. Class notes: [MSU](class_notes-MSU.md), [KBTU](class_notes-KBTU.md)
   2. Introduction slides:
      [MSU](course_materials/course_introduction-MSU.pptx),
      [KBTU](course_materials/course_introduction-KBTU.pptx)
   3. Syllabus:
      [MSU](course_materials/Syllabus-ECE_4793-6793_and_CSE_4353-6353-2026_Fall-Applications_of_Literate_Programming_in_Software_Development.pdf),
      [KBTU](course_materials/CSDA_5101_Syllabus-Advanced_Software_Paradigms-Fall_2026.pdf)
   4. Exercise: [What your prompt didn't say](exercises/spec-quality/handout.md)
   5. [warmup\_truncate.py](exercises/spec-quality/warmup_truncate.py)
   6. [my\_truncate.py](exercises/spec-quality/my_truncate.py)
2. Week 1: Writing a spec and tests
   1. Exercise: [writing a spec and tests](exercises/spec-design.md)
   2. [test\_truncate.py](exercises/spec-quality/test_truncate.py)
   3. [run\_tests.py](exercises/spec-quality/run_tests.py)
   4. Introduction to the CodeChat Editor (CCE)
3. Week 2: Review of literate programming
   1. Introduction to literate programming (LP)
   2. [Origins of LP](origins.md)
   3. Current approaches to LP
   4. Single-file approaches to LP
   5. Project-based approaches to LP
4. Week 3-4: Introduction to social coding
   1. [Introduction to Git and GitHub](git_intro.md)
5. Week 5: CodeChat Editor use - design as documentation
   1. Create a project, a TOC, use (hopefully) xrefs, gathers.
   2. Exercise: create a project with MD files, code files, xrefs, gathers based
      on code you wrote for another class or a small open-source project.
6. Week 6: Integrating CCE, Git, and social coding with LLM use
   1. Write detailed specs in Markdown.
   2. Apply LLM commands to a branch, to staged files, etc.
   3. Always use LLM review.
7. Week 7: Data structures as design; LLM techniques
   1. Document data structure design using CCE comments.
   2. Focus each agent on a narrowly-defined problem.
   3. Avoid stale context.
   4. Subagent use.
8. Week 8: spec design for project 1.
9. Week 9: implementation for project 1.
10. Week 10: finalize project 1.
11. Week 11-15: final project.
12. Misc
    1. [Table of contents](toc.md)
    2. [License](LICENSE.md)
    3. [Ignores](.gitignore)
13. Tools
    1. [Specification](chat_grader.md)
    2. [Grading tools README](grader/README.md)
    3. Git homework grader
       1. [git\_homework.py](grader/grader/git_homework.py)
       2. [test\_git\_homework.py](grader/tests/test_git_homework.py)
    4. Teams chat downloader
       1. [teams\_export.py](grader/grader/teams_export.py)
       2. [test\_teams\_export.py](grader/tests/test_teams_export.py)
       3. [Capture token setup guide](course_materials/capture-token-setup-guide.html)
    5. Packaging and checks
       1. [\_\_init\_\_.py](grader/grader/__init__.py)
       2. [pyproject.toml](grader/pyproject.toml)
       3. [poetry.toml](grader/poetry.toml)
       4. [pre\_commit\_check.py](grader/tests/pre_commit_check.py)
       5. [ci\_utils.py](grader/tests/ci_utils.py)
       6. [Code coverage config](grader/.coveragerc)
       7. [Flake8 config](grader/.flake8)
       8. [mypy config](grader/mypy.ini)
