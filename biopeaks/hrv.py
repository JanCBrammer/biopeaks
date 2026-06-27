# -*- coding: utf-8 -*-
"""Compute time-domain heart rate variability (HRV) features."""

import numpy as np


def hrv_features(peaks, sfreq):
    """Compute time-domain heart rate variability (HRV) features.

    Derive the standard time-domain HRV features from a series of cardiac
    extrema (R-peaks or systolic peaks). The features are computed from the
    NN-interval series (the durations between successive peaks), expressed in
    milliseconds.

    Parameters
    ----------
    peaks : ndarray
        Cardiac extrema (R-peaks or systolic peaks), in samples.
    sfreq : int
        Sampling frequency of the cardiac signal containing `peaks`, in Hz.

    Returns
    -------
    features : dict
        Mapping of feature name to value. The NN-interval features
        (`mean_nn`, `median_nn`, `sdnn`, `rmssd`, `sdsd`) are in milliseconds,
        `nn50` and `nn20` are counts, `pnn50` and `pnn20` are percentages, and
        the heart-rate features (`mean_hr`, `min_hr`, `max_hr`) are in beats
        per minute.

    Raises
    ------
    ValueError
        If fewer than three peaks are provided, since the successive-difference
        features (e.g., `rmssd`) require at least two NN intervals.

    Notes
    -----
    The features follow the conventional time-domain HRV definitions [1]_:

    * ``mean_nn``, ``median_nn``: central tendency of the NN intervals.
    * ``sdnn``: standard deviation of the NN intervals.
    * ``rmssd``: root mean square of successive NN-interval differences.
    * ``sdsd``: standard deviation of successive NN-interval differences.
    * ``nn50``, ``nn20``: number of successive NN-interval differences greater
      than 50 ms and 20 ms, respectively.
    * ``pnn50``, ``pnn20``: ``nn50`` and ``nn20`` as a percentage of the number
      of successive differences.
    * ``mean_hr``, ``min_hr``, ``max_hr``: instantaneous heart rate derived
      from the NN intervals.

    Standard deviations use one degree of freedom (sample standard deviation).

    References
    ----------
    .. [1] Shaffer, F., & Ginsberg, J. P. (2017). An Overview of Heart Rate
       Variability Metrics and Norms. Frontiers in Public Health, 5, 258.
    """
    peaks = np.ravel(peaks)
    if peaks.size < 3:
        raise ValueError("`peaks` must contain at least three elements to "
                         "compute HRV features.")

    nn = np.diff(peaks) / sfreq * 1000    # NN intervals in milliseconds
    nn_diff = np.diff(nn)                  # successive NN-interval differences
    instant_hr = 60000 / nn               # instantaneous heart rate in bpm

    return {
        "mean_nn": np.mean(nn),
        "median_nn": np.median(nn),
        "sdnn": np.std(nn, ddof=1),
        "rmssd": np.sqrt(np.mean(nn_diff ** 2)),
        "sdsd": np.std(nn_diff, ddof=1),
        "nn50": int(np.sum(np.abs(nn_diff) > 50)),
        "pnn50": np.sum(np.abs(nn_diff) > 50) / nn_diff.size * 100,
        "nn20": int(np.sum(np.abs(nn_diff) > 20)),
        "pnn20": np.sum(np.abs(nn_diff) > 20) / nn_diff.size * 100,
        "mean_hr": np.mean(instant_hr),
        "min_hr": np.min(instant_hr),
        "max_hr": np.max(instant_hr),
    }
