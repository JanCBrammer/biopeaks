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