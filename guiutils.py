# -*- coding: utf-8 -*-
"""
Created on Sat Apr 13 09:07:32 2019

@author: John Doe
"""

import wfdb
import numpy as np


def load_data(data_dir):
    # convert all data formats to numpy array
    
    
    data = wfdb.rdrecord(data_dir)
    return np.asarray(data.p_signal[:, 0])