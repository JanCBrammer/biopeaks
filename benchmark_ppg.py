# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 14:24:54 2019

@author: John Doe
"""

from wfdb.processing import compare_annotations
from glob import glob
import matplotlib.pyplot as plt
import numpy as np
from ppg_offline import peaks_signal


records = glob(r'C:\Users\u117148\surfdrive\Beta\Data\PPG\signal\*')
annotations = glob(r'C:\Users\u117148\surfdrive\Beta\Data\PPG\annotations\*')
subjects = list(zip(records, annotations))

sfreq = 300

sensitivity = []
precision = []
   
for subject in subjects:
#  
#selection = [1, 7, 9]
#for i in selection:
#    
#    subject = subjects[i]

    print('processing subject {}'.format(subject[0][-4:]))

    data = np.loadtxt(subject[0])
    annotation = np.loadtxt(subject[1])


    #algopeaks = peaks_signal(ecg, sfreq)
    peaks = peaks_signal(data, sfreq)

    # tolerance for match between algorithmic and manual annotation (in sec)
    tolerance = 0.05
    comparitor = compare_annotations(peaks, annotation,
                                     int(np.rint(tolerance * sfreq)))
    tp = comparitor.tp
    fp = comparitor.fp
    fn = comparitor.fn

    sensitivity.append(float(tp) / (tp + fn))
    precision.append(float(tp) / (tp + fp))
    print(sensitivity[-1], precision[-1])

print(np.mean(sensitivity), np.mean(precision))
