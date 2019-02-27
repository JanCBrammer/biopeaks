# -*- coding: utf-8 -*-
"""
Created on Wed Dec  5 17:33:13 2018

@author: John Doe
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch, find_peaks, argrelextrema, medfilt
from scipy.interpolate import interp1d
from filters import butter_lowpass_filter, butter_bandpass_filter


def extrema_signal(signal, sfreq):
    

    N = np.size(signal)
    # get an initial estimate of dominant breathing rate and corresponding IBI
    # assume rate ranging from 10 to 30 breaths per minute
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

    filt = butter_lowpass_filter(signal, 2 * freq_est, sfreq)
    
    # identify preliminary local extrema
    locmax = argrelextrema(filt, np.greater)[0]
    locmin = argrelextrema(filt, np.less)[0]
    extrema = np.sort((np.append(locmax, locmin)))
    
    
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
    # i.e. cases where the alternation of peaks and troughs is broken;
    # for each local extreme of kind i, compute difference to
    # the next following local extreme of the kind i and of the kind j,
    # if the ii difference is smaller than the ij difference, there are two
    # consecutive local extrema of the kind i
    
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
        if np.where(pt_all_select)[0].size > 0:    # where returns only indices of True elements
            
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
            
            
    
    # refine the position of the peaks and troughs, since they're  often 
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
        
    amp_peaks = signal[adjusted_peaks]
    amp_troughs = signal[adjusted_troughs]

        
#    plt.figure()
#    plt.plot(signal, c='g')
#    plt.plot(filt)
#    plt.scatter(adjusted_peaks, signal[adjusted_peaks], c='m', s=150)
#    plt.scatter(adjusted_troughs, signal[adjusted_troughs], c='g', s=150)

    return adjusted_peaks, adjusted_troughs, amp_peaks, amp_troughs


def extrema_signal_zerocross(signal, sfreq):
    

    N = np.size(signal)
    # get an initial estimate of dominant breathing rate and corresponding IBI
    # assume rate ranging from 10 to 30 breaths per minute
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

    filt = butter_lowpass_filter(signal, 2 * freq_est, sfreq)
    
    locmax = argrelextrema(filt, np.greater)[0]
    locmin = argrelextrema(filt, np.less)[0]
    extrema = np.sort((np.append(locmax, locmin)))
    
    
    # in the following, only consider those extrema that have a minimum
    # vertical difference to their direct neighbor, i.e. define outliers in
    # absolute vertical distance between neighboring peaks
    vertdiff = np.abs(np.diff(filt[extrema]))
    avgvertdiff = np.mean(vertdiff)
    minvert = np.where(vertdiff > avgvertdiff * 0.3)[0]
    extrema = extrema[minvert]
    
    # now, find the baseline by...
    x_interp = extrema[:-1] + np.diff(extrema) / 2
    y_interp = filt[extrema[:-1]] + np.diff(filt[extrema]) / 2
    baseinterp = interp1d(x_interp, y_interp, kind='quadratic', fill_value='extrapolate')
    base = baseinterp(np.linspace(0, N, N))
    filt = filt - base
      
    # now, for each period between zero crossings select the local maximum
    zero_cross = np.where(np.diff(np.signbit(filt)))[0]
    zero_cross = np.concatenate((np.zeros(1),
                                 zero_cross,
                                 np.array([np.size(signal) - 1]))).astype(int) 
    peaks = []
    troughs = []
    for z in range(np.size(zero_cross) - 1):
        
        search_samples = np.arange(zero_cross[z],
                                   zero_cross[z + 1],
                                   dtype=int)
        search_signal = filt[search_samples]
        
        locex = np.argmax(np.abs(search_signal))
    
        if np.sign(search_signal[locex]) == 1:
            peaks.append(search_samples[locex])
        elif np.sign(search_signal[locex]) == -1:
            troughs.append(search_samples[locex])
        
        
    peaks = np.ravel(peaks)
    troughs = np.ravel(troughs)
    
    
    # refine the position of the troughs, since it's often 
    # slightly misplaced (troughs are rather sharp extrema), don't redefine
    # peaks, since those can have rather large plateaus and the peak detection
    # on the filtered data places them in the middle of the plateaus, which
    # makes sense
    
    n_search_window = 0.3 * sfreq    # unilateral extend of search window around preliminary peaks in samples
    
    adjusted_troughs = []
    for t in troughs:
        
        search_samples = np.arange(t - n_search_window,
                                   t + n_search_window,
                                   dtype=int)
        
        # make sure that the search window doesn't exceed the boundaries of the trial
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

        
#    for p in peaks:
#        
#        search_samples = np.arange(p - n_search_window,
#                                   p + n_search_window,
#                                   dtype=int)
#        
#        # make sure that the search window doesn't exceed the boundaries of the trial
#        if search_samples[0] <= 0:
#            search_samples = np.arange(0,
#                                       p + n_search_window,
#                                       dtype=int)
#        elif search_samples[-1] >= N:
#            search_samples = np.arange(p - n_search_window,
#                                       N,
#                                       dtype=int)
#            
#        search_signal = signal[search_samples]
#        adjusted_p = search_samples[np.argmax(search_signal)]
#        adjusted_peaks.append(adjusted_p)


    
    
    plt.figure()
    plt.plot(signal, c='g')
    plt.plot(filt)
#    plt.axhline(y=0, c='r')
#    plt.scatter(x_interp, y_interp)
#    plt.plot(np.linspace(0, N, N), base, c='y')
#    plt.scatter(extrema, filt[extrema])

#    plt.scatter(zero_cross, np.zeros(len(signal))[zero_cross])
    plt.scatter(peaks, signal[peaks], c='m', s=150)
    plt.scatter(adjusted_troughs, signal[adjusted_troughs], c='g', s=150)
    plt.scatter(extrema[minvert], filt[extrema[minvert]], marker='X', c='r', s=200)

#    return adjusted_peaks, adjusted_troughs



    
def breathmetrics(signal, sfreq):
    
    srateAdjust = sfreq / 1000.    # convert to msec
    swSizes = [np.floor(100 * srateAdjust),    # sampling windows in msec
               np.floor(300 * srateAdjust),
               np.floor(700 * srateAdjust),
               np.floor(1000 * srateAdjust),
               np.floor(5000 * srateAdjust)]

    
    # pad end of signal so larger windows can be used
    padInd = int(min(np.size(signal), max(swSizes) * 2))
    #paddedResp = np.append(signal, np.zeros(padInd))
    paddedResp = np.append(signal,
                           np.flip(signal[np.size(signal) - padInd:], axis=0))
    
    # initializing vector to store points where there is a peak or trough
    swPeakVect = np.zeros(len(paddedResp))
    swTroughVect = np.zeros(len(paddedResp))
    
    # peaks and troughs must exceed these values
    peakThreshold = np.mean(signal) + np.std(signal) / 2.
    troughThreshold = np.mean(signal) - np.std(signal) / 2.
    
    # shifting window to be unbiased by starting point
    SHIFTS = np.arange(1, 4)
    nWindows = int(len(swSizes) * len(SHIFTS))
    
    # find extrema in each sliding window, in each shift, and return peaks that
    # are agreed upon by majority windows
    # find extrema in each window of the signal using each window size and offset
    for win in range(len(swSizes)):
    
        sw = swSizes[win]
        # cut off end of signal based on sw size
        nIters  = int(np.floor(len(paddedResp) / sw))
    
        for shift in SHIFTS:
            
            # store maxima and minima of each window
            argmaxVect = np.zeros(nIters)
            argminVect = np.zeros(nIters) 
            
            #shift starting point of sliding window to get unbiased maxes
            windowInit = (sw - np.floor(sw / shift)) 
            # iterate by this window size and find all maxima and minima
            windowIter = int(windowInit)
            
            for i in range(nIters):
                
                thisWindow = paddedResp[windowIter:windowIter + int(sw)]
                
                maxVal, maxInd = max(thisWindow), np.argmax(thisWindow)
                if maxVal > peakThreshold:
                    # index in window + location of window in original resp time
                    argmaxVect[i] = windowIter + maxInd
                
                minVal, minInd = min(thisWindow), np.argmin(thisWindow)
                if minVal < troughThreshold:
                    # index in window + location of window in original resp time
                    argminVect[i] = windowIter + minInd
                    
                windowIter += int(sw)
    						   
            # add 1 to consensus vector
            nonZeroMax = np.nonzero(argmaxVect)[0]
            nonZeroMin = np.nonzero(argminVect)[0]
            swPeakVect[argmaxVect[nonZeroMax].astype(int)] += 1
            swTroughVect[argminVect[nonZeroMin].astype(int)] += 1
    
    
    # find threshold that makes minimal difference in number of extrema found
    # similar idea to knee method of k-means clustering
            
    nPeaksFound = np.zeros(nWindows)
    nTroughsFound = np.zeros(nWindows)
    
    for threshold_ind in range(nWindows):
        nPeaksFound[threshold_ind] = sum(swPeakVect > threshold_ind)
        nTroughsFound[threshold_ind] = sum(swTroughVect > threshold_ind)
    
    bestPeakDiff = np.argmax(np.diff(nPeaksFound))
    bestTroughDiff = np.argmax(np.diff(nTroughsFound))
    
    bestDecisionThreshold = np.floor(np.mean([bestPeakDiff, bestTroughDiff]))
    
    peakInds = np.where(swPeakVect >= bestDecisionThreshold)[0].astype(int)
    troughInds = np.where(swTroughVect >= bestDecisionThreshold)[0].astype(int) 
            
            
    # sometimes there are multiple peaks or troughs in series which shouldn't 
    # be possible. This loop ensures the series alternates peaks and troughs.
    
    # first we must find the first peak
    offByN = True
    tri = 0
    
    while offByN:
        if peakInds[tri] > troughInds[tri]:
            troughInds = troughInds[tri + 1:]
        else:
            offByN = False
    
    correctedPeaks = np.asarray([])
    correctedTroughs = np.asarray([])
    
    pki = 0   # peak ind
    tri = 0    # trough ind
    
    # variable to decide whether to record peak and trough inds
    proceedCheck = True
    
    # find peaks and troughs that alternate
    while (pki < len(peakInds) - 1) and (tri < len(troughInds) - 1):
        
        # time difference between peak and next trough
        peakTroughDiff = troughInds[tri] - peakInds[pki]
        
        # check if two peaks in a row
        peakPeakDiff = peakInds[pki + 1] - peakInds[pki]
        
        if peakPeakDiff < peakTroughDiff:
            # if two peaks in a row, take larger peak
            nxtPk = np.argmax([paddedResp[peakInds[pki]],
                               paddedResp[peakInds[pki + 1]]])
            if nxtPk == 1:
                # forget current peak and select next one
                pki += 1
            else:
                # forget next peak, keep current one
                peakInds = np.setdiff1d(peakInds, peakInds[pki + 1])
            # there still might be another peak to remove so go back and check
            # again
            proceedCheck = False
        
        # if the next extrema is a trough, check for trough series
        if proceedCheck is True:
            
            # check if trough is after this trough
            troughTroughDiff = troughInds[tri + 1] - troughInds[tri]
            troughPeakDiff = peakInds[pki + 1] - troughInds[tri]
            
            if troughTroughDiff < troughPeakDiff:
                # if two troughs in a row, take larger trough
                nxtTr = np.argmin([paddedResp[troughInds[tri]],
                                   paddedResp[troughInds[tri + 1]]]);
                if nxtTr == 1:
                    # take second trough
                    tri += 1
                else:
                    # remove second trough
                    troughInds = np.setdiff1d(troughInds, troughInds[tri + 1])
                # there still might be another trough to remove so go back and 
                # check again
                proceedCheck = False
    
        # if both of the above pass we can save values
        if proceedCheck is True:
            # if peaks aren't ahead of troughs
            if peakTroughDiff > 0:
                correctedPeaks = np.append(correctedPeaks, peakInds[pki])
                correctedTroughs = np.append(correctedTroughs, troughInds[tri])
                
                # step forward
                tri += 1
                pki += 1
            else:
                # peaks got ahead of troughs. This shouldn't ever happen.
                print('Peaks got ahead of troughs. This shouldnt happen.')
                break
        proceedCheck = True
    
    # remove any peaks or troughs in padding
    retainPeaks = correctedPeaks < np.size(signal)
    retainTroughs = correctedTroughs < np.size(signal)
    correctedPeaks = correctedPeaks[retainPeaks]
    correctedTroughs = correctedTroughs[retainTroughs]
        
    return correctedPeaks.astype(int), correctedTroughs.astype(int)