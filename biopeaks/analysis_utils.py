# -*- coding: utf-8 -*-
"""Generic analysis utilities."""

import numpy as np
from scipy.interpolate import interp1d


def interp_stats(peaks, stats, nsamp):
    """Interpolate instantaneous statistics.

    Interpolate instantaneous statistics between the associated samples (i.e.,
    extrema) over a vector ranging up to a specific sample.

    Parameters
    ----------
    peaks : ndarray
        Samples associated with the instantaneous statistics. Must have the same
        number of elements as stats.
    stats : ndarray
        The instantaneous statistics associated with each peak. Must have the
        same number of elements as peaks.
    nsamp : int
        Interpolate statistics over a vector containing samples from 0 to nsamp.

    Returns
    -------
    ndarray
        The interpolated instantaneous statistics.

    See Also
    --------
    scipy.interpolate.interp1d

    Notes
    -----
    Stats values for the samples up until the first peak and from last peak to
    the last sample (nsamp) are extrapolated using the value of the first and
    last element of stats respectively. First order spline interpolation is
    used, since higher order interpolation (e.g., cubic) can lead to
    biologically implausible interpolated stats values due to over- or
    undershooting (i.e., violations of monotonicity).
    """
    f = interp1d(np.ravel(peaks), stats, kind='slinear',
                 bounds_error=False, fill_value=([stats[0]], [stats[-1]]))
    samples = np.arange(0, nsamp)    # implicitly preserves original sampling rate
    statsintp = f(samples)

    return statsintp
