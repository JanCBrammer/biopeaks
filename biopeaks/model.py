# -*- coding: utf-8 -*-
"""Model component of the MVC implementation.

Stores the current state of the application. Receives state updates from the
View or Controller and informs View about changes in state.
"""

import numpy as np
from pathlib import Path
from PySide2.QtCore import QObject, Signal, Slot, Property


class Model(QObject):

    signal_changed = Signal(object)
    peaks_changed = Signal(object)
    marker_changed = Signal(object)
    segment_changed = Signal(object)
    # makes sure that the emitted stats signal has the same length as self._sec
    period_changed = Signal(object)
    rate_changed = Signal(object)
    tidalamp_changed = Signal(object)
    path_changed = Signal(str)
    status_changed = Signal(str)
    progress_changed = Signal(int)
    model_reset = Signal()

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
        self._sfreq = None
        self._sfreqmarker = None
        self._loaded = False
        self._plotting = True
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
        self._correctbatchpeaks = False
        self._savestats = {"period": False, "rate": False, "tidalamp": False}
        self._filetype = None
        self._customheader = {"signalidx": None, "markeridx": None,
                              "skiprows": None, "sfreq": None, "separator": None}

    def reset(self):
        """
        Don't reset attributes that aren't ideosyncratic to the dataset (e.g.,
        channels, batchmode, savestats etc.). Also don't reset attributes that
        must be permanently accessible during batch processing (e.g., fpaths,
        wdirpeaks, wdirstats, filetype, customheader).
        """
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
        self._sfreq = None
        self._sfreqmarker = None
        self._loaded = False
        self._wpathpeaks = None
        self._rpathpeaks = None
        self._wpathsignal = None
        self._rpathsignal = None
        self._wpathstats = None

        self.model_reset.emit()

    # The following attributes are set by the View or Controller (i.e., they
    # are not slots connected to a signal).

    @property
    def plotting(self):
        return self._plotting

    @plotting.setter
    def plotting(self, value):    # Controller
        self._plotting = value

    @property
    def loaded(self):
        return self._loaded

    @loaded.setter
    def loaded(self, value):    # Controller
        self._loaded = value

    @property
    def sfreqmarker(self):
        return self._sfreqmarker

    @sfreqmarker.setter
    def sfreqmarker(self, value):    # Controller
        self._sfreqmarker = value

    @property
    def sfreq(self):
        return self._sfreq

    @sfreq.setter
    def sfreq(self, value):    # Controller
        self._sfreq = value

    @property
    def savestats(self):
        return self._savestats

    @savestats.setter
    def savestats(self, value):    # View
        self._savestats = value

    @property
    def signal(self):
        return self._signal

    @signal.setter
    def signal(self, value):    # Controller
        self._signal = value
        # Check if attribute is reset to None, in that case do not emit its
        # signal. Also do not emit signal if plotting is not desired (e.g.,
        # during batch processing).
        if value is not None and self._plotting:
            self.signal_changed.emit(value)

    @property
    def peaks(self):
        return self._peaks

    @peaks.setter
    def peaks(self, value):    # Controller

        if isinstance(value, np.ndarray) and value.size > 1:
            self._peaks = value
        if value is not None and self._plotting:
            self.peaks_changed.emit(value)

    @property
    def periodintp(self):
        return self._periodintp

    @periodintp.setter
    def periodintp(self, value):    # Controller
        self._periodintp = value
        if value is not None and self._plotting:
            self.period_changed.emit(value)

    @property
    def rateintp(self):
        return self._rateintp

    @rateintp.setter
    def rateintp(self, value):    # Controller
        self._rateintp = value
        if value is not None and self._plotting:
            self.rate_changed.emit(value)

    @property
    def tidalampintp(self):
        return self._tidalampintp

    @tidalampintp.setter
    def tidalampintp(self, value):    # Controller
        self._tidalampintp = value
        if value is not None and self._plotting:
            self.tidalamp_changed.emit(value)

    @property
    def sec(self):
        return self._sec

    @sec.setter
    def sec(self, value):    # Controller
        self._sec = value

    @property
    def marker(self):
        return self._marker

    @marker.setter
    def marker(self, value):    # Controller
        self._marker = value
        if value is not None and self._plotting:
            # In case the marker channel is sampled at a different rate than
            # signal channel (possible for EDF format), generate the seconds
            # vector for the markers on the spot.
            if len(value) != len(self._signal):
                sec = np.linspace(0, len(value) / self._sfreqmarker,
                                  len(value))
            else:
                sec = self._sec
            self.marker_changed.emit([sec, value])

    @property
    def rpathsignal(self):
        return self._rpathsignal

    @rpathsignal.setter
    def rpathsignal(self, value):    # Controller
        self._rpathsignal = value
        if value is not None:
            displaypath = Path(value).name
            self.path_changed.emit(displaypath)

    @property
    def wpathsignal(self):
        return self._wpathsignal

    @wpathsignal.setter
    def wpathsignal(self, value):    # Controller
        self._wpathsignal = value

    @property
    def fpaths(self):
        return self._fpaths

    @fpaths.setter
    def fpaths(self, value):    # Controller
        self._fpaths = value

    @property
    def wpathpeaks(self):
        return self._wpathpeaks

    @wpathpeaks.setter
    def wpathpeaks(self, value):    # Controller
        self._wpathpeaks = value

    @property
    def rpathpeaks(self):
        return self._rpathpeaks

    @rpathpeaks.setter
    def rpathpeaks(self, value):    # Controller
        self._rpathpeaks = value

    @property
    def wdirpeaks(self):
        return self._wdirpeaks

    @wdirpeaks.setter
    def wdirpeaks(self, value):    # Controller
        self._wdirpeaks = value

    @property
    def wpathstats(self):
        return self._wpathstats

    @wpathstats.setter
    def wpathstats(self, value):    # Controller
        self._wpathstats = value

    @property
    def wdirstats(self):
        return self._wdirstats

    @wdirstats.setter
    def wdirstats(self, value):    # Controller
        self._wdirstats = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):    # View, Controller
        self._status = value
        if value is not None:
            self.status_changed.emit(value)

    @property
    def customheader(self):
        return self._customheader

    @customheader.setter
    def customheader(self, value):    # View, Controller
        self._customheader = value

    # The following attributes are slots that are connected to signals
    # from the View or Controller.

    @Property(object)
    def filetype(self):
        return self._filetype

    @Slot(object)
    def set_filetype(self, value):    # View, Controller
        self._filetype = value

    @Property(object)
    def segment(self):
        return self._segment

    @Slot(object)
    def set_segment(self, values):    # View

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
            # Ensure that the segment has a minimum duration of 5 seconds. If
            # this is not the case algorithms break (convolution kernel length
            # etc.).
            elif endsamp - begsamp < 5:
                self.status_changed.emit("Please select a segment longer than "
                                         "5 seconds. The current segment is "
                                         f"{endsamp - begsamp} seconds long.")
                self.segment_changed.emit(self._segment)
                return
            self.status_changed.emit(f"Valid segment {begsamp} - {endsamp}.")
            self._segment = [begsamp, endsamp]
            self.segment_changed.emit(self._segment)

    @Property(str)
    def batchmode(self):
        return self._batchmode

    @Slot(str)
    def set_batchmode(self, value):    # View, Controller
        self._batchmode = value

    @Property(str)
    def markerchan(self):
        return self._markerchan

    @Slot(str)
    def set_markerchan(self, value):    # View
        self._markerchan = value

    @Property(str)
    def signalchan(self):
        return self._signalchan

    @Slot(str)
    def set_signalchan(self, value):    # View
        self._signalchan = value

    @Property(str)
    def modality(self):
        return self._modality

    @Slot(str)
    def set_modality(self, value):    # View
        self._modality = value

    @Property(int)
    def peakseditable(self):
        return self._peakseditable

    @Slot(int)
    def set_peakseditable(self, value):    # View
        if value == 2:
            self._peakseditable = True
        elif value == 0:
            self._peakseditable = False

    @Property(int)
    def savebatchpeaks(self):
        return self._savebatchpeaks

    @Slot(int)
    def set_savebatchpeaks(self, value):    # View
        if value == 2:
            self._savebatchpeaks = True
        elif value == 0:
            self._savebatchpeaks = False

    @Property(int)
    def correctbatchpeaks(self):
        return self._correctbatchpeaks

    @Slot(int)
    def set_correctbatchpeaks(self, value):    # View
        if value == 2:
            self._correctbatchpeaks = True
        elif value == 0:
            self._correctbatchpeaks = False

    @Slot(int)
    def progress(self, value):    # Controller
        self._progress = value
        if value is not None:
            self.progress_changed.emit(value)
