# -*- coding: utf-8 -*-
"""
Created on Sat Sep 21 16:13:35 2019

@author: John Doe
"""

#import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
from scipy.signal import medfilt
from scipy.stats import iqr


def threshold_normalization(data, alpha, window_half):
    wh = window_half
    # compute threshold
    th = np.zeros(data.size)
    if data.size <= 2 * wh:
        th[:] = alpha * (iqr(np.abs(data)) / 2)
    else:
        for i in range(data.size):
            if i <= wh:
                th[i] = alpha * (iqr(np.abs(data[:i + wh])) / 2)
            elif np.logical_and(i > wh, i < data.size - wh):
                th[i] = alpha * (iqr(np.abs(data[i - wh:i + wh])) / 2)
            elif i >= (data.size - wh):
                th[i] = alpha * (iqr(np.abs(data[i - wh:])) / 2)
    # normalize data by threshold
    return np.divide(data, th), th

def update_indices(source_idcs, update_idcs, update):
    '''
    for every element s in source_idcs, change every element u in update_idcs
    accoridng to update, if u is larger than s
    '''
    update_idcs_buffer = update_idcs
    for s in source_idcs:
        # for each list, find the indices (of indices) that need to be updated
        updates = [i for i, j in enumerate(update_idcs) if j > s]
#        print('updates: {}'.format(updates))
        for u in updates:
            update_idcs_buffer[u] += update
#        print('update_idcs: {}'.format(update_idcs_buffer))
    return update_idcs_buffer

'''
implementation of Jukka A. Lipponen & Mika P. Tarvainen (2019): A robust
algorithm for heart rate variability time series artefact correction using
novel beat classification, Journal of Medical Engineering & Technology,
DOI: 10.1080/03091902.2019.1640306
'''
def get_rr(peaks):

    # set free parameters
    c1 = 0.13
    c2 = 0.17
    alpha = 5.2
    window_half = 45

    # compute RR series (make sure it has same numer of elements as peaks)
    rr = np.ediff1d(peaks, to_begin=0)

    # compute differences of consecutive RRs
    drrs = np.ediff1d(rr, to_begin=0)
    # normalize by threshold
    drrs, _ = threshold_normalization(drrs, alpha, window_half)

    # cast drrs to two-dimesnional subspace s1
    s12 = np.zeros(drrs.size)
    for d in range(drrs.size):

        if np.logical_and(d > 0, d < drrs.size - 1):
            if drrs[d] > 0:
                s12[d] = np.max([drrs[d - 1], drrs[d + 1]])
            elif drrs[d] < 0:
                s12[d] = np.min([drrs[d - 1], drrs[d + 1]])
        elif d == 0:
            if drrs[d] > 0:
                s12[d] = np.max(drrs[:d + 1])
            elif drrs[d] < 0:
                s12[d] = np.min(drrs[:d + 1])
        elif d == drrs.size:
            if drrs[d] > 0:
                s12[d] = np.max(drrs[d - 1:])
            elif drrs[d] < 0:
                s12[d] = np.min(drrs[d - 1:])

    # cast drrs to two-dimensional subspace s2 (looping over d a second
    # consecutive time is choice to be explicit rather than efficient)
    s22 = np.zeros(drrs.size)
    for d in range(drrs.size):

        if d < drrs.size - 2:
            if drrs[d] > 0:
                s22[d] = np.max([drrs[d + 1], drrs[d + 2]])
            elif drrs[d] < 0:
                s22[d] = np.min([drrs[d + 1], drrs[d + 2]])
        elif d >= drrs.size - 2:
            if drrs[d] > 0:
                s22[d] = np.max(drrs[d:])
            elif drrs[d] < 0:
                s22[d] = np.min(drrs[d:])

    # compute deviation of RRs from median RRs
    medrr = medfilt(rr, 11)
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
            eq3 = np.logical_and(drrs[i] > 1, s22[i] < -1)
            eq4 = np.abs(mrrs[i]) > 3
            eq5 = np.logical_and(drrs[i] < -1, s22[i] > 1)

        if ~np.any([eq3, eq4, eq5]):
            # if none of the three equations is true: normal beat
            continue

        # if any of the three equations is true: check for missing or extra
        # peaks
        eq6 = np.abs(rr[i] / 2 - medrr[i]) < th2[i]
        eq7 = np.abs(rr[i] + rr[i + 1] - medrr[i]) < th2[i]

        if np.any([eq3, eq4]):
            longshort_idcs.append(i)
            if np.abs(drrs[i + 1]) < np.abs(drrs[i + 2]):
                longshort_idcs.append(i + 1)
        if eq5:
            longshort_idcs.append(i)
            if np.abs(drrs[i + 1]) < np.abs(drrs[i + 2]):
                longshort_idcs.append(i + 1)
        if eq6:
            missed_idcs.append(i)
        if eq7:
            extra_idcs.append(i)

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
        rr = np.ediff1d(peaks, to_begin=0)
        # update remaining indices
        missed_idcs = update_indices(extra_idcs, missed_idcs, -1)
        etopic_idcs = update_indices(extra_idcs, etopic_idcs, -1)
        longshort_idcs = update_indices(extra_idcs, longshort_idcs, -1)

    # add missing peaks
    if missed_idcs:
        # calculate the position(s) of new beat(s)
        prev_peaks = peaks[[i - 1 for i in missed_idcs]]
        next_peaks = peaks[[i + 1 for i in missed_idcs]]
        added_peaks = prev_peaks + (next_peaks - prev_peaks) / 2
        # add the new peaks
        peaks = np.insert(peaks, missed_idcs, added_peaks)
        # re-calculate the RR series
        rr = np.ediff1d(peaks, to_begin=0)
        # update remaining indices
        etopic_idcs = update_indices(missed_idcs, etopic_idcs, 1)
        longshort_idcs = update_indices(missed_idcs, longshort_idcs, 1)

    # interpolate etopic as well as long or short peaks (important to do this
    # after peaks are deleted and/or added)
    interp_idcs = np.concatenate((etopic_idcs, longshort_idcs))
    if interp_idcs.size > 0:
        interp_idcs.sort(kind='mergesort')
        # ignore the artifacts during interpolation
        x = np.delete(np.arange(0, rr.size), interp_idcs)
        # interpolate artifacts
        interp_rr = np.interp(interp_idcs, x, rr[x])
        rr[interp_idcs] = interp_rr
#        plt.figure(0)
#        plt.plot(rr)

    return peaks, rr

#path = r'C:\Users\JohnDoe\Desktop\beats.csv'
#peaks = np.ravel(pd.read_csv(path))
#
#correct_rr(peaks)
#
#savearray = pd.DataFrame(peaks)
#savearray.to_csv(r'C:\Users\JohnDoe\Desktop\beats_corrected.csv', index=False, header=['peaks'])
