# -*- coding: utf-8 -*-
"""Generic analysis utilities."""

import numpy as np
from scipy.interpolate import interp1d


def interp_stats(peaks, stats, nsamp):
    """
    interpolate descriptive statistics over the entire duration of the
    signal: samples up until first peak and from last peak to end of signal
    are set to the value of the first and last element of stats respectively;
    linear (2nd order) interpolation is chosen since cubic (4th order)
    interpolation can lead to biologically implausible interpolated values
    and erratic fluctuations due to overfitting
    """
    f = interp1d(np.ravel(peaks), stats, kind='slinear',
                 bounds_error=False, fill_value=([stats[0]], [stats[-1]]))
    # internally, for consistency in plotting etc., keep original sampling
    # rate
    samples = np.arange(0, nsamp)
    statsintp = f(samples)

    return statsintp
