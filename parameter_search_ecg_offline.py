# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 14:24:54 2019

@author: John Doe
"""

import wfdb
from wfdb.processing import compare_annotations
import glob
import matplotlib.pyplot as plt
import numpy as np
from ecg_offline1 import peaks_signal

records = glob.glob(r'C:\Users\John Doe\surfdrive\Beta\Data\ECG\mitdb\*.dat')
annotations = glob.glob(r'C:\Users\John Doe\surfdrive\Beta\Data\ECG\mitdb'
                        '\*.atr')

sampto = 'end'
sampfrom = 0

weights = [0.5, 0.4, 0.3, 0.2]
kernels = [0.05, 0.075, 0.1, 0.125, 1.5]

means = []

for weight in weights:
    
    for kernel in kernels:
        
        sensitivity = []
        precision = []
                
        for subject in zip(records, annotations):
            
            data = wfdb.rdrecord(subject[0][:-4], sampto=sampto)
            annotation = wfdb.rdann(subject[1][:-4], 'atr',
                                    sampfrom=sampfrom,
                                    sampto=sampto)
        
            sfreq = data.fs
            ecg = data.p_signal[:, 0]
        
            manupeaks = annotation.sample
            algopeaks = peaks_signal(ecg,
                                     sfreq,
                                     kernel,
                                     weight)
                
            # tolerance for match between algorithmic and manual annotation (in sec)
            tolerance = 0.05    
            comparitor = compare_annotations(manupeaks, algopeaks,
                                             int(tolerance * sfreq))
            tp = comparitor.tp
            fp = comparitor.fp
            fn = comparitor.fn
        
        #    plt.figure()
        #    plt.plot(ecg)
        #    plt.scatter(training_peaks, ecg[training_peaks], c='0')
        #    plt.scatter(manupeaks, ecg[manupeaks], c='m')
        #    plt.scatter(algopeaks, ecg[algopeaks], c='g', marker='X', s=150)
        
            sensitivity.append(float(tp) / (tp + fn))
            precision.append(float(tp) / (tp + fp))
            
        means.append((np.mean(sensitivity), np.mean(precision)))
            
        print 'weight =', weight, 'kernel =', kernel, (np.mean(sensitivity), np.mean(precision))