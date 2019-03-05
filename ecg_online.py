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
        filt = butter_bandpass_filter(x, 8, 20, 360, order=3)
        sqrd = filt**2
        
        # filter with moving averages
        ma1 = np.convolve(sqrd, np.ones((w1,))/w1, mode='same')
        ma2 = np.convolve(sqrd, np.ones((w2,))/w2, mode='same')
        
        # calculate threshold for R peaks detection
        z = np.mean(sqrd)
        alpha = ma2 + beta * z 
        amp_thresh = ma2 + alpha
       
#        plt.plot(block_idcs, x, c='b')
#        plt.plot(block_idcs, sqrd)
#        plt.plot(block_idcs, ma1, c='m')
#        plt.plot(block_idcs, ma2, c='g')

        # find QRS complexes
        QRS_idcs = np.where(ma1 > amp_thresh)[0]
        
            
        # find R peaks within QRS complexes
        
            
            
        peaks.append()
        
        block += 1
        
#    plt.scatter(peaks, signal[peaks], c='r')
    return peaks
