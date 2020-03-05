# -*- coding: utf-8 -*-

import numpy as np
from os import path
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty


class Model(QObject):

    # costum signals
    signal_changed = pyqtSignal(object)
    peaks_changed = pyqtSignal(object)
    marker_changed = pyqtSignal(object)
    segment_changed = pyqtSignal(object)
    # makes sure that the emitted stats signal has the same length as self._sec
    period_changed = pyqtSignal(object)
    rate_changed = pyqtSignal(object)
    tidalamp_changed = pyqtSignal(object)
    path_changed = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    progress_changed = pyqtSignal(int)
    model_reset = pyqtSignal()

    # the following model attributes aren't slots, but are set by controller
    # methods

    @property
    def savestats(self):
        return self._savestats

    @savestats.setter
    def savestats(self, value):
        self._savestats = value

    @property
    def signal(self):
        return self._signal

    @signal.setter
    def signal(self, value):
        self._signal = value
        # check if attribute is reset to None, in that case do not emit its
        # signal, also do not emit signal if plotting is not desired (e.g.,
        # during batch processing)
        if value is not None and self.plotting:
            self.signal_changed.emit(value)

    @property
    def peaks(self):
        return self._peaks

    @peaks.setter
    def peaks(self, value):

        if isinstance(value, np.ndarray) and value.size > 1:
            self._peaks = value
        if value is not None and self.plotting:
            self.peaks_changed.emit(value)

    @property
    def period(self):
        return self._period

    @period.setter
    def period(self, value):
        self._period = value

    @property
    def periodintp(self):
        return self._periodintp

    @periodintp.setter
    def periodintp(self, value):
        self._periodintp = value
        if value is not None and self.plotting:
            self.period_changed.emit(value)

    @property
    def rateintp(self):
        return self._rateintp

    @rateintp.setter
    def rateintp(self, value):
        self._rateintp = value
        if value is not None and self.plotting:
            self.rate_changed.emit(value)

    @property
    def tidalampintp(self):
        return self._tidalampintp

    @tidalampintp.setter
    def tidalampintp(self, value):
        self._tidalampintp = value
        if value is not None and self.plotting:
            self.tidalamp_changed.emit(value)

    @property
    def sec(self):
        return self._sec

    @sec.setter
    def sec(self, value):
        self._sec = value

    @property
    def marker(self):
        return self._marker

    @marker.setter
    def marker(self, value):
        self._marker = value
        if value is not None and self.plotting:
            # In case the marker channel is sampled at a different rate than
            # signak channel (possible for EDF format), generate the seconds
            # vector for the markers on the spot.
            if len(value) != len(self._signal):
                sec = np.linspace(0, len(value) / self.sfreqmarker,
                                  len(value))
            else:
                sec = self._sec
            self.marker_changed.emit([sec, value])

    @property
    def rpathsignal(self):
        return self._rpathsignal

    @rpathsignal.setter
    def rpathsignal(self, value):
        self._rpathsignal = value
        if value is not None:
            _, displaypath = path.split(value)
            self.path_changed.emit(displaypath)

    @property
    def wpathsignal(self):
        return self._wpathsignal

    @wpathsignal.setter
    def wpathsignal(self, value):
        self._wpathsignal = value

    @property
    def fpaths(self):
        return self._fpaths

    @fpaths.setter
    def fpaths(self, value):
        self._fpaths = value

    @property
    def wpathpeaks(self):
        return self._wpathpeaks

    @wpathpeaks.setter
    def wpathpeaks(self, value):
        self._wpathpeaks = value

    @property
    def rpathpeaks(self):
        return self._rpathpeaks

    @rpathpeaks.setter
    def rpathpeaks(self, value):
        self._rpathpeaks = value

    @property
    def wdirpeaks(self):
        return self._wdirpeaks

    @wdirpeaks.setter
    def wdirpeaks(self, value):
        self._wdirpeaks = value

    @property
    def wpathstats(self):
        return self._wpathstats

    @wpathstats.setter
    def wpathstats(self, value):
        self._wpathstats = value

    @property
    def wdirstats(self):
        return self._wdirstats

    @wdirstats.setter
    def wdirstats(self, value):
        self._wdirstats = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        if value is not None:
            self.status_changed.emit(value)

    @property
    def filetype(self):
        return self._filetype

    @filetype.setter
    def filetype(self, value):
        self._filetype = value

    # the following model attributes are slots that are connected to signals
    # from the view or controller

    @pyqtProperty(object)
    def segment(self):
        return self._segment

    @pyqtSlot(object)
    def set_segment(self, values):

        self._segment = None

        if values[0] and values[1]:
            begsamp = float(values[0])
            endsamp = float(values[1])
            evalarray = [np.asarray([begsamp, endsamp]) >= self._sec[0],
                         np.asarray([begsamp, endsamp]) <= self._sec[-1]]
            # Ensure that values are inside temporal bounds.
            if not np.all(evalarray):
                self.status_changed.emit(f"Error: Invalid segment {begsamp} - "
                                         f"{endsamp}.")
                self.segment_changed.emit(self._segment)
                return
            # Ensure that order is valid.
            if begsamp > endsamp:
                self.status_changed.emit(f"Error: Invalid segment {begsamp} - "
                                         f"{endsamp}.")
                self.segment_changed.emit(self._segment)
                return
            # Ensure that the segment has a minimum duration of 5
            # seconds. If this is not the case algorithms break
            # (convolution kernel length etc.).
            elif endsamp - begsamp < 5:
                self.status_changed.emit(f"Please select a segment longer than "
                                         f"5 seconds. The current segment is "
                                         f"{endsamp - begsamp} seconds long.")
                self.segment_changed.emit(self._segment)
                return
            self.status_changed.emit(f"Valid segment {begsamp} - {endsamp}.")
            self._segment = [begsamp, endsamp]
            self.segment_changed.emit(self._segment)

    @pyqtProperty(str)
    def batchmode(self):
        return self._batchmode

    @pyqtSlot(str)
    def set_batchmode(self, value):
        self._batchmode = value

    @pyqtProperty(str)
    def markerchan(self):
        return self._markerchan

    @pyqtSlot(str)
    def set_markerchan(self, value):
        self._markerchan = value

    @pyqtProperty(str)
    def signalchan(self):
        return self._signalchan

    @pyqtSlot(str)
    def set_signalchan(self, value):
        self._signalchan = value

    @pyqtProperty(str)
    def modality(self):
        return self._modality

    @pyqtSlot(str)
    def set_modality(self, value):
        self._modality = value

    @pyqtProperty(int)
    def peakseditable(self):
        return self._peakseditable

    @pyqtSlot(int)
    def set_peakseditable(self, value):
        if value == 2:
            self._peakseditable = True
        elif value == 0:
            self._peakseditable = False

    @pyqtProperty(int)
    def savebatchpeaks(self):
        return self._savebatchpeaks

    @pyqtSlot(int)
    def set_savebatchpeaks(self, value):
        if value == 2:
            self._savebatchpeaks = True
        elif value == 0:
            self._savebatchpeaks = False

    @pyqtSlot(int)
    def progress(self, value):
        self._progress = value
        if value is not None:
            self.progress_changed.emit(value)


    def __init__(self):
        super().__init__()

        self._signal = None
        self._peaks = None
        self._periodintp = None
        self._rateintp = None
        self._tidalampintp = None
        self._sec = None
        self._marker = None
        self._segment = None
        self._status = None
        self._progress = None
        self.sfreq = None
        self.sfreqmarker = None
        self.loaded = False
        self.plotting = True
        self._signalchan = None
        self._markerchan = None
        self._modality = None
        self._batchmode = None
        self._peakseditable = False
        self._fpaths = None
        self._wpathpeaks = None
        self._wdirpeaks = None
        self._rpathpeaks = None
        self._wpathsignal = None
        self._rpathsignal = None
        self._wpathstats = None
        self._wdirstats = None
        self._savebatchpeaks = False
        self._savestats = {"period":False, "rate":False, "tidalamp":False}
        self._filetype = None

    def reset(self):
        self._signal = None
        self._peaks = None
        self._periodintp = None
        self._rateintp = None
        self._tidalampintp = None
        self._sec = None
        self._marker = None
        self._segment = None
        self._status = None
        self._progress = None
        self.sfreq = None
        self.sfreqmarker = None
        self.loaded = False
        self._wpathpeaks = None
        self._rpathpeaks = None
        self._wpathsignal = None
        self._rpathsignal = None
        self._wpathstats = None
        self._filetype = None
        # don't reset attributes that aren't ideosyncratic to the dataset
        # (e.g., channels, batchmode, savestats etc.); also don't reset
        # attributes that must be permanently accessible during batch
        # processing (e.g., fpaths, wdirpeaks, wdirstats)
        self.model_reset.emit()
