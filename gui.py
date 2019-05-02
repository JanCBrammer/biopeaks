# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 18:52:52 2019

@author: John Doe
"""

import sys
import numpy as np
from guiutils import load_data
from ecg_offline import peaks_signal
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton,
                             QFileDialog, QAction, QMainWindow,
                             QVBoxLayout, QHBoxLayout, QLineEdit,
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
        self.sfreq = None
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
        self.sfreqbox = QLineEdit(self)
        self.sfreqbutton = QPushButton('update sampling frequency', self)
        self.sfreqbutton.clicked.connect(self.update_sfreq)
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
        self.hlayout.addWidget(self.sfreqbox)
        self.hlayout.addWidget(self.sfreqbutton)

        self.show()

    # toolbar methods
    def load_data(self):
        
        if self.sfreq is not None:
            loadname = QFileDialog.getOpenFileNames(self, 'Open file', '\home')
            if loadname[0]:
                # until batch processing is implemented, select first file from list
                loadname = loadname[0][0]
            
                # initiate plot to show user that their data loaded successfully
                self.data = load_data(loadname)
                if self.data is not None:
                    # clear axis and history toolbar for new data
                    self.ax.clear()
                    self.navitools.update()
                    # set x-axis to seconds
                    self.xtime = (np.arange(0, self.data.size) / self.sfreq)
                    self.line = self.ax.plot(self.xtime, self.data)
                    self.ax.set_xlabel('seconds')
                    self.canvas.draw()
        else:
            print('please enter the sampling frequency of your data')
                
    def find_peaks(self):
        # identify and show peaks
        if self.data is not None:
            self.peaks = peaks_signal(self.data, self.sfreq)
            self.plot_peaks()
            
    def save_peaks(self):
        savename, _ = QFileDialog.getSaveFileName(self, 'Save peaks',
                                                  'untitled.csv',
                                                  'CSV (*.csv)')
        if savename and (self.peaks is not None):
            # save peaks in seconds
            np.savetxt(savename, self.time[self.peaks])
            
    # other methods
    def update_sfreq(self, text):
#        try:
        self.sfreq = int(self.sfreqbox.text())
        # re-calculate peaks and re-plot data and peaks
        if self.data is not  None:
            self.ax.clear()
            self.navitools.update()
            # set x-axis to seconds
            self.xtime = (np.arange(0, self.data.size) / self.sfreq)
            self.line = self.ax.plot(self.xtime, self.data)
            self.ax.set_xlabel('seconds')
            self.canvas.draw()
        if self.peaks is not None:
            self.find_peaks()
        print('setting sampling frequency to {}'.format(self.sfreq))
#        except:
#            print('please enter numerical value')
        
    def enable_editing(self, state):
        if self.editcheckbox.isChecked():
            self.editingenabled = True
        else:
            self.editingenabled = False
            
    def edit_peaks(self, event):
        if self.editingenabled is True:
            if self.peaks is not None:
                peaksamp = int(np.rint(event.xdata * self.sfreq))
                 # search peak in a window of 200 msec, centered on selected
                 # x coordinate
                extend = int(np.rint(self.sfreq * 0.1))
                searchrange = np.arange(peaksamp - extend,
                                        peaksamp + extend)
                if event.key == 'd':
                    peakidx = np.argmin(np.abs(self.peaks - peaksamp))
                    # only delete peaks that are within search range
                    if np.any(searchrange == self.peaks[peakidx]): 
                        self.peaks = np.delete(self.peaks, peakidx)
                        self.plot_peaks()
                elif event.key == 'a':
                    peakidx = np.argmax(np.abs(self.data[searchrange]))
                    newpeak = searchrange[0] + peakidx
                    # only add new peak if it doesn't exist already
                    if np.all(self.peaks != newpeak):
                        insertidx = np.searchsorted(self.peaks, newpeak)
                        self.peaks = np.insert(self.peaks, insertidx, newpeak)
                        self.plot_peaks()
                
    def plot_peaks(self):
        if self.scat is not None:
            # in case of re-plotting, remove the current peaks
            self.scat.remove()
        self.scat = self.ax.scatter(self.xtime[self.peaks],
                                    self.data[self.peaks], c='m')
        self.canvas.draw()
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())
    