# -*- coding: utf-8 -*-
"""
Created on Tue Mar 5 10:14:36 2019

@author: U117148
"""

import numpy as np
from filters import butter_bandpass_filter
import matplotlib.pyplot as plt

def rpeaks(signal, sfreq):

#    plt.figure()
    
    # enforce numpy and vector-form
    signal = np.ravel(signal)

    # set free parameters
    window_size = np.ceil(3 * sfreq)
    window_overlap = np.ceil(1 * sfreq)
    # kernel lengths for moving averages
    w1 = int(np.ceil(0.096 * sfreq))
    w2 = int(np.ceil(0.61 * sfreq))
    # amount of samples to shift the window on each iteration
    stride = np.int(window_size - window_overlap)
    # threshold parameter
    beta = 0.8
    
    # initiate stuff
    block = 0
    peaks = []
   
    while block * stride + window_size <= len(signal):
        block_idcs = np.arange(block * stride, block * stride + window_size, 
                                  dtype = int)
        # amplify QRS complexes
        x = signal[block_idcs]
        filt = butter_bandpass_filter(x, 8, 20, 360, order=2)
        sqrd = filt**2
        
        # filter with moving averages
        ma1 = moving_average(sqrd, w1)
        ma2 = moving_average(sqrd, w2)
        
        # calculate threshold for R peaks detection
        z = np.mean(sqrd)
        alpha = ma2 + beta * z 
        amp_thresh = ma2 + alpha
               
#        plt.plot(block_idcs, x, c='b')
#        plt.plot(block_idcs, sqrd)
#        plt.plot(block_idcs, ma1, c='m')
#        plt.plot(block_idcs, amp_thresh, c='g')

        # find QRS complexes
        QRS_idcs = np.where(ma1[:amp_thresh.size] > amp_thresh)[0]
        QRS_edges = np.where(np.diff(QRS_idcs) > 1)[0]
        # add start of first QRS and end of last QRS complex
        QRS_edges = np.concatenate(([0],
                                    QRS_edges + 1,
                                    [QRS_idcs.size-1]))
        
        if QRS_edges.size > 0:
            # for each QRS...
            for i in zip(QRS_edges[0:], QRS_edges[1:]):
                beg_QRS = QRS_idcs[i[0]]
                end_QRS = QRS_idcs[i[1]-1]
                
                # ... check if the QRS complex has the minimally required
                # duration...
                if (end_QRS - beg_QRS) >= w1:
                    
#                    plt.axvspan(block_idcs[beg_QRS], block_idcs[end_QRS],
#                                alpha=0.25)

                    #... and find R peaks within QRS complexes
                    peak = np.argmax(x[beg_QRS:end_QRS])
                    peaks.append(block_idcs[beg_QRS:end_QRS][peak])
              
            
        block += 1
    
    peaks = np.unique(peaks)
#    plt.scatter(peaks, signal[peaks], c='r')
    return peaks


def moving_average(signal, window_size):
    
    cumsum = np.cumsum(np.insert(signal, 0, 0)) 
    return (cumsum[window_size:] - cumsum[:-window_size]) / float(window_size)
