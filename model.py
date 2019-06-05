# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 18:47:12 2019

@author: John Doe
"""

from PyQt5.QtCore import QObject, pyqtSignal


class Model(QObject):
    
    def __init__(self):
        super().__init__()
        
        ##############
        # attributes #
        ##############
        self.signal = None
        self.peaks = None
        self.sfreq = None
        self.sec = None
        self.modality = None
        self.channel = None
        self.signalpath = None
        self.editable = False
        self.loaded = False

    
    