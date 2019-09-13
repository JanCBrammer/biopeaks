# -*- coding: utf-8 -*-
"""
Created on Fri Jan 18 11:01:04 2019

@author: John Doe
"""

import numpy as np
import matplotlib.pyplot as plt
from filters import butter_highpass_filter
from scipy.signal import find_peaks

def moving_average(signal, window_size):
    
    return np.convolve(signal, np.ones((window_size,)) / window_size,
                       mode='same')


def peaks_ecg(signal, sfreq, enable_plot=False):
    
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
    peaks = []
    
    for i in range(num_qrs):
        
        beg = beg_qrs[i]
        end = end_qrs[i]
        len_qrs = end - beg
                
        if len_qrs > min_len:
            
            # visualize QRS intervals
            if enable_plot is True:
                ax2.axvspan(beg, end, facecolor='m', alpha=0.5)
            
            data = filt[beg:end]
            locmax, _ = find_peaks(data)
            locmin, _ = find_peaks(data * -1)
            extrema = np.concatenate((locmax, locmin))
            extrema.sort(kind='mergesort')
            
            if extrema.size > 0:
                peakidx = np.argmax(np.square(data[extrema]))
                peak = beg + extrema[peakidx]
                peaks.append(peak)
            
    if enable_plot is True:
        ax1.scatter(np.arange(filt.size)[peaks], filt[peaks], c='r')

    # prepare data for handling in biopeaks gui (must be ndarray to allow
    # homogeneous handling with respiratory data)
    returnarray = np.ndarray((np.size(peaks), 1))
    returnarray[:, 0] = peaks
    returnarray = returnarray.astype(int)

    return returnarray

