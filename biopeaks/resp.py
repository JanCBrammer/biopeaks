# -*- coding: utf-8 -*-
"""Extract features from respiratory signals."""

import numpy as np
from itertools import cycle
from biopeaks.filters import butter_bandpass_filter
from biopeaks.analysis_utils import interp_stats


def resp_extrema(signal, sfreq):
    """Detect local extrema in a respiratory signal.

    Detect inhalation peaks and exhalation troughs with a variant of the
    "zero-crossing algorithm with amplitude threshold" [1]. Baseline drift
    must be removed from the raw breathing signal (i.e., the signal must be
    centered around zero) in order to be able to reliable detect zero-crossings.

    Parameters
    ----------
    signal : ndarray
        The respiratory signal.
    sfreq : int
        The sampling frequency of `signal`.

    Returns
    -------
    extrema : ndarray
        Alternating sequence of samples marking the inhalation peaks and
        exhalation troughs (sequence can start with either inhalation peak or
        exhalation trough).

    References
    ----------
    [1] D. Khodadad et al., “Optimized breath detection algorithm in electrical
    impedance tomography,” Physiol. Meas., vol. 39, no. 9, Sep. 2018,
    doi: 10.1088/1361-6579/aad7e6.
    """
    signal = butter_bandpass_filter(signal, lowcut=.05, highcut=3, sfreq=sfreq,
                                    order=2)    # preserve breathing rates > 3 bpm and < 180 bpm

    greater = signal > 0
    smaller = signal < 0

    risex = np.where(np.bitwise_and(smaller[:-1], greater[1:]))[0]    # detect rising zero crossings
    fallx = np.where(np.bitwise_and(greater[:-1], smaller[1:]))[0]    # detect falling zero crossings

    allx = np.concatenate((risex, fallx))
    allx.sort(kind="mergesort")

    argextreme = cycle([np.argmax, np.argmin])
    if fallx[0] < risex[0]:
        next(argextreme)    # cycle once to switch order

    extrema = []
    for beg, end in zip(allx[0:], allx[1:]):

        extreme = next(argextreme)(signal[beg:end])
        extrema.append(beg + extreme)

    extrema = np.asarray(extrema)

    vertdiff = np.abs(np.diff(signal[extrema]))
    mediandiff = np.median(vertdiff)
    minvert = np.where(vertdiff > mediandiff * 0.3)[0]
    extrema = extrema[minvert]    # retain consider extrema that have a minimum vertical difference to their direct neighbor, i.e. define outliers in absolute amplitude difference between neighboring extrema

    amps = signal[extrema]
    extdiffs = np.sign(np.diff(amps))
    extdiffs = np.add(extdiffs[0:-1], extdiffs[1:])
    removeext = np.where(extdiffs != 0)[0] + 1
    extrema = np.delete(extrema, removeext)    # remove extrema that cause breaks in the alternation of peaks and troughs

    return extrema


def resp_stats(extrema, signal, sfreq):
    """Compute instantaneous respiratory features.

    Compute tidal amplitude, as well as respiratory period and -rate based on
    respiratory extrema (i.e., inhalation peaks, exhalation throughs). Tidal
    amplitude is computed as vertical trough-peak differences. I.e., to each
    peak, assign the vertical (amplitude) difference of that peak to the
    preceding trough. Breathing period and -rate are calculated as horizontal
    (temporal) peak-peak differences. I.e., to each peak assign the horizontal
    difference to the preceding peak.

    Parameters
    ----------
    extrema : ndarray
        Alternating sequence of samples marking the inhalation peaks and
        exhalation troughs (sequence can start with either inhalation peak or
        exhalation trough).
    signal : ndarray
        The respiratory signal.
    sfreq : int
        The sampling frequency of `signal`.

    Returns
    -------
    periodintp, rateintp, tidalampintp : ndarray, ndarray, ndarray
        Vectors with the same number of elements as `signal`, containing the
        instantaneous respiratory period, -rate, and tidal amplitude.
    """
    extrema = ensure_peak_trough_alternation(extrema, signal)
    amplitudes = signal[extrema]

    # Pad the amplitude series in such a way that it always starts with a
    # trough and ends with a peak (i.e., series of trough-peak pairs)
    # in order to be able to interpolate tidal amplitudes by assigning to each
    # peak the vertical difference to the preceding trough. Drawing all
    # passible cases in a 2(extrema start w/ peak vs. extrema start w/ trough)
    # x 2(extrema end w/ peak vs. extrema end w/ trough) matrix helps figuring
    # out how to pad series.
    if amplitudes[0] > amplitudes[1]:    # series starts with peak

        if np.remainder(extrema.size, 2) != 0:    # check if number of extrema is even
            extrema = np.pad(extrema.astype(float), (1, 0), 'constant',
                             constant_values=(np.nan,))     # prepend NAN (i.e., trough)
            amplitudes = np.pad(amplitudes.astype(float), (1, 0), 'constant',
                                constant_values=(np.nan,))
        else:
            extrema = np.pad(extrema.astype(float), (1, 1), 'constant',
                             constant_values=(np.nan,))    # pad with NANs on both ends (prepend trough and append peak)
            amplitudes = np.pad(amplitudes.astype(float), (1, 1), 'constant',
                                constant_values=(np.nan,))

    elif amplitudes[0] < amplitudes[1]:    # series starts with trough

        if np.remainder(extrema.size, 2) != 0:
            extrema = np.pad(extrema.astype(float), (0, 1), 'constant',
                             constant_values=(np.nan,))    # append NAN (i.e., peak)
            amplitudes = np.pad(amplitudes.astype(float), (0, 1), 'constant',
                                constant_values=(np.nan,))

    peaks = extrema[1::2]
    amppeaks = amplitudes[1::2]
    amptroughs = amplitudes[0:-1:2]
    tidalamps = amppeaks - amptroughs

    nan_idcs = np.where(np.isnan(tidalamps))[0]
    tidalamps = np.delete(tidalamps, nan_idcs)    # remove tidal amplitudes that are NAN
    peaks = np.delete(peaks, nan_idcs)    # remove peaks that are part of a trough-peak pair that resulted in a tidal amplitude of NAN
    tidalampintp = interp_stats(peaks, tidalamps, signal.size)

    period = np.ediff1d(peaks, to_begin=0) / sfreq
    period[0] = np.mean(period[1:])
    periodintp = interp_stats(peaks, period, signal.size)
    rateintp = 60 / periodintp

    return periodintp, rateintp, tidalampintp


def ensure_peak_trough_alternation(extrema, signal):
    """Ensure peak-trough alternation in respiratory extrema.

    Ensure that the alternation of inhalation peaks and exhalation troughs is
    unbroken (it might be due to user edits).

    Parameters
    ----------
    extrema : [type]
        Samples marking the inhalation peaks and exhalation troughs.
    signal : ndarray
        The respiratory signal.

    Returns
    -------
    alternating_extrema : ndarray
        Alternating sequence of inhalation peaks and exhalation troughs (can
        start with either peak or trough).
    """
    amp_at_ext = signal[extrema]
    amp_at_ext += abs(min(amp_at_ext))    # enforce positive values in order to be able to rely on sign differences
    amp_diffs = np.diff(amp_at_ext)
    sign_amp_diffs = np.sign(amp_diffs)    # 1: positive amplitude difference, -1: negative amplitude difference, 0: no amplitude difference
    sign_equal = sign_amp_diffs[:-1] == sign_amp_diffs[1:]    # extrema at which the amplitude doesn't switch sign
    sign_constant = sign_amp_diffs[:-1] == 0    # extrema at which the amplitude is equal to the previous extreme
    delete_ext = np.where(np.logical_or(sign_equal, sign_constant))[0]

    alternating_extrema = np.delete(extrema, delete_ext + 1)

    return alternating_extrema
