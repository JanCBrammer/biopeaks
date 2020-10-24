# -*- coding: utf-8 -*-
"""Unit tests for resp module."""

import pytest
import numpy as np
from pathlib import Path
from biopeaks.resp import (resp_extrema, resp_stats,
                           ensure_peak_trough_alternation)
from biopeaks.io_utils import read_edf


@pytest.fixture
def resp_data():
    datadir = Path(__file__).parent.resolve().joinpath("testdata")
    data = read_edf(datadir.joinpath("EDFmontage0.edf"), channel="A5",
                    channeltype="signal")
    return data


@pytest.fixture
def signal():
    return np.array([-1, -1, 5, -3, -5, -5, -1, 0, 1, 0])


@pytest.fixture
def extrema(signal):
    return np.arange(signal.size)


def test_resp_extrema(resp_data):

    test_extrema = resp_extrema(resp_data["signal"], resp_data["sfreq"])
    assert np.allclose(np.sum(test_extrema), 40410033, atol=5)


def test_resp_stats(signal, extrema):

    period, rate, tidalamp = resp_stats(extrema, signal, sfreq=1)
    assert np.mean(period) == 6
    assert np.mean(rate) == 10
    assert np.mean(tidalamp) == 6


def test_ensure_peak_trough_alternation(signal, extrema):

    alternating_extrema = ensure_peak_trough_alternation(extrema, signal)
    assert np.sum(alternating_extrema - np.array([0, 2, 4, 8, 9])) == 0
