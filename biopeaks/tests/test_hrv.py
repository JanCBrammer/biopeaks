# -*- coding: utf-8 -*-
"""Unit tests for hrv module."""

import pytest
import numpy as np
from biopeaks.hrv import hrv_features


def test_hrv_features_alternating_intervals():
    """Hand-computed features for an alternating 1000/800 ms NN series."""
    sfreq = 1000    # 1 sample == 1 ms
    # NN intervals (ms): 1000, 800, 1000, 800, 1000
    peaks = np.array([0, 1000, 1800, 2800, 3600, 4600])

    features = hrv_features(peaks, sfreq)

    assert np.isclose(features["mean_nn"], 920)
    assert np.isclose(features["median_nn"], 1000)
    assert np.isclose(features["sdnn"], np.sqrt(12000))      # ddof=1
    assert np.isclose(features["rmssd"], 200)
    assert np.isclose(features["sdsd"], np.sqrt(160000 / 3))  # ddof=1
    assert features["nn50"] == 4
    assert np.isclose(features["pnn50"], 100)
    assert features["nn20"] == 4
    assert np.isclose(features["pnn20"], 100)
    assert np.isclose(features["mean_hr"], 66)               # mean of 60, 75
    assert np.isclose(features["min_hr"], 60)                # 60000 / 1000
    assert np.isclose(features["max_hr"], 75)                # 60000 / 800


def test_hrv_features_constant_intervals_have_zero_variability():
    """A perfectly regular rhythm has no variability."""
    sfreq = 250
    peaks = np.arange(0, 250 * 11, 250)    # ten 1000 ms NN intervals

    features = hrv_features(peaks, sfreq)

    assert np.isclose(features["mean_nn"], 1000)
    assert np.isclose(features["sdnn"], 0)
    assert np.isclose(features["rmssd"], 0)
    assert np.isclose(features["sdsd"], 0)
    assert features["nn50"] == 0
    assert np.isclose(features["pnn50"], 0)
    assert np.isclose(features["mean_hr"], 60)


def test_hrv_features_sampling_rate_scales_intervals():
    """Halving the sampling rate doubles the NN duration for fixed peaks."""
    peaks = np.array([0, 100, 200, 300])

    coarse = hrv_features(peaks, sfreq=100)
    fine = hrv_features(peaks, sfreq=200)

    assert np.isclose(coarse["mean_nn"], 2 * fine["mean_nn"])
    assert np.isclose(coarse["mean_hr"], fine["mean_hr"] / 2)


@pytest.mark.parametrize(
    "peaks", [np.array([]), np.array([10]), np.array([10, 20])]
)
def test_hrv_features_requires_at_least_three_peaks(peaks):
    with pytest.raises(ValueError):
        hrv_features(peaks, sfreq=1000)
