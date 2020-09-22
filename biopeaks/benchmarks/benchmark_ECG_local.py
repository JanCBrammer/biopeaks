# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from pathlib import Path
from biopeaks.heart import ecg_peaks
from wfdb.processing import compare_annotations


data_dir = Path(".../experiment_data")    # replace with your local "experiment_data" directory once you've downloaded the database

condition = "hand_bike"    # can be one of {"sitting", "maths", "walking", "hand_bike", "jogging"}
sfreq = 250
tolerance = 1    # in samples
print(f"Setting tolerance for match between algorithmic and manual annotation"
      f" to 1 sample, corresponding to {1 / sfreq} seconds at a sampling rate of {sfreq}.")

sensitivity = []
precision = []

for subject in data_dir.glob("subject_*"):

    record = subject.joinpath(f"{condition}/ECG.tsv")
    annotation = subject.joinpath(f"{condition}/annotation_cables.tsv")

    try:
        ecg = np.ravel(pd.read_csv(record, sep=" ", usecols=[1],
                                   header=None))
    except FileNotFoundError:
        print(f"no ECG available for {record}")
        continue
    try:
        manupeaks = np.ravel(pd.read_csv(annotation, header=None))
    except FileNotFoundError:
        print(f"no annotations available for {annotation}")
        continue

    algopeaks = ecg_peaks(ecg, sfreq)

    if algopeaks.size > 1:

        comparitor = compare_annotations(manupeaks, algopeaks, tolerance)
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
