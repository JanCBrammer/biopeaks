# -*- coding: utf-8 -*-

import pytest
import numpy as np
from biopeaks.heart import _find_artifacts, correct_peaks


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
def artifact_idcs(k_peaks, n_peaks):
    idcs = np.arange(k_peaks, n_peaks, k_peaks)
    return idcs


@pytest.fixture
def peaks_correct(n_peaks):
    # Simulate sinusoidally changing heart periods.
    rr = np.sin(np.arange(n_peaks))
    # Add some noise.
    rng = np.random.default_rng(42)
    rr_noisy = rng.normal(rr, .1)
    # Scale to range of 250msec and offset by 1000msec. I.e., heart period
    # fluctuates in a range of 250msec around 1000msec.
    rr_scaled = 1000 + rr_noisy * 125

    peaks = np.cumsum(np.rint(rr_scaled)).astype(int)

    return peaks


@pytest.fixture
def peaks_misaligned(request, peaks_correct, artifact_idcs):

    rmssd = compute_rmssd(peaks_correct)
    displacement = request.param * rmssd

    peaks_misaligned = peaks_correct.copy()
    peaks_misaligned[artifact_idcs] = (peaks_misaligned[artifact_idcs] -
                                       displacement)

    return peaks_misaligned


@pytest.fixture
def peaks_missing(peaks_correct, artifact_idcs):

    peaks_missing = peaks_correct.copy()
    peaks_missing = np.delete(peaks_missing, artifact_idcs)

    return peaks_missing


@pytest.fixture
def peaks_extra(peaks_correct, artifact_idcs):

    extra_peaks = ((peaks_correct[artifact_idcs + 1] -
                    peaks_correct[artifact_idcs]) / 15 +
                   peaks_correct[artifact_idcs])

    peaks_extra = peaks_correct.copy()
    peaks_extra = np.insert(peaks_extra, artifact_idcs, extra_peaks)

    return peaks_extra


@pytest.mark.parametrize("peaks_misaligned", [2, 4, 8],
                         indirect=["peaks_misaligned"])
def test_misaligned_detection(peaks_misaligned, artifact_idcs):

    artifacts = _find_artifacts(peaks_misaligned, sfreq=1)
    assert artifacts["longshort"] == list(artifact_idcs)


def test_missed_detection(peaks_missing, artifact_idcs):

    artifacts = _find_artifacts(peaks_missing, sfreq=1)
    missing_idcs = [j - i for i, j in enumerate(artifact_idcs)]    # account for the fact that peak indices are shifted to the left after deletion of peaks
    assert artifacts["missed"] == missing_idcs


def test_extra_detection(peaks_extra, artifact_idcs):

    artifacts = _find_artifacts(peaks_extra, sfreq=1)
    extra_idcs = [j + (i + 1) for i, j in enumerate(artifact_idcs)]    # account for the fact that peak indices are shifted to the right after insertion of peaks
    assert artifacts["extra"] == extra_idcs


def idfn(val):
    if isinstance(val, bool):
        return f"iterative_{val}"


@pytest.mark.parametrize("peaks_misaligned, iterative, rmssd_diff",
                         [(2, True, 33), (2, False, 26),
                          (4, True, 133), (4, False, 126),
                          (8, True, 467), (8, False, 460)],
                         indirect=["peaks_misaligned"], ids=idfn)
def test_misaligned_correction(peaks_correct, peaks_misaligned, iterative,
                               rmssd_diff):

    peaks_corrected = correct_peaks(peaks_misaligned, sfreq=1,
                                    iterative=iterative)

    rmssd_correct = compute_rmssd(peaks_correct)
    rmssd_corrected = compute_rmssd(peaks_corrected)
    rmssd_uncorrected = compute_rmssd(peaks_misaligned)

    # Assert that correction does not produce peaks that exceed the temporal
    # bounds of the original peaks.
    assert peaks_correct[0] <= peaks_corrected[0]
    assert peaks_correct[-1] >= peaks_corrected[-1]

    # Assert that after artifact correction, the difference in RMSSD to the
    # undistorted signal decreases. This also implicitely tests if the peak
    # distortion affects the RMSSD (manipulation check).
    rmssd_diff_uncorrected = np.abs(rmssd_correct - rmssd_uncorrected)
    rmssd_diff_corrected = np.abs(rmssd_correct - rmssd_corrected)
    assert int(rmssd_diff_uncorrected - rmssd_diff_corrected) == rmssd_diff


@pytest.mark.parametrize("iterative, rmssd_diff", [(True, 3), (False, 3)],
                         ids=idfn)
def test_extra_correction(peaks_correct, peaks_extra, iterative, rmssd_diff):

    peaks_corrected = correct_peaks(peaks_extra, sfreq=1,
                                    iterative=iterative)

    rmssd_correct = compute_rmssd(peaks_correct)
    rmssd_corrected = compute_rmssd(peaks_corrected)
    rmssd_uncorrected = compute_rmssd(peaks_extra)

    # Assert that correction does not produce peaks that exceed the temporal
    # bounds of the original peaks.
    assert peaks_correct[0] <= peaks_corrected[0]
    assert peaks_correct[-1] >= peaks_corrected[-1]

    # Assert that after artifact correction, the difference in RMSSD to the
    # undistorted signal decreases. This also implicitely tests if the peak
    # distortion affects the RMSSD (manipulation check).
    rmssd_diff_uncorrected = np.abs(rmssd_correct - rmssd_uncorrected)
    rmssd_diff_corrected = np.abs(rmssd_correct - rmssd_corrected)

    assert int(rmssd_diff_uncorrected - rmssd_diff_corrected) == rmssd_diff


@pytest.mark.parametrize("iterative, rmssd_diff", [(True, 13), (False, 13)],
                         ids=idfn)
def test_missing_correction(peaks_correct, peaks_missing, iterative,
                            rmssd_diff):

    peaks_corrected = correct_peaks(peaks_missing, sfreq=1,
                                    iterative=iterative)

    rmssd_correct = compute_rmssd(peaks_correct)
    rmssd_corrected = compute_rmssd(peaks_corrected)
    rmssd_uncorrected = compute_rmssd(peaks_missing)

    # Assert that correction does not produce peaks that exceed the temporal
    # bounds of the original peaks.
    assert peaks_correct[0] <= peaks_corrected[0]
    assert peaks_correct[-1] >= peaks_corrected[-1]

    # Assert that after artifact correction, the difference in RMSSD to the
    # undistorted signal decreases. This also implicitely tests if the peak
    # distortion affects the RMSSD (manipulation check).
    rmssd_diff_uncorrected = np.abs(rmssd_correct - rmssd_uncorrected)
    rmssd_diff_corrected = np.abs(rmssd_correct - rmssd_corrected)

    assert int(rmssd_diff_uncorrected - rmssd_diff_corrected) == rmssd_diff


###############################################################################

# import matplotlib.pyplot as plt
# from biopeaks.heart import _find_artifacts, _correct_artifacts, correct_peaks

# def show_artifact_correction(peaks_original, peaks_uncorrected,
#                              peaks_corrected, artifacts):

#     rr_original = np.ediff1d(peaks_original, to_begin=0)
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
#     ax1.plot(rr_original, label="original")
#     ax1.plot(rr_corrected, label="corrected")
#     ax1.legend(loc="upper right")


# peaks = generate_peaks(n_peaks=1000)

# peaks_missing = distort_peaks(peaks, kind="missing")
# artifacts_missing = _find_artifacts(peaks_missing, sfreq=1)
# # peaks_missing_corrected = correct_peaks(peaks_missing, sfreq=1)
# peaks_missing_corrected = _correct_artifacts(artifacts_missing, peaks_missing)

# show_artifact_correction(peaks, peaks_missing, peaks_missing_corrected,
#                           artifacts_missing)

# peaks_extra = distort_peaks(peaks, kind="extra")
# artifacts_extra = _find_artifacts(peaks_extra, sfreq=1)
# # peaks_extra_corrected = correct_peaks(peaks_extra, sfreq=1)
# peaks_extra_corrected = _correct_artifacts(artifacts_extra, peaks_extra)

# show_artifact_correction(peaks, peaks_extra, peaks_extra_corrected,
#                           artifacts_extra)

# peaks_misaligned = distort_peaks(peaks, kind="misaligned", k=100,
#                                   displacement_factor=2)
# artifacts_misaligned = _find_artifacts(peaks_misaligned, sfreq=1)
# # peaks_misaligned_corrected = correct_peaks(peaks_misaligned, sfreq=1)
# peaks_misaligned_corrected = _correct_artifacts(artifacts_misaligned,
#                                                 peaks_misaligned)

# show_artifact_correction(peaks, peaks_misaligned, peaks_misaligned_corrected,
#                           artifacts_misaligned)
