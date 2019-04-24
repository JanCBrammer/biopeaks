# -*- coding: utf-8 -*-
"""
Created on Sat Apr 13 09:07:32 2019

@author: John Doe
"""

import os
import wfdb
import numpy as np


def load_data(datadir):
    
    # convert all data formats to numpy array
    
    filename, file_extension = os.path.splitext(datadir)
    print(filename, file_extension)
    
    if file_extension == '.dat':
        data = wfdb.rdrecord(datadir[:-4])
        data = np.asarray(data.p_signal[:, 0])
        return data
    elif file_extension == '.txt':
        data = np.loadtxt(datadir)
        return data
    else:
        print('select either a .dat or .txt file')    