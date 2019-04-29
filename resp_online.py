# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np
import matplotlib.pyplot as plt
from filters import butter_lowpass_filter


def extrema_signal(signal, sfreq, enable_plot=True):

    if enable_plot is True:
        plt.figure()
    
    # enforce numpy and vector-form
    signal = np.ravel(signal)

    # set free parameters
    window_size = np.ceil(4 * sfreq)
    # amount of samples to shift the window on each iteration
    stride = np.ceil(1 * sfreq)
    
    # initiate stuff
    block = 0
    last_extreme = np.inf

    while block * stride + window_size <= len(signal):
        block_idcs = np.arange(block * stride, block * stride + window_size, 
                                  dtype = int)
        
        x = signal[block_idcs]
        # filter out fluctuations that occur faster than 0.5 Hz (breathing
        # rate faster than 30)
        x_filt = butter_lowpass_filter(x, 0.5, sfreq, order=2)
        grad = np.gradient(x_filt)
        
        if enable_plot is True:
            plt.plot(block_idcs, grad)
            plt.plot(block_idcs, x_filt, c='g')
            plt.plot(block_idcs, x, c='r')
            plt.axhline(y = 0)
        
        # detect changes in sign in gradient
        extrema = inflection_nonzero(grad)
        
        if extrema.size > 0 and enable_plot is True:
            exdiff = (extrema[-1] - last_extreme) / sfreq
            plt.scatter(block_idcs[extrema[-1]], x[extrema[-1]], c='y',
                        marker='+', s=200)
            if exdiff > 0.2:
                plt.scatter(block_idcs[extrema[-1]], x[extrema[-1]], c='m',
                            marker='x', s=200)
            
            last_extreme = extrema[-1]

        block += 1


def inflection_nonzero(signal):
        pos = signal > 0
        npos = ~pos
        return ((pos[:-1] & npos[1:]) | (npos[:-1] & pos[1:])).nonzero()[0]