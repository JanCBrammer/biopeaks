# -*- coding: utf-8 -*-

import os
import numpy as np
from biopeaks.heart import ppg_peaks
from wfdb.processing import compare_annotations


record_dir = r"C:\Users\JohnDoe\surfdrive\Beta\example_data\PPG\signal"
annotation_dir = r"C:\Users\JohnDoe\surfdrive\Beta\example_data\PPG\annotations"
records = os.listdir(record_dir)
annotations = os.listdir(annotation_dir)
subjects = list(zip(records, annotations))

sfreq = 300
# Set tolerance to 50 milliseconds (Elgendi et al., 2013)
tolerance = int(np.rint(.05 * sfreq))    # tolerance must be in samples for wfdb
print(f"Setting tolerance for match between algorithmic and manual annotation"
      f" to {tolerance} samples, corresponding to 50 milliseconds at a sampling rate of {sfreq}.")

sensitivity = []
precision = []

for subject in subjects:

    data = np.loadtxt(os.path.join(record_dir, subject[0]))
    annotation = np.loadtxt(os.path.join(annotation_dir, subject[1]))
    peaks = ppg_peaks(data, sfreq)

    comparitor = compare_annotations(peaks, annotation, tolerance)
    tp = comparitor.tp
    fp = comparitor.fp
    fn = comparitor.fn

    sensitivity.append(float(tp) / (tp + fn))
    precision.append(float(tp) / (tp + fp))
    print(f"sensitivity = {sensitivity[-1]}, precision = {precision[-1]}")

print(f"mean precision = {np.mean(precision)}, std precision = {np.std(precision)}")
print(f"mean sensitivity = {np.mean(sensitivity)}, std sensitivity = {np.std(sensitivity)}")
