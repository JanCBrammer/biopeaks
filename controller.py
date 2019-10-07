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
from ecg_offline import ecg_peaks, ecg_period
from resp_offline import resp_extrema, resp_period
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt5.QtWidgets import QFileDialog
getOpenFileName = QFileDialog.getOpenFileName
getOpenFileNames = QFileDialog.getOpenFileNames
getSaveFileName = QFileDialog.getSaveFileName
getExistingDirectory = QFileDialog.getExistingDirectory
peakfuncs = {'ECG': ecg_peaks,
             'RESP': resp_extrema}

# threading is implemented according to https://pythonguis.com/courses/
# multithreading-pyqt-applications-qthreadpool/complete-example/
class WorkerSignals(QObject):

    progress = pyqtSignal(int)


class Worker(QRunnable):

    def __init__(self, fn, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        self.signals.progress.emit(0)
        self.fn(**self.kwargs)
        self.signals.progress.emit(1)


class Controller(QObject):

    def __init__(self, model):
        super().__init__()

        self._model = model
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)

    ###########
    # methods #
    ###########
    def open_signal(self):
        self._model.fpaths = getOpenFileNames(None, 'Choose your data',
                                              '\home')[0]
        print('controller: {}'.format(self._model.fpaths))
        if self._model.fpaths:
            if (self._model.batchmode == 'multiple files' and
                len(self._model.fpaths) >= 1):
                self.get_wpathpeaks()
                if self._model.wdirpeaks:
                    self.threader(status='processing files',
                                  fn=self.batch_processor)
            elif (self._model.batchmode == 'single file' and
                  len(self._model.fpaths) == 1):
                self._model.reset()
                self.threader(status='loading file', fn=self.read_chan,
                              path=self._model.fpaths[0], chantype='signal')

    def open_markers(self):
        if self._model.batchmode == 'single file':
            # only read markerss from file if file has been loaded and signal
            # has not been segmented yet
            if self._model.loaded and self._model.segment is None:
                self.threader(status='docking markers', fn=self.read_chan,
                              path=self._model.rpathsignal, chantype='markers')
            else:
                self._model.status = 'error: no data available'

    def read_chan(self, path, chantype):
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
                if not chanidx:
                    self._model.status = 'error: channel not found'
                    return
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
                data = pd.read_csv(path, delimiter='\t', usecols=[chanidx],
                                   header=None, comment='#')
                if chantype == 'signal':
                    datalen = data.size
                    sec = np.linspace(0, datalen / sfreq, datalen)
                    self._model.rpathsignal = path
                    # important to set seconds PRIOR TO signal,
                    # otherwise plotting behaves unexpectadly (since
                    # plotting is triggered as soon as signal changes)
                    self._model.sec = sec
                    self._model.signal = np.ravel(data)
                    self._model.sfreq = sfreq
                    self._model.loaded = True
                elif chantype == 'markers':
                    self._model.markers = np.ravel(data)
            else:
                self._model.status = 'error: wrong file format'


    def segment_signal(self):
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
        if self._model.rateintp is not None:
            self._model.rateintp = self._model.rateintp[begsamp:endsamp]

    def save_signal(self):
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

    def read_peaks(self):
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

    def find_peaks(self):
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
        # account for the fact that depending on sensor modality, data.peaks
        # has different shapes; preserve ndarrays throughout editing!
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

    def save_peaks(self):
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
            # pad extrema with NAN in order to simulate equal number of peaks
            # and troughs if needed
            if np.remainder(extrema.size, 2) != 0:
                extrema = np.append(extrema, np.nan)
            # determine if series starts with peak or trough to be able
            # to save peaks and troughs separately
            amps = self._model.signal[extrema]
            if extrema[0] > extrema[1]:
                peaks = extrema[0:-1:2]
                troughs = extrema[1::2]
            elif extrema[0] < extrema[1]:
                peaks = extrema[1::2]
                troughs = extrema[0:-1:2]
            # make sure extrema are float: IMPORTANT, if seconds are
            # saved as int, rounding errors (i.e. misplaced peaks) occur
            savearray = np.column_stack((peaks / self._model.sfreq,
                                         troughs / self._model.sfreq))
            savearray = pd.DataFrame(savearray)
            savearray.to_csv(self._model.wpathpeaks, index=False,
                             header=['peaks', 'troughs'], na_rep='nan')

    def calculate_rate(self):
        if self._model.peaks is None:
            self._model.status = 'error: no peaks available'
            return
        if self._model.modality == 'ECG':
            (self._model.peaks,
             self._model.period,
             self._model.periodintp) = ecg_period(peaks=self._model.peaks,
                                                  sfreq=self._model.sfreq,
                                                  nsamp=self._model.signal.
                                                  size)
            self._model.rateintp = 60 / self._model.periodintp
        elif self._model.modality == 'RESP':
            (self._model.period,
             self._model.periodintp) = resp_period(extrema=self._model.peaks,
                                                   signal=self._model.signal,
                                                   sfreq=self._model.sfreq)
            self._model.rateintp = 60 / self._model.periodintp

    def calculate_breathamp(self):
        pass

    def get_wpathsignal(self):
        if self._model.loaded:
            self._model.wpathsignal = getSaveFileName(None, 'Save signal',
                                                      'untitled.txt',
                                                      'text (*.txt)')[0]
            if self._model.wpathsignal:
                self.threader(status='saving signal', fn=self.save_signal)
        else:
            self._model.status = 'error: no data available'

    def get_rpathpeaks(self):
        if self._model.loaded:
            if self._model.peaks is None:
                self._model.rpathpeaks = getOpenFileName(None,
                                                         'Choose your peaks',
                                                         '\home')[0]
                if self._model.rpathpeaks:
                    self.threader(status='loading peaks', fn=self.read_peaks)
            else:
                self._model.status = 'error: peaks already in memory'
        else:
            self._model.status = 'error: no data available'

    def get_wpathpeaks(self):
        if self._model.batchmode == 'single file':
            if self._model.peaks is not None:
                self._model.wpathpeaks = getSaveFileName(None, 'Save peaks',
                                                         'untitled.csv',
                                                         'CSV (*.csv)')[0]
                if self._model.wpathpeaks:
                    self.threader(status='saving peaks', fn=self.save_peaks)
            else:
                self._model.status = 'error: no peaks available'
        elif self._model.batchmode == 'multiple files':
            self._model.wdirpeaks = getExistingDirectory(None,
                                                         'Choose a directory '
                                                         'for saving the '
                                                         'peaks',
                                                         '\home')

    def batch_processor(self):
        # disable plotting during batch processing, since matplotlib cannot
        # update the canvas fast enough when multiple plotting operations must
        # be executed in rapid succession (i.e., when small files are
        # processed); the user can still get an impression of the progress
        # since the current file path is displayed
        self._model.plotting = False
        for fpath in self._model.fpaths:
            # reset model before reading new dataset
            self._model.reset()
            self.read_chan(fpath, chantype='signal')
            # in case the file cannot be loaded successfully (e.g., wrong
            # format or non-existing channel), move on to next file
            if self._model.loaded:

                self.find_peaks()

                # save peaks to self.wpathpeaks with "<fname>_peaks" ending
                _, fname = os.path.split(fpath)
                fpartname, _ = os.path.splitext(fname)
                self._model.wpathpeaks = os.path.join(self._model.wdirpeaks,
                                                      '{}{}'.format(fpartname,
                                                                    '_peaks'
                                                                    '.csv'))
                self.save_peaks()
        # enable plotting again once the batch is done
        self._model.plotting = True

    def threader(self, status, fn, **kwargs):
        # note that the worker's signal must be connected to the controller's
        # method each time a new worker is instantiated
        self._model.status = status
        worker = Worker(fn, **kwargs)
        worker.signals.progress.connect(self._model.progress)
        self.threadpool.start(worker)

    def verify_segment(self, values):
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
                    self._model.status = 'valid selection {}'.format(values)
                    self._model.segment = [begsamp, endsamp]
                else:
                    self._model.status = 'invalid selection {}'.format(values)
            else:
                self._model.status = 'invalid selection {}'.format(values)
