# -*- coding: utf-8 -*-

import h5py
import numpy as np
from pathlib import Path
from biopeaks.heart import ppg_peaks
from wfdb.processing import compare_annotations


data_dir = Path(".../TBME2013-PPGRR-Benchmark_R3/data")    # replace with your local "data" directory once you've downloaded the database

sfreq = 300
tolerance = int(np.rint(.05 * sfreq))    # in samples; 50 milliseconds in accordance with Elgendi et al., 2013, doi:10.1371/journal.pone.0076585
print(f"Setting tolerance for match between algorithmic and manual annotation"
      f" to {tolerance} samples, corresponding to 50 milliseconds at a sampling rate of {sfreq}.")

sensitivity = []
precision = []

for subject in data_dir.iterdir():

    f = h5py.File(subject, "r")
    record = np.ravel(f["signal"]["pleth"]["y"])
    annotation = np.ravel(f["labels"]["pleth"]["peak"]["x"])

    peaks = ppg_peaks(record, sfreq)

    comparitor = compare_annotations(peaks, annotation, tolerance)
    tp = comparitor.tp
    fp = comparitor.fp
    fn = comparitor.fn

    sensitivity.append(float(tp) / (tp + fn))
    precision.append(float(tp) / (tp + fp))

    print(f"\nResults {subject}")
    print("-" * len(str(subject)))
    print(f"sensitivity = {sensitivity[-1]}")
    print(f"precision = {precision[-1]}")

print(f"\nAverage results over {len(precision)} records")
print("-" * 31)
print(f"sensitivity: mean = {np.mean(sensitivity)}, std = {np.std(sensitivity)}")
print(f"precision: mean = {np.mean(precision)}, std = {np.std(precision)}")
