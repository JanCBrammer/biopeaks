# -*- coding: utf-8 -*-
"""
Created on Fri Jan 18 11:01:04 2019

@author: John Doe
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from filters import butter_highpass_filter

def moving_average(signal, window_size):
    
    return np.convolve(signal, np.ones((window_size,)) / window_size,
                       mode='same')
    
def peaks_ecg(signal, sfreq, enable_plot=False):
    
    filt = butter_highpass_filter(signal, .5, sfreq)
    grad = np.gradient(filt)
    absgrad = np.abs(grad)
    smoothgrad = moving_average(absgrad, int(np.rint(0.125 * sfreq)))
    normgrad = normalize(smoothgrad.reshape(-1, 1), axis=0)
    
    # use clustering to identify QRS complexes (based on gradient only)
    clustering = KMeans(n_clusters=2, random_state=42)
    clustering.fit(normgrad)
    labels = clustering.labels_
    
    # identify cluster with fewer instances (since this corresponds to QRS)
    label_counts = np.unique(labels, return_counts=True)[1]
    qrs_label = np.argmin(label_counts)
    qrs = labels == qrs_label
    
    # identify start and end of QRS
    beg_qrs = np.where(np.logical_and(np.logical_not(qrs[0:-1]), qrs[1:]))[0]
    end_qrs = np.where(np.logical_and(qrs[0:-1], np.logical_not(qrs[1:])))[0]
    # throw out QRS-ends that precede first QRS-start
    end_qrs = end_qrs[end_qrs > beg_qrs[0]]
    
    # identify R-peaks within QRS (ignore QRS that are too short)
    num_qrs = min(beg_qrs.size, end_qrs.size)
    min_len = np.mean(end_qrs[:num_qrs] - beg_qrs[:num_qrs]) * 0.4
    peaks = []
    
    for i in range(num_qrs):
        
        beg = beg_qrs[i]
        end = end_qrs[i]
                
        if (end - beg) > min_len:
            
            peak = beg + np.argmax(np.square(filt[beg:end]))
            peaks.append(peak)
    

    # prepare data for handling in biopeaks gui (must be ndarray to allow
    # homogeneous handling with respiratory data)
    returnarray = np.ndarray((np.size(peaks), 1))
    returnarray[:, 0] = peaks
    returnarray = returnarray.astype(int)

    return returnarray
        