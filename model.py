# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 18:47:12 2019

@author: John Doe
"""

from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

        
class Model(QObject):
    
    signal_changed = pyqtSignal()
    peaks_changed = pyqtSignal()
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
    def signalpath(self):
        return self._signalpath

    @signalpath.setter
    def signalpath(self, value):
        self._signalpath = value
        self.path_changed.emit()
        
    @property
    def begsamp(self):
        return self._begsamp
    
    @ begsamp.setter
    def begsamp(self, value):
        self._begsamp = value
        self.segment_changed.emit()
        
    @property
    def endsamp(self):
        return self._endsamp
    
    @ endsamp.setter
    def endsamp(self, value):
        self._endsamp = value
        self.segment_changed.emit()

    def __init__(self):
        super().__init__()

        self._signal = None
        self._peaks = None
        self._signalpath = None
        self._begsamp = np.nan
        self._endsamp = np.nan
        self.sfreq = None
        self.sec = None
        self.loaded = False
        
    def reset(self):
        self._signal = None
        self._peaks = None
        self._signalpath = None
        self._begsamp = np.nan
        self._endsamp = np.nan
        self.sfreq = None
        self.sec = None
        self.loaded = False
        