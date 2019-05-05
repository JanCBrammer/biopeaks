# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 18:52:52 2019

@author: John Doe
"""

import sys
import numpy as np
from scipy.signal import argrelmin, argrelmax
from guiutils import LoadData
from ecg_offline import peaks_signal
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QWidget,
                             QFileDialog, QAction, QMainWindow,
                             QVBoxLayout, QHBoxLayout,
                             QCheckBox)
from PyQt5.QtGui import QIcon
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as
                                                FigureCanvas)
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as
                                                NavigationToolbar)


# custom widgets
class CustomNavigationToolbar(NavigationToolbar):
    # only retain desired functionality
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in
                 ('Home','Pan', 'Zoom')]
    

class Window(QMainWindow):
 
    def __init__(self):
        super().__init__()
        self.initUI()
 
    def initUI(self):
        self.setWindowTitle('biopeaks')
        self.setGeometry(50, 50, 1500, 500)
        self.setWindowIcon(QIcon('python_icon.png'))
                
        # initialize data and parameters
        self.data = None
        self.peaks = None
        self.scat = None
        self.editingenabled = False

        # set up toolbar
        toolbar = self.addToolBar('Toolbar')

        loadData = QAction(QIcon('open_icon.png'), 'Load data', self)
        loadData.triggered.connect(self.load_data)
        toolbar.addAction(loadData)      

        findPeaks = QAction(QIcon('plot_icon.png'), 'Find peaks', self)
        findPeaks.triggered.connect(self.find_peaks)
        toolbar.addAction(findPeaks)      

        savePeaks = QAction(QIcon('save_icon.png'), 'Save peaks', self)
        savePeaks.triggered.connect(self.save_peaks)
        toolbar.addAction(savePeaks)      

        # set up the central widget containing the plot and navigationtoolbar
        self.centwidget = QWidget()
        self.setCentralWidget(self.centwidget)

        # define GUI elements
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.navitools = CustomNavigationToolbar(self.canvas, self)
        self.editcheckbox = QCheckBox('edit peaks', self)
        self.editcheckbox.stateChanged.connect(self.enable_editing)
        
        # connect canvas to keyboard and mouse input for peak editing;
        # only widgets (e.g. canvas) that currently have focus capture
        # keyboard input: "You must enable keyboard focus for a widget if
        # it processes keyboard events."
        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.canvas.setFocus()
        self.canvas.mpl_connect('key_press_event', self.edit_peaks)
        
        # define GUI layout
        self.vlayout = QVBoxLayout(self.centwidget)
        self.vlayout.addWidget(self.canvas)
        
        self.hlayout = QHBoxLayout()
        self.vlayout.addLayout(self.hlayout)
        
        self.hlayout.addWidget(self.navitools)
        self.hlayout.addWidget(self.editcheckbox)

        self.show()

    # toolbar methods
    def load_data(self):
        
        loadname = QFileDialog.getOpenFileNames(self, 'Open file', '\home')
        if loadname[0]:
            # until batch processing is implemented, select first file from
            # list; modality is hardcoded as ECG for now until selection of
            # modality is implemented
            self.data = LoadData(loadname[0][0], 'ECG')
        
            if self.data.loaded is True:
                # clear axis and history toolbar for new data, also remove old
                # peaks from memory
                self.ax.clear()
                self.navitools.update()
                self.peaks = None
                # initiate plot to show user that data loaded successfully            
                self.line = self.ax.plot(self.data.sec, self.data.signal)
                self.ax.set_xlabel('seconds')
                self.canvas.draw()
            else:
                print('make sure to load data in the OpenSignals format')
                
    def find_peaks(self):
        if self.peaks is None:
            # identify and show peaks
            if self.data is not None:
                self.peaks = peaks_signal(self.data.signal, self.data.sfreq)
                self.plot_peaks()
        else:
            print('the peaks for this dataset are already in memory')
            
    def save_peaks(self):
        if self.peaks is not None:
            savename, _ = QFileDialog.getSaveFileName(self, 'Save peaks',
                                                      'untitled.csv',
                                                      'CSV (*.csv)')
            if savename:
                # save peaks in seconds
                np.savetxt(savename, self.data.sec[self.peaks])
            
    def enable_editing(self, state):
        if self.editcheckbox.isChecked():
            self.editingenabled = True
        else:
            self.editingenabled = False
            
    def edit_peaks(self, event):
        if self.editingenabled is True:
            if self.peaks is not None:
                peaksamp = int(np.rint(event.xdata * self.data.sfreq))
                # search peak in a window of 200 msec, centered on selected
                # x coordinate
                extend = int(np.rint(self.data.sfreq * 0.1))
                searchrange = np.arange(peaksamp - extend,
                                        peaksamp + extend)
                if event.key == 'd':
                    peakidx = np.argmin(np.abs(self.peaks - peaksamp))
                    # only delete peaks that are within search range
                    if np.any(searchrange == self.peaks[peakidx]): 
                        self.peaks = np.delete(self.peaks, peakidx)
                        self.plot_peaks()
                elif event.key == 'a':
#                    searchsignal = self.data.signal[searchrange]
#                    peakidx = np.argmax(np.abs(searchsignal -
#                                               np.mean(searchsignal)))
#                    newpeak = searchrange[0] + peakidx
                    searchsignal = self.data.signal[searchrange]
                    locmax = argrelmax(searchsignal)[0]
                    locmin = argrelmin(searchsignal)[0]
                    locext = np.concatenate((locmax, locmin))
                    locext.sort(kind='mergesort')
                    peakidx = np.argmin(np.abs(searchrange[locext] - peaksamp))
                    newpeak = searchrange[0] + locext[peakidx]
                    # only add new peak if it doesn't exist already
                    if np.all(self.peaks != newpeak):
                        insertidx = np.searchsorted(self.peaks, newpeak)
                        self.peaks = np.insert(self.peaks, insertidx, newpeak)
                        self.plot_peaks()
            else:
                print('please search peaks before editing them')
                
    def plot_peaks(self):
        if self.scat is not None:
            # in case of re-plotting, remove the current peaks
            self.scat.remove()
        self.scat = self.ax.scatter(self.data.sec[self.peaks],
                                    self.data.signal[self.peaks], c='m')
        self.canvas.draw()
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())
    