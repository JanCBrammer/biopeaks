# -*- coding: utf-8 -*-
"""Collection of filters.

To obtain a zero-phase, non-causal filter, scipy.signal.filtfilt is used to
filter the signal. I.e. the filtered signal is not phase shifted with respect
to the original signal since the filtering is performed in both directions
(phase shifts cancel each other out).
"""

from scipy.signal import butter, filtfilt
import numpy as np


def butter_lowpass(cutoff, sfreq, order=5):
    """Design IIR low-pass Butterworth filter.

    Parameters
    ----------
    cutoff : float
        Cutoff frequency. Passband is below `cutoff`.
    sfreq : int
        Sampling frequency of signal.
    order : int, optional
        Filter order, by default 5.

    Returns
    -------
    b, a : ndarray, ndarray
        Numerator (`b`) and denominator (`a`) polynomials of the IIR filter.
    """
    nyq = 0.5 * sfreq
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low')
    return b, a


def butter_lowpass_filter(signal, cutoff, sfreq, order=5):
    """Apply IIR low-pass Butterworth filter.

    Parameters
    ----------
    signal : ndarray
        The signal to be filtered.
    cutoff : float
        Cutoff frequency. Passband is below `cutoff`.
    sfreq : int
        Sampling frequency of `signal`.
    order : int, optional
        Filter order, by default 5.

    Returns
    -------
    y : ndarray
        The filtered signal.
    """
    b, a = butter_lowpass(cutoff, sfreq, order=order)
    y = filtfilt(b, a, signal, method='pad')
    return y


def butter_highpass(cutoff, sfreq, order=5):
    """Design IIR high-pass Butterworth filter.

    Parameters
    ----------
    cutoff : float
        Cutoff frequency. Passband is above `cutoff`.
    sfreq : int
        Sampling frequency of `signal`.
    order : int, optional
        Filter order, by default 5.

    Returns
    -------
    b, a : ndarray, ndarray
        Numerator (`b`) and denominator (`a`) polynomials of the IIR filter.
    """
    nyq = 0.5 * sfreq
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high')
    return b, a


def butter_highpass_filter(signal, cutoff, sfreq, order=5):
    """Apply IIR high-pass Butterworth filter.

    Parameters
    ----------
    signal : ndarray
        The signal to be filtered.
    cutoff : float
        Cutoff frequency. Passband is above `cutoff`.
    sfreq : int
        Sampling frequency of `signal`.
    order : int, optional
        Filter order, by default 5.

    Returns
    -------
    y : ndarray
        The filtered signal.
    """
    b, a = butter_highpass(cutoff, sfreq, order=order)
    y = filtfilt(b, a, signal, method='pad')
    return y


def butter_bandpass(lowcut, highcut, sfreq, order=5):
    """Design IIR band-pass Butterworth filter.

    Parameters
    ----------
    lowcut, highcut : float, float
        Cutoff frequencies. Passband is between `lowcut` and `highcut`.
    sfreq : int
        Sampling frequency of `signal`.
    order : int, optional
        Filter order, by default 5.

    Returns
    -------
    b, a : ndarray, ndarray
        Numerator (`b`) and denominator (`a`) polynomials of the IIR filter.
    """
    nyq = 0.5 * sfreq
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(signal, lowcut, highcut, sfreq, order=5):
    """Apply IIR band-pass Butterworth filter.

    Parameters
    ----------
    signal : ndarray
        The signal to be filtered.
    lowcut, highcut : float, float
        Cutoff frequencies. Passband is between `lowcut` and `highcut`.
    sfreq : int
        Sampling frequency of `signal`.
    order : int, optional
        Filter order, by default 5.

    Returns
    -------
    y : ndarray
        The filtered signal.
    """
    b, a = butter_bandpass(lowcut, highcut, sfreq, order=order)
    y = filtfilt(b, a, signal, method='pad')
    return y


def moving_average(signal, window_size):
    """Apply a moving average filter.

    Parameters
    ----------
    signal : ndarray
        The signal to be filtered.
    window_size : int
        The width of the filter kernel in samples.

    Returns
    -------
    y : ndarray
        The filtered signal.
    """
    y = np.convolve(signal, np.ones((window_size,)) / window_size, mode='same')
    return y


def powerline_filter(signal, sfreq):
    """Apply a 50Hz powerline filter.

    Smooth out 50Hz powerline noise with a kernel the width of one period of
    50 Hz.

    Parameters
    ----------
    signal : ndarray
        The signal to be filtered.
    sfreq : int
        Sampling frequency of `signal`.

    Returns
    -------
    y : ndarray
        The filtered signal.
    """
    if sfreq >= 100:
        b = np.ones(int(sfreq / 50))
    else:
        b = np.ones(2)
    a = [len(b)]
    y = filtfilt(b, a, signal, method="pad")
    return y
