# Contributor Guide

Thanks for your interest in contributing to `biopeaks`! Before you continue,
please have a look at the [code of conduct](https://github.com/JanCBrammer/biopeaks/blob/master/code_of_conduct.md).


## Ways to contribute

### Reporting bugs or asking questions

Please report bugs or ask questions by [opening an issue](https://help.github.com/en/github/managing-your-work-on-github/creating-an-issue)
in the [`biopeaks` repository](https://github.com/JanCBrammer/biopeaks).


### Improve documentation, tests, or code

If you plan to contribute relatively large changes, please [open an issue](https://help.github.com/en/github/managing-your-work-on-github/creating-an-issue)
in the [`biopeaks` repository](https://github.com/JanCBrammer/biopeaks) before
you start working on your contribution. This way we can discuss your plans before you start writing/coding.

Follow these steps to contribute documentation, tests, or code:

1. [Fork](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo) the [`biopeaks` repository](https://github.com/JanCBrammer/biopeaks).
2. Add a `topic` branch with a descriptive name to your fork. For example, if you want to contribute an improvement to the documentation you could call the `topic` branch `improve_docs`.
3. Install `biopeaks` in development mode:
   1. Make a [local clone of your fork](https://docs.github.com/en/free-pro-team@latest/github/getting-started-with-github/fork-a-repo#step-2-create-a-local-clone-of-your-fork).
   2. Navigate to the directory containing the cloned fork.
   3. Install `biopeaks` with `pip install -e .` The `e` stand for editable, meaning you can immediatly test all the changes you make to the cloned fork. The `.` simply tells pip to install the content of the current directory.
4. Implement your contribution in the `topic` branch.
5. If you contribute code that is not covered by the existing tests, please add tests if possible.
6. [Make a pull request](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork) from the `topic` branch on your fork to the [`dev` branch of the `biopeaks` repository](https://github.com/JanCBrammer/biopeaks/tree/dev).
7. Once all tests pass and your contribution has been reviewed, your PR will merged and you'll be added to the list of contributors.


## Conventions

### code style:

* aim for simplicity and readability
* follow [PEP8 guidelines](https://www.python.org/dev/peps/pep-0008/)
* write code in Python 3.6+

### architecture:

* The GUI is structured according to a variant of the
  [model-view-controller architecture](https://martinfowler.com/eaaDev/uiArchs.html).
  To understand the relationship of the `model`, `view`, and `controller` have a look
  at how each of them is instantiated in [`__main__.py`](https://github.com/JanCBrammer/biopeaks/blob/master/biopeaks/__main__.py).
  For example, the `view` has references to the `model` as well as the
  `controller`, whereas the `model` has no reference to any of the other
  components of the architecture (i.e., the `model` is agnostic to the `view` and
  `controller`).


## Resources

### [Using git](https://github.com/dictcp/awesome-git)

### [Using GitHub](https://docs.github.com/en)

