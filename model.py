# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 18:47:12 2019

@author: John Doe
"""

from PyQt5.QtCore import QObject, pyqtSignal

        
class Model(QObject):
    
    # costum signals
    signal_changed = pyqtSignal()
    peaks_changed = pyqtSignal()
    markers_changed = pyqtSignal(int)
    path_changed = pyqtSignal()
    segment_changed = pyqtSignal()

    @property
    def signal(self):
        return self._signal

    @signal.setter
    def signal(self, value):
        self._signal = value
        self.signal_changed.emit()
        
    @property
    def peaks(self):
        return self._peaks

    @peaks.setter
    def peaks(self, value):
        self._peaks = value
        self.peaks_changed.emit()
        
    @property
    def markers(self):
        return self._markers

    @markers.setter
    def markers(self, value):
        self._markers = value
        self.markers_changed.emit(1)
        
    @property
    def signalpath(self):
        return self._signalpath

    @signalpath.setter
    def signalpath(self, value):
        self._signalpath = value
        self.path_changed.emit()
        
    @property
    def segment(self):
        return self._segment
    
    @ segment.setter
    def segment(self, value):
        self._segment = value
        self.segment_changed.emit()
        

    def __init__(self):
        super().__init__()

        self._signal = None
        self._peaks = None
        self.sec = None
        self._markers = None
        self._segment = None
        self._signalpath = None
        self.sfreq = None
        self.loaded = False
        self.signalchan = None
        self.markerchan = None
        
    def reset(self):
        self._signal = None
        self._peaks = None
        self.sec = None
        self._markers = None
        self._segment = None
        self._signalpath = None
        self.sfreq = None
        self.loaded = False
        # don't reset channels
        