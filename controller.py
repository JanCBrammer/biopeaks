# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 18:47:13 2019

@author: John Doe
"""

import os
import json
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from ecg_offline import peaks_ecg
from ppg_offline import peaks_ppg
from resp_offline import extrema_resp
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt5.QtWidgets import QFileDialog

## threading is implemented according to https://pythonguis.com/courses/
## multithreading-pyqt-applications-qthreadpool/complete-example/

class Worker(QRunnable):
    
    def __init__(self, fn):
        super(Worker, self).__init__()

        self.fn = fn
        
    def run(self):
        self.fn()
        
        
class Controller(QObject):
    
    def __init__(self, model):
        super().__init__()

        self._model = model
        self.threadpool = QThreadPool()

        ##############
        # attributes #
        ##############
        self.fnames = None
        self.numfiles = None
        self.batchmode = None
       
    ###########
    # methods #
    ###########
    def open_signal(self):
        self.fnames = QFileDialog.getOpenFileNames(None, 'Choose your data',
                                                   '\home')[0]
        print(self.fnames)
        if self.fnames:
            self.numfiles = np.size(self.fnames)
#            if self.batchmode == 'multiple files':
#                self.savedir = QFileDialog.getExistingDirectory(None,
#                                                                'Choose a '
#                                                                'directory '
#                                                                'for saving '
#                                                                'the peaks',
#                                                                 '\home')
            batch = self.batch_constructor
            self.batch_executer(batch)
    
    def open_peaks(self):
        pass
    
    def change_modality(self, value):
        self._model.modality = value
        print(value)
        
    def change_channel(self, value):
        self._model.channel = value
        print(value)
        
    def change_batchmode(self, value):
        self.batchmode = value
        print(value)
        
    def change_editable(self, value):
        if value == 2:
            self._model.editable = True
        elif value == 0:
            self._model.editable = False
        print(value)
        
    def read_signal(self, path):
        _, self.file_extension = os.path.splitext(path)
        if self.file_extension == '.txt':
            # open file and check if it's encoded in OpenSignals format
            with open(path, 'r') as f:
                # read first line and check if user provided an OpenSignals
                # file
                if 'OpenSignals' in f.readline():
                    if self._model.channel == 0:
                        self._model.channel = self._model.modality
                    # read second line and convert json header to dict (only
                    # selects first device / MAC adress)
                    metadata = json.loads(f.readline()[1:])
                    metadata = metadata[list(metadata.keys())[0]]
                    # parse header and extract relevant metadata
                    sfreq = metadata['sampling rate']
                    sensors = metadata['sensor']
                    channels = metadata['label']
                    # select channel and load data
                    if type(self._model.channel) is str:
                        # find the index of the sensor that corresponds to the
                        # selected modality; it doesn't matter if sensor is
                        # called <modality>BIT or <modality>BITREV
                        sensidx = [i for i, s in enumerate(sensors)
                                    if self._model.channel in s]
                    elif type(self._model.channel) is int:
                        sensidx = [i for i, s in enumerate(channels)
                                    if str(self._model.channel) in s]
                    if sensidx:
                        # select only first sensor of the selected modality
                        # (it is conceivable that multiple sensors of the same
                        # kind have been recorded)
                        sensidx = sensidx[0]
                        # since analog channels start in column 5 (zero based),
                        # add 5 to sensor index to obtain signal from selected
                        # modality; load data with pandas for performance
                        sensidx += 5
                        signal = pd.read_csv(path, delimiter = '\t',
                                             usecols=[sensidx], header=None,
                                             comment='#')
                        siglen = signal.size
                        sec = np.linspace(0, siglen / sfreq, siglen,
                                          1 / sfreq)
                        self._model.signal = np.ravel(signal)
                        self._model.sfreq = sfreq
                        self._model.sec = sec
                        self._model.loaded = True
                                                
                        
    def read_peaks(self):
        pass
    
    def find_peaks(self):
        if self._model.loaded:
            if self._model.modality == 'ECG':
                peaks = peaks_ecg(self._model.signal,
                                  self._model.sfreq)
            elif self._model.modality == 'PPG':
                peaks = peaks_ppg(self._model.signal,
                                  self._model.sfreq)
            elif self._model.modality == 'RESP':
                peaks = extrema_resp(self._model.signal,
                                     self._model.sfreq)
            self._model.peaks = peaks
    
    def edit_peaks(self, event):
        # account for the fact that depending on sensor modality, data.peaks
        # has different shapes; preserve ndarrays throughout editing!
        if self._model.editable:
            if self._model.peaks is not None:
                cursor = int(np.rint(event.xdata * self._model.sfreq))
                # search peak in a window of 200 msec, centered on selected
                # x coordinate of cursor position
                extend = int(np.rint(self._model.sfreq * 0.1))
                searchrange = np.arange(cursor - extend,
                                        cursor + extend)
                if event.key == 'd':
                    peakidx = np.argmin(np.abs(self._model.peaks[:, 0] -
                                               cursor))
                    # only delete peaks that are within search range
                    if np.any(searchrange == self._model.peaks[peakidx, 0]): 
                        self._model.peaks = np.delete(self._model.peaks,
                                                      peakidx, axis=0)
                        self.plot_update('peaks')
                elif event.key == 'a':
                    searchsignal = self._model.signal[searchrange]
                    # use find_peaks to also detect local extrema that are
                    # plateaus
                    locmax, _ = find_peaks(searchsignal)
                    locmin, _ = find_peaks(searchsignal * -1)
                    locext = np.concatenate((locmax, locmin))
                    locext.sort(kind='mergesort')
                    if locext.size > 0:
                        peakidx = np.argmin(np.abs(searchrange[locext] -
                                                   cursor))
                        newpeak = searchrange[0] + locext[peakidx]
                        # only add new peak if it doesn't exist already
                        if np.all(self._model.peaks[:, 0] != newpeak):
                            insertidx = np.searchsorted(self._model.
                                                        peaks[:, 0], newpeak)
                            if self._model.peaks.shape[1] == 1:
                                insertarr = [newpeak]
                                self._model.peaks = np.insert(self._model.
                                                              peaks, insertidx,
                                                              insertarr,
                                                              axis=0)
                            elif self._model.peaks.shape[1] == 2:
                                insertarr = [newpeak,
                                             self._model.signal[newpeak]]
                                self._model.peaks = np.insert(self._model.
                                                              peaks, insertidx,
                                                              insertarr,
                                                              axis=0)                            
                            self.plot_update('peaks')
    
    def save_peaks(self):
        pass
    
    def plot_update(self, value):
        if value == 'signal':
            self.signal_changed.emit()
        elif value == 'peaks':
            self.peaks_changed.emit()
    
    def batch_constructor(self):
        for fname in self.fnames:
            self.read_signal(fname)
#            if self.batchmode == 'multiple files':
            self.find_peaks()
            # save peaks to savepath with "<fname>_peaks" ending
                    
    def batch_executer(self, batch):
        worker = Worker(batch)
        self.threadpool.start(worker)

            
            
    
    
    
    
    
    