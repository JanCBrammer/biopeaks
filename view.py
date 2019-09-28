# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 18:47:12 2019

@author: John Doe
"""

from PyQt5.QtWidgets import (QWidget, QComboBox, QAction, QMainWindow,
                             QVBoxLayout, QHBoxLayout, QCheckBox,
                             QLabel, QStatusBar, QGroupBox, QDockWidget,
                             QLineEdit, QFormLayout, QPushButton, QProgressBar)
from PyQt5.QtCore import (Qt, QSignalMapper, QRegExp, pyqtSignal)
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
    
    # define costum signals here, since they must be part of the class
    # definition and cannot be dynamically added as class attributes after
    # the class has been defined
    segment_updated = pyqtSignal(object)

    def __init__(self, model, controller):
        super().__init__()

        self._model = model
        self._controller = controller
        self.segmentcursor = False
        
                        
        #################################################################
        # define GUI layout and connect input widgets to external slots #
        #################################################################
        
        self.setWindowTitle('biopeaks')
        self.setGeometry(50, 50, 1750, 750)
        self.setWindowIcon(QIcon('python_icon.png'))
        
        # figure
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        # axes for signal
        self.ax0 = self.figure.add_axes([.05, .55, .9, .4])
        self.ax0.get_yaxis().set_visible(False)
        self.ax0.set_frame_on(False)
        # axes for markers docked below signal axes
        self.ax1 = self.figure.add_axes([.05, .275, .9, .225],
                                        sharex=self.ax0)
        self.ax1.set_frame_on(False)
        self.ax1.get_xaxis().set_visible(False)
        self.ax1.get_yaxis().set_visible(False)
        # axes for rate or amplitude docked below markers
        self.ax2 = self.figure.add_axes([.05, .05, .9, .225],
                                        sharex=self.ax0)
        self.ax2.set_frame_on(False)
        self.ax2.get_xaxis().set_visible(False)
        self.navitools = CustomNavigationToolbar(self.canvas, self)
        
        # peak editing
        self.editcheckbox = QCheckBox('edit peaks', self)
        self.editcheckbox.stateChanged.connect(self._controller.
                                               change_editable)
        
        # processing mode (batch or single file)
        self.batchmenulabel = QLabel('processing mode')
        self.batchmenu = QComboBox(self)
        self.batchmenu.addItem('single file')
        self.batchmenu.addItem('multiple files')
        self.batchmenu.currentTextChanged.connect(self._controller.
                                                  change_batchmode)
        # initialize with default value
        self._controller.change_batchmode(self.batchmenu.currentText())
        
        # modality selection
        self.modmenulabel = QLabel('modality')
        self.modmenu = QComboBox(self)
        self.modmenu.addItem('ECG')
#        self.modmenu.addItem('PPG')
        self.modmenu.addItem('RESP')
        self.modmenu.currentTextChanged.connect(self._controller.
                                                change_modality)
        # initialize with default value
        self._controller.change_modality(self.modmenu.currentText())
        
        # channel selection
        self.sigchanmenulabel = QLabel('data channel')
        self.sigchanmenu = QComboBox(self)
        self.sigchanmenu.addItem('ECG')
#        self.sigchanmenu.addItem('PPG')
        self.sigchanmenu.addItem('RESP')
        self.sigchanmenu.addItem('A1')
        self.sigchanmenu.addItem('A2')
        self.sigchanmenu.addItem('A3')
        self.sigchanmenu.addItem('A4')
        self.sigchanmenu.addItem('A5')
        self.sigchanmenu.addItem('A6')
        self.sigchanmenu.currentTextChanged.connect(self._controller.
                                                    change_signalchan)
        # initialize with default value
        self._controller.change_signalchan(self.sigchanmenu.currentText())
        
        self.markerschanmenulabel = QLabel('marker channel')
        self.markerschanmenu = QComboBox(self)
        self.markerschanmenu.addItem('I1')
        self.markerschanmenu.addItem('I2')
        self.markerschanmenu.addItem('A1')
        self.markerschanmenu.addItem('A2')
        self.markerschanmenu.addItem('A3')
        self.markerschanmenu.addItem('A4')
        self.markerschanmenu.addItem('A5')
        self.markerschanmenu.addItem('A6')
        self.markerschanmenu.currentTextChanged.connect(self._controller.
                                                        change_markerchan)
        # initialize with default value
        self._controller.change_markerchan(self.markerschanmenu.currentText())
        
        # segment selection; this widget can be openend / set visible from
        # the menu and closed from within itself (see mapping of segmentermap);
        # it provides utilities to select a segment from the signal
        self.segmentermap = QSignalMapper(self)
        self.segmenter = QDockWidget('select a segment', self)
        # disable closing such that widget can only be closed by confirming
        # selection or custom button
        self.segmenter.setFeatures(QDockWidget.NoDockWidgetFeatures)
        # limit number of decimals to two
        regex = QRegExp('[0-9]*\.?[0-9]{2}')
        validator = QRegExpValidator(regex)
        
        self.startlabel = QLabel('start')
        self.startedit = QLineEdit()
        self.startedit.setValidator(validator)
        
        self.endlabel = QLabel('end')
        self.endedit = QLineEdit()
        self.endedit.setValidator(validator)
        
        segmentfromcursor = QAction(QIcon('mouse_icon.png'),
                                    'select with mouse',
                                    self)
        segmentfromcursor.triggered.connect(self.enable_segmentedit)
        self.startedit.addAction(segmentfromcursor, 1)
        self.endedit.addAction(segmentfromcursor, 1)
        
        self.previewedit = QPushButton('update selection')
        self.previewedit.clicked.connect(self.emit_segment)
        # use previosly defined costum signal that sends start and end of
        # selected segment to controller from within emit_segment
        self.segment_updated.connect(self._controller.change_segment)
        
        self.confirmedit = QPushButton('confirm selection')
        lambdafn = lambda: self._controller.threader(status='segmenting'
                                                     ' signal',
                                                     fn=self._controller.
                                                     segment_signal)
        self.confirmedit.clicked.connect(lambdafn)
        self.confirmedit.clicked.connect(self.segmentermap.map)
        self.segmentermap.setMapping(self.confirmedit, 0)
        
        self.abortedit = QPushButton('abort selection')
        self.abortedit.clicked.connect(self.segmentermap.map)
        # reset the segment to None
        self.segmentermap.setMapping(self.abortedit, 2)
        
        self.segmenterlayout= QFormLayout()
        self.segmenterlayout.addRow(self.startlabel, self.startedit)
        self.segmenterlayout.addRow(self.endlabel, self.endedit)
        self.segmenterlayout.addRow(self.previewedit)
        self.segmenterlayout.addRow(self.confirmedit)
        self.segmenterlayout.addRow(self.abortedit)
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
        
        markersmenu = signalmenu.addMenu('markers')
        dockmarkers = QAction('dock', self)
        dockmarkers.triggered.connect(self._controller.open_markers)
        markersmenu.addAction(dockmarkers)
        undockmarkers = QAction('undock', self)
        undockmarkers.triggered.connect(lambda: self.dock_markers(0))        
        markersmenu.addAction(undockmarkers)
        
        segmentSignal = QAction('select segment', self)
        segmentSignal.triggered.connect(self.segmentermap.map)
        self.segmentermap.setMapping(segmentSignal, 1)
        signalmenu.addAction(segmentSignal)
        
        self.segmentermap.mapped.connect(self.toggle_segmenter)
        
        saveSignal = QAction('save', self)
        saveSignal.triggered.connect(self._controller.get_wpathsignal)
        signalmenu.addAction(saveSignal)
        
        # peak menu
        peakmenu = menubar.addMenu('peaks')
        
        findPeaks = QAction('find', self)
        lambdafn = lambda: self._controller.threader(status='finding peaks',
                                                     fn=self._controller.
                                                     find_peaks)
        findPeaks.triggered.connect(lambdafn)
        peakmenu.addAction(findPeaks)
        
        savePeaks = QAction('save', self)
        savePeaks.triggered.connect(self._controller.get_wpathpeaks)
        peakmenu.addAction(savePeaks) 

        loadPeaks = QAction('load', self)
        loadPeaks.triggered.connect(self._controller.get_rpathpeaks)
        peakmenu.addAction(loadPeaks)
        
        # analysis menu
        analyzemenu = menubar.addMenu('analysis')
        
        rate = QAction('rate', self)
        rate.triggered.connect(self._controller.calculate_rate)
        analyzemenu.addAction(rate)
        
        breathamp = QAction('breathing amplitude', self)
        breathamp.triggered.connect(self._controller.calculate_breathamp)
        analyzemenu.addAction(breathamp)
        
        # set up status bar to display error messages and current file path
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 1)
        self.statusBar.addPermanentWidget(self.progressBar)
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
        self.canvas.mpl_connect('button_press_event', self.get_xcursor)
        
        # define GUI layout
        self.vlayout0 = QVBoxLayout(self.centwidget)
        self.vlayout1 = QFormLayout()
        self.hlayout0 = QHBoxLayout()
        self.hlayout1 = QHBoxLayout()

        self.optionsgroup = QGroupBox('select options')
        self.vlayout1.addRow(self.modmenulabel, self.modmenu)
        self.vlayout1.addRow(self.sigchanmenulabel, self.sigchanmenu)
        self.vlayout1.addRow(self.markerschanmenulabel, self.markerschanmenu)
        self.vlayout1.addRow(self.batchmenulabel, self.batchmenu)
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
        self._model.rrinterp_changed.connect(self.plot_stats)
        self._model.markers_changed.connect(self.dock_markers)
        self._model.path_changed.connect(self.display_path)
        self._model.segment_changed.connect(self.plot_segment)
        self._model.status_changed.connect(self.display_status)
        self._model.progress_changed.connect(self.display_progress)
        self._model.model_reset.connect(self.reset_plot)
    
    ###########
    # methods #
    ###########

    def plot_signal(self):
        self.ax0.clear()
        self.ax0.relim()
        self.ax1.clear()
        self.ax1.relim()
        # reset navitools history
        self.navitools.update()
        self.line = self.ax0.plot(self._model.sec, self._model.signal,
                                  zorder=1)
        self.ax0.set_xlabel('seconds', fontsize='large', fontweight='heavy')
        self.canvas.draw()
        print("plot_signal listening")
#        print(self.ax0.collections, self.ax0.patches, self.ax0.artists)

    def plot_peaks(self):
        # self.scat is listed in ax.collections
        if self.ax0.collections:
            self.ax0.collections[0].remove()
        self.scat = self.ax0.scatter(self._model.sec[self._model.peaks[:, 0]],
                                     self._model.signal[self._model.
                                                        peaks[:, 0]],
                                                        c='m',
                                                        zorder=2)
        self.canvas.draw()
        print("plot_peaks listening")
#        print(self.ax0.collections, self.ax0.patches, self.ax0.artists)

    def plot_segment(self):
        # self.segementspan is listed in ax.patches
        if self.ax0.patches:
            self.ax0.patches[0].remove()
        self.segmentspan = self.ax0.axvspan(self._model.segment[0],
                                           self._model.segment[1],
                                           color='m',
                                           alpha=0.25)
        self.canvas.draw()
        self.confirmedit.setEnabled(True)
#        print(self.ax0.collections, self.ax0.patches, self.ax0.artists)
        
    def plot_stats(self):
        pass
        
    def dock_markers(self, value):
        if value == 1:
            # manually restore home view to avoid corrupted scale in 
            # marker channel plot
            self.navitools.home()
            self.ax1.clear()
            self.markers = self.ax1.plot(self._model.sec,
                                         self._model.markers)
            # reset navitools history
            self.navitools.update()
        elif value == 0:
            # reset markers, otherwise they are replotted, e.g. after
            # segmentation of the signal
            self._model.markers = None
            self.statusBar.showMessage('undocking markers')
            self.ax1.clear()
            self.ax1.relim()
            self.statusBar.clearMessage()
        self.canvas.draw()

    def display_path(self):
        self.currentFile.setText(self._model.rpathsignal)
        
    def display_status(self, status):
        # display status until new status is set
        self.statusBar.showMessage(status)
        
    def display_progress(self, value):
        # if value is 0, the progressbar indicates a busy state
        self.progressBar.setRange(0, value)
        
    def toggle_segmenter(self, value):
        if self._model.loaded:
            # open segmenter when called from signalmenu
            if value == 1:
                self.segmenter.setVisible(True)
                self.confirmedit.setEnabled(False)
                self.startedit.clear()
                self.endedit.clear()
            # close segmenter after segment has been confirmed
            elif value == 0:
                self.segmenter.setVisible(False)
                if self.ax0.patches:
                    self.ax0.patches[0].remove()
            # close segmenter after segmentation has been aborted (reset
            # segment)
            elif value == 2:
                self._model.segment = None
                self.segmenter.setVisible(False)
                if self.ax0.patches:
                    self.ax0.patches[0].remove()
                
    def enable_segmentedit(self):
        # disable peak editing to avoid interference
        self.editcheckbox.setCheckState(0)
        if self.startedit.hasFocus():
            self.segmentcursor = 'start'
        elif self.endedit.hasFocus():
            self.segmentcursor = 'end'
            
    def get_xcursor(self, event):
        # event.button 1 corresponds to left mouse button
        if event.button == 1:
            # limit number of decimal places to two
            if self.segmentcursor == 'start':
                self.startedit.selectAll()
                self.startedit.insert('{:.2f}'.format(event.xdata))
            elif self.segmentcursor == 'end':
                self.endedit.selectAll()
                self.endedit.insert('{:.2f}'.format(event.xdata))
            # disable segment cursor again after value has been set
            self.segmentcursor = False  
            
    def emit_segment(self):
        begsamp = self.startedit.text()
        endsamp = self.endedit.text()
        self.segment_updated.emit([begsamp, endsamp])
        
    def reset_plot(self):
        self.ax0.clear()
        self.ax0.relim()
        self.ax1.clear()
        self.ax1.relim()
        self.canvas.draw()
        self.navitools.update()
        self.currentFile.clear()
