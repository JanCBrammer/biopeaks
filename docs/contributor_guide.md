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
4. Implement your contribution in the `topic` branch, following the [conventions](#conventions).
5. [Make a pull request](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork) from the `topic` branch on your fork to the [`dev` branch of the `biopeaks` repository](https://github.com/JanCBrammer/biopeaks/tree/dev).
6. Once all tests pass and your contribution has been reviewed, your PR will merged and you'll be added to the list of contributors.


## Conventions

### General

* avoid introducing new dependencies
* write [numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html) docstrings
  for every (non-private) new function
* add tests if you contribute code that is not covered by the existing [tests](#tests)

### Code style

* aim for simplicity and readability
* follow [PEP8 guidelines](https://www.python.org/dev/peps/pep-0008/)
* write code in Python 3.6+

### Architecture

* The GUI is structured according to a variant of the
  [model-view-controller architecture](https://martinfowler.com/eaaDev/uiArchs.html).
  To understand the relationship of the `model`, `view`, and `controller` have a look
  at how each of them is instantiated in [`__main__.py`](https://github.com/JanCBrammer/biopeaks/blob/master/biopeaks/__main__.py).
  For example, the `view` has references to the `model` as well as the
  `controller`, whereas the `model` has no reference to any of the other
  components of the architecture (i.e., the `model` is agnostic to the `view` and
  `controller`).


## Documentation

The documentation is hosted on GitHub pages, essentially a static website associated
with the `biopeaks` repository: <https://jancbrammer.github.io/biopeaks/>. It
is automatically build from the `/docs` folder in the root of the `biopeaks` repository.
The website is re-build every very time the content of `/docs` changes on the
master branch (pushes, merged pull requests). `/docs` includes an `index.md` file
that constitutes the "landing page". It contains links to all other parts of the
documentation. The layout of the website is defined in `/docs/layouts`. For
additional information, head over to the [GitHub pages documentation](https://docs.github.com/en/free-pro-team@latest/github/working-with-github-pages).


## Tests

The OpenSignals test data have been recorded with<br/>
software: opensignals v2.0.0, 20190805<br/>
hardware: BITalino (r)evolution (firmware 1281)

The EDF test data have been downloaded from https://www.teuniz.net/edf_bdf_testfiles/

All test data are part of the biopeaks installation and do not have to be downloaded.

Please make sure to have [pytest](https://docs.pytest.org/en/latest/) as well as
[pytest-qt](https://pypi.org/project/pytest-qt/) installed before running the tests:

```
conda install -c conda-forge pytest
conda install -c conda-forge pytest-qt
```

The tests can then be run in the test directory by using [pytest](https://docs.pytest.org/en/latest/):
```
pytest -v
```


## Algorithm benchmarks

### ECG
To validate the performance of the ECG peak detector `heart.ecg_peaks()`, please install the [wfdb](https://github.com/MIT-LCP/wfdb-python) and [aiohttp](https://github.com/aio-libs/aiohttp):
```
conda install -c conda-forge wfdb
conda install -c conda-forge aiohttp
```

You can then run the `benchmark_ECG_stream` script in the `benchmarks` folder. The script streams ECG and annotation files from the [Glasgow University Database (GUDB)](http://researchdata.gla.ac.uk/716/).
You can select an experiment, ECG channel, and annotation file (for details have a look at the docstrings of `BenchmarkDetectorGUDB.benchmark_records()` in `benchmarks\benchmark_utils`).

Alternatively, you can download the GUDB and run the `benchmark_ECG_local` script in the `benchmarks` folder. In the script, replace the `data_dir` with your local directory (see comments in the script).

### PPG

To validate the performance of the PPG peak detector `heart.ppg_peaks()`
please download the [Capnobase IEEE TBME benchmark dataset](http://www.capnobase.org/index.php?id=857) and install [wfdb](https://github.com/MIT-LCP/wfdb-python) and [h5py](https://www.h5py.org/):
```
conda install -c conda-forge wfdb
conda install -c conda-forge h5py
```

You can then run the `benchmark_PPG_local` script in the `benchmarks` folder. In the script, replace the `data_dir` with your local directory (see comments in the script).


## Resources

### [Using git](https://github.com/dictcp/awesome-git)

### [Using GitHub](https://docs.github.com/en)

