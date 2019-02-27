# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 14:24:54 2019

@author: John Doe
"""

import wfdb
import matplotlib.pyplot as plt
import numpy as np
from resp_offline import extrema_signal

records = wfdb.get_record_list('bidmc', records='all')

for record in records[:3]:
    
    data = wfdb.rdrecord(record, pb_dir='bidmc')
    annotation = wfdb.rdann(record, pb_dir='bidmc', extension='breath')
    
    sfreq = data.fs
    resp_chan = data.sig_name.index('RESP,')
    resp = data.p_signal[:, resp_chan]
    peaks = annotation.sample
    mypeaks, mytroughs, _, _ = extrema_signal(resp, sfreq)
    
#    plt.figure()
#    plt.plot(resp)
#    plt.scatter(peaks, resp[peaks], c='r')
#    plt.scatter(mypeaks, resp[mypeaks], c='r', marker='X')
#    plt.scatter(mytroughs, resp[mytroughs], c='r', marker='X')
    
    
    # acceptance window: if an algorithmically annotated peak falls within
    # t msec of any of the two manually annotated peaks, it is scored as 
    # true positive, t is the average disagreement between both manual
    # annotators
    
    # calculate two metrics for evaluation (according to AAMI guidelines):
    # 1. sensitivity: how many of the manually annotated peaks does the 
    # algorithm annotate as peaks (TP / TP + FN)?
    # 2. precision: out of all peaks that are algorithmically annotated as 
    # peaks (TP + FP), how many are correct (TP)?
    

