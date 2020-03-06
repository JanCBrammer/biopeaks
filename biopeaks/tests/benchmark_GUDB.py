# -*- coding: utf-8 -*-

import glob
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from biopeaks.ecg import ecg_peaks
from wfdb.processing import compare_annotations


GUDB_dir = r"directory\containing\GUDB"

os.chdir(GUDB_dir)

records = []
annotations = []
condition = "hand_bike"

for subject in glob.glob("subject_*"):
    records.append(os.path.join(subject, condition, "ECG.tsv"))
    annotations.append(os.path.join(subject, condition,
                                    "annotation_cables.tsv"))

sensitivity = []
precision = []

sfreq = 250

for record, annotation in zip(records, annotations):

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

        # Tolerance for match between algorithmic and manual annotation (in
        # sec): corresponds to one sample
        tolerance = 1 / sfreq
        comparitor = compare_annotations(manupeaks, algopeaks,
                                         int(np.rint(tolerance * sfreq)))
        tp = comparitor.tp
        fp = comparitor.fp
        fn = comparitor.fn

        # plt.figure()
        # plt.plot(ecg)
        # plt.scatter(manupeaks, ecg[manupeaks], c="m")
        # plt.scatter(algopeaks, ecg[algopeaks], c='g', marker='X', s=150)

        sensitivity.append(float(tp) / (tp + fn))
        precision.append(float(tp) / (tp + fp))
        print(f"sensitivity = {sensitivity[-1]}, precision = {precision[-1]}")

print(f"mean precision = {np.mean(precision)}, std precision = {np.std(precision)}")
print(f"mean sensitivity = {np.mean(sensitivity)}, std sensitivity = {np.std(sensitivity)}")
