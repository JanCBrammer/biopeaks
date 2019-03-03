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
sensitivity1 = []
sensitivity2 = []
precision1 = []
precision2 = []

for record in records:

    print 'processing record ' + record

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

#    plt.figure()
#    plt.plot(resp)
#    plt.scatter(manupeaks1, resp[manupeaks1], c='m')
#    plt.scatter(manupeaks2, resp[manupeaks2], c='b')
#    plt.scatter(algopeaks, resp[algopeaks], c='g', marker='X', s=150)

    # perform benchmarking against each annotator seperately; an
    # algorythmically annotated peaks is scored as true positives if it is
    # within 700 msec of a manually annotated peak, this relatively large
    # window was chosen to account for the clipping that occurs in many of the
    # recordings; clipping results in large palteaus that make placement of
    # peak somewhat arbitrary (algorithm places peak at the edges while manual
    # annotation places peak towards the middle); for non-clipped peaks, the
    # agreement of manual and algorithmic annotation is within a range smaller
    # than 700 msec (enable plotting to confirm)

    # unilateral extend of acceptance margin centered on each algopeak; in sec
    acceptance_margin = 0.7
    
    tp1 = []
    fn1 = []
    # true positives; unique peaks that are in both, algopeaks and manupeaks (
    # within the specified acceptance margin)
    # false negatives: returns unique peaks in manupeaks that are not in
    # true positives
    for manupeak in manupeaks1:

        # get the algorithmically annotated peak that is closest to manupeak...
        mindiff = min(np.abs(algopeaks - manupeak))
        # ... and evaluate if algopeak falls within the acceptance margin
        # around the closest manupeak
        if mindiff <= acceptance_margin * sfreq:
            tp1.append(manupeak)
        elif mindiff > acceptance_margin * sfreq:
            fn1.append(manupeak)

    tp2 = []
    fn2 = []
    # true positives; unique peaks that are in both, algopeaks and manupeaks (
    # within the specified acceptance margin)
    # false negatives: returns unique peaks in manupeaks that are not in
    # true positives
    for manupeak in manupeaks2:

        # get the algorithmically annotated peak that is closest to manupeak...
        mindiff = min(np.abs(algopeaks - manupeak))
        # ... and evaluate if algopeak falls within the acceptance margin
        # around the closest manupeak
        if mindiff <= acceptance_margin * sfreq:
            tp2.append(manupeak)
        elif mindiff > acceptance_margin * sfreq:
            fn2.append(manupeak)

    fp1 = []
    fp2 = []
    # true positives; unique peaks that are in both, algopeaks and manupeaks (
    # wuthih the specified acceptance margin)
    for algopeak in algopeaks:

        # get the manually annotated peak that is closest to algopeak...
        mindiff1 = min(np.abs(manupeaks1 - algopeak))
        mindiff2 = min(np.abs(manupeaks2 - algopeak))
        # ... and evaluate if algopeak falls within the acceptance margin
        # around the closest manupeak
        if mindiff1 > acceptance_margin * sfreq:
            fp1.append(algopeak)
        if mindiff2 > acceptance_margin * sfreq:
            fp2.append(algopeak)

    # calculate two metrics for benchmarking (according to AAMI guidelines):
    # 1. sensitivity: how many of the manually annotated peaks does the
    # algorithm annotate as peaks (TP / TP + FN)?
    # 2. precision: out of all peaks that are algorithmically annotated as
    # peaks (TP + FP), how many are correct (TP)?
    sensitivity1.append(float(len(tp1)) / (len(tp1) + len(fn1)))
    precision1.append(float(len(tp1)) / (len(tp1) + len(fp1)))
    sensitivity2.append(float(len(tp2)) / (len(tp2) + len(fn2)))
    precision2.append(float(len(tp2)) / (len(tp2) + len(fp2)))

print np.mean(sensitivity1), np.mean(precision1)
print np.mean(sensitivity2), np.mean(precision2)
