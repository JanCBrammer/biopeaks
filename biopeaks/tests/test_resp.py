# -*- coding: utf-8 -*-
"""Unit tests for resp module."""

import pytest
import numpy as np
from biopeaks.resp import ensure_peak_trough_alternation

@pytest.fixture
def signal():
    return np.array([-1, -1, 5, -3, -5, -5, -1, 0, 1, 0])

@pytest.fixture
def extrema(signal):
    return np.arange(signal.size)


def test_ensure_peak_trough_alternation(signal, extrema):

    alternating_extrema = ensure_peak_trough_alternation(extrema, signal)
    print(alternating_extrema)
    assert np.sum(alternating_extrema - np.array([0, 2, 4, 8, 9])) == 0


