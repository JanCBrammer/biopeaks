# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 18:47:13 2019

@author: John Doe
"""

import time
import os
import json
import pandas as pd
import numpy as np
from ecg_offline import peaks_ecg
from ppg_offline import peaks_ppg
from resp_offline import extrema_resp
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QFileDialog

# threading is implemented according to https://pythonguis.com/courses/
# multithreading-pyqt-applications-qthreadpool/complete-example/

    
class WorkerSignals(QObject):

    batch_progress = pyqtSignal(str)
    
    
class Worker(QRunnable):
    
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()    
        self.kwargs['batch_progress_sig'] = self.signals.batch_progress 
        
    def run(self):
        self.fn(*self.args, **self.kwargs)
        
        
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
    # signals #
    ###########
    signal_changed = pyqtSignal()
    peaks_changed = pyqtSignal()
    
    ###########
    # methods #
    ###########
    
    def open_signal(self):
        self.fnames = QFileDialog.getOpenFileNames(None, 'Open file', '\home')[0]
        print(self.fnames)
        if self.fnames:
            self.numfiles = np.size(self.fnames)
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
        print('finding peaks')
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
    
    def edit_peaks(self):
        pass
    
    def save_peaks(self):
        pass
    
    def batch_progress(self, value):
        if value == 'signal':
            self.signal_changed.emit()
        elif value == 'peaks':
            self.peaks_changed.emit()
    
    def batch_constructor(self, batch_progress_sig):
        if self.batchmode == 'multiple files':
            pass
            # open file dialog to get savepath
        for fname in self.fnames:
            print(fname)
            self.read_signal(fname)
            batch_progress_sig.emit('signal')
            self.find_peaks()
            batch_progress_sig.emit('peaks')
            if self.batchmode == 'multiple files':
                pass
                # save peaks to savepath with "<fname>_peaks" ending
                    
    def batch_executer(self, batch):
        worker = Worker(batch)
        worker.signals.batch_progress.connect(self.batch_progress)
        self.threadpool.start(worker)

            
            
    
    
    
    
    
    