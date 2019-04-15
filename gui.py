# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 18:52:52 2019

@author: John Doe
"""

import sys
from guiutils import load_data
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton,
                             QFileDialog, QAction, QMainWindow,
                             QVBoxLayout, QSizePolicy)
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
        
        # set up toolbar
        openData = QAction(QIcon('open_icon.png'), 'Open', self)
        openData.triggered.connect(self.open_data)
        toolbar = self.addToolBar('File')
        toolbar.addAction(openData)      
        
        # set up the central widget containing the plot and navigationtoolbar
        self.centwidget = QWidget()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.navitools = NavigationToolbar(self.canvas, self)
        self.layout = QVBoxLayout(self.centwidget)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.navitools)
        self.setCentralWidget(self.centwidget)
        
        self.show()

    # toolbar methods
    def open_data(self):
        fname = QFileDialog.getOpenFileNames(self, 'Open file', '\home')
        print(fname[0])
        data = load_data(fname[0][0][:-4])
       
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(data)
        self.canvas.draw()
   


if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())
    