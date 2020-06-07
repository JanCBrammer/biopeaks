# Tests

## GUI
The OpenSignals test data have been recorded with<br/>
software: opensignals v2.0.0, 20190805<br/>
hardware: BITalino (r)evolution (firmware 1281)

The EDF test data have been downloaded from https://www.teuniz.net/edf_bdf_testfiles/

Please make sure to have [pytest](https://docs.pytest.org/en/latest/) as well as
[pytest-qt](https://pypi.org/project/pytest-qt/) installed before running the frontend tests.

The tests can be run in the test directory by using [pytest](https://docs.pytest.org/en/latest/):
```
pytest -v
```


## Extrema detection benchmarks
In order to validate the performance of the ECG peak detector `heart.ecg_peaks()`,
please download the [Glasgow University Database (GUDB)](http://researchdata.gla.ac.uk/716/).
In addition you need to install the [wfdb](https://github.com/MIT-LCP/wfdb-python) package either with conda
```
conda install -c conda-forge wfdb
```
or pip.

```
pip install wfdb
```
You can then run the `benchmark_ECG` script in the test folder.

In order to validate the performance of the PPG peak detector `heart.ppg_peaks()`
please download the [Capnobase IEEE TBME benchmark dataset](http://www.capnobase.org/index.php?id=857).
After extracting the PPG signals and peak annotations you can run the `benchmark_PPG` script in the test folder.