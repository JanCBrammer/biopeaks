# -*- coding: utf-8 -*-

import pytest
import numpy as np
import matplotlib.pyplot as plt
# from PySide2.QtCore import Qt
from biopeaks.heart import _find_artifacts, _correct_artifacts, correct_peaks


def generate_peaks(n_peaks=1000, random_state=42):

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


def distort_peaks(peaks, kind=None, k=100, displacement_factor=None):
    """
    Distort every k'th peak (by displacement_factor if kind="misaligned).

    """

    n_peaks = peaks.size
    assert n_peaks > k, "Too few peaks to generate artifacts."

    peaks_distorted = peaks.copy()    # make sure that peaks array is not mutated in-place!
    idcs = np.arange(k, n_peaks, k)
    if kind == "missing":
        peaks_distorted = np.delete(peaks_distorted, idcs)
    elif kind == "extra":
        extra_peaks = (peaks_distorted[idcs + 1] -
                       peaks_distorted[idcs]) / 15 + peaks_distorted[idcs]
        peaks_distorted = np.insert(peaks_distorted, idcs, extra_peaks)
    elif kind == "misaligned":
        rmssd = compute_rmssd(peaks_distorted)
        displacement = displacement_factor * rmssd
        peaks_distorted[idcs] = peaks_distorted[idcs] - displacement

    return peaks_distorted


def compute_rmssd(peaks):
    rr = np.ediff1d(peaks, to_begin=0)
    rr[0] = np.mean(rr[1:])
    rmssd = np.sqrt(np.mean(rr ** 2))

    return rmssd


@pytest.fixture
def n_peaks():
    return 1000


@pytest.fixture
def k_peaks():
    return 100


@pytest.fixture
def peaks_correct(n_peaks):
    peaks = generate_peaks(n_peaks)
    return peaks


@pytest.fixture(params=[2, 4, 8])    # automatically runs the test(s) using this fixture with all values of params
def peaks_misaligned(request, peaks_correct, k_peaks):
    peaks_misaligned = distort_peaks(peaks_correct, kind="misaligned",
                                     k=k_peaks,
                                     displacement_factor=request.param)
    return peaks_misaligned


@pytest.fixture
def peaks_missing(peaks_correct, k_peaks):
    peaks_distorted = distort_peaks(peaks_correct, kind="missing", k=k_peaks)
    return peaks_distorted


@pytest.fixture
def peaks_extra(peaks_correct, k_peaks):
    peaks_distorted = distort_peaks(peaks_correct, kind="extra", k=k_peaks)
    return peaks_distorted


def test_misaligned_detection(peaks_misaligned, n_peaks, k_peaks):

    artifacts = _find_artifacts(peaks_misaligned, sfreq=1)
    assert artifacts["longshort"] == list(np.arange(k_peaks, n_peaks, k_peaks))


def test_missed_detection(peaks_missing, n_peaks, k_peaks):

    artifacts = _find_artifacts(peaks_missing, sfreq=1)
    missing_idcs = [j - i for i, j in enumerate(list(np.arange(k_peaks,
                                                               n_peaks,
                                                               k_peaks)))]    # account for the fact that peak indices are shifted to the left after deletion of peaks
    assert artifacts["missed"] == missing_idcs


def test_extra_detection(peaks_extra, n_peaks, k_peaks):

    artifacts = _find_artifacts(peaks_extra, sfreq=1)
    extra_idcs = [j + (i + 1) for i, j in enumerate(list(np.arange(k_peaks,
                                                                   n_peaks,
                                                                   k_peaks)))]    # account for the fact that peak indices are shifted to the right after insertion of peaks
    assert artifacts["extra"] == extra_idcs


# @pytest.mark.paramertize("iterative", [True, False])
# def test_misaligned_correction(peaks_misaligned, peaks_correct, iterative):

#     peaks_corrected = correct_peaks(peaks_misaligned, sfreq=1,
#                                     iterative=iterative)
#     period_corrected = compute_rmssd(peaks_corrected)
#     period_correct = compute_rmssd(peaks_correct)
#     period_uncorrected = compute_rmssd(peaks_misaligned)
#     assert np.allclose(period_uncorrected - period_correct, 467, atol=.1)
#     # assert np.allclose(period_corrected - period_correct, 7, atol=.1)


# @pytest.mark.paramertize("iterative", [True, False])
# def test_missed_correction(peaks_missing, peaks_correct, iterative, rmssddiff):

#     peaks_corrected = correct_peaks(peaks_missing, sfreq=1,
#                                     iterative=iterative)

#     period_corrected = compute_rmssd(peaks_corrected)
#     period_uncorrected = compute_rmssd(peaks_missing)
#     assert np.allclose(period_uncorrected - period_corrected, rmssddiff,
#                        atol=.1)




###############################################################################

# def show_artifact_correction(peaks_uncorrected, peaks_corrected, artifacts):

#     rr_uncorrected = np.ediff1d(peaks_uncorrected, to_begin=0)
#     rr_corrected = np.ediff1d(peaks_corrected, to_begin=0)

#     fig, (ax0, ax1) = plt.subplots(nrows=2, ncols=1, sharex=True, sharey=True)
#     ax0.plot(rr_uncorrected)
#     colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
#     for color, item in enumerate(artifacts.items()):
#         c = colors[color]
#         ax0.scatter(item[1], rr_uncorrected[item[1]],
#                     label=item[0], color=c, zorder=3)
#     ax0.vlines(np.arange(0, rr_uncorrected.size), ymin=rr_uncorrected.min(),
#                 ymax=rr_uncorrected.max(), alpha=.1, label="peaks")
#     ax0.legend(loc="upper right")
#     ax1.plot(rr_corrected)


# peaks = generate_peaks(n_peaks=1000)

# peaks_missing = distort_peaks(peaks, kind="missing")
# artifacts_missing = _find_artifacts(peaks_missing, sfreq=1)
# # peaks_missing_corrected = correct_peaks(peaks_missing, sfreq=1)
# peaks_missing_corrected = _correct_artifacts(artifacts_missing, peaks_missing)

# show_artifact_correction(peaks_missing, peaks_missing_corrected,
#                           artifacts_missing)

# peaks_extra = distort_peaks(peaks, kind="extra")
# artifacts_extra = _find_artifacts(peaks_extra, sfreq=1)
# # peaks_extra_corrected = correct_peaks(peaks_extra, sfreq=1)
# peaks_extra_corrected = _correct_artifacts(artifacts_extra, peaks_extra)

# show_artifact_correction(peaks_extra, peaks_extra_corrected,
#                           artifacts_extra)

# peaks_misaligned = distort_peaks(peaks, kind="misaligned", k=100,
#                                   displacement_factor=2)
# artifacts_misaligned = _find_artifacts(peaks_misaligned, sfreq=1)
# # peaks_misaligned_corrected = correct_peaks(peaks_misaligned, sfreq=1)
# peaks_misaligned_corrected = _correct_artifacts(artifacts_misaligned,
#                                                 peaks_misaligned)

# show_artifact_correction(peaks_misaligned, peaks_misaligned_corrected,
#                           artifacts_misaligned)
