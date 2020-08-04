# -*- coding: utf-8 -*-

import numpy as np
from itertools import cycle
from .filters import butter_bandpass_filter
from .analysis_utils import interp_stats


def resp_extrema(signal, sfreq):

    # Slow baseline drifts / fluctuations must be removed from the raw
    # breathing signal (i.e., the signal must be centered around zero) in order
    # to be able to reliable detect zero-crossings.

    # Remove baseline by applying a lowcut at .05Hz (preserves breathing rates
    # higher than 3 breath per minute) and high frequency noise by applying a
    # highcut at 3 Hz (preserves breathing rates slower than 180 breath per
    # minute).
    signal = butter_bandpass_filter(signal, lowcut=.05, highcut=3, fs=sfreq,
                                    order=2)

    greater = signal > 0
    smaller = signal < 0

    # detect zero crossings
    risex = np.where(np.bitwise_and(smaller[:-1], greater[1:]))[0]
    fallx = np.where(np.bitwise_and(greater[:-1], smaller[1:]))[0]

    allx = np.concatenate((risex, fallx))
    allx.sort(kind="mergesort")

    argextreme = cycle([np.argmax, np.argmin])
    if fallx[0] < risex[0]:
        next(argextreme)    # cycle once to switch order

    # find extrema
    extrema = []
    for beg, end in zip(allx[0:], allx[1:]):

        extreme = next(argextreme)(signal[beg:end])
        extrema.append(beg + extreme)

    extrema = np.asarray(extrema)

    # only consider those extrema that have a minimum vertical difference to
    # their direct neighbor, i.e. define outliers in absolute amplitude
    # difference between neighboring extrema
    vertdiff = np.abs(np.diff(signal[extrema]))
    mediandiff = np.median(vertdiff)
    minvert = np.where(vertdiff > mediandiff * 0.3)[0]
    extrema = extrema[minvert]

    # check if the alternation of peaks and troughs is unbroken: if alternation
    # of sign in extdiffs is broken, remove the extrema that cause the breaks
    amps = signal[extrema]
    extdiffs = np.sign(np.diff(amps))
    extdiffs = np.add(extdiffs[0:-1], extdiffs[1:])
    removeext = np.where(extdiffs != 0)[0] + 1
    extrema = np.delete(extrema, removeext)

    return extrema


def resp_stats(extrema, signal, sfreq):
    '''
    tidal amplitude is calculated as vertical trough-peak differences;
    breathing period is calculated as horizontal peak-peak differences
    '''
    # check if the alternation of peaks and troughs is
    # unbroken (it might be due to user edits);
    # if alternation of sign in extdiffs is broken, remove
    # the extreme (or extrema) that cause(s) the break(s)
    amplitudes = signal[extrema]
    extdiffs = np.sign(np.diff(amplitudes))
    extdiffs = np.add(extdiffs[0:-1], extdiffs[1:])
    removeext = np.where(extdiffs != 0)[0] + 1
    extrema = np.delete(extrema, removeext)
    amplitudes = np.delete(amplitudes, removeext)


    # pad the amplitude series in such a way that it always starts with a
    # trough and ends with a peak (i.e., series of trough-peak pairs),
    # in order to be able to interpolate tidal amplitudes by assigning to each
    # peak the vertical difference to the preceding trough; drawing all
    # passible cases in a 2(extrema start w/ peak vs. extrema start w/ trough)
    # x 2(extrema end w/ peak vs. extrema end w/ trough) matrix helps figuring
    # out how to pad series

    # determine if series starts with peak or trough
    if amplitudes[0] > amplitudes[1]:
        # series starts with peak
        # check if number of extrema is even
        if np.remainder(extrema.size, 2) != 0:
            # prepend NAN (i.e., trough)
            extrema = np.pad(extrema.astype(float), (1, 0), 'constant',
                             constant_values=(np.nan,))
            amplitudes = np.pad(amplitudes.astype(float), (1, 0), 'constant',
                                constant_values=(np.nan,))
        else:
            # pad with NANs on both ends (prepend trough and append peak)
            extrema = np.pad(extrema.astype(float), (1, 1), 'constant',
                             constant_values=(np.nan,))
            amplitudes = np.pad(amplitudes.astype(float), (1, 1), 'constant',
                                constant_values=(np.nan,))

    elif amplitudes[0] < amplitudes[1]:
        # series starts with trough
        # check if number of extrema is even
        if np.remainder(extrema.size, 2) != 0:
            # append NAN (i.e., peak)
            extrema = np.pad(extrema.astype(float), (0, 1), 'constant',
                             constant_values=(np.nan,))
            amplitudes = np.pad(amplitudes.astype(float), (0, 1), 'constant',
                                constant_values=(np.nan,))

    # calculate tidal amplitude
    peaks = extrema[1::2]
    amppeaks = amplitudes[1::2]
    amptroughs = amplitudes[0:-1:2]
    tidalamps = amppeaks - amptroughs
    # remove tidal amplitudes that are NAN, as well as any peak that is part of
    # a trough-peak pair that resulted in a tidal amplitude of NAN
    nan_idcs = np.where(np.isnan(tidalamps))[0]
    tidalamps = np.delete(tidalamps, nan_idcs)
    peaks = np.delete(peaks, nan_idcs)
    # to each peak, assign the vertical difference of that peak to the
    # preceding trough
    tidalampintp = interp_stats(peaks, tidalamps, signal.size)

    # calculate breathing period and rate
    # to each peak assign the horizontal difference to the preceding peak
    period = np.ediff1d(peaks, to_begin=0) / sfreq
    period[0] = np.mean(period[1:])
    periodintp = interp_stats(peaks, period, signal.size)
    rateintp = 60 / periodintp

    return periodintp, rateintp, tidalampintp
