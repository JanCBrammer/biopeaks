# -*- coding: utf-8 -*-
"""
Created on Thu May  9 14:38:15 2019

@author: U117148
"""

import numpy as np
import matplotlib.pyplot as plt
from resp_offline import extrema_signal

signal = np.loadtxt(r'C:\Users\JohnDoe\surfdrive\Beta\Data\RESP\Bitalino'
                    r'\abele_zombies_spider_chest.txt')[:, 6]


# toy example
peaks = extrema_signal(signal, 1000)[:, 1]
diffs = np.sign(np.diff(peaks))
diffs = np.add(diffs[0:-1], diffs[1:])
plt.figure()
plt.plot(diffs)
removeidcs = np.where(diffs != 0)[0] + 1
peaks = np.delete(peaks, removeidcs)
diffs = np.sign(np.diff(peaks))
plt.figure()
plt.plot(diffs)


# validation in peaks returned by GUI (load peaks and see if the the correct
# peaks have been thrown out: tried a whole bunch of test cases and it works
# absolutely fine)
peaks = np.loadtxt(r'C:\Users\JohnDoe\Desktop\foopeaks.csv')
plt.plot(signal)
plt.scatter(peaks[:, 0], peaks[:, 2], c='r')
plt.scatter(peaks[:, 1], peaks[:, 3], c='m')