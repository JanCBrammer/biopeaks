# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 18:52:52 2019

@author: John Doe
"""

import sys
import numpy as np
from guiutils import load_data
from ecg_offline import peaks_signal
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton,
                             QFileDialog, QAction, QMainWindow,
                             QVBoxLayout, QHBoxLayout, QLineEdit)
from PyQt5.QtGui import QIcon
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as
                                                FigureCanvas)
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as
                                                NavigationToolbar)


class Window(QMainWindow):
 
    def __init__(self):
        super().__init__()
        self.initUI()
 
    def initUI(self):
        self.setWindowTitle('biopeaks')
        self.setGeometry(50, 50, 1500, 500)
        self.setWindowIcon(QIcon('python_icon.png'))
        
        # initialize data
        self.data = None
        self.peaks = None
        self.sfreq = 1000
        
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
        self.ax.set_xlabel('seconds')
        self.navitools = NavigationToolbar(self.canvas, self)
        self.sfreqbox = QLineEdit(self)
        self.sfreqbutton = QPushButton('update sampling frequency', self)
        self.sfreqbutton.clicked.connect(self.update_sfreq)
        
        # define GUI layout
        self.vlayout = QVBoxLayout(self.centwidget)
        self.vlayout.addWidget(self.canvas)
        
        self.hlayout = QHBoxLayout()
        self.vlayout.addLayout(self.hlayout)
        
        self.hlayout.addWidget(self.navitools)
        self.hlayout.addWidget(self.sfreqbutton)
        self.hlayout.addWidget(self.sfreqbox)

        self.show()

    # toolbar methods
    def load_data(self):
        loadname = QFileDialog.getOpenFileNames(self, 'Open file', '\home')
        print(loadname[0])
        if loadname[0]:
            # until batch processing is implemented, select first file from list
            loadname = loadname[0][0]
            print(loadname)
        
        # initiate plot to show user that their data loaded successfully
            self.data = load_data(loadname)
            if self.data is not None:
                # clear axis and history toolbar for new data
                self.ax.clear()
                self.navitools.update()
                # set x-axis to seconds
                xvals = (np.arange(0, self.data.size) / self.sfreq)
                self.ax.plot(xvals, self.data)
                self.canvas.draw()
        
    def find_peaks(self):
        # identify and show peaks
        if self.data is not None:
            self.peaks = peaks_signal(self.data, self.sfreq)
            self.ax.scatter(self.peaks, self.data[self.peaks], c='m')
            self.canvas.draw()
            
    def save_peaks(self):
        savename, _ = QFileDialog.getSaveFileName(self, 'Save peaks',
                                                  'untitled.csv',
                                                  'CSV (*.csv)')
        if savename and (self.peaks is not None):
            np.savetxt(savename, self.peaks)
            
    # other methods
    def update_sfreq(self, text):
        try:
            self.sfreq = int(self.sfreqbox.text())
        except:
            print('please enter numerical value')
        print(self.sfreq)
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())
    