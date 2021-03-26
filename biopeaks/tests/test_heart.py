# -*- coding: utf-8 -*-
"""Unit tests for heart module."""

import pytest
import numpy as np
from pathlib import Path
from biopeaks.heart import (ecg_peaks, ppg_peaks, heart_stats, _find_artifacts,
                            _correct_artifacts, correct_peaks)
from biopeaks.io_utils import read_edf


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

    rr = np.sin(np.arange(n_peaks))    # simulate sinusoidally changing heart periods
    rng = np.random.default_rng(42)
    rr_noisy = rng.normal(rr, .1)    # add some noise
    rr_scaled = 1000 + rr_noisy * 125    # make heart period fluctuate in a range of 250 msec around 1000 msec
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
def peaks_missed(peaks_correct, artifact_idcs):

    peaks_missed = peaks_correct.copy()
    peaks_missed = np.delete(peaks_missed, artifact_idcs)

    return peaks_missed


@pytest.fixture
def peaks_extra(peaks_correct, artifact_idcs):

    extra_peaks = ((peaks_correct[artifact_idcs + 1] -
                    peaks_correct[artifact_idcs]) / 15 +
                   peaks_correct[artifact_idcs])

    peaks_extra = peaks_correct.copy()
    peaks_extra = np.insert(peaks_extra, artifact_idcs, extra_peaks)

    return peaks_extra


@pytest.fixture
def artifacts_misaligned(artifact_idcs):
    artifacts = {"ectopic": list(artifact_idcs + 1), "missed": [], "extra": [],
                 "longshort": list(artifact_idcs)}
    return artifacts


@pytest.fixture
def artifacts_missed(artifact_idcs):
    missed_idcs = [j - i for i, j in enumerate(artifact_idcs)]    # account for the fact that peak indices are shifted to the left after deletion of peaks
    artifacts = {"ectopic": [], "missed": missed_idcs, "extra": [],
                 "longshort": []}
    return artifacts


@pytest.fixture
def artifacts_extra(artifact_idcs):
    extra_idcs = [j + (i + 1) for i, j in enumerate(artifact_idcs)]    # account for the fact that peak indices are shifted to the right after insertion of peaks
    artifacts = {"ectopic": [], "missed": [], "extra": extra_idcs,
                 "longshort": []}
    return artifacts


@pytest.mark.parametrize("peaks_misaligned", [2, 4, 8],
                         indirect=["peaks_misaligned"])
def test_misaligned_detection(peaks_misaligned, artifacts_misaligned):

    artifacts = _find_artifacts(peaks_misaligned, sfreq=1)
    assert artifacts == artifacts_misaligned    # check for identical key-value pairs


def test_missed_detection(peaks_missed, artifacts_missed):

    artifacts = _find_artifacts(peaks_missed, sfreq=1)
    assert artifacts == artifacts_missed


def test_extra_detection(peaks_extra, artifacts_extra):

    artifacts = _find_artifacts(peaks_extra, sfreq=1)
    assert artifacts == artifacts_extra


@pytest.mark.parametrize("peaks_misaligned", [2, 4, 8],
                         indirect=["peaks_misaligned"])
def test_misaligned_correction(peaks_misaligned, artifacts_misaligned):

    peaks_corrected = _correct_artifacts(artifacts_misaligned,
                                         peaks_misaligned)

    assert np.unique(peaks_corrected).size == peaks_misaligned.size    # make sure that no peak duplication occurs and that number of peaks doesn't change


def test_missed_correction(peaks_missed, artifacts_missed):

    peaks_corrected = _correct_artifacts(artifacts_missed, peaks_missed)

    assert np.unique(peaks_corrected).size == (peaks_missed.size +
                                               len(artifacts_missed["missed"]))


def test_extra_correction(peaks_extra, artifacts_extra):

    peaks_corrected = _correct_artifacts(artifacts_extra, peaks_extra)

    assert np.unique(peaks_corrected).size == (peaks_extra.size
                                               - len(artifacts_extra["extra"]))


def idfn(val):
    if isinstance(val, bool):
        return f"iterative_{val}"


@pytest.mark.parametrize("peaks_misaligned, iterative, rmssd_diff",
                         [(2, True, 33), (2, False, 27),
                          (4, True, 133), (4, False, 113),
                          (8, True, 467), (8, False, 444)],
                         indirect=["peaks_misaligned"], ids=idfn)
def test_misaligned_correction_wrapper(peaks_correct, peaks_misaligned,
                                       iterative, rmssd_diff):

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
def test_extra_correction_wrapper(peaks_correct, peaks_extra, iterative,
                                  rmssd_diff):

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
def test_missed_correction_wrapper(peaks_correct, peaks_missed, iterative,
                                   rmssd_diff):

    peaks_corrected = correct_peaks(peaks_missed, sfreq=1,
                                    iterative=iterative)

    rmssd_correct = compute_rmssd(peaks_correct)
    rmssd_corrected = compute_rmssd(peaks_corrected)
    rmssd_uncorrected = compute_rmssd(peaks_missed)

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


@pytest.fixture
def ecg_data():

    datadir = Path(__file__).parent.resolve().joinpath("testdata")
    data = read_edf(datadir.joinpath("EDFmontage0.edf"), channel="A3",
                    channeltype="signal")
    return data


@pytest.fixture
def ppg_data():

    datadir = Path(__file__).parent.resolve().joinpath("testdata")
    data = read_edf(datadir.joinpath("EDFmontage0.edf"), channel="A5",
                    channeltype="signal")
    return data


def test_ecg_peaks(ecg_data):

    test_extrema = ecg_peaks(ecg_data["signal"], ecg_data["sfreq"])
    assert np.allclose(np.sum(test_extrema), 202504458, atol=5)


def test_ppg_peaks(ppg_data):

    test_extrema = ppg_peaks(ppg_data["signal"], ppg_data["sfreq"])
    assert np.allclose(np.sum(test_extrema), 20238288, atol=5)


def test_heart_stats(peaks_correct):

    period, rate = heart_stats(peaks_correct, sfreq=1000, nsamp=peaks_correct[-1])
    assert np.allclose(np.mean(period), 1, atol=.01)
    assert np.allclose(np.mean(rate), 60, atol=1)
