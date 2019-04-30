# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np
import matplotlib.pyplot as plt
from filters import butter_lowpass_filter


def extrema_signal(signal, sfreq, enable_plot=True):
    '''
    the goal is to provide real-time estimates of a) breathing rate, and b)
    the current phase of breathing (inspiration, expiration); a will be
    estimated based on negative zero-crossings of the signals gradient (i.e.,
    one breathing cycle is defined as peak-to-peak difference, since peaks are
    more sharply defined with the Bitalino belt []); b) is simply the gradient
    of the signal at any time;
    free parameters: lrate, filterorder, filterboundary, weight gradthreshold,
    weight horzdiff
    
    '''
    

    if enable_plot is True:
        plt.figure()
    
    # enforce numpy and vector-form
    signal = np.ravel(signal)

    # set free parameters
    window_size = np.ceil(3 * sfreq)
    # amount of samples to shift the window on each iteration
    stride = np.ceil(1 * sfreq)
    
    # initiate stuff
    block = 0
    last_extreme = 0
    gradthresh = 0
    lrate = 0.1

    while block * stride + window_size <= len(signal):
        block_idcs = np.arange(block * stride, block * stride + window_size, 
                                  dtype = int)
        
        x = signal[block_idcs]
        # filter out fluctuations that occur faster than 0.5 Hz (breathing
        # rate faster than 30), this implicitly ensures a minimum horizontal
        # distance between peaks, no need to apply an additional threshold in
        # time
        x_filt = butter_lowpass_filter(x, 0.5, sfreq, order=2)
        grad = np.gradient(x_filt)
        
        if enable_plot is True:
            plt.plot(block_idcs, grad)
            plt.plot(block_idcs, x_filt, c='g')
            plt.plot(block_idcs, x, c='r')
            plt.axhline(y = 0)
        
        # get negative zero crossings
        extrema = neg_crossings(grad)
                    
        if extrema.size > 0 and enable_plot is True:
            extreme = extrema[-1]
            plt.scatter(block_idcs[extreme], x[extreme], c='y',
                        marker='P', s=200)
            horzdiff = block_idcs[extreme] - last_extreme
            # get average gradient in 200msec preceding each negative zero
            # crossing
            extend = int(np.ceil(0.2 * sfreq))
            if grad[extreme - extend:extreme].size > 0:
                avggrad = np.average(grad[extreme - extend:extreme])
            
                # if the current temporal difference exceeds a second, consider
                # the current zero crossing a valid extreme; also the average 
                # gradient preceding the extreme must exceeed a threshold
                if (horzdiff > 1 * sfreq) and (avggrad > 0.3 * gradthresh):
                    plt.scatter(block_idcs[extreme], x[extreme], c='m',
                                marker='X', s=200)
                    # update parameter
                    gradthresh = (1 - lrate) * gradthresh + lrate * avggrad
                    print(gradthresh)

            last_extreme = block_idcs[extreme]

        block += 1

def neg_crossings(signal):
        pos = signal > 0
        return (pos[:-1] & ~pos[1:]).nonzero()[0]