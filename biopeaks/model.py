# -*- coding: utf-8 -*-
"""Model component of the MVC application."""

import numpy as np
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, Property


class Model(QObject):
    """Model component of the MVC application.

    Stores the current state of the application. Receives state updates from
    the View or Controller and informs View about changes in state.

    Attributes
    ----------
    signal
    peaks
    periodintp
    rateintp
    tidalampintp
    sec
    marker
    segment
    status
    progress
    sfreq
    sfreqmarker
    loaded
    plotting
    signalchan
    markerchan
    modality
    batchmode
    peakseditable
    fpaths
    wpathpeaks
    wdirpeaks
    rpathpeaks
    wpathsignal
    rpathsignal
    wpathstats
    wdirstats
    savebatchpeaks
    correctbatchpeaks
    savestats
    filetype
    customheader
    signal_changed : Signal
        Notify View that the signal attribute changed.
    peaks_changed : Signal
        Notify View that the peaks attribute changed.
    marker_changed : Signal
        Notify View that the marker attribute changed.
    segment_changed : Signal
        Notify View that the segment attribute changed.
    period_changed : Signal
        Notify View that the period attribute changed.
    rate_changed : Signal
        Notify View that the rate attribute changed.
    tidalamp_changed : Signal
        Notify View that the tidalamp attribute changed.
    path_changed : Signal
        Notify View that the rpathsignal attribute changed.
    status_changed : Signal
        Notify View that the status attribute changed.
    progress_changed : Signal
        Notify View that the progress attribute changed.
    model_reset : Signal
        Notify View that attributes have been reset to their default value.
        See reset method.

    """

    signal_changed = Signal(object)
    peaks_changed = Signal(object)
    marker_changed = Signal(object)
    segment_changed = Signal(object)
    period_changed = Signal(object)
    rate_changed = Signal(object)
    tidalamp_changed = Signal(object)
    path_changed = Signal(str)
    status_changed = Signal(str)
    progress_changed = Signal(int)
    model_reset = Signal()

    def __init__(self):
        """Instantiate all attributes with their default value."""
        super().__init__()

        self._loaded = False
        self._peakseditable = False
        self._plotting = True
        self._savebatchpeaks = False
        self._correctbatchpeaks = False
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
        self._signalchan = None
        self._markerchan = None
        self._modality = None
        self._batchmode = None
        self._fpaths = None
        self._wpathpeaks = None
        self._wdirpeaks = None
        self._rpathpeaks = None
        self._wpathsignal = None
        self._rpathsignal = None
        self._wpathstats = None
        self._wdirstats = None
        self._filetype = None
        self._savestats = {"period": False, "rate": False, "tidalamp": False}
        self._customheader = {"signalidx": None, "markeridx": None,
                              "skiprows": None, "sfreq": None, "separator": None}

    def reset(self):
        """Reset attributes to their default value.

        Only resets attributes that are idiosyncratic to the current dataset.
        Doesn't reset attributes that must be permanently accessible during
        batch processing (e.g., fpaths, wdirpeaks, wdirstats, filetype,
        customheader).

        See Also
        --------
        controller.Controller._batch_processor
        """
        self._loaded = False
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
        """bool: Indicates whether or not View should be updated in response
        to state changes.

        Set by Controller. Default is True.
        """
        return self._plotting

    @plotting.setter
    def plotting(self, value):
        self._plotting = value

    @property
    def loaded(self):
        """bool: Indicates whether or not current dataset (signal and/or
        marker) has been loaded successfully.

        Set by Controller. Default is False.
        """
        return self._loaded

    @loaded.setter
    def loaded(self, value):
        self._loaded = value

    @property
    def sfreqmarker(self):
        """int: Sampling frequency of the marker channel.

        Set by Controller. Default is None.
        """
        return self._sfreqmarker

    @sfreqmarker.setter
    def sfreqmarker(self, value):
        self._sfreqmarker = value

    @property
    def sfreq(self):
        """int: Sampling frequency of the signal channel.

        Set by Controller. Default is None.
        """
        return self._sfreq

    @sfreq.setter
    def sfreq(self, value):
        self._sfreq = value

    @property
    def savestats(self):
        """dict of bool: Indicates which statistics (one of {"period", "rate",
        "tidalamp"}) to save.

        Set by View. Default is False for all statistics.
        """
        return self._savestats

    @savestats.setter
    def savestats(self, value):
        self._savestats = value

    @property
    def signal(self):
        """ndarray of float: Vector representing the biosignal channel
        (electrocardiogram, photoplethysmogram, or breathing).

        Set by Controller. Default is None.
        """
        return self._signal

    @signal.setter
    def signal(self, value):
        self._signal = value
        # Check if attribute is reset to None, in that case do not emit its
        # signal. Also do not emit signal if plotting is not desired (e.g.,
        # during batch processing).
        if value is not None and self._plotting:
            self.signal_changed.emit(value)

    @property
    def peaks(self):
        """ndarray of int: Vector representing the local extrema (R-peaks,
        systolic peaks, or breathing extrema).

        Set by Controller. Default is None.
        """
        return self._peaks

    @peaks.setter
    def peaks(self, value):
        if isinstance(value, np.ndarray) and value.size > 1:
            self._peaks = value
        if value is not None and self._plotting:
            self.peaks_changed.emit(value)

    @property
    def periodintp(self):
        """ndarray of float: Vector representing the instantaneous heart or
        breathing -period.

        The period is interpolated between peaks over the entire duration of
        signal. Set by Controller. Default is None.
        """
        return self._periodintp

    @periodintp.setter
    def periodintp(self, value):
        self._periodintp = value
        if value is not None and self._plotting:
            self.period_changed.emit(value)

    @property
    def rateintp(self):
        """ndarray of float: Vector representing the instantaneous heart or
        breathing -rate.

        The rate is interpolated between peaks over the entire duration of
        signal. Set by Controller. Default is None.
        """
        return self._rateintp

    @rateintp.setter
    def rateintp(self, value):
        self._rateintp = value
        if value is not None and self._plotting:
            self.rate_changed.emit(value)

    @property
    def tidalampintp(self):
        """ndarray of float: Vector representing the instantaneous tidal
        amplitude associated with a breathing signal.

        The tidal amplitude is interpolated between peaks over the entire
        duration of signal. Set by Controller. Default is None.
        """
        return self._tidalampintp

    @tidalampintp.setter
    def tidalampintp(self, value):
        self._tidalampintp = value
        if value is not None and self._plotting:
            self.tidalamp_changed.emit(value)

    @property
    def sec(self):
        """ndarray of float: Vector representing the seconds associated with
        each sample in signal and marker.

        Set by Controller. Default is None.
        """
        return self._sec

    @sec.setter
    def sec(self, value):
        self._sec = value

    @property
    def marker(self):
        """ndarray of float: Vector representing the marker channel.

        Set by Controller. Default is None.
        """
        return self._marker

    @marker.setter
    def marker(self, value):
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
        """str: File system location of the file containing the signal and
        marker to be loaded.

        Set by Controller. Default is None.
        """
        return self._rpathsignal

    @rpathsignal.setter
    def rpathsignal(self, value):
        self._rpathsignal = value
        if value is not None:
            displaypath = Path(value).name
            self.path_changed.emit(displaypath)

    @property
    def wpathsignal(self):
        """str: File system location of the file containing the segmented
        signal and marker.

        Set by Controller. Default is None.
        """
        return self._wpathsignal

    @wpathsignal.setter
    def wpathsignal(self, value):
        self._wpathsignal = value

    @property
    def fpaths(self):
        """list of str: Multiple instances of rpathsignal.

        Depending on the processing mode, either first element is selected as
        rpathsignal or all elements are used for batch procssing. Set by
        Controller. Default is None.
        """
        return self._fpaths

    @fpaths.setter
    def fpaths(self, value):
        self._fpaths = value

    @property
    def wpathpeaks(self):
        """str: File system location for saving the file containing the extrema.

        Set by Controller. Default is None.
        """
        return self._wpathpeaks

    @wpathpeaks.setter
    def wpathpeaks(self, value):
        self._wpathpeaks = value

    @property
    def rpathpeaks(self):
        """str: File system location of the file containing the extrema to be
        loaded.

        Set by Controller. Default is None.
        """
        return self._rpathpeaks

    @rpathpeaks.setter
    def rpathpeaks(self, value):
        self._rpathpeaks = value

    @property
    def wdirpeaks(self):
        """str: Directory for saving the files containing the extrema during
        batch processing.

        Set by Controller. Default is None.
        """
        return self._wdirpeaks

    @wdirpeaks.setter
    def wdirpeaks(self, value):
        self._wdirpeaks = value

    @property
    def wpathstats(self):
        """str: File system location for saving the file containing the
        statistics.

        Set by Controller. Default is None.
        """
        return self._wpathstats

    @wpathstats.setter
    def wpathstats(self, value):
        self._wpathstats = value

    @property
    def wdirstats(self):
        """str: Directory for saving the files containing the statistics during
        batch processing.

        Set by Controller. Default is None.
        """
        return self._wdirstats

    @wdirstats.setter
    def wdirstats(self, value):
        self._wdirstats = value

    @property
    def status(self):
        """str: Status message displayed in the View.

        Set by View or Controller. Default is None.
        """
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        if value is not None:
            self.status_changed.emit(value)

    @property
    def customheader(self):
        """dict of {int, str}: Header information when loading a Custom dataset.

        Set by View or Controller. Default is None for all keys.
        """
        return self._customheader

    @customheader.setter
    def customheader(self, value):
        self._customheader = value

    # The following attributes are slots that are connected to signals
    # from the View or Controller.

    @Property(object)
    def filetype(self):
        """str: Indicates the type of dataset (one of {"OpenSignals", "EDF",
        "Custom"}).

        Set by View or Controller. Default is None.
        """
        return self._filetype

    @Slot(object)
    def set_filetype(self, value):
        self._filetype = value

    @Property(object)
    def segment(self):
        """list of float: Start and end of the user-selected segment in seconds.

        Set by View. Default is None.
        """
        return self._segment

    @Slot(object)
    def set_segment(self, values):

        self._segment = None

        if values[0] and values[1]:
            beg = float(values[0])
            end = float(values[1])
            evalarray = [np.asarray([beg, end]) >= self._sec[0],
                         np.asarray([beg, end]) <= self._sec[-1]]
            # Ensure that values are inside temporal bounds.
            if not np.all(evalarray):
                self.status_changed.emit(f"Error: Invalid segment {beg} - {end}.")
                self.segment_changed.emit(self._segment)
                return
            # Ensure that order is valid.
            if beg > end:
                self.status_changed.emit(f"Error: Invalid segment {beg} - "
                                         f"{end}.")
                self.segment_changed.emit(self._segment)
                return
            # Ensure that the segment has a minimum duration of 5 seconds. If
            # this is not the case algorithms break (convolution kernel length
            # etc.).
            elif end - beg < 5:
                self.status_changed.emit("Please select a segment longer than "
                                         "5 seconds. The current segment is "
                                         f"{end - beg} seconds long.")
                self.segment_changed.emit(self._segment)
                return
            self.status_changed.emit(f"Valid segment {beg} - {end}.")
            self._segment = [beg, end]
            self.segment_changed.emit(self._segment)

    @Property(str)
    def batchmode(self):
        """str: Processing mode (one of {"single file", "multiple files"}).

        Set by View or Controller. Default is None.
        """
        return self._batchmode

    @Slot(str)
    def set_batchmode(self, value):
        self._batchmode = value

    @Property(str)
    def markerchan(self):
        """str: Marker channel. One of {"none", "I1", "I2", "A1", "A2", "A3",
        "A4", "A5", "A6"}.

        Set by View. Default is None.
        """
        return self._markerchan

    @Slot(str)
    def set_markerchan(self, value):
        self._markerchan = value

    @Property(str)
    def signalchan(self):
        """str: Signal channel. One of {"A1", "A2", "A3", "A4", "A5", "A6"}.

        Set by View. Default is None.
        """
        return self._signalchan

    @Slot(str)
    def set_signalchan(self, value):
        self._signalchan = value

    @Property(str)
    def modality(self):
        """str: Signal modality. One of {"ECG", "PPG", "RESP"}.

        Set by View. Default is None.
        """
        return self._modality

    @Slot(str)
    def set_modality(self, value):
        self._modality = value

    @Property(int)
    def peakseditable(self):
        """bool: Indicates whether or not the extrema are user-editable.

        Set by View. Default is False.
        """
        return self._peakseditable

    @Slot(int)
    def set_peakseditable(self, value):
        if value == 2:
            self._peakseditable = True
        elif value == 0:
            self._peakseditable = False

    @Property(int)
    def savebatchpeaks(self):
        """bool: Indicates whether or not to save the extrema during batch
        processing.

        Set by View. Default is False.
        """
        return self._savebatchpeaks

    @Slot(int)
    def set_savebatchpeaks(self, value):
        if value == 2:
            self._savebatchpeaks = True
        elif value == 0:
            self._savebatchpeaks = False

    @Property(int)
    def correctbatchpeaks(self):
        """bool: Indicates whether or not to auto-correct the extrema during
        batch processing.

        Set by View. Default is False.
        """
        return self._correctbatchpeaks

    @Slot(int)
    def set_correctbatchpeaks(self, value):
        if value == 2:
            self._correctbatchpeaks = True
        elif value == 0:
            self._correctbatchpeaks = False

    @Slot(int)
    def progress(self, value):
        """int: Conveys the progress signal of the Controller's worker thread.

        Necessary because View or Controller cannot directly be connected to
        the Controller's worker thread. Doesn't have a corresponding getter
        since value is never assessed directly. Set by Controller. Default is
        None.
        """
        self._progress = value
        if value is not None:
            self.progress_changed.emit(value)
