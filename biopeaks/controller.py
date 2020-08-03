# -*- coding: utf-8 -*-

from functools import wraps
from .heart import ecg_peaks, ppg_peaks, correct_peaks, heart_period
from .resp import resp_extrema, resp_stats
from .io_utils import (read_custom, read_opensignals, read_edf,
                       write_custom, write_opensignals, write_edf)
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.signal import find_peaks as find_peaks_scipy
from PySide2.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide2.QtWidgets import QFileDialog
getOpenFileName = QFileDialog.getOpenFileName
getOpenFileNames = QFileDialog.getOpenFileNames
getSaveFileName = QFileDialog.getSaveFileName
getExistingDirectory = QFileDialog.getExistingDirectory

peakfuncs = {"ECG": ecg_peaks,
             "PPG": ppg_peaks,
             "RESP": resp_extrema}

readfuncs = {"Custom": read_custom,
             "OpenSignals": read_opensignals,
             "EDF": read_edf}

writefuncs = {"Custom": write_custom,
              "OpenSignals": write_opensignals,
              "EDF": write_edf}


# threading is implemented according to https://pythonguis.com/courses/
# multithreading-pyqt-applications-qthreadpool/complete-example/
class WorkerSignals(QObject):

    progress = Signal(int)


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
    @wraps(fn)
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
                                              "\\home")[0]
        if not self._model.fpaths:
            self._model.customheader = dict.fromkeys(self._model.customheader, None)    # for custom files also reset header
            self._model.set_filetype(None)    # reset file type
            return
        if (self._model.batchmode == 'multiple files' and
            len(self._model.fpaths) >= 1):
            self.batch_processor()
        elif (self._model.batchmode == 'single file' and
              len(self._model.fpaths) == 1):
            self._model.reset()
            self.read_channels()


    def get_wpathsignal(self):
        if not self._model.loaded:
            self._model.status = "Error: no data available."
            return

        if self._model.filetype == "OpenSignals":
            filefilter = "OpenSignals (*.txt)"
        elif self._model.filetype == "EDF":
            filefilter = "EDF (*.edf)"
        elif self._model.filetype == "Custom":
            filefilter = f"Plain text (*{Path(self._model.rpathsignal).suffix})"
        self._model.wpathsignal = getSaveFileName(None, 'Save signal',
                                                  "untitled",
                                                  filefilter)[0]
        if self._model.wpathsignal:
            self.save_channels()


    def get_rpathpeaks(self):
        if not self._model.loaded:
            self._model.status = "Error: no data available."
            return

        if self._model.peaks is not None:
            self._model.status = "Error: peaks already in memory."
            return

        self._model.rpathpeaks = getOpenFileName(None,
                                                 'Choose your peaks',
                                                 "\\home")[0]
        if self._model.rpathpeaks:
            self.read_peaks()


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
                                                         "\\home")


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
                if not value:
                    continue
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
                                                         "\\home")


    def batch_processor(self):
        """
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
        """
        self.get_wpathpeaks()
        self.get_wpathstats()

        if self._model.wdirstats is None:
            self._model.status = "No statistics selected for saving."
            return

        self._model.status = "Processing files."
        self._model.plotting = False

        self.batchmethods = [self.read_channels, self.find_peaks,
                             self.autocorrect_peaks, self.calculate_stats,
                             self.save_stats]
        if self._model.wdirpeaks:    # optional
            self.batchmethods.append(self.save_peaks)

        self.iterbatchmethods = iter(self.batchmethods)

        self._model.progress_changed.connect(self.dispatcher)

        self.dispatcher(1)    # initiate processing


    def dispatcher(self, progress):
        """
        Start with first method on first file. As soon as one method has
        finished, (indicated by emission of progress_changed), execute next
        method. Once all methods are executed, go to the next file and start
        cycling through methods again.
        """
        if not progress:
            return

        try:
            batchmethod = next(self.iterbatchmethods)

        except StopIteration:    # all methods finished on current file
            self._model.reset()    # reset for new file
            self.iterbatchmethods = iter(self.batchmethods)    # restart cycling through batch methods
            batchmethod = next(self.iterbatchmethods)
            self._model.fpaths.pop(0)    # go to next file

            if not self._model.fpaths:    # all files have been processed
                self._model.plotting = True
                self._model.progress_changed.disconnect(self.dispatcher)
                self._model.wdirpeaks = None
                self._model.wdirstats = None
                return

        if batchmethod.__name__ == "read_channels":    # set paths prior to calling first method
            fname = Path(self._model.fpaths[0]).stem
            self._model.wpathstats = Path(self._model.wdirstats).joinpath(f"{fname}_stats.csv")
            if self._model.wdirpeaks:    # optional
                self._model.wpathpeaks = Path(self._model.wdirpeaks).joinpath(f"{fname}_peaks.csv")

        batchmethod()


    @threaded
    def read_channels(self):
        self._model.status = "Loading file."

        path = self._model.fpaths[0]
        filetype = self._model.filetype
        readfunc = readfuncs[filetype]

        biosignalinfo = (self._model.customheader if filetype == "Custom"
                         else self._model.signalchan)
        biosignal = readfunc(path, biosignalinfo, channeltype="signal")

        if biosignal["error"]:
            self._model.status = biosignal["error"]
            self._model.customheader = dict.fromkeys(self._model.customheader, None)    # for custom files also reset header
            self._model.set_filetype(None)    # reset file type
            return

        # Important to set seconds PRIOR TO signal, otherwise plotting
        # behaves unexpectadly (since plotting is triggered as soon as
        # signal changes).
        self._model.sfreq = biosignal["sfreq"]    # in case of custom file, sfreq is now taken over from customheader
        self._model.sec = biosignal["sec"]
        self._model.signal = biosignal["signal"]
        self._model.loaded = True
        self._model.rpathsignal = path

        markerinfo = (self._model.customheader if filetype == "Custom"
                      else self._model.markerchan)
        if filetype == "Custom" and markerinfo["markeridx"] is None:
            return
        if markerinfo == "none":
            return
        marker = readfunc(path, markerinfo, channeltype="marker")

        if marker["error"]:
            self._model.status = marker["error"]
            return

        self._model.sfreqmarker = marker["sfreq"]    # only not set to None in case of EDF
        self._model.marker = marker["signal"]


    @threaded
    def segment_signal(self):
        self._model.status = "Segmenting signal."
        # Convert from seconds to samples.
        begsamp = int(np.rint(self._model.segment[0] * self._model.sfreq))
        endsamp = int(np.rint(self._model.segment[1] * self._model.sfreq))
        siglen = endsamp - begsamp
        sec = np.linspace(0, siglen / self._model.sfreq, siglen)
        self._model.sec = sec
        self._model.signal = self._model.signal[begsamp:endsamp]

        if self._model.peaks is not None:
            peakidcs = np.where((self._model.peaks > begsamp) &
                                (self._model.peaks < endsamp))[0]
            peaks = self._model.peaks[peakidcs]
            peaks -= begsamp
            self._model.peaks = peaks
        if self._model.periodintp is not None:
            self._model.periodintp = self._model.periodintp[begsamp:endsamp]
        if self._model.rateintp is not None:
            self._model.rateintp = self._model.rateintp[begsamp:endsamp]
        if self._model.tidalampintp is not None:
            self._model.tidalampintp = self._model.tidalampintp[begsamp:
                                                                endsamp]

        # Since the marker channel might be sampled at a different rate in EDF
        # data, treat it separately.
        if self._model.marker is None:
            return
        if self._model.filetype == "EDF":
            sfreq = self._model.sfreqmarker
        else:
            sfreq = self._model.sfreq
        begsamp = int(np.rint(self._model.segment[0] * sfreq))
        endsamp = int(np.rint(self._model.segment[1] * sfreq))
        self._model.marker = self._model.marker[begsamp:endsamp]
        if endsamp - begsamp <= 1:
            self._model.status = "Error: There are not enough samples in the" \
                                 " marker channel to resolve this segment."

    @threaded
    def save_channels(self):
        self._model.status = "Saving signal."

        if self._model.segment is None:
            self._model.status = "Error: Cannot save non-segmented file."
            return

        filetype = self._model.filetype
        writefunc = writefuncs[filetype]

        headerinfo = (self._model.customheader if filetype == "Custom"
                      else self._model.sfreq)

        status = writefunc(self._model.rpathsignal, self._model.wpathsignal,
                           self._model.segment, headerinfo)    # only write_edf() returns status, other write functions return None (no return)

        if status:
            self._model.status = status

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
            peaks = peaks.to_numpy()
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
        if not self._model.loaded:
            self._model.status = "Error: no data available."
            return
        if self._model.peaks is not None:
            self._model.status = "Error: peaks already in memory."
            return
        peakfunc = peakfuncs[self._model.modality]
        self._model.peaks = peakfunc(self._model.signal,
                                     self._model.sfreq)


    @threaded
    def autocorrect_peaks(self):
        if self._model.modality == "RESP":
            self._model.status = "Only ECG or PPG peaks can be auto-corrected."
            return
        if self._model.peaks is None:
            self._model.status = "Error: no peaks available."
            return
        if (self._model.batchmode == "multiple files" and
            not self._model.correctbatchpeaks):
            return
        self._model.status = f"Auto-correcting {self._model.modality} peaks"
        self._model.peaks = correct_peaks(self._model.peaks, self._model.sfreq)


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
        if self._model.modality != "RESP":
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
        if self._model.modality in ["ECG", "PPG"]:
            (self._model.periodintp,
             self._model.rateintp) = heart_period(peaks=self._model.peaks,
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
        savekeys = [key for key, value in self._model.savestats.items() if value]
        savearray = np.zeros((self._model.signal.size, len(savekeys)))
        for i, key in enumerate(savekeys):
            if key == 'period':
                savearray[:, i] = self._model.periodintp
            if key == 'rate':
                savearray[:, i] = self._model.rateintp
            if key == 'tidalamp':
                savearray[:, i] = self._model.tidalampintp
        savearray = pd.DataFrame(savearray)
        savearray.to_csv(self._model.wpathstats, index=False, header=savekeys,
                         float_format="%.4f")
