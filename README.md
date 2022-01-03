<img src="https://github.com/JanCBrammer/biopeaks/raw/master/docs/images/logo.png" alt="logo" style="width:600px;"/>

![GH Actions](https://github.com/JanCBrammer/biopeaks/workflows/test/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/JanCBrammer/biopeaks/branch/master/graph/badge.svg)](https://codecov.io/gh/JanCBrammer/biopeaks)
[![DOI](https://www.zenodo.org/badge/172897525.svg)](https://www.zenodo.org/badge/latestdoi/172897525)
[![PyPI version](https://img.shields.io/pypi/v/biopeaks.svg)](https://pypi.org/project/biopeaks/)
[![JOSS](https://joss.theoj.org/papers/10.21105/joss.02621/status.svg)](https://doi.org/10.21105/joss.02621)


# General Information

`biopeaks` is a straightforward graphical user interface for feature extraction from electrocardiogram (ECG), photoplethysmogram (PPG) and breathing biosignals.
It processes these biosignals semi-automatically with sensible defaults and offers the following functionality:

+ processes files in the open biosignal formats [EDF](https://en.wikipedia.org/wiki/European_Data_Format), [OpenSignals (Bitalino)](https://bitalino.com/en/software)
as well as plain text files (.txt, .csv, .tsv)
+ interactive biosignal visualization
+ biosignal segmentation
+ benchmarked, automatic extrema detection (R-peaks in ECG, systolic peaks in PPG, exhalation troughs and inhalation
peaks in breathing signals) with signal-specific, sensible defaults
+ automatic state-of-the-art [artifact correction](https://www.tandfonline.com/doi/full/10.1080/03091902.2019.1640306)
 for ECG and PPG extrema
+ manual editing of extrema
+ extraction of instantaneous features: (heart- or breathing-) rate and period, as well as breathing amplitude
+ .csv export of extrema and instantaneous features for further analysis (e.g., heart rate variability)
+ automatic analysis of multiple files (batch processing)


![GUI](https://github.com/JanCBrammer/biopeaks/raw/master/docs/images/screenshot_statistics.png)


# Installation

`biopeaks` can be installed from PyPI:

```
pip install biopeaks
```

Alternatively, on Windows, download [biopeaks.exe](https://github.com/JanCBrammer/biopeaks/releases/latest)
and run it. Running the executable does not require a Python installation.

You can find more details on the installation [here](https://jancbrammer.github.io/biopeaks/installation.html).


# Documentation

Have a look at the [user guide](https://jancbrammer.github.io/biopeaks/user_guide.html) to get started with `biopeaks`.


# Contributors welcome!

Improvements or additions to the repository (documentation, tests, code) are welcome and encouraged.
Spotted a typo in the documentation? Caught a bug in the code? Ideas for improving the documentation,
increase test coverage, or adding features to the GUI? Get started with the [contributor guide](https://jancbrammer.github.io/biopeaks/contributor_guide.html).


# Citation

Please refer to the [biopeaks paper](https://joss.theoj.org/papers/10.21105/joss.02621) in The Journal of Open Source Software.


# Changelog

Have a look at the [changelog](https://jancbrammer.github.io/biopeaks/changelog.html) to get an overview of what has changed throughout the versions of `biopeaks`.




