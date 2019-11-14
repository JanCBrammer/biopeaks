# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 17:55:48 2019

@author: John Doe
"""

import wfdb
import random
import matplotlib.pyplot as plt
import numpy as np
from wfdb.processing import compare_annotations
from biopeaks.ecg import peaks_ecg
from biopeaks.resp import extrema_resp

'''
What I want to provide here is a way to evaluate the quality of the backend
algorithms as objectively as possible: the extrema detection algorithms for
both modalities (breathing, ecg), are benchmarked against public databases
containing signals and expert annotations on extrema locations;

the function provides the opportunity to visually inspect the signal along
with both kinds of annotations (algorithmic, expert) to clarify potential
discrepancies; setting enable_plot=True results in the generation of a plot per
record

breathing extrema detection is benchmarked on the bidmc dataset (link)

ecg extrema detection is benchmarked on the mitdb (link)

a critical parameter during detector evaluation is tolerance: it is set in the
unit of seconds and describes how much discrepancy is allowed between an
algorithmically identified extreme and an extreme manually identified by an
expert;

for breathing, tolerance is set to 700 msec; this relatively large value was
chosen to account for the clipping that occurs in many of the bidmc recordings;
clipping results in large palteaus that make placement of peaks somewhat
arbitrary; for non-clipped peaks, the agreement of manual and algorithmic
annotation is within a range smaller than 700 msec (enable plotting to confirm)

for ecg, tolerance is set to one tenth of the signal's sampling rate, following
the convention described by (link)

note that the wfdb package fetches the records from a database directly, there
is no need to download the files locally
'''

def benchmark_detector(modality, tolerance, enable_plot=False):

    if modality == 'ecg':
        dataset = 'mitdb'
        detector = peaks_ecg
        channel = 'MLII'
        extension = 'atr'
    elif modality == 'breath':
        dataset = 'bidmc'
        detector = extrema_resp
        channel = 'RESP,'
        extension = 'breath'
        
    # fetch the list of all records
    records = wfdb.get_record_list(dataset, records='all')
      
    sensitivity = []
    precision = []
    print('starting test of {} detector'.format(modality))

    for record in records:
        
        print('processing record {}'.format(record))
        # load data and annotation files from server
        data = wfdb.rdsamp(record, channel_names=[channel], pb_dir=dataset,
                           warn_empty=True)
        annotation = wfdb.rdann(record, pb_dir=dataset, extension=extension)
        sfreq = data[1]['fs']
        signal = np.ravel(data[0])
        if signal.size <= 1:
            print('no signal available for record {}'.format(record))
            continue
        
        # get manually identified extrema
        if modality == 'ecg':
            anno = annotation.sample
        elif modality == 'breath':
            # there are two annotators for the breathing data, select one at
            # random for each record
            random.seed(42)
            annotators = annotation.aux_note
            annotator = random.choice(annotators)
            anno_idcs = [i for i, j in enumerate(annotators) if j == annotator]
            anno = annotation.sample[anno_idcs]
            
        # get algorithmically identified extrema
        algo = detector(signal, sfreq)
        # convert output format of the detector for handling with the wfdb API
        if modality == 'ecg':
            algo = np.ravel(algo)
        elif modality == 'breath':
            algo = np.ravel(algo[:, 0])
            # only select peaks, since there are no trough annotations in the
            # dataset
            if signal[algo[0]] > signal[algo[1]]:
                algo = algo[0:-1:2]
            elif signal[algo[0]] < signal[algo[1]]:
                algo = algo[1::2]
                
        # visualize the algorithmic (green), and manual (magenta) annotations
        if enable_plot is True:
            plt.figure()
            plt.plot(signal)
            plt.scatter(anno, signal[anno], c='m')
            plt.scatter(algo, signal[algo], c='g', marker='X', s=150)
                
        # compare algorithmic and manual annotations
        tolerance_samp = int(np.rint(tolerance * sfreq))
        comparison = compare_annotations(anno, algo, tolerance_samp)
        tp = comparison.tp
        fp = comparison.fp
        fn = comparison.fn
        # calculate two metrics for benchmarking (according to AAMI):
        # 1. sensitivity: how many of the manually annotated peaks does the
        # algorithm annotate as peaks (TP / TP + FN)?
        # 2. precision: out of all peaks that are algorithmically annotated as
        # peaks (TP + FP), how many are correct (TP)?
        sensitivity.append(tp / (tp + fn))
        precision.append(tp / (tp + fp))
        
        print('sensitivity = {}, precision = {}'.format(sensitivity[-1],
              precision[-1]))

    print('mean over all records:\
          sensitivity = {},\
          precision = {}'.format(np.mean(sensitivity), np.mean(precision)))

# run the evaluation for both modalities
benchmark_detector('ecg', tolerance=0.036)
#benchmark_detector('breath', tolerance=0.7)
