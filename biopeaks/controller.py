# -*- coding: utf-8 -*-
"""Controller component of the MVC application."""

import sys
import threading
import pandas as pd
import numpy as np
from functools import wraps
from biopeaks.heart import ecg_peaks, ppg_peaks, correct_peaks, heart_stats
from biopeaks.resp import ensure_peak_trough_alternation, resp_extrema, resp_stats
from biopeaks.io_utils import (read_custom, read_opensignals, read_edf,
                               write_custom, write_opensignals, write_edf)
from pathlib import Path
from scipy.signal import find_peaks as find_peaks_scipy
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtWidgets import QFileDialog
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

running_coverage = "coverage" in sys.modules
if running_coverage:
    print("Enabling Worker tracing during testing with coverage.")


class WorkerSignal(QObject):
    """Signal to be used in QRunnable.

    Custom signals can only be defined on objects derived from QObject. Since
    QRunnable is not derived from QObject, QRunnable cannot be extended with
    signals directly.

    Attributes
    ----------
    progress : Signal
        Progress signal to be emitted by QRunnable.

    """

    progress = Signal(int)


class Worker(QRunnable):
    """Execute a Controller method."""

    def __init__(self, method, controller, **kwargs):
        """Initiate with Controller instance, and -method, as well as signal.

        Parameters
        ----------
        method : method
            The Controller method to be executed.
        controller : QObject
            The Controller instance.
        """
        super(Worker, self).__init__()
        self.method = method
        self.kwargs = kwargs
        self.signals = WorkerSignal()
        self.controller = controller

    def run(self):
        """Execute method."""
        self.signals.progress.emit(0)
        if running_coverage:
            sys.settrace(threading._trace_hook)
        self.method(self.controller, **self.kwargs)
        self.signals.progress.emit(1)


def threaded(method):
    """Execute a Controller method in a thread.

    This decorator executes a Controller method in a separate thread that is
    managed by QThreadPool. Note that the Controller instance (i.e., self) is
    automatically passed in as first argument to threader.

    Parameters
    ----------
    method : method
        A Controller method.
    """
    @wraps(method)
    def threader(controller, **kwargs):
        worker = Worker(method, controller, **kwargs)
        worker.signals.progress.connect(controller._model.progress)
        controller.threadpool.start(worker)
    return threader


class Controller(QObject):
    """Controller component of the MVC application.

    Manipulates the state of the Model based on user input from the View.

    """

    def __init__(self, model):
        """Initiate with Model and threadpool.

        Parameters
        ----------
        model : QObject
            Model component of the MVC application.
        """
        super().__init__()

        self._model = model
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)

    def load_channels(self):
        """Load channels from file.

        Open a file dialog and let user load one or multiple files containing
        a biosignal and/or marker channel. Depending on the configuration,
        either load single dataset or initiate batch processing with multiple
        datasets.
        """
        self._model.fpaths = getOpenFileNames(None, 'Choose your data',
                                              "\\home")[0]
        if not self._model.fpaths:
            self._model.set_filetype(None)    # reset file type
            self._model.customheader = dict.fromkeys(self._model.customheader, None)    # for custom files also reset header
            return
        if (self._model.batchmode == 'multiple files' and
            len(self._model.fpaths) >= 1):
            self._batch_processor()
        elif (self._model.batchmode == 'single file' and
              len(self._model.fpaths) == 1):
            self._model.reset()
            self._load_channels()

    def save_channels(self):
        """Save channels to file.

        Open a file dialog and let user save a file containing a biosignal
        and/or marker channel.
        """
        if not self._model.loaded:
            self._model.status = "Error: no data available."
            return
        filefilter = f"{self._model.filetype} (*{Path(self._model.rpathsignal).suffix})"
        self._model.wpathsignal = getSaveFileName(None, 'Save signal',
                                                  "untitled",
                                                  filefilter)[0]
        if self._model.wpathsignal:
            self._save_channels()

    def load_peaks(self):
        """Load extrema from file.

        Open a file dialog and let user load a file containing extrema.
        """
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
            self._load_peaks()

    def save_peaks(self):
        """Save extrema to file.

        Open a file dialog and let user save a file containing the extrema.
        """
        if self._model.batchmode == 'single file':
            if self._model.peaks is None:
                self._model.status = "Error: no peaks available."
                return
            self._model.wpathpeaks = getSaveFileName(None, 'Save peaks',
                                                     'untitled.csv',
                                                     'CSV (*.csv)')[0]
            if self._model.wpathpeaks:
                self._save_peaks()
        elif self._model.batchmode == 'multiple files':
            if not self._model.savebatchpeaks:
                return
            self._model.wdirpeaks = getExistingDirectory(None,
                                                         'Choose a directory '
                                                         'for saving the '
                                                         'peaks',
                                                         "\\home")

    def save_stats(self):
        """Save statistics to file.

        Open a file dialog and let user save a file containing the statistics.
        """
        nitems = sum(self._model.savestats.values())    # count number of items selected for saving
        if nitems < 1:
            self._model.status = "Error: no statistics selected for saving."
            return
        if self._model.batchmode == 'single file':
            for key, value in self._model.savestats.items():
                if not value:    # check is there is data for the selected stats
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
                self._save_stats()

        elif self._model.batchmode == 'multiple files':
            self._model.wdirstats = getExistingDirectory(None,
                                                         'Choose a directory '
                                                         'for saving the '
                                                         'statistics',
                                                         "\\home")

    def edit_peaks(self, key_event):
        """Edit extrema based on cursor position.

        Editing is based on the current cursor position in the data's
        x-coordinates (i.e., seconds). If the user pressed the "d" key, delete
        the local extreme that is closest to the current cursor position.
        If the user pressed the "a" key, search the local extreme that is
        closest to the current cursor position and add it to the extrema.

        Parameters
        ----------
        key_event : KeyEvent
            Event containing information about the current key press and cursor
            position in data coordinates.

        See Also
        --------
        matplotlib.backend_bases.KeyEvent
        """
        if not self._model.peakseditable:
            return
        if self._model.peaks is None:
            return
        cursor = int(np.rint(key_event.xdata * self._model.sfreq))
        extend = int(np.rint(self._model.sfreq * 0.1))
        searchrange = np.arange(cursor - extend, cursor + extend)    # search peak in a window of 200 msec, centered on selected x coordinate of cursor position
        retainidcs = np.logical_and(searchrange > 0,
                                    searchrange < self._model.signal.size)    # make sure that searchrange doesn't extend beyond signal
        searchrange = searchrange[retainidcs]
        if key_event.key == 'd':
            peakidx = np.argmin(np.abs(self._model.peaks - cursor))
            if np.any(searchrange == self._model.peaks[peakidx]):    # only delete peaks that are within search range
                self._model.peaks = np.delete(self._model.peaks, peakidx)
        elif key_event.key == 'a':
            searchsignal = self._model.signal[searchrange]
            locmax, _ = find_peaks_scipy(searchsignal)    # use Scipy's find_peaks to also detect local extrema that are plateaus
            locmin, _ = find_peaks_scipy(searchsignal * -1)
            locext = np.concatenate((locmax, locmin))
            locext.sort(kind='mergesort')
            if locext.size < 1:
                return
            peakidx = np.argmin(np.abs(searchrange[locext] - cursor))
            newpeak = searchrange[0] + locext[peakidx]
            if np.all(self._model.peaks != newpeak):    # only add new peak if it doesn't exist already
                insertidx = np.searchsorted(self._model.peaks, newpeak)
                self._model.peaks = np.insert(self._model.peaks, insertidx,
                                              [newpeak])

    @threaded
    def segment_dataset(self):
        """Segment the dataset.

        Limit the dataset (biosignal and/or marker -channel as well as extrema)
        to the user-selected segment. I.e., retain the portion of the dataset
        that corresponds to the segment and discard the portion(s) outside the
        segment.
        """
        self._model.status = "Segmenting signal."
        begsamp = int(np.rint(self._model.segment[0] * self._model.sfreq))    # convert from seconds to samples
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

        if self._model.marker is None:
            return
        if self._model.filetype == "EDF":    # since marker channel might be sampled at a different rate segment it separately
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
    def find_peaks(self):
        """Find extrema using modality-specific algorithms."""
        self._model.status = "Finding peaks."
        if not self._model.loaded:
            self._model.status = "Error: no data available."
            return
        if self._model.peaks is not None:
            self._model.status = "Error: peaks already in memory."
            return
        peakfunc = peakfuncs[self._model.modality]
        self._model.peaks = peakfunc(self._model.signal, self._model.sfreq)

    @threaded
    def autocorrect_peaks(self):
        """Auto-correct cardiac extrema."""
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

    @threaded
    def calculate_stats(self):
        """Calculate modality-specific statistics."""
        self._model.status = "Calculating statistics."
        if (self._model.peaks is None) or (np.size(self._model.peaks) < 2):
            self._model.status = "Error: no peaks available."
            return
        if self._model.modality in ["ECG", "PPG"]:
            (self._model.periodintp,
             self._model.rateintp) = heart_stats(peaks=self._model.peaks,
                                                 sfreq=self._model.sfreq,
                                                 nsamp=self._model.signal.size)
        elif self._model.modality == 'RESP':
            (self._model.periodintp,
             self._model.rateintp,
             self._model.tidalampintp) = resp_stats(extrema=self._model.peaks,
                                                    signal=self._model.signal,
                                                    sfreq=self._model.sfreq)

    def _batch_processor(self):
        """Process a set of files.

        Initiates batch processing. After initiation, _dispatcher handles the
        sequential execution of methods that are called on each file of the
        batch. _dispatcher starts with first method on first file. As soon as
        one method has finished, (indicated by emission of progress_changed),
        it executes next method. Once all methods are executed, it proceeds
        with the next file and starts cycling through methods again.
        This slightly convoluted way of handling a batch is necessary for the
        following reason. Since each method is run in a thread, looping over
        the files of a batch (as opposed to handling method execution with the
        _dispatcher) will lead to ill-defined states of the model. _dispatcher
        ensures strictly sequential execution of methods (although limiting
        the threadpools capacity to one thread at a time should achieve the
        same). Also, busy-waiting can be avoided by using _dispatcher.
        Plotting is disabled during batch processing (model.plotting),
        since matplotlib cannot update the canvas fast enough when multiple
        plotting operations must be executed in rapid succession (e.g., when
        small files are processed). The user can still get an impression of the
        progress since the current file path is displayed.
        """
        self.save_peaks()
        self.save_stats()

        if self._model.wdirstats is None:
            self._model.status = "No statistics selected for saving."
            return

        self._model.status = "Processing files."
        self._model.plotting = False

        self.batchmethods = [self._load_channels, self.find_peaks,
                             self.autocorrect_peaks, self.calculate_stats,
                             self._save_stats]
        if self._model.wdirpeaks:    # optional
            self.batchmethods.append(self._save_peaks)

        self.iterbatchmethods = iter(self.batchmethods)

        self._model.progress_changed.connect(self._dispatcher)

        self._dispatcher(1)    # initiate processing

    def _dispatcher(self, progress):
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
                self._model.progress_changed.disconnect(self._dispatcher)
                self._model.wdirpeaks = None
                self._model.wdirstats = None
                return

        if batchmethod.__name__ == "_load_channels":    # set paths prior to calling first method
            fname = Path(self._model.fpaths[0]).stem
            self._model.wpathstats = Path(self._model.wdirstats).joinpath(f"{fname}_stats.csv")
            if self._model.wdirpeaks:    # optional
                self._model.wpathpeaks = Path(self._model.wdirpeaks).joinpath(f"{fname}_peaks.csv")

        batchmethod()

    @threaded
    def _load_channels(self):
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

        self._model.sfreq = biosignal["sfreq"]    # in case of custom file, sfreq is now taken over from customheader
        self._model.sec = biosignal["sec"]    # set seconds prior to signal, otherwise plotting in View behaves unexpectedly (since plotting is triggered as soon as signal changes)
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
    def _save_channels(self):
        self._model.status = "Saving signal."

        if self._model.segment is None:
            self._model.status = "Error: Cannot save non-segmented file."
            return

        filetype = self._model.filetype
        writefunc = writefuncs[filetype]

        headerinfo = (self._model.customheader if filetype == "Custom"
                      else self._model.sfreq)

        status = writefunc(self._model.rpathsignal, self._model.wpathsignal,
                           self._model.segment, headerinfo)    # only io_utils.write_edf returns status, other write functions return None (no return)

        if status:
            self._model.status = status

    @threaded
    def _load_peaks(self):
        self._model.status = "Loading peaks."
        dfpeaks = pd.read_csv(self._model.rpathpeaks)
        if dfpeaks.shape[1] == 1:
            peaks = dfpeaks['peaks'].copy()
            peaks = peaks * self._model.sfreq    # convert back to samples
            peaks = peaks.to_numpy()
            peaks = np.rint(peaks).astype(int)    # reshape to a format understood by plotting function (ndarray of int)
            self._model.peaks = peaks
        elif dfpeaks.shape[1] == 2:
            extrema = np.concatenate((dfpeaks['peaks'].copy(),
                                      dfpeaks['troughs'].copy()))
            sortidcs = extrema.argsort(kind='mergesort')
            extrema = extrema[sortidcs]
            extrema = extrema[~np.isnan(extrema)]    # remove NANs that may have been appended in case of odd number of extrema (see _save_peaks)
            extrema = np.rint(extrema * self._model.sfreq).astype(int)    # convert extrema from seconds to samples
            self._model.peaks = extrema

    @threaded
    def _save_peaks(self):
        self._model.status = "Saving peaks."

        if self._model.modality != "RESP":
            savearray = pd.DataFrame(self._model.peaks / self._model.sfreq)    # convert to seconds
            savearray.to_csv(self._model.wpathpeaks, index=False,
                             header=['peaks'])
        elif self._model.modality == 'RESP':
            extrema = ensure_peak_trough_alternation(self._model.peaks,
                                                     self._model.signal)    # work on local copy of extrema to avoid call to plotting function
            amps = self._model.signal[extrema]

            if np.remainder(extrema.size, 2) != 0:
                extrema = np.append(extrema, np.nan)    # pad extrema with NAN in order to ensure equal number of peaks and troughs

            if amps[0] > amps[1]:    # determine if series starts with peak or trough to be able to save peaks and troughs separately
                peaks = extrema[0:-1:2]
                troughs = extrema[1::2]
            elif amps[0] < amps[1]:
                peaks = extrema[1::2]
                troughs = extrema[0:-1:2]
            savearray = np.column_stack((peaks / self._model.sfreq,
                                         troughs / self._model.sfreq))    # make sure extrema are float: IMPORTANT, if seconds are saved as int, rounding errors (i.e. misplaced peaks) occur
            savearray = pd.DataFrame(savearray)
            savearray.to_csv(self._model.wpathpeaks, index=False,
                             header=['peaks', 'troughs'], na_rep='nan')

    @threaded
    def _save_stats(self):
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
