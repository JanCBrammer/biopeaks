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

for record in records[:1]:

    data = wfdb.rdrecord(record, pb_dir='bidmc')
    annotation = wfdb.rdann(record, pb_dir='bidmc', extension='breath')

    sfreq = data.fs
    resp_chan = data.sig_name.index('RESP,')
    resp = data.p_signal[:, resp_chan]
    annotators = annotation.aux_note
    # get the indices of each annotator's peaks (i gives index, j gives string)
    annotator1 = [i for i, j in enumerate(annotators) if j == 'ann1']
    annotator2 = [i for i, j in enumerate(annotators) if j == 'ann2']
    manupeaks1 = annotation.sample[annotator1]
    manupeaks2 = annotation.sample[annotator2]
    algopeaks, _, _, _ = extrema_signal(resp, sfreq)
    
    # perform validation against each annotator seperately
    # an algorythmically annotated peaks is scored as true positives if it is
    # within 200ms of a manually annotated peak (Daluwatte et al. 2015)
    
    for p in algopeaks:
        
    # true positives: all peaks that are in both, algo and manu
    # false positives: all peaks that are in algo but not in manu
    # false negatives: all peaks that are in manu but not in algo
    
    
    
    
#    plt.figure()
#    plt.plot(resp)
#    plt.scatter(manupeaks, resp[manupeaks], c='r')
#    plt.scatter(algopeaks, resp[algopeaks], c='r', marker='X')
    
    
    # acceptance window: if an algorithmically annotated peak falls within
    # t msec of any of the two manually annotated peaks, it is scored as 
    # true positive, t is the average disagreement between both manual
    # annotators
    
    # calculate two metrics for evaluation (according to AAMI guidelines):
    # 1. sensitivity: how many of the manually annotated peaks does the 
    # algorithm annotate as peaks (TP / TP + FN)?
    # 2. precision: out of all peaks that are algorithmically annotated as 
    # peaks (TP + FP), how many are correct (TP)?
    

