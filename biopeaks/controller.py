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
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt5.QtWidgets import QFileDialog
getOpenFileName = QFileDialog.getOpenFileName
getOpenFileNames = QFileDialog.getOpenFileNames
getSaveFileName = QFileDialog.getSaveFileName
getExistingDirectory = QFileDialog.getExistingDirectory
from .ecg import ecg_peaks, ecg_period
from .resp import resp_extrema, resp_stats
peakfuncs = {'ECG': ecg_peaks,
             'RESP': resp_extrema}


# threading is implemented according to https://pythonguis.com/courses/
# multithreading-pyqt-applications-qthreadpool/complete-example/
class WorkerSignals(QObject):

    progress = pyqtSignal(int)


class Worker(QRunnable):

    def __init__(self, fn, controller, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.controller = controller

    def run(self):
        self.signals.progress.emit(0)
        self.fn(self.controller, **self.kwargs)
        self.signals.progress.emit(1)


# decorator that runs Controller methods in Worker thread
def threaded(fn):
    def threader(controller, **kwargs):
        worker = Worker(fn, controller, **kwargs)
        worker.signals.progress.connect(controller._model.progress)
        controller.threadpool.start(worker)
    return threader


class Controller(QObject):

    def __init__(self, model):
        super().__init__()

        self._model = model
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)
        self.threading_enabled = True

    ###########
    # methods #
    ###########
    def get_fpaths(self):
        self._model.fpaths = getOpenFileNames(None, 'Choose your data',
                                              '\home')[0]
        if self._model.fpaths:
            if (self._model.batchmode == 'multiple files' and
                len(self._model.fpaths) >= 1):
                self.batch_processor()
            elif (self._model.batchmode == 'single file' and
                  len(self._model.fpaths) == 1):
                self._model.reset()
                self.read_chan(path=self._model.fpaths[0])


    def get_wpathsignal(self):
        if self._model.loaded:
            self._model.wpathsignal = getSaveFileName(None, 'Save signal',
                                                      'untitled.txt',
                                                      'text (*.txt)')[0]
            if self._model.wpathsignal:
                self.save_signal()
        else:
            self._model.status = 'error: no data available'


    def get_rpathpeaks(self):
        if self._model.loaded:
            if self._model.peaks is None:
                self._model.rpathpeaks = getOpenFileName(None,
                                                         'Choose your peaks',
                                                         '\home')[0]
                if self._model.rpathpeaks:
                    self.read_peaks()
            else:
                self._model.status = 'error: peaks already in memory'
        else:
            self._model.status = 'error: no data available'


    def get_wpathpeaks(self):
        if self._model.batchmode == 'single file':
            if self._model.peaks is None:
                self._model.status = 'error: no peaks available'
                return
            self._model.wpathpeaks = getSaveFileName(None, 'Save peaks',
                                                     'untitled.csv',
                                                     'CSV (*.csv)')[0]
            if self._model.wpathpeaks:
                self.save_peaks()
        elif self._model.batchmode == 'multiple files':
            if not self._model.savebatchpeaks:
                return
            self._model.wdirpeaks = getExistingDirectory(None,
                                                         'Choose a directory '
                                                         'for saving the '
                                                         'peaks',
                                                         '\home')
            
            
    def get_wpathstats(self):
        # count number of items selected for saving
        nitems = sum(self._model.savestats.values())
        if nitems < 1:
            self._model.status = "error: no statistics selected for saving"
            return
        # get paths
        if self._model.batchmode == 'single file':
            # check is there is data for the selected stats
            for key, value in self._model.savestats.items():
                if value:
                    if key == "period" and self._model.periodintp is None:
                        self._model.status = "error: no statistics available"
                        return
                    elif key == "rate" and self._model.rateintp is None:
                        self._model.status = "error: no statistics available"
                        return
                    elif key == "tidalamp" and self._model.tidalampintp is None:
                        self._model.status = "error: no statistics available"
                        return
            self._model.wpathstats = getSaveFileName(None, 'Save statistics',
                                                     'untitled.csv',
                                                     'CSV (*.csv)')[0]
            if self._model.wpathstats:
                self.save_stats()
           
        elif self._model.batchmode == 'multiple files':
            self._model.wdirstats = getExistingDirectory(None,
                                                         'Choose a directory '
                                                         'for saving the '
                                                         'statistics',
                                                         '\home')


    def batch_processor(self):
        '''
        Initiates batch processing. After initiation, the dispatcher method
        handles the sequential execution of methods that are called on each
        file of the batch. The dispatcher only listenes to the threader's
        progress signal during batch processing. The progress signal informs
        the dispatcher that a method has finshed and that the next method can
        be called. This slightly convoluted way of handling a batch is
        necessary for the following reason. Since each method is run in a
        thread (decorator), looping over the files of a batch will lead to ill-
        defined states of the model. The dispatcher ensures strictly sequential
        execution of methods (although limiting the threadpools capacity to one
        thread at a time should achieve the same). Also, busy-waiting can be
        avoided by using the dispatcher. Plotting is disabled during batch
        processing (model.plotting flag), since matplotlib cannot update the
        canvas fast enough when multiple plotting operations must be executed
        in rapid succession (i.e., when small files are processed). The user
        can still get an impression of the progress since the current file path
        is displayed.
        TODO: make method calls and their order more explicit!
        '''

        self.methodnb = 0
        self.nmethods = 4
        self.filenb = 0
        self.nfiles = len(self._model.fpaths)
        
        self.get_wpathpeaks()
        self.get_wpathstats()

        self._model.status = 'processing files'
        self._model.plotting = False
        self._model.progress_changed.connect(self.dispatcher)

        # initiate processing
        self.dispatcher(1)


    def dispatcher(self, progress):
        '''
        Start with first method on first file. As soon as one method has
        finished, (indicated by emission of progress_changed), execute next
        method. Once all methods are executed, go to the next file and start
        cycling through methods again.
        '''
        if progress == 0:
            return
        if self.filenb == self.nfiles:
            self._model.plotting = True
            self._model.progress_changed.disconnect(self.dispatcher)
            self._model.wdirpeaks = None
            self._model.wdirstats = None
            return
        fpath = self._model.fpaths[self.filenb]
        if self.methodnb == 0:
            self.methodnb += 1
            self._model.reset()
            self.read_chan(path=fpath)
        elif self.methodnb == 1:
            self.methodnb += 1
            self.find_peaks()
        elif self.methodnb == 2:
            self.methodnb += 1
            self.calculate_stats()
        elif self.methodnb == 3:
            self.methodnb += 1
            if self._model.wdirpeaks:
                _, fname = os.path.split(fpath)
                fpartname, _ = os.path.splitext(fname)
                self._model.wpathpeaks = os.path.join(self._model.wdirpeaks,
                                                      f"{fpartname}_peaks.csv")
                self.save_peaks()
            else:
                self.dispatcher(1)
        elif self.methodnb == 4:
            # once all methods are executed, move to next file and start with
            # first method again
            self.methodnb = 0
            self.filenb += 1
            if self._model.wdirstats:
                _, fname = os.path.split(fpath)
                fpartname, _ = os.path.splitext(fname)
                self._model.wpathstats = os.path.join(self._model.wdirstats,
                                                      f"{fpartname}_stats.csv")
                self.save_stats()
            else:
                self.dispatcher(1)
            

    @threaded
    def read_chan(self, path):
        self._model.status = 'loading file'
        _, file_extension = os.path.splitext(path)
        if file_extension != '.txt':
            self._model.status = 'error: wrong file format'
            return
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

                # load signal
                if self._model.signalchan == 'infer from modality':
                    schan = self._model.modality
                    # find the index of the sensor that corresponds to the
                    # selected modality; it doesn't matter if sensor is
                    # called <modality>BIT or <modality>BITREV
                    schanidx = [i for i, s in enumerate(sensors)
                                if schan in s]
                else:
                    # search analogue channels
                    schan = self._model.signalchan
                    schanidx = [i for i, s in enumerate(channels)
                                if int(schan[1]) == s]
                if not schanidx:
                    self._model.status = 'error: signal-channel not found'
                    return
                # select only first sensor of the selected
                # modality (it is conceivable that multiple sensors
                # of the same kind have been recorded)
                schanidx = schanidx[0]
                # since analog channels start in column 5 (zero
                # based), add 5 to sensor index to obtain signal
                # from selected modality
                schanidx += 5
                # load data with pandas for performance
                signal = pd.read_csv(path, delimiter='\t', usecols=[schanidx],
                                     header=None, comment='#')
                signallen = signal.size
                sec = np.linspace(0, signallen / sfreq, signallen)
                self._model.rpathsignal = path
                # important to set seconds PRIOR TO signal,
                # otherwise plotting behaves unexpectadly (since
                # plotting is triggered as soon as signal changes)
                self._model.sec = sec
                self._model.signal = np.ravel(signal)
                self._model.sfreq = sfreq
                self._model.loaded = True

                # load markers
                if self._model.markerchan == 'none':
                    return
                mchan = self._model.markerchan
                if mchan[0] == 'A':
                    mchanidx = [i for i, s in enumerate(channels)
                                if int(mchan[1]) == s]
                elif mchan[0] == 'I':
                    mchanidx = int(mchan[1])
                if not mchanidx:
                    self._model.status = 'error: marker-channel not found'
                    return
                if mchan[0] != 'I':
                    # select only first sensor of the selected
                    # modality (it is conceivable that multiple sensors
                    # of the same kind have been recorded)
                    mchanidx = mchanidx[0]
                    # since analog channels start in column 5 (zero
                    # based), add 5 to sensor index to obtain signal
                    # from selected modality
                    mchanidx += 5
                markers = pd.read_csv(path, delimiter='\t', usecols=[mchanidx],
                                      header=None, comment='#')
                self._model.markers = np.ravel(markers)
            else:
                self._model.status = 'error: wrong file format'


    @threaded
    def segment_signal(self):
        self._model.status = 'segmenting signal'
        # convert from seconds to samples
        begsamp = int(np.rint(self._model.segment[0] * self._model.sfreq))
        endsamp = int(np.rint(self._model.segment[1] * self._model.sfreq))
        siglen = endsamp - begsamp
        sec = np.linspace(0, siglen / self._model.sfreq, siglen)
        self._model.sec = sec
        self._model.signal = self._model.signal[begsamp:endsamp]
        if self._model.peaks is not None:
            peakidcs = np.where((self._model.peaks >= begsamp) &
                                (self._model.peaks <= endsamp))[0]
            peaks = self._model.peaks[peakidcs]
            peaks -= begsamp
            self._model.peaks = peaks
        if self._model.markers is not None:
            self._model.markers = self._model.markers[begsamp:endsamp]
        if self._model.periodintp is not None:
            self._model.periodintp = self._model.periodintp[begsamp:endsamp]
        if self._model.rateintp is not None:
            self._model.rateintp = self._model.rateintp[begsamp:endsamp]
        if self._model.tidalampintp is not None:
            self._model.tidalampintp = self._model.tidalampintp[begsamp:
                                                                endsamp]


    @threaded
    def save_signal(self):
        self._model.status = 'saving signal'
        # if the signal has not been segmented, simply copy it to new
        # location
        if self._model.segment is None:
            if self._model.rpathsignal != self._model.wpathsignal:
                copyfile(self._model.rpathsignal, self._model.wpathsignal)
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
            with open(self._model.rpathsignal, 'r') as oldfile, \
                open(self._model.wpathsignal, 'w', newline='') as newfile:
                # read header (first three lines) and write it to
                # new file
                for line in islice(oldfile, 3):
                    newfile.write(line)
                # then write the data to the new file
                data.to_csv(newfile, sep='\t', header=False,
                            index=False)


    @threaded
    def read_peaks(self):
        self._model.status = 'loading peaks'
        dfpeaks = pd.read_csv(self._model.rpathpeaks)
        if dfpeaks.shape[1] == 1:
            peaks = dfpeaks['peaks'].copy()
            # convert back to samples
            peaks = peaks * self._model.sfreq
            # reshape to a format understood by plotting function
            # (ndarray of type int)
            peaks = np.rint(peaks).astype(int)
            self._model.peaks = peaks
        elif dfpeaks.shape[1] == 2:
            extrema = np.concatenate((dfpeaks['peaks'].copy(),
                                      dfpeaks['troughs'].copy()))
            # mergesort extrema
            sortidcs = extrema.argsort(kind='mergesort')
            extrema = extrema[sortidcs]
            # remove NANs that may have been appended in case of odd number of
            # extrema (see save_peaks)
            extrema = extrema[~np.isnan(extrema)]
            # convert extrema from seconds to samples
            extrema = np.rint(extrema * self._model.sfreq)
            # convert to biopeaks array format
            self._model.peaks = extrema.astype(int)


    @threaded
    def find_peaks(self):
        self._model.status = 'finding peaks'
        if self._model.loaded:
            if self._model.peaks is None:
                peakfunc = peakfuncs[self._model.modality]
                self._model.peaks = peakfunc(self._model.signal,
                                             self._model.sfreq)
            else:
                self._model.status = 'error: peaks already in memory'
        else:
            self._model.status = 'error: no data available'


    def edit_peaks(self, event):
        if not self._model.peakseditable:
            return
        if self._model.peaks is None:
            return
        cursor = int(np.rint(event.xdata * self._model.sfreq))
        # search peak in a window of 200 msec, centered on selected
        # x coordinate of cursor position
        extend = int(np.rint(self._model.sfreq * 0.1))
        searchrange = np.arange(cursor - extend, cursor + extend)
        if event.key == 'd':
            peakidx = np.argmin(np.abs(self._model.peaks - cursor))
            # only delete peaks that are within search range
            if np.any(searchrange == self._model.peaks[peakidx]):
                self._model.peaks = np.delete(self._model.peaks, peakidx)
        elif event.key == 'a':
            searchsignal = self._model.signal[searchrange]
            # use find_peaks to also detect local extrema that are
            # plateaus
            locmax, _ = find_peaks(searchsignal)
            locmin, _ = find_peaks(searchsignal * -1)
            locext = np.concatenate((locmax, locmin))
            locext.sort(kind='mergesort')
            if locext.size < 1:
                return
            peakidx = np.argmin(np.abs(searchrange[locext] - cursor))
            newpeak = searchrange[0] + locext[peakidx]
            # only add new peak if it doesn't exist already
            if np.all(self._model.peaks != newpeak):
                insertidx = np.searchsorted(self._model.peaks, newpeak)
                insertarr = [newpeak]
                self._model.peaks = np.insert(self._model.peaks, insertidx,
                                              insertarr)


    @threaded
    def save_peaks(self):
        self._model.status = 'saving peaks'
        # save peaks in seconds
        if self._model.modality == 'ECG':
            savearray = pd.DataFrame(self._model.peaks / self._model.sfreq)
            savearray.to_csv(self._model.wpathpeaks, index=False,
                             header=['peaks'])
        elif self._model.modality == 'RESP':
            # check if the alternation of peaks and troughs is
            # unbroken (it might be at this point due to user edits);
            # if alternation of sign in extdiffs is broken, remove
            # the extreme (or extrema) that cause(s) the break(s)
            amps = self._model.signal[self._model.peaks]
            extdiffs = np.sign(np.diff(amps))
            extdiffs = np.add(extdiffs[0:-1], extdiffs[1:])
            removeext = np.where(extdiffs != 0)[0] + 1
            # work on local copy of extrema to avoid call to plotting
            # function
            extrema = np.delete(self._model.peaks, removeext)
            amps = self._model.signal[extrema]
            # pad extrema with NAN in order to simulate equal number of peaks
            # and troughs if needed
            if np.remainder(extrema.size, 2) != 0:
                extrema = np.append(extrema, np.nan)
            # determine if series starts with peak or trough to be able
            # to save peaks and troughs separately
            if amps[0] > amps[1]:
                peaks = extrema[0:-1:2]
                troughs = extrema[1::2]
            elif amps[0] < amps[1]:
                peaks = extrema[1::2]
                troughs = extrema[0:-1:2]
            # make sure extrema are float: IMPORTANT, if seconds are
            # saved as int, rounding errors (i.e. misplaced peaks) occur
            savearray = np.column_stack((peaks / self._model.sfreq,
                                         troughs / self._model.sfreq))
            savearray = pd.DataFrame(savearray)
            savearray.to_csv(self._model.wpathpeaks, index=False,
                             header=['peaks', 'troughs'], na_rep='nan')


    @threaded
    def calculate_stats(self):
        self._model.status = 'calculating statistics'
        if (self._model.peaks is None) or (np.size(self._model.peaks) < 2):
            self._model.status = 'error: no peaks available'
            return
        if self._model.modality == 'ECG':
            (self._model.peaks,
             self._model.periodintp,
             self._model.rateintp) = ecg_period(peaks=self._model.peaks,
                                                sfreq=self._model.sfreq,
                                                nsamp=self._model.signal.size)
        elif self._model.modality == 'RESP':
            (self._model.periodintp,
             self._model.rateintp,
             self._model.tidalampintp) = resp_stats(extrema=self._model.peaks,
                                                    signal=self._model.signal,
                                                    sfreq=self._model.sfreq)
            
            
    @threaded
    def save_stats(self):
        savekeys = []
        for key, value in self._model.savestats.items():
            if value == True:
                savekeys.append(key)
        savearray = np.zeros((self._model.signal.size, len(savekeys)))
        for i, key in enumerate(savekeys):
            if key == 'period':
                savearray[:, i] = self._model.periodintp
            if key == 'rate':
                savearray[:, i] = self._model.rateintp
            if key == 'tidalamp':
                savearray[:, i] = self._model.tidalampintp
        savearray = pd.DataFrame(savearray)
        savearray.to_csv(self._model.wpathstats, index=False, header=savekeys)
                