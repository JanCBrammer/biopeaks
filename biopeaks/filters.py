# -*- coding: utf-8 -*-

from scipy.signal import butter, filtfilt
import numpy as np

# use filtfilt to obtain a zero-phase filter, i.e. the filtered signal is not
# phase shifted with respect to the original signal since the filtering is
# performed in both directions (phase shifts cancel each other out)


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low')
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data, method='pad')
    return y


def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high')
    return b, a


def butter_highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data, method='pad')
    return y


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data, method='pad')
    return y


def moving_average(signal, window_size):
    return np.convolve(signal, np.ones((window_size,)) / window_size,
                       mode='same')


def powerline_filter(data, sfreq):
    """Smoothing out 50Hz power-line noise with a kernel the width of one
    period of 50 Hz."""
    if sfreq >= 100:
        b = np.ones(int(sfreq / 50))
    else:
        b = np.ones(2)
    a = [len(b)]
    y = filtfilt(b, a, data, method="pad")
    return y
