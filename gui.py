# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 18:52:52 2019

@author: John Doe
"""

import sys
import numpy as np
from scipy.signal import find_peaks
from guiutils import LoadData
from ecg_offline import peaks_signal
from resp_offline import extrema_signal
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QWidget, QComboBox,
                             QFileDialog, QAction, QMainWindow,
                             QVBoxLayout, QHBoxLayout, QCheckBox)
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
                 ('Home','Pan', 'Zoom', 'Back', 'Forward')]
    

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
        self.modmenu = QComboBox(self)
        self.modmenu.addItem('ECG')
        self.modmenu.addItem('RESP')
        
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
        self.hlayout.addWidget(self.modmenu)
        self.hlayout.addWidget(self.editcheckbox)

        self.show()

    # toolbar methods
    def load_data(self):
        loadname = QFileDialog.getOpenFileNames(self, 'Open file', '\home')
        if loadname[0]:
            # until batch processing is implemented, select first file from
            # list; modality is hardcoded as ECG for now until selection of
            # modality is implemented
            self.data = LoadData(loadname[0][0], self.modmenu.currentText())
        
            if self.data.loaded is True:
                # clear axis and history toolbar for new data, also remove old
                # peaks and corresponding plot elements from memory
                self.ax.clear()
                self.navitools.update()
                self.peaks = None
                self.scat = None
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
                if self.modmenu.currentText() == 'ECG':
                    # for ECG data, data.signal returns a vector with indices
                    # of R-peaks
                    self.peaks = peaks_signal(self.data.signal,
                                              self.data.sfreq)
                elif self.modmenu.currentText() == 'RESP':
                    # for respiration data, data.signal returns a two column
                    # vector, with indices in column 0 and amplitudes at 
                    # indices in column 1
                    self.peaks = extrema_signal(self.data.signal,
                                                self.data.sfreq)
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
            
    # other methods
    def edit_peaks(self, event):
        # account for the fact that depending on sensor modality, data.peaks
        # has different shapes; preserve ndarrays throughout editing!
        if self.editcheckbox.isChecked():
            if self.peaks is not None:
                cursor = int(np.rint(event.xdata * self.data.sfreq))
                # search peak in a window of 200 msec, centered on selected
                # x coordinate of cursor position
                extend = int(np.rint(self.data.sfreq * 0.1))
                searchrange = np.arange(cursor - extend,
                                        cursor + extend)
                if event.key == 'd':
                    peakidx = np.argmin(np.abs(self.peaks[:, 0] - cursor))
                    # only delete peaks that are within search range
                    if np.any(searchrange == self.peaks[peakidx, 0]): 
                        self.peaks = np.delete(self.peaks, peakidx, axis=0)
                        self.plot_peaks()
                elif event.key == 'a':
                    searchsignal = self.data.signal[searchrange]
                    # use find_peaks to also detect local extrema that are
                    # plateaus
                    locmax, _ = find_peaks(searchsignal)
                    locmin, _ = find_peaks(searchsignal * -1)
                    locext = np.concatenate((locmax, locmin))
                    locext.sort(kind='mergesort')
                    if locext.size > 0:
                        peakidx = np.argmin(np.abs(searchrange[locext] -
                                                   cursor))
                        newpeak = searchrange[0] + locext[peakidx]
                        # only add new peak if it doesn't exist already
                        if np.all(self.peaks[:, 0] != newpeak):
                            insertidx = np.searchsorted(self.peaks[:, 0],
                                                        newpeak)
                            if self.peaks.shape[1] == 1:
                                insertarr = [newpeak]
                                self.peaks = np.insert(self.peaks, insertidx,
                                                       insertarr, axis=0)
                            elif self.peaks.shape[1] == 2:
                                insertarr = [newpeak,
                                             self.data.signal[newpeak]]
                                self.peaks = np.insert(self.peaks, insertidx,
                                                       insertarr, axis=0)                            
                            self.plot_peaks()
            else:
                print('please search peaks before editing them')
                
    def plot_peaks(self):
        if self.scat is not None:
            # in case of re-plotting, remove the current peaks
            self.scat.remove()
        self.scat = self.ax.scatter(self.data.sec[self.peaks[:, 0]],
                                    self.data.signal[self.peaks[:, 0]], c='m')
        self.canvas.draw()
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())
    