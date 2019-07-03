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
from itertools import islice
from shutil import copyfile
from ecg_offline import peaks_ecg
from ppg_offline import peaks_ppg
from resp_offline import extrema_resp
from PyQt5.QtCore import (QObject, QRunnable, QThreadPool, QWaitCondition,
                          QMutex)
from PyQt5.QtWidgets import QFileDialog

peakfuncs = {'ECG': peaks_ecg,
             'PPG': peaks_ppg,
             'RESP': extrema_resp}

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
        self.mutex = QMutex()
        self.plot_signal_finished = QWaitCondition()
        self.plot_peaks_finished = QWaitCondition()
        
        self.fpaths = None
        self.wpathpeaks = None
        self.wdirpeaks = None
        self.rpathpeaks = None
        self.wpathsignal = None
        self.batchmode = None
        self.modality = None
        self.peakseditable = False

    ###########
    # methods #
    ###########
    def open_signal(self):
        self.fpaths = QFileDialog.getOpenFileNames(None, 'Choose your data',
                                                   '\home')[0]
        if self.fpaths:
            if self.batchmode == 'multiple files':
                self.get_wpathpeaks()
                batch = self.batch_constructor
                self.batch_executer(batch)
            # if single file mode is active, process only first file even if
            # list of files was selected
            elif self.batchmode == 'single file':
                self._model.reset()
                self.read_chan(self.fpaths[0], chantype='signal')
            
    def open_markers(self):
        if (self.batchmode == 'single file') and (self._model.loaded):
            self.read_chan(self._model.rpathsignal, chantype='markers')
    
    def read_chan(self, path, chantype):
        _, self.file_extension = os.path.splitext(path)
        if self.file_extension == '.txt':
            # open file and check if it's encoded in OpenSignals format
            with open(path, 'r') as f:
                # read first line and check if user provided an OpenSignals
                # file
                if 'OpenSignals' in f.readline():
                    # read second line and convert json header to dict (only
                    # selects first device / MAC adress)
                    metadata = json.loads(f.readline()[1:])
                    metadata = metadata[list(metadata.keys())[0]]
                    # parse header and extract relevant metadata
                    sfreq = metadata['sampling rate']
                    sensors = metadata['sensor']
                    channels = metadata['channels']
                    # select channel and load data
                    if chantype == 'signal':
                        channel = self._model.signalchan
                    elif chantype == 'markers':
                        channel = self._model.markerchan
                    if channel[0] == 'A':
                        chanidx = [i for i, s in enumerate(channels)
                                    if int(channel[1]) == s]
                    elif channel[0] == 'I':
                        chanidx = int(channel[1])
                    else:
                        # find the index of the sensor that corresponds to the
                        # selected modality; it doesn't matter if sensor is
                        # called <modality>BIT or <modality>BITREV
                        chanidx = [i for i, s in enumerate(sensors)
                                    if channel in s]
                    if chanidx:
                        if channel[0] != 'I':
                            # select only first sensor of the selected
                            # modality (it is conceivable that multiple sensors
                            # of the same kind have been recorded)
                            chanidx = chanidx[0]
                            # since analog channels start in column 5 (zero
                            # based), add 5 to sensor index to obtain signal
                            # from selected modality
                            chanidx += 5
                        # load data with pandas for performance
                        data = pd.read_csv(path, delimiter='\t',
                                           usecols=[chanidx], header=None,
                                           comment='#')
                        if chantype == 'signal':
                            datalen = data.size
                            sec = np.linspace(0, datalen / sfreq, datalen)
                            self._model.rpathsignal = path
                            # important to set seconds PRIOR TO signal,
                            # otherwise plotting behaves unexpectadly (since 
                            # plotting is triggered as soon as signal changes)
                            self._model.sec = sec
                            self._model.signal= np.ravel(data) 
                            self._model.sfreq = sfreq
                            self._model.loaded = True
                        elif chantype == 'markers':
                            self._model.markers = np.ravel(data)
                        
    def segment_signal(self):
        # convert from seconds to samples
        begsamp = int(np.rint(self._model.segment[0] * self._model.sfreq))
        endsamp = int(np.rint(self._model.segment[1] * self._model.sfreq))
        siglen = endsamp - begsamp
        sec = np.linspace(0, siglen / self._model.sfreq, siglen)
        self._model.sec = sec
        self._model.signal = self._model.signal[begsamp:endsamp]
        if self._model.peaks is not None:
            peakidcs = np.where((self._model.peaks[:, 0] >= begsamp) &
                                (self._model.peaks[:, 0] <= endsamp))[0]
            peaks = self._model.peaks[peakidcs, :]
            peaks[:, 0] -= begsamp
            self._model.peaks = peaks
        if self._model.markers is not None:
            self._model.markers = self._model.markers[begsamp:endsamp]
        
    def save_signal(self):
        if self._model.loaded:
            self.wpathsignal, _ = QFileDialog.getSaveFileName(None,
                                                              'Save signal',
                                                              'untitled.txt',
                                                              'text (*.txt)')
            if self.wpathsignal:
                # if the signal has not been segmented, simply copy it
                if self._model.segment is None:
                    copyfile(self._model.rpathsignal, self.wpathsignal)
                # if signal has been segmented apply segmentation to all
                # channels in the dataset
                elif self._model.segment is not None:
                    begsamp = int(np.rint(self._model.segment[0] *
                                          self._model.sfreq))
                    endsamp = int(np.rint(self._model.segment[1] *
                                          self._model.sfreq))
                    data = pd.read_csv(self._model.rpathsignal, delimiter='\t',
                                       header=None, comment='#')
                    data = data.iloc[begsamp:endsamp, :]
                    with open(self._model.rpathsignal, 'r') as oldfile:
                        with open(self.wpathsignal, 'w',
                                  newline='') as newfile:
                            # read header (first three lines) and write it to
                            # new file
                            for line in islice(oldfile, 3):
                                    newfile.write(line)
                            # then write the data to the new file
                            data.to_csv(newfile, sep='\t', header=False,
                                        index=False)
                
                
    def read_peaks(self):
        if self._model.loaded and self._model.peaks is None:
            self.rpathpeaks = QFileDialog.getOpenFileNames(None,
                                                           'Choose your peaks',
                                                           '\home')[0][0]
            if self.rpathpeaks:
                dfpeaks = pd.read_csv(self.rpathpeaks)
                if dfpeaks.shape[1] == 1:
                    peaks = dfpeaks['peaks'].copy()
                    # convert back to samples
                    peaks = peaks * self._model.sfreq
                    # reshape to a format understood by plotting function
                    # (ndarray of type int)
                    peaks = np.rint(peaks[:, np.newaxis]).astype(int)
                    self._model.peaks = peaks
                elif dfpeaks.shape[1] == 4:
                    # mergesort peaks and troughs
                    extrema = np.concatenate((dfpeaks['peaks'].copy(),
                                              dfpeaks['troughs'].copy()))
                    extrema.sort(kind='mergesort')
                    extrema = extrema * self._model.sfreq
                    extrema = np.rint(extrema[:, np.newaxis]).astype(int)
                    self._model.peaks = extrema
            
    def find_peaks(self):
        if self._model.loaded and self._model.peaks is None:
            peakfunc = peakfuncs[self.modality]
            peaks = peakfunc(self._model.signal,
                             self._model.sfreq)
            self._model.peaks = peaks
        
    def edit_peaks(self, event):
        # account for the fact that depending on sensor modality, data.peaks
        # has different shapes; preserve ndarrays throughout editing!
        if self.peakseditable:
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
    
    def get_wpathpeaks(self):
        if self.batchmode == 'single file' and self._model.peaks is not None:
            self.wpathpeaks, _ = QFileDialog.getSaveFileName(None,
                                                             'Save peaks',
                                                             'untitled.csv',
                                                             'CSV (*.csv)')
            self.save_peaks()
        elif self.batchmode == 'multiple files':
            self.wdirpeaks = QFileDialog.getExistingDirectory(None,
                                                              'Choose a '
                                                              'directory '
                                                              'for saving '
                                                              'the peaks',
                                                              '\home')
        
    def save_peaks(self):
        if self.wpathpeaks:
            # save peaks in seconds
            if self._model.peaks.shape[1] == 1:
                savearray = pd.DataFrame(self._model.peaks / self._model.sfreq)
                savearray.to_csv(self.wpathpeaks, index=False,
                                 header=['peaks'])
            elif self._model.peaks.shape[1] == 2:
                # check if the alternation of peaks and troughs is
                # unbroken (it might be at this point due to user edits);
                # if alternation of sign in extdiffs is broken, remove
                # the extreme (or extrema) that cause(s) the break(s)
                extdiffs = np.sign(np.diff(self._model.peaks[:, 1]))
                extdiffs = np.add(extdiffs[0:-1], extdiffs[1:])
                removeext = np.where(extdiffs != 0)[0] + 1
                # work on local copy of extrema to avoid call to plotting
                # function
                extrema = np.delete(self._model.peaks, removeext, axis=0)
                # determine if series starts with peak or trough to be able
                # to save peaks and troughs separately (as well as the
                # corresponding amplitudes)
                if extrema[0, 1] > extrema[1, 1]:
                    peaks = extrema[0:-3:2, 0]
                    troughs = extrema[1:-2:2, 0]
                    amppeaks = extrema[0:-3:2, 1]
                    amptroughs = extrema[1:-2:2, 1]
                elif extrema[0, 1] < extrema[1, 1]:
                    peaks = extrema[1:-2:2, 0]
                    troughs = extrema[0:-3:2, 0]
                    amppeaks = extrema[1:-2:2, 1]
                    amptroughs = extrema[0:-3:2, 1]
                # make sure extrema are float: IMPORTANT, if seconds are
                # saved as int, rounding errors (i.e. misplaced peaks) occur
                savearray = np.column_stack((peaks / self._model.sfreq,
                                             troughs / self._model.sfreq,
                                             amppeaks,
                                             amptroughs))
                savearray = pd.DataFrame(savearray)
                savearray.to_csv(self.wpathpeaks, index=False,
                                 header=['peaks', 'troughs',
                                         'amppeaks', 'amptroughs'])
            
    def batch_constructor(self):
        for fpath in self.fpaths:
            # reset model before reading new dataset
            self._model.reset()
            self.read_chan(fpath, chantype='signal')
            # wait for plotting to be done, otherwise processing of the next
            # file gets initiated before plotting of the current file has
            # finished
            self.mutex.lock()
            self.plot_signal_finished.wait(self.mutex)
            self.mutex.unlock()
            
            self.find_peaks()
            # wait for plotting to be done, otherwise processing of the next
            # file gets initiated before plotting of the current file has
            # finished
            self.mutex.lock()
            self.plot_peaks_finished.wait(self.mutex)
            self.mutex.unlock()
            
            # save peaks to self.wpathpeaks with "<fname>_peaks" ending
            _, fname = os.path.split(fpath)
            fpartname, _ = os.path.splitext(fname)
            self.wpathpeaks = os.path.join(self.wdirpeaks,
                                           '{}{}'.format(fpartname,
                                            '_peaks.csv'))
            self.save_peaks()
                    
    def batch_executer(self, batch):
        worker = Worker(batch)
        self.threadpool.start(worker)
        
    def change_modality(self, value):
        self.modality = value
        print(value)
        
    def change_signalchan(self, value):
        self._model.signalchan = value
        print(value)
        
    def change_markerchan(self, value):
        self._model.markerchan = value
        print(value)
        
    def change_batchmode(self, value):
        self.batchmode = value
        print(value)
        
    def change_editable(self, value):
        if value == 2:
            self.peakseditable = True
        elif value == 0:
            self.peakseditable = False
        print(value)
        
    def change_segment(self, values):
        # check if any of the fields is empty
        if values[0] and values[1]:
            begsamp = float(values[0])
            endsamp = float(values[1])
            # check if values are inside temporal bounds
            evalarray = [np.asarray([begsamp, endsamp]) >= self._model.sec[0],
                         np.asarray([begsamp, endsamp]) <= self._model.sec[-1]]
            if np.all(evalarray):
                # check if order is valid
                if begsamp < endsamp:
                    print('valid selection {}'.format(values))
                    self._model.segment = [begsamp, endsamp]
                else:
                    print('invalid selection {}'.format(values))
            