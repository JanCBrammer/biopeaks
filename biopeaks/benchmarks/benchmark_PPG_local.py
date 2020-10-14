# -*- coding: utf-8 -*-
"""Benchmark the heart.ppg_peaks detector.

Before running this script, please download the Capnobase IEEE TBME benchmark
dataset from http://www.capnobase.org/index.php?id=857. Then specify `data_dir`
and optionally `tolerance`.
"""

import h5py
import numpy as np
from pathlib import Path
from biopeaks.heart import ppg_peaks
from wfdb.processing import compare_annotations


sfreq = 300
data_dir = Path(".../TBME2013-PPGRR-Benchmark_R3/data")    # replace with your local "data" directory once you've downloaded the database
tolerance = int(np.rint(.05 * sfreq))    # in samples; 50 milliseconds in accordance with doi:10.1371/journal.pone.0076585

print(f"Setting tolerance for match between algorithmic and manual annotation"
      f" to {tolerance} sample(s), corresponding to {tolerance / sfreq} seconds"
      f" at a sampling rate of {sfreq}.")

sensitivity = []
precision = []

for subject in data_dir.iterdir():

    f = h5py.File(subject, "r")
    record = np.ravel(f["signal"]["pleth"]["y"])
    annotation = np.ravel(f["labels"]["pleth"]["peak"]["x"])

    peaks = ppg_peaks(record, sfreq)

    comparitor = compare_annotations(annotation, peaks, tolerance)
    tp = comparitor.tp
    fp = comparitor.fp
    fn = comparitor.fn

    sensitivity.append(tp / (tp + fn))
    precision.append(tp / (tp + fp))

    print(f"\nResults {subject}")
    print("-" * len(str(subject)))
    print(f"sensitivity = {sensitivity[-1]}")
    print(f"precision = {precision[-1]}")

print(f"\nAverage results over {len(precision)} records")
print("-" * 31)
print(f"sensitivity: mean = {round(np.mean(sensitivity), 4)}, std = {round(np.std(sensitivity), 4)}")
print(f"precision: mean = {round(np.mean(precision), 4)}, std = {round(np.std(precision), 4)}")
