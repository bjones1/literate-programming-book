Introduction to Git
===================

If you don't have an account on github.com, create one. Send me your github
userid.

First, clone https://github.com/bjones1/literate-programming-book.

Git tracks changes to files over time in discrete units called commits.

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

* Clone https://github.com/bjones1/literate-programming-fall-2024.

Lots of resources online! A [tutorial](https://learngitbranching.js.org), many
videos.
