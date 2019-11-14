# -*- coding: utf-8 -*-
"""
Created on Wed Dec  5 17:33:13 2018

@author: John Doe
"""

import numpy as np
from scipy.signal import welch, find_peaks, argrelextrema
from .filters import butter_lowpass_filter
from .analysis_utils import interp_stats


def resp_extrema(signal, sfreq):

    N = np.size(signal)
    # get an initial estimate of dominant breathing rate; assume rate ranging
    # from 5 to 60 breaths per minute
    fmin, fmax = .08, 1
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
            search_samples = np.arange(0, t + n_search_window, dtype=int)
        elif search_samples[-1] >= N:
            search_samples = np.arange(t - n_search_window, N, dtype=int)

        search_signal = signal[search_samples]
        adjusted_t = search_samples[np.argmin(search_signal)]
        adjusted_troughs.append(adjusted_t)

    adjusted_peaks = []
    for p in peaks:

        search_samples = np.arange(p - n_search_window, p + n_search_window,
                                   dtype=int)

        # make sure that the search window doesn't exceed the boundaries of the
        # trial
        if search_samples[0] <= 0:
            search_samples = np.arange(0, p + n_search_window, dtype=int)
        elif search_samples[-1] >= N:
            search_samples = np.arange(p - n_search_window, N, dtype=int)

        search_signal = signal[search_samples]
        adjusted_p = search_samples[np.argmax(search_signal)]
        adjusted_peaks.append(adjusted_p)

    # prepare data for handling in biopeaks gui
    returnarray = np.concatenate((adjusted_peaks,
                                  adjusted_troughs)).astype(int)
    returnarray.sort(kind='mergesort')
    

    return returnarray


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
    period[0] = np.mean(period)
    periodintp = interp_stats(peaks, period, signal.size)
    rateintp = 60 / periodintp
    
    return periodintp, rateintp, tidalampintp
