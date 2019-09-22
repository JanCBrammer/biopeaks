# -*- coding: utf-8 -*-
"""
Created on Sat Sep 21 16:13:35 2019

@author: John Doe
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import medfilt
from scipy.stats import iqr

'''
implementation of Jukka A. Lipponen & Mika P. Tarvainen (2019): A robust
algorithm for heart rate variability time series artefact correction using
novel beat classification, Journal of Medical Engineering & Technology,
DOI: 10.1080/03091902.2019.1640306
'''

# set free parameters
c1 = 0.13
c2 = 0.17
alpha = 5.2
window_half = 45

def threshold_normalization(data, alpha=alpha, window_half=window_half):
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

path = r'C:\Users\JohnDoe\Desktop\beats.csv'

# load beats
beats = np.ravel(pd.read_csv(path))

# compute RR series in msec (make sure it has same numer of elements as beats)
rr = np.ediff1d(beats, to_begin=0) / 1000

# compute differences of consecutive RRs in msec
drrs = np.ediff1d(rr, to_begin=0)
# normalize by threshold
drrs = threshold_normalization(drrs)

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
     
# cast drrs to two-dimensional subspace s2 (looping over d twice is conscious
# choice to be explicit rather than efficient)
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
mrrs = rr - medfilt(rr, 11)
mrrs[mrrs < 0] = mrrs[mrrs < 0] * 2
# normalize by threshold
mrrs, th2 = threshold_normalization(mrrs)

# decision algorithm

for i in range(beats.size - 2):
    
    # check for etopic beats
    if np.abs(drrs[i]) <= 1:
        continue
    
    eq1 = np.logical_and(drrs[i] > 1, s12[i] < (-c1 * drrs[i] + c2))
    eq2 = np.logical_and(drrs[i] < -1, s12[i] > (-c1 * drrs[i] - c2))
    
    if np.any(eq1, eq2):
        # if any of the two equations is true 
        # TODO: correct etopic beat
        continue
    else:
        # if none of the two equations is true
        state = 'foo'
        
    if state != 'foo':
        continue
    
    if np.logical_or(np.abs(drrs[i]) > 1, np.abs(mrrs[i]) > 3):
        eq3 = (np.sign(drrs[i]) * drrs[i + 1]) < -1
        eq4 = np.abs(mrrs[i]) > 3
        eq5 = (np.sign(drrs[i]) * drrs[i + 2]) < -1
        
    if np.any(eq3, eq4, eq5):
        state = 'bar'
    else:
        # normal beat
        continue
    
    if state != 'bar':
        continue
    
    eq6 = np.abs(rr[i] / 2 - mrrs[i]) < th2[i]
    eq7 = np.abs(rr[i] + rr[i + 1] - mrrs[i]) < th2[i]
    
    if eq6:
        # TODO: correct missed beat
        continue
    if eq7:
        # TODO: correct extra beat
        continue
    if np.logical_or(eq3, eq4):
        # TODO: correct long/short
        continue
    if eq5:
        # TODO: correct long/short
        continue
