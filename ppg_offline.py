# -*- coding: utf-8 -*-
"""
Created on Thu Dec 20 11:23:25 2018

@author: U117148
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import argrelmax
from filters import butter_bandpass_filter
from sklearn.cluster import KMeans


def peaks_ppg(signal, sfreq):
    
    signal_filt = butter_bandpass_filter(signal,
                                         .8,
                                         30,
                                         sfreq,
                                         order=3)   
        
    # select only positive peaks
    peaks = argrelmax(signal_filt)[0]
    
    height = signal_filt[peaks]
    
    # to get an initial set of template peaks, cluster peaks by height
    clustering = KMeans(n_clusters=2, random_state=42)
    clustering.fit(height.reshape(-1, 1))
    labels = clustering.labels_
    label_counts = np.unique(labels, return_counts=True)
    
    # selecting the cluster containing the peaks based on height
    medheight = []
    for i in label_counts[0]:
        height_i = height[labels == i]
        medheight_i = np.median(height_i)
        medheight = np.append(medheight, medheight_i)
    peak_label = np.argmax(medheight)
    peak_label_idcs = np.where(labels == peak_label)[0]
    template_peaks = peaks[peak_label_idcs]

    # build a peak template based on the peaks identified by clustering
    extend = int(np.rint(0.25 * sfreq))
    template = np.zeros((template_peaks.size, extend * 2))
    for i in range(template_peaks.size):
        beg = template_peaks[i] - extend
        end = template_peaks[i] + extend
        if (beg > 0) and (end < signal_filt.size):
            template[i, :] = signal_filt[beg:end]
    template = np.mean(template, axis=0)
    
    # compute normalized cross correlation between a window surrounding each
    # peak and the template
    normcrosscorrs = []
    for peak in peaks:
        beg = peak - extend
        end = peak + extend
        if (beg > 0) and (end < signal_filt.size):
            window = signal_filt[beg:end]
            normcrosscorr = (np.dot(template, window) /
                             np.sqrt(np.sum(template**2) * np.sum(window**2)))
            normcrosscorrs.append(normcrosscorr)
        else:
            normcrosscorrs.append(0)
            
    # only retain peaks that are correlated enough with the template
    thresh_peaks = peaks[np.asarray(normcrosscorrs) > .8]
    
    # throw out peaks that follow another peak within 200 msec
    peakdiff = np.diff(thresh_peaks)
    discard_peaks = np.where(peakdiff < 0.2 * sfreq)[0]
    
    final_peaks = np.delete(thresh_peaks, discard_peaks)
    
#    plt.figure()
#    plt.plot(signal_filt)
#    plt.scatter(template_peaks, signal_filt[template_peaks], c='y', marker='X', s=200)
#    plt.scatter(final_peaks, signal_filt[final_peaks], c='g')
#    plt.scatter(thresh_peaks[discard_peaks], signal_filt[thresh_peaks[discard_peaks]], c='r')
    
    # prepare data for handling in biopeaks gui (must be ndarray to allow
    # homogeneous handling with respiratory data)
    returnarray = np.ndarray((np.size(final_peaks), 1))
    returnarray[:, 0] = final_peaks
    returnarray = returnarray.astype(int)

    return returnarray
    
   