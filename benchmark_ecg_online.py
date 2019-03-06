# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 14:24:54 2019

@author: John Doe
"""

import wfdb
from wfdb import processing
import matplotlib.pyplot as plt
import numpy as np
from ecg_online import rpeaks

records = wfdb.get_record_list('mitdb', records='all')

sensitivity = []
precision = []

for record in records[:1]:

    print 'processing record ' + record

    data = wfdb.rdrecord(record, pb_dir='mitdb')
    annotation = wfdb.rdann(record, pb_dir='mitdb', extension='atr')

    sfreq = data.fs
    ecg = data.p_signal[:, 0]

    manupeaks = annotation.sample
    algopeaks = rpeaks(ecg, sfreq)
    
    comparitor = processing.compare_annotations(manupeaks, algopeaks, 5)
    tp = comparitor.tp
    fp = comparitor.fp
    fn = comparitor.fn

#    plt.figure()
#    plt.plot(ecg)
#    plt.scatter(manupeaks, ecg[manupeaks], c='m')
#    plt.scatter(algopeaks, ecg[algopeaks], c='g', marker='X', s=150)


    sensitivity.append(float(tp) / (tp + fn))
    precision.append(float(tp) / (tp + fp))
    print sensitivity[-1], precision[-1]

print np.mean(sensitivity), np.mean(precision)
