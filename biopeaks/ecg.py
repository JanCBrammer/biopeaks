# -*- coding: utf-8 -*-
"""
Created on Fri Jan 18 11:01:04 2019

@author: John Doe
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, medfilt
from .filters import butter_highpass_filter
from .analysis_utils import (moving_average, threshold_normalization,
                             interp_stats, update_indices)


def ecg_peaks(signal, sfreq, enable_plot=False):
    """ 
    enable_plot is for debugging purposes when the function is called in
    isolation
    """

    # initiate plot
    if enable_plot is True:
        plt.figure()
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212, sharex=ax1)
        
    filt = butter_highpass_filter(signal, .5, sfreq)
    grad = np.gradient(filt)
    absgrad = np.abs(grad)
    smoothgrad = moving_average(absgrad, int(np.rint(0.125 * sfreq)))
    avggrad = moving_average(smoothgrad, int(np.rint(1 * sfreq)))
    gradthreshold = 1.5 * avggrad
    mindelay = int(np.rint(sfreq * 0.3))

    # visualize thresholding
    if enable_plot is True:
        ax1.plot(filt)
        ax2.plot(smoothgrad)
        ax2.plot(gradthreshold)
        
    # identify start and end of QRS
    qrs = smoothgrad > gradthreshold
    beg_qrs = np.where(np.logical_and(np.logical_not(qrs[0:-1]), qrs[1:]))[0]
    end_qrs = np.where(np.logical_and(qrs[0:-1], np.logical_not(qrs[1:])))[0]
    # throw out QRS-ends that precede first QRS-start
    end_qrs = end_qrs[end_qrs > beg_qrs[0]]
    
    # identify R-peaks within QRS (ignore QRS that are too short
    num_qrs = min(beg_qrs.size, end_qrs.size)
    min_len = np.mean(end_qrs[:num_qrs] - beg_qrs[:num_qrs]) * 0.4
    peaks = [0]
    
    for i in range(num_qrs):
        
        beg = beg_qrs[i]
        end = end_qrs[i]
        len_qrs = end - beg
                
        if len_qrs < min_len:
            continue
            
        # visualize QRS intervals
        if enable_plot is True:
            ax2.axvspan(beg, end, facecolor='m', alpha=0.5)
        
        # find local maxima and their prominence within QRS
        data = signal[beg:end]
        locmax, props = find_peaks(data, prominence=(None, None))
        
        if locmax.size > 0:
            # identify most prominent local maximum
            peak = beg + locmax[np.argmax(props["prominences"])]
            # enforce minimum delay between peaks
            if peak - peaks[-1] > mindelay:
                peaks.append(peak)
 
    peaks.pop(0)
            
    if enable_plot is True:
        ax1.scatter(np.arange(filt.size)[peaks], filt[peaks], c='r')

    return np.asarray(peaks).astype(int)


def ecg_period(peaks, sfreq, nsamp):
    """
    implementation of Jukka A. Lipponen & Mika P. Tarvainen (2019): A robust
    algorithm for heart rate variability time series artefact correction using
    novel beat classification, Journal of Medical Engineering & Technology,
    DOI: 10.1080/03091902.2019.1640306
    """
    peaks = np.ravel(peaks)

    # set free parameters
    c1 = 0.13
    c2 = 0.17
    alpha = 5.2
    window_half = 45
    medfilt_order = 11

    # compute period series (make sure it has same numer of elements as peaks);
    # peaks are in samples, convert to seconds
    rr = np.ediff1d(peaks, to_begin=0) / sfreq
    # for subsequent analysis it is important that the first element has
    # a value in a realistic range (e.g., for median filtering)
    rr[0] = np.mean(rr)

    # compute differences of consecutive periods
    drrs = np.ediff1d(rr, to_begin=0)
    drrs[0] = np.mean(drrs)
    # normalize by threshold
    drrs, _ = threshold_normalization(drrs, alpha, window_half)

    # pad drrs with one element
    padding = 2
    drrs_pad = np.pad(drrs, padding, 'reflect')
    # cast drrs to two-dimesnional subspace s1
    s12 = np.zeros(drrs.size)
    for d in np.arange(padding, padding + drrs.size):

        if drrs_pad[d] > 0:
            s12[d - padding] = np.max([drrs_pad[d - 1], drrs_pad[d + 1]])
        elif drrs_pad[d] < 0:
            s12[d - padding] = np.min([drrs_pad[d - 1], drrs_pad[d + 1]])

    # cast drrs to two-dimensional subspace s2 (looping over d a second
    # consecutive time is choice to be explicit rather than efficient)
    s22 = np.zeros(drrs.size)
    for d in np.arange(padding, padding + drrs.size):

        if drrs_pad[d] > 0:
            s22[d - padding] = np.max([drrs_pad[d + 1], drrs_pad[d + 2]])
        elif drrs_pad[d] < 0:
            s22[d - padding] = np.min([drrs_pad[d + 1], drrs_pad[d + 2]])


    # compute deviation of RRs from median RRs
    # pad RR series before filtering
    padding = medfilt_order // 2
    rr_pad = np.pad(rr, padding, 'reflect')
    medrr = medfilt(rr_pad, medfilt_order)
    # remove padding
    medrr = medrr[padding:padding + rr.size]
    mrrs = rr - medrr
    mrrs[mrrs < 0] = mrrs[mrrs < 0] * 2
    # normalize by threshold
    mrrs, th2 = threshold_normalization(mrrs, alpha, window_half)


    # artifact identification
    #########################
    # keep track of indices that need to be interpolated, removed, or added
    extra_idcs = []
    missed_idcs = []
    etopic_idcs = []
    longshort_idcs = []

    for i in range(peaks.size - 2):

        # check for etopic peaks
        if np.abs(drrs[i]) <= 1:
            continue

        # based on figure 2a
        eq1 = np.logical_and(drrs[i] > 1, s12[i] < (-c1 * drrs[i] - c2))
        eq2 = np.logical_and(drrs[i] < -1, s12[i] > (-c1 * drrs[i] + c2))

        if np.any([eq1, eq2]):
            # if any of the two equations is true
            etopic_idcs.append(i)
            continue

        # if none of the two equations is true
        # based on figure 2b
        if np.logical_or(np.abs(drrs[i]) > 1, np.abs(mrrs[i]) > 3):
            # long
            eq3 = np.logical_and(drrs[i] > 1, s22[i] < -1)
            eq4 = np.abs(mrrs[i]) > 3
            # short
            eq5 = np.logical_and(drrs[i] < -1, s22[i] > 1)

        if ~np.any([eq3, eq4, eq5]):
            # if none of the three equations is true: normal beat
            continue

        # if any of the three equations is true: check for missing or extra
        # peaks
        # missing
        eq6 = np.abs(rr[i] / 2 - medrr[i]) < th2[i]
        # extra
        eq7 = np.abs(rr[i] + rr[i + 1] - medrr[i]) < th2[i]

        # check if short or extra
        if np.any([eq3, eq4]):
            if eq7:
                extra_idcs.append(i)
            else:
                longshort_idcs.append(i)
                if np.abs(drrs[i + 1]) < np.abs(drrs[i + 2]):
                    longshort_idcs.append(i + 1)
        # check if long or missing
        if eq5:
            if eq6:
                missed_idcs.append(i)
            else:
                longshort_idcs.append(i)
                if np.abs(drrs[i + 1]) < np.abs(drrs[i + 2]):
                    longshort_idcs.append(i + 1)

#    # visualize artifact type indices
#    plt.figure(0)
#    plt.plot(rr)
#    plt.scatter(longshort_idcs, rr[longshort_idcs], marker='v', c='m', s=100,
#                zorder=3)
#    plt.scatter(etopic_idcs, rr[etopic_idcs], marker='v', c='g', s=100,
#                zorder=3)
#    plt.scatter(extra_idcs, rr[extra_idcs], marker='v', c='y', s=100,
#                zorder=3)
#    plt.scatter(missed_idcs, rr[missed_idcs], marker='v', c='r', s=100,
#                zorder=3)
#
#    # visualize first threshold
#    plt.figure(1)
#    plt.plot(np.abs(drrs))
#    plt.axhline(1, c='r')
#
#    # visualize decision boundaries
#    plt.figure(2)
#    plt.scatter(drrs, s12)
#    x = np.linspace(min(drrs), max(drrs), 1000)
#    plt.plot(x, -c1 * x - c2)
#    plt.plot(x, -c1 * x + c2)
#    plt.vlines([-1, 1], ymin=min(s12), ymax=max(s12))
#
#    plt.figure(3)
#    plt.scatter(drrs, s22)
#    plt.vlines([-1, 1], ymin=min(s22), ymax=max(s22))
#    plt.hlines([-1, 1], xmin=min(drrs), xmax=max(drrs))

    # artifact correction
    #####################
    # the integrity of indices must be maintained if peaks are inserted or
    # deleted: for each deleted beat, decrease indices following that beat in
    # all other index lists by 1; likewise, for each added beat, increment the
    # indices following that beat in all other lists by 1

    # delete extra peaks
    if extra_idcs:
        # delete the extra peaks
        peaks = np.delete(peaks, extra_idcs)
        # re-calculate the RR series
        rr = np.ediff1d(peaks, to_begin=0) / sfreq
#        print('extra: {}'.format(peaks[extra_idcs]))
        # update remaining indices
        missed_idcs = update_indices(extra_idcs, missed_idcs, -1)
        etopic_idcs = update_indices(extra_idcs, etopic_idcs, -1)
        longshort_idcs = update_indices(extra_idcs, longshort_idcs, -1)

    # add missing peaks
    if missed_idcs:
        # calculate the position(s) of new beat(s)
        prev_peaks = peaks[[i - 1 for i in missed_idcs]]
        next_peaks = peaks[missed_idcs]
        added_peaks = prev_peaks + (next_peaks - prev_peaks) / 2
        # add the new peaks
        peaks = np.insert(peaks, missed_idcs, added_peaks)
        # re-calculate the RR series
        rr = np.ediff1d(peaks, to_begin=0) / sfreq
#        print('missed: {}'.format(peaks[missed_idcs]))
        # update remaining indices
        etopic_idcs = update_indices(missed_idcs, etopic_idcs, 1)
        longshort_idcs = update_indices(missed_idcs, longshort_idcs, 1)

    # interpolate etopic as well as long or short peaks (important to do this
    # after peaks are deleted and/or added)
    interp_idcs = np.concatenate((etopic_idcs, longshort_idcs)).astype(int)
    if interp_idcs.size > 0:
        interp_idcs.sort(kind='mergesort')
        # ignore the artifacts during interpolation
        x = np.delete(np.arange(0, rr.size), interp_idcs)
        # interpolate artifacts
        interp_artifacts = np.interp(interp_idcs, x, rr[x])
        rr[interp_idcs] = interp_artifacts
#        print('interpolated: {}'.format(peaks[interp_idcs]))
##        plt.figure(0)
##        plt.plot(rr)

    # interpolate rr at the signals sampling rate for plotting; the rate
    # corresponding to the first peak is set to the mean RR
    rr[0] = np.mean(rr)
    periodintp = interp_stats(peaks, rr, nsamp)
    rateintp = 60 / periodintp


    return peaks.astype(int), periodintp, rateintp

#path = r'C:\Users\JohnDoe\Desktop\beats.csv'
#peaks = np.ravel(pd.read_csv(path))
#
#get_rr(peaks, 1000, 100)
#
#savearray = pd.DataFrame(peaks)
#savearray.to_csv(r'C:\Users\JohnDoe\Desktop\beats_corrected.csv', index=False, header=['peaks'])
