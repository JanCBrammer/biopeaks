# -*- coding: utf-8 -*-

import pytest
import numpy as np
import matplotlib.pyplot as plt
# from PySide2.QtCore import Qt
from biopeaks.heart import _find_artifacts, _correct_artifacts, correct_peaks


def generate_peaks(n_peaks=1000, kind="missing", random_state=42):

    # Simulate sinusoidally changing heart periods.
    rr = np.sin(np.arange(n_peaks))
    # Add some noise.
    rng = np.random.default_rng(random_state)
    rr_noisy = rng.normal(rr, .1)
    # Scale to range of 250msec and offset by 1000msec. I.e., heart period
    # fluctuates in a range of 250msec around 1000msec.
    rr_scaled = 1000 + rr_noisy * 125

    peaks = np.cumsum(np.rint(rr_scaled)).astype(int)

    return peaks


def distort_peaks(peaks, kind="missing", displacement_factor=None):

    n_peaks = peaks.size
    assert n_peaks >= 1000, "Too few peaks to generate artifacts."

    idcs = np.arange(100, n_peaks, 100)
    if kind == "missing":
        peaks = np.delete(peaks, idcs)
    elif kind == "extra":
        extra_peaks = (peaks[idcs + 1] - peaks[idcs]) / 2 + peaks[idcs]
        peaks = np.insert(peaks, idcs, extra_peaks)
    elif kind == "misaligned":
        rr = np.ediff1d(peaks, to_begin=0)
        rr[0] = np.mean(rr[1:])
        rmssd = np.sqrt(np.mean(rr ** 2))
        displacement = displacement_factor * rmssd
        peaks[idcs] = peaks[idcs] - displacement

    return peaks


# @pytest.fixture(params=[2, 4, 8])
# def peaks_misaligned(request):
#     peaks = generate_peaks(1000)
#     peaks_misaligned = distort_peaks(peaks, kind="misaligned",
#                                      displacement_factor=request.param)
#     return peaks_misaligned




def show_artifact_correction(peaks_uncorrected, peaks_corrected, artifacts):

    rr_uncorrected = np.ediff1d(peaks_uncorrected, to_begin=0)
    rr_corrected = np.ediff1d(peaks_corrected, to_begin=0)

    fig, (ax0, ax1) = plt.subplots(nrows=2, ncols=1, sharex=True, sharey=True)
    ax0.plot(rr_uncorrected)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for color, item in enumerate(artifacts.items()):
        c = colors[color]
        ax0.scatter(item[1], rr_uncorrected[item[1]],
                    label=item[0], color=c, zorder=3)
    ax0.legend(loc="upper right")
    ax1.plot(rr_corrected)


peaks = generate_peaks(1000)

peaks_missing = distort_peaks(peaks, kind="missing")
artifacts_missing = _find_artifacts(peaks_missing, sfreq=1)
peaks_missing_corrected = correct_peaks(peaks_missing, sfreq=1)#_correct_artifacts(artifacts_missing, peaks_missing)

show_artifact_correction(peaks_missing, peaks_missing_corrected,
                         artifacts_missing)

peaks_extra = distort_peaks(peaks, kind="extra")
artifacts_extra = _find_artifacts(peaks_extra, sfreq=1)
peaks_extra_corrected = correct_peaks(peaks_extra, sfreq=1)#_correct_artifacts(artifacts_extra, peaks_extra)

show_artifact_correction(peaks_extra, peaks_extra_corrected,
                         artifacts_extra)

peaks_misaligned = distort_peaks(peaks, kind="misaligned",
                                 displacement_factor=2)
artifacts_misaligned = _find_artifacts(peaks_misaligned, sfreq=1)
peaks_misaligned_corrected = correct_peaks(peaks_misaligned, sfreq=1)#_correct_artifacts(artifacts_misaligned, peaks_misaligned)

show_artifact_correction(peaks_misaligned, peaks_misaligned_corrected,
                         artifacts_misaligned)
