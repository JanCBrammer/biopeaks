# -*- coding: utf-8 -*-

from .ecg import ecg_peaks, ecg_period
from .resp import resp_extrema, resp_stats
from .io_utils import read_opensignals, write_opensignals, read_edf
import os
import pandas as pd
import numpy as np
from scipy.signal import find_peaks as find_peaks_scipy
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
                self.read_signal(path=self._model.fpaths[0])

                # If requested, read marker channel.
                if self._model.markerchan == "none":
                    return
                if self._model.loaded:
                    self.read_marker(path=self.rpathsignal)


    def get_wpathsignal(self):
        if self._model.loaded:
            self._model.wpathsignal = getSaveFileName(None, 'Save signal',
                                                      'untitled.txt',
                                                      'text (*.txt)')[0]
            if self._model.wpathsignal:
                self.save_signal()
        else:
            self._model.status = "Error: no data available."


    def get_rpathpeaks(self):
        if self._model.loaded:
            if self._model.peaks is None:
                self._model.rpathpeaks = getOpenFileName(None,
                                                         'Choose your peaks',
                                                         '\home')[0]
                if self._model.rpathpeaks:
                    self.read_peaks()
            else:
                self._model.status = "Error: peaks already in memory."
        else:
            self._model.status = "Error: no data available."


    def get_wpathpeaks(self):
        if self._model.batchmode == 'single file':
            if self._model.peaks is None:
                self._model.status = "Error: no peaks available."
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
            self._model.status = "Error: no statistics selected for saving."
            return
        # get paths
        if self._model.batchmode == 'single file':
            # check is there is data for the selected stats
            for key, value in self._model.savestats.items():
                if value:
                    if key == "period" and self._model.periodintp is None:
                        self._model.status = "Error: no statistics available."
                        return
                    elif key == "rate" and self._model.rateintp is None:
                        self._model.status = "Error: no statistics available."
                        return
                    elif key == "tidalamp" and self._model.tidalampintp is None:
                        self._model.status = "Error: no statistics available."
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

        self._model.status = "Processing files."
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
            # this condition works because filenb starts at 0
            self._model.plotting = True
            self._model.progress_changed.disconnect(self.dispatcher)
            self._model.wdirpeaks = None
            self._model.wdirstats = None
            return
        fpath = self._model.fpaths[self.filenb]
        if self.methodnb == 0:
            self.methodnb += 1
            self._model.reset()
            self.read_signal(path=fpath)
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
    def read_signal(self, path):
        self._model.status = "Loading file."
        _, file_extension = os.path.splitext(path)

        if file_extension not in [".txt", ".edf"]:
            self._model.status = "Error: Please select an OpenSignals or EDF file."
            return

        if file_extension == ".txt":

            # Read signal and associated metadata.
            output = read_opensignals(path, self._model.signalchan,
                                      channeltype="signal")
            # If the io utility returns an error, print the error and return.
            if output["status"]:
                self._model.status = output["status"]
                return

            self._model.filetype = "OpenSignals"

        elif file_extension == ".edf":

            # Read signal and associated metadata.
            output = read_edf(path, self._model.signalchan,
                              channeltype="signal")
            # If the io utility returns an error, print the error and return.
            if output["status"]:
                self._model.status = output["status"]
                return

            self._model.filetype = "EDF"

        # Important to set seconds PRIOR TO signal, otherwise plotting
        # behaves unexpectadly (since plotting is triggered as soon as
        # signal changes).
        self._model.sec = output["sec"]
        self._model.signal = output["signal"]
        self._model.sfreq = output["sfreq"]
        self._model.loaded = True
        self._model.rpathsignal = path


    def read_marker(self, path):
        output = read_opensignals(path, self._model.markerchan,
                                  channeltype="marker")
        # If the io utility returns an error, print the error and return.
        if output["status"]:
            self._model.status = output["status"]
            return
        self._model.markers = output["signal"]


    @threaded
    def segment_signal(self):
        self._model.status = "Segmenting signal."
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
        self._model.status = "Saving signal."

        if self._model.segment is not None:
            begsamp = int(np.rint(self._model.segment[0] * self._model.sfreq))
            endsamp = int(np.rint(self._model.segment[1] * self._model.sfreq))

        if self._model.filetype == "OpenSignals":
            write_opensignals(self._model.rpathsignal, self._model.wpathsignal,
                              segment=[begsamp, endsamp])

        elif self._model.filetype == "EDF":
            pass


    @threaded
    def read_peaks(self):
        self._model.status = "Loading peaks."
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
        self._model.status = "Finding peaks."
        if self._model.loaded:
            if self._model.peaks is None:
                peakfunc = peakfuncs[self._model.modality]
                self._model.peaks = peakfunc(self._model.signal,
                                             self._model.sfreq)
            else:
                self._model.status = "Error: peaks already in memory."
        else:
            self._model.status = "Error: no data available."


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
        # make sure that searchrange doesn't extend beyond signal
        retainidcs = np.logical_and(searchrange > 0,
                                    searchrange < self._model.signal.size)
        searchrange = searchrange[retainidcs]
        if event.key == 'd':
            peakidx = np.argmin(np.abs(self._model.peaks - cursor))
            # only delete peaks that are within search range
            if np.any(searchrange == self._model.peaks[peakidx]):
                self._model.peaks = np.delete(self._model.peaks, peakidx)
        elif event.key == 'a':
            searchsignal = self._model.signal[searchrange]
            # use Scipy's find_peaks to also detect local extrema that are
            # plateaus
            locmax, _ = find_peaks_scipy(searchsignal)
            locmin, _ = find_peaks_scipy(searchsignal * -1)
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
        self._model.status = "Saving peaks."
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
        self._model.status = "Calculating statistics."
        if (self._model.peaks is None) or (np.size(self._model.peaks) < 2):
            self._model.status = "Error: no peaks available."
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
