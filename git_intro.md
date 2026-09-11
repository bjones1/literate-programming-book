Introduction to Git
===================

If you don't have an account on [GitHub](https://github.com/), create one. Send
me your GitHub userid. Then, clone the
[e-book](https://github.com/bjones1/literate-programming-book).

Summary
-------

A Git repository tracks changes to files over time in discrete units called
commits.<sup>[1](#fGU2e6HP9t)</sup>

![An annotated graph of the literate-programming-fall-2024 repository, showing a commit, files in a commit, a local and remote branch, and the HEAD.](course_materials/git_graph_annotated.png)

* The staging area (or index) selects which changes to files to store in a
  commit.
* A commit records these changes to a group of files to the local repository (or
  repo). It's a snapshot of your files.
* A repository is a graph of commits; they can be local or remote.
* A branch refers to a commit and all its children in the repository.
* The head refers to the currently active commit.

Local actions:

* Stage changes to files to the staging area/index, or discard mistakes.
* Commit them to the local repository.
* Add a branch; merge a branch into another; delete a branch.
* Check out a branch or a commit, which updates files and the head.

Remote actions:

* Clone (copy) commits a remote repo to a new local repo.
* Push commits from the local repo to a remote repo.
* Fetch commits from the remote repo to the local repo (opposite of push).

Practice:

* Clone
  [https://github.com/bjones1/literate-programming-fall-2024](https://github.com/bjones1/literate-programming-fall-2024).
* Browse to
  [https://github.com/bjones1/literate-programming-github-fall-2026](https://github.com/bjones1/literate-programming-github-fall-2026).

Lots of resources online! A [tutorial](https://learngitbranching.js.org), many
videos.

### Footnotes

1. <a id="fGU2e6HP9t"></a>Prompt to used create this image:
   > The image @course\_materials/git\_graph.png shows a screenshot of the
   > VSCode Git GUI. Add annotations to this image to show:
   >
   > 1. A commit
   > 2. Files in a commit.
   > 3. A local branch.
   > 4. A remote branch.
   > 5. The HEAD.
