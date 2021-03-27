# -*- coding: utf-8 -*-
"""Collection of filters.

To obtain a zero-phase, non-causal filter, scipy.signal.sosfiltfilt is used to
filter the signal. I.e. the filtered signal is not phase shifted with respect
to the original signal since the filtering is performed in both directions
(phase shifts cancel each other out).

Following SciPy recommendations, the second-order sections format is used to
avoid numerical error with transfer function (ba) format.
"""

from scipy.signal import butter, sosfiltfilt, filtfilt
import numpy as np


def _butter_lowpass(cutoff, sfreq, order=5):
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
    sos : ndarray
        Second-order sections representation of the IIR filter.
    """
    nyq = 0.5 * sfreq
    normal_cutoff = cutoff / nyq
    sos = butter(order, normal_cutoff, btype="low", output="sos")
    return sos


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
    sos = _butter_lowpass(cutoff, sfreq, order=order)
    y = sosfiltfilt(sos, signal)
    return y


def _butter_highpass(cutoff, sfreq, order=5):
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
    sos : ndarray
        Second-order sections representation of the IIR filter.
    """
    nyq = 0.5 * sfreq
    normal_cutoff = cutoff / nyq
    sos = butter(order, normal_cutoff, btype="high", output="sos")
    return sos


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
    sos = _butter_highpass(cutoff, sfreq, order=order)
    y = sosfiltfilt(sos, signal)
    return y


def _butter_bandpass(lowcut, highcut, sfreq, order=5):
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
    sos : ndarray
        Second-order sections representation of the IIR filter.
    """
    nyq = 0.5 * sfreq
    low = lowcut / nyq
    high = highcut / nyq
    sos = butter(order, [low, high], btype="band", output="sos")
    return sos


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
    sos = _butter_bandpass(lowcut, highcut, sfreq, order=order)
    y = sosfiltfilt(sos, signal)
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
    y = np.convolve(signal, np.ones((window_size,)) / window_size, mode="same")
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
