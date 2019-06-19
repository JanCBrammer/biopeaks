# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 18:47:12 2019

@author: John Doe
"""

from PyQt5.QtWidgets import (QWidget, QComboBox, QAction, QMainWindow,
                             QVBoxLayout, QHBoxLayout, QCheckBox,
                             QLabel, QStatusBar, QGroupBox, QDockWidget,
                             QLineEdit, QFormLayout, QPushButton)
from PyQt5.QtCore import Qt, QSignalMapper, QRegExp
from PyQt5.QtGui import QIcon, QRegExpValidator
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as
                                                FigureCanvas)
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as
                                                NavigationToolbar)

class CustomNavigationToolbar(NavigationToolbar):
    # only retain desired functionality of navitoolbar
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in
                 ('Home', 'Pan', 'Zoom', 'Back', 'Forward')]
    
    
class View(QMainWindow):
    def __init__(self, model, controller):
        super().__init__()

        self._model = model
        self._controller = controller
        
        #################################################################
        # define GUI layout and connect input widgets to external slots #
        #################################################################
        
        self.setWindowTitle('biopeaks')
        self.setGeometry(50, 50, 1750, 750)
        self.setWindowIcon(QIcon('python_icon.png'))
        
        # figure
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.get_yaxis().set_visible(False)
        self.ax.set_frame_on(False)
        self.line = None
        self.scat = None
        self.begline = None
        self.endline = None
        self.segmentspan = None
        self.navitools = CustomNavigationToolbar(self.canvas, self)
        
        # peak editing
        self.editcheckbox = QCheckBox('edit peaks', self)
        self.editcheckbox.stateChanged.connect(self._controller.
                                               change_editable)
        
        # modality selection
        self.batchmenulabel = QLabel('processing mode:')
        self.batchmenu = QComboBox(self)
        self.batchmenu.addItem('single file')
        self.batchmenu.addItem('multiple files')
        self.batchmenu.currentTextChanged.connect(self._controller.
                                                  change_batchmode)
        # initialize with default value
        self._controller.change_batchmode(self.batchmenu.currentText())
        
        # modality selection
        self.modmenulabel = QLabel('modality:')
        self.modmenu = QComboBox(self)
        self.modmenu.addItem('ECG')
        self.modmenu.addItem('PPG')
        self.modmenu.addItem('RESP')
        self.modmenu.currentTextChanged.connect(self._controller.
                                                change_modality)
        # initialize with default value
        self._controller.change_modality(self.modmenu.currentText())
        
        # channel selection
        self.chanmenulabel = QLabel('channel:')
        self.chanmenu = QComboBox(self)
        self.chanmenu.addItem('ECG')
        self.chanmenu.addItem('PPG')
        self.chanmenu.addItem('RESP')
        self.chanmenu.addItem('A1')
        self.chanmenu.addItem('A2')
        self.chanmenu.addItem('A3')
        self.chanmenu.addItem('A4')
        self.chanmenu.addItem('A5')
        self.chanmenu.addItem('A6')
        self.chanmenu.currentTextChanged.connect(self._controller.
                                                 change_channel)
        # initialize with default value
        self._controller.change_channel(self.chanmenu.currentText())
        
        # segment selection; this widget will be openend / set visible from
        # the menu and closed from within itself (see mapping of segmentermap);
        # it provides utilities to select a segment from the signal
        self.segmentermap = QSignalMapper(self)
        self.segmenter = QDockWidget('select a segment', self)
        
        regex = QRegExp('[0-9]+')
        validator = QRegExpValidator(regex)
        self.startlabel = QLabel('start')
        self.startedit = QLineEdit()
        self.startedit.setValidator(validator)
        self.startedit.textEdited.connect(self._controller.change_begsamp)
        self.endlabel = QLabel('end')
        self.endedit = QLineEdit()
        self.endedit.setValidator(validator)
        self.endedit.textEdited.connect(self._controller.change_endsamp)
        self.confirmedit = QPushButton('confirm selection')
        self.confirmedit.clicked.connect(self._controller.segment_signal)
        self.confirmedit.clicked.connect(self.segmentermap.map)
        self.segmentermap.setMapping(self.confirmedit, 0)
        self.segmenterlayout= QFormLayout()
        self.segmenterlayout.addRow(self.startlabel, self.startedit)
        self.segmenterlayout.addRow(self.endlabel, self.endedit)
        self.segmenterlayout.addRow(self.confirmedit)
        self.segmenterwidget = QWidget()
        self.segmenterwidget.setLayout(self.segmenterlayout)
        self.segmenter.setWidget(self.segmenterwidget)
        
        self.segmenter.setVisible(False)
        self.segmenter.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.segmenter)
        

        # set up menubar
        menubar = self.menuBar()
        
        # signal menu
        signalmenu = menubar.addMenu('data')
        
        openSignal = QAction('load', self)
        openSignal.triggered.connect(self._controller.open_signal)
        signalmenu.addAction(openSignal)
        
        segmentSignal = QAction('select segment', self)
        segmentSignal.triggered.connect(self.segmentermap.map)
        self.segmentermap.setMapping(segmentSignal, 1)
        signalmenu.addAction(segmentSignal)
        
        self.segmentermap.mapped.connect(self.toggle_segmenter)
        
        saveSignal = QAction('save', self)
        saveSignal.triggered.connect(self._controller.save_signal)
        signalmenu.addAction(saveSignal)
    
        # peak menu
        peakmenu = menubar.addMenu('peaks')
        
        findPeaks = QAction('find', self)
        findPeaks.triggered.connect(self._controller.find_peaks)
        peakmenu.addAction(findPeaks)
        
        savePeaks = QAction('save', self)
        savePeaks.triggered.connect(self._controller.get_savepath)
        peakmenu.addAction(savePeaks) 

        loadPeaks = QAction('load', self)
        loadPeaks.triggered.connect(self._controller.read_peaks)
        peakmenu.addAction(loadPeaks) 
        
        # set up status bar to display error messages and current file path
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.currentFile = QLabel()
        self.statusBar.addPermanentWidget(self.currentFile)

        # set up the central widget containing the plot and navigationtoolbar
        self.centwidget = QWidget()
        self.setCentralWidget(self.centwidget)

        # connect canvas to keyboard and mouse input for peak editing;
        # only widgets (e.g. canvas) that currently have focus capture
        # keyboard input: "You must enable keyboard focus for a widget if
        # it processes keyboard events."
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.setFocus()
        self.canvas.mpl_connect('key_press_event', self._controller.edit_peaks)
        
        # define GUI layout
        self.vlayout0 = QVBoxLayout(self.centwidget)
        self.vlayout1 = QVBoxLayout()
        self.hlayout0 = QHBoxLayout()
        self.hlayout1 = QHBoxLayout()

        self.optionsgroup = QGroupBox('select options')
        self.vlayout1.addWidget(self.modmenulabel)
        self.vlayout1.addWidget(self.modmenu)
        self.vlayout1.addWidget(self.chanmenulabel)
        self.vlayout1.addWidget(self.chanmenu)
        self.vlayout1.addWidget(self.batchmenulabel)
        self.vlayout1.addWidget(self.batchmenu)
        self.optionsgroup.setLayout(self.vlayout1)
        self.hlayout0.addWidget(self.optionsgroup)
        self.hlayout0.addWidget(self.canvas)
        self.hlayout0.setStretch(0, 1)
        self.hlayout0.setStretch(1, 15)
        self.vlayout0.addLayout(self.hlayout0)
        
        self.hlayout1.addWidget(self.navitools)
        self.hlayout1.addWidget(self.editcheckbox)
        self.vlayout0.addLayout(self.hlayout1)

        ##############################################
        # connect output widgets to external signals #
        ##############################################
        self._model.signal_changed.connect(self.plot_signal)
        self._model.peaks_changed.connect(self.plot_peaks)
        self._model.path_changed.connect(self.display_path)
        self._model.segment_changed.connect(self.plot_segment)
    
    ###########
    # methods #
    ###########
    def plot_signal(self):
        print('plot signal is listening')
        self.ax.clear()
        self.navitools.update()
        self.line = self.ax.plot(self._model.sec, self._model.signal)
        self.ax.set_xlabel('seconds', fontsize='x-large', fontweight='heavy')
        self.canvas.draw()
    
    def plot_peaks(self):
        print('plot peaks is listening')
        if self.scat is not None:
            # in case of re-plotting, remove the current peaks
            self.scat.remove()
        self.scat = self.ax.scatter(self._model.sec[self._model.peaks[:, 0]],
                                    self._model.signal[self._model.
                                                       peaks[:, 0]], c='m')
        self.canvas.draw()
        
    def plot_segment(self):
        # remove old plot elements
        if self.begline is not None:
            self.begline.remove()
        if self.endline is not None:
            self.endline.remove()
        if self.segmentspan is not None:
            self.segmentspan.remove()
        # plot new elements, NANs won't be plotted
        self.begline = self.ax.axvline(self._model.begsamp, color='m')           
        self.endline = self.ax.axvline(self._model.endsamp, color='m')           
        if self._model.begsamp < self._model.endsamp:
            self.segmentspan = self.ax.axvspan(self._model.begsamp,
                                               self._model.endsamp,
                                               color='m',
                                               alpha=0.5)
        else:
            # set segmentspan to None again, so there won't be an attempt 
            # to remove a a none-existing plot element the next time
            # plot_segment is called
            self.segmentspan = None
        self.canvas.draw()
        
    def toggle_segmenter(self, value):
        if self._model.loaded:
            if value == 1:
                self.segmenter.setVisible(True)
            elif value == 0:
                self.segmenter.setVisible(False)
            
    def display_path(self):
        self.currentFile.setText(self._model.signalpath)
        