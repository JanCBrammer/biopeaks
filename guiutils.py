# -*- coding: utf-8 -*-
"""
Created on Sat Apr 13 09:07:32 2019

@author: John Doe
"""

import os
import json
import numpy as np


class LoadData:
    
    def __init__(self, datadir, modality):
        self.modality = modality
        self.datadir = datadir
        self.signal = None
        self.sfreq = None
        self.loaded = False
        self.check_filetype()
        
    def check_filetype(self):
        _, self.file_extension = os.path.splitext(self.datadir)
        self.extract_data()
        
    def extract_data(self):
        if self.file_extension == '.txt':
            # open file and check if it's encoded in OpenSignals format
            f = open(self.datadir, 'r')
            if 'OpenSignals' in f.readline():
                # convert json header to dict (only selects first device / MAC 
                # adress)
                metadata = json.loads(f.readline()[1:])
                metadata = metadata[list(metadata.keys())[0]]
                # parse header and extract relevant metadata
                self.sfreq = metadata['sampling rate']
                sensors = metadata['sensor']
                # find the index of the sensor that corresponds to the
                # selected modality; it doesn't matter if sensor is called
                # <modality>BIT or <modality>BITREV; select only first sensor
                # of the selected modality (it is conceivable that multiple
                # sensors of the same kind have been recorded)
                sensidx = [i for i, s in enumerate(sensors)
                            if self.modality in s][0]
                # since analog channels start in column 5 (zero based), add
                # 5 to sensor index to obtain signal from selected modality
                sensidx += + 5
                self.signal = np.loadtxt(self.datadir)[:, sensidx]
                siglen = self.signal.size
                self.sec = np.linspace(0, siglen / self.sfreq,
                                       siglen, 1. / self.sfreq)
                self.loaded = True
   