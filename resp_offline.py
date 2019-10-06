# -*- coding: utf-8 -*-
"""
Created on Wed Dec  5 17:33:13 2018

@author: John Doe
"""

import numpy as np
from scipy.signal import welch, find_peaks, argrelextrema
from filters import butter_lowpass_filter

def rate_resp(peaks):
    # check if the alternation of peaks and troughs is
    # unbroken (it might be due to user edits);
    # if alternation of sign in extdiffs is broken, remove
    # the extreme (or extrema) that cause(s) the break(s)
    extdiffs = np.sign(np.diff(peaks[:, 1]))
    extdiffs = np.add(extdiffs[0:-1], extdiffs[1:])
    removeext = np.where(extdiffs != 0)[0] + 1
    peaks = np.delete(peaks, removeext, axis=0)
    
    # determine if series starts with peak or trough to be able
    # to save peaks and troughs separately (as well as the
    # corresponding amplitudes)
    if extrema[0, 1] > extrema[1, 1]:
        peaks = extrema[0:-1:2, 0]
        troughs = extrema[1::2, 0]
        amppeaks = extrema[0:-1:2, 1]
        amptroughs = extrema[1::2, 1]
    elif extrema[0, 1] < extrema[1, 1]:
        peaks = extrema[1::2, 0]
        troughs = extrema[0:-1:2, 0]
        amppeaks = extrema[1::2, 1]
        amptroughs = extrema[0:-1:2, 1]

def extrema_resp(signal, sfreq):

    N = np.size(signal)
    # get an initial estimate of dominant breathing rate; assume rate ranging
    # from 10 to 30 breaths per minute
    fmin, fmax = .16, 0.5
    f, powden = welch(signal, sfreq, nperseg=N)
    f_range = np.logical_and(f >= fmin, f <= fmax)
    f = f[f_range]
    powden = powden[f_range]
    pow_peaks = find_peaks(powden)[0]
    if len(pow_peaks) > 0:
        max_pow = pow_peaks[np.argmax(powden[pow_peaks])]
    else:
        max_pow = np.argmax(powden)
    freq_est = f[max_pow]

    filt = butter_lowpass_filter(signal, 2 * freq_est, sfreq, order=2)

    # identify preliminary local extrema (separately for peaks and troughs)
    locmax = argrelextrema(filt, np.greater)[0]
    locmin = argrelextrema(filt, np.less)[0]
    extrema = np.concatenate((locmax, locmin))
    extrema.sort(kind='mergesort')

    # in the following, only consider those extrema that have a minimum
    # vertical difference to their direct neighbor, i.e. define outliers in
    # absolute vertical distance between neighboring peaks
    vertdiff = np.abs(np.diff(filt[extrema]))
    avgvertdiff = np.mean(vertdiff)
    minvert = np.where(vertdiff > avgvertdiff * 0.3)[0]
    extrema = extrema[minvert]
    peaks = locmax[np.in1d(locmax, extrema)]
    troughs = locmin[np.in1d(locmin, extrema)]

    # because some local extrema could be thrown out by now, there could be
    # cases where multiple local extrema of the same kind occur consecutively;
    # i.e. cases where the alternation of peaks and troughs is broken; for each
    # local extreme of kind i, compute difference to the next following local
    # extreme of the kind i and of the kind j, if the ii difference is smaller
    # than the ij difference, there are two consecutive local extrema of the
    # kind i
    remove_p = []
    for p in range(len(peaks) - 1):

        current_p = peaks[p]
        next_p = peaks[p + 1]
        pp = np.abs(current_p - next_p)

        pt_all = troughs - current_p
        # select only those differences which are larger than zero, since
        # those are the troughs whose indices are larger than the index of
        # the current peak
        pt_all_select = pt_all > 0
        # where returns only indices of True elements
        if np.where(pt_all_select)[0].size > 0:

            next_t = troughs[pt_all_select][np.argmin(pt_all[pt_all_select])]
            pt = np.abs(current_p - next_t)

            # if there are two consecutive peaks, remove the last one
            if pp < pt:
                remove_p.append(p + 1)

    peaks = np.delete(peaks, remove_p)

    remove_t = []
    for t in range(len(troughs) - 1):

        current_t = troughs[t]
        next_t = troughs[t + 1]
        tt = np.abs(current_t - next_t)

        tp_all = peaks - current_t
        # select only those differences which are larger than zero, since
        # those are the peaks whose indices are larger than the index of
        # the current trough
        tp_all_select = tp_all > 0
        if np.where(tp_all_select)[0].size > 0:

            next_p = peaks[tp_all_select][np.argmin(tp_all[tp_all_select])]
            tp = np.abs(current_t - next_p)

            # if there are two consecutive troughs, remove the last one
            if tt < tp:
                remove_t.append(t + 1)

    troughs = np.delete(troughs, remove_t)

    # refine the position of the peaks and troughs, since they're often
    # slightly misplaced due to the filtering

    # unilateral extend of search window around preliminary peaks in samples
    n_search_window = 0.3 * sfreq

    adjusted_troughs = []
    for t in troughs:

        search_samples = np.arange(t - n_search_window,
                                   t + n_search_window,
                                   dtype=int)

        # make sure that the search window doesn't exceed the boundaries of the
        # trial
        if search_samples[0] <= 0:
            search_samples = np.arange(0,
                                       t + n_search_window,
                                       dtype=int)
        elif search_samples[-1] >= N:
            search_samples = np.arange(t - n_search_window,
                                       N,
                                       dtype=int)

        search_signal = signal[search_samples]
        adjusted_t = search_samples[np.argmin(search_signal)]
        adjusted_troughs.append(adjusted_t)

    adjusted_peaks = []
    for p in peaks:

        search_samples = np.arange(p - n_search_window,
                                   p + n_search_window,
                                   dtype=int)

        # make sure that the search window doesn't exceed the boundaries of the
        # trial
        if search_samples[0] <= 0:
            search_samples = np.arange(0,
                                       p + n_search_window,
                                       dtype=int)
        elif search_samples[-1] >= N:
            search_samples = np.arange(p - n_search_window,
                                       N,
                                       dtype=int)

        search_signal = signal[search_samples]
        adjusted_p = search_samples[np.argmax(search_signal)]
        adjusted_peaks.append(adjusted_p)

    # prepare data for handling in biopeaks gui
    returnarray = np.concatenate((adjusted_peaks,
                                  adjusted_troughs)).astype(int)
    returnarray.sort(kind='mergesort')
    

    return returnarray
        