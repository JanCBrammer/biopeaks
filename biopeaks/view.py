# -*- coding: utf-8 -*-

from PySide2.QtWidgets import (QWidget, QComboBox, QAction, QMainWindow,
                               QVBoxLayout, QHBoxLayout, QCheckBox,
                               QLabel, QStatusBar, QGroupBox, QDockWidget,
                               QLineEdit, QFormLayout, QPushButton,
                               QProgressBar, QSplitter, QDialog)
from PySide2.QtCore import Qt, QSignalMapper, QRegExp
from PySide2.QtGui import QIcon, QRegExpValidator
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as
                                                FigureCanvas)
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as
                                                NavigationToolbar)
import biopeaks.resources    # noqa


class CustomNavigationToolbar(NavigationToolbar):
    # only retain desired functionality of navitoolbar
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in
                 ("Home", "Pan", "Zoom", "Back", "Forward")]


class View(QMainWindow):

    def __init__(self, model, controller):
        super().__init__()

        self._model = model
        self._controller = controller
        self.segmentcursor = False
        self.togglecolors = {"#1f77b4": "m", "m": "#1f77b4"}


        #################################################################
        # define GUI layout and connect input widgets to external slots #
        #################################################################

        self.setWindowTitle("biopeaks")
        self.setGeometry(50, 50, 1750, 750)
        self.setWindowIcon(QIcon(":/python_icon.png"))

        # figure0 for signal
        self.figure0 = Figure()
        self.canvas0 = FigureCanvas(self.figure0)
        # Enforce minimum height, otherwise resizing with self.splitter causes
        # mpl to throw an error because figure is resized to height 0. The
        # widget can still be fully collapsed with self.splitter-
        self.canvas0.setMinimumHeight(1)    # in pixels
        self.ax00 = self.figure0.add_subplot(1, 1, 1)
        self.ax00.set_frame_on(False)
        self.figure0.subplots_adjust(left=0.04, right=0.98, bottom=0.25)
        self.line00 = None
        self.scat = None
        self.segmentspan = None


        # figure1 for marker
        self.figure1 = Figure()
        self.canvas1 = FigureCanvas(self.figure1)
        self.canvas1.setMinimumHeight(1)
        self.ax10 = self.figure1.add_subplot(1, 1, 1, sharex=self.ax00)
        self.ax10.get_xaxis().set_visible(False)
        self.ax10.set_frame_on(False)
        self.figure1.subplots_adjust(left=0.04, right=0.98)
        self.line10 = None


        # figure2 for statistics
        self.figure2 = Figure()
        self.canvas2 = FigureCanvas(self.figure2)
        self.canvas2.setMinimumHeight(1)
        self.ax20 = self.figure2.add_subplot(3, 1, 1, sharex=self.ax00)
        self.ax20.get_xaxis().set_visible(False)
        self.ax20.set_frame_on(False)
        self.line20 = None
        self.ax21 = self.figure2.add_subplot(3, 1, 2, sharex=self.ax00)
        self.ax21.get_xaxis().set_visible(False)
        self.ax21.set_frame_on(False)
        self.line21 = None
        self.ax22 = self.figure2.add_subplot(3, 1, 3, sharex=self.ax00)
        self.ax22.get_xaxis().set_visible(False)
        self.ax22.set_frame_on(False)
        self.line22 = None
        self.figure2.subplots_adjust(left=0.04, right=0.98)

        # navigation bar
        self.navitools = CustomNavigationToolbar(self.canvas0, self)

        # peak editing
        self.editcheckbox = QCheckBox("editable", self)
        self.editcheckbox.stateChanged.connect(self._model.set_peakseditable)

        # peak saving batch
        self.savecheckbox = QCheckBox("save during batch processing", self)
        self.savecheckbox.stateChanged.connect(self._model.set_savebatchpeaks)

        # peak auto-correction batch
        self.correctcheckbox = QCheckBox("correct during batch processing",
                                         self)
        self.correctcheckbox.stateChanged.connect(self._model.set_correctbatchpeaks)

        # selecting stats for saving
        self.periodcheckbox = QCheckBox("period", self)
        self.periodcheckbox.stateChanged.connect(lambda: self.select_stats("period"))
        self.ratecheckbox = QCheckBox("rate", self)
        self.ratecheckbox.stateChanged.connect(lambda: self.select_stats("rate"))
        self.tidalampcheckbox = QCheckBox("tidal amplitude", self)
        self.tidalampcheckbox.stateChanged.connect(lambda: self.select_stats("tidalamp"))

        # channel selection
        self.sigchanmenulabel = QLabel("biosignal")
        self.sigchanmenu = QComboBox(self)
        self.sigchanmenu.addItem("A1")
        self.sigchanmenu.addItem("A2")
        self.sigchanmenu.addItem("A3")
        self.sigchanmenu.addItem("A4")
        self.sigchanmenu.addItem("A5")
        self.sigchanmenu.addItem("A6")
        self.sigchanmenu.currentTextChanged.connect(self._model.set_signalchan)
        # initialize with default value
        self._model.set_signalchan(self.sigchanmenu.currentText())

        self.markerchanmenulabel = QLabel("marker")
        self.markerchanmenu = QComboBox(self)
        self.markerchanmenu.addItem("none")
        self.markerchanmenu.addItem("I1")
        self.markerchanmenu.addItem("I2")
        self.markerchanmenu.addItem("A1")
        self.markerchanmenu.addItem("A2")
        self.markerchanmenu.addItem("A3")
        self.markerchanmenu.addItem("A4")
        self.markerchanmenu.addItem("A5")
        self.markerchanmenu.addItem("A6")
        self.markerchanmenu.currentTextChanged.connect(self._model.
                                                       set_markerchan)
        # initialize with default value
        self._model.set_markerchan(self.markerchanmenu.currentText())

        # processing mode (batch or single file)
        self.batchmenulabel = QLabel("mode")
        self.batchmenu = QComboBox(self)
        self.batchmenu.addItem("single file")
        self.batchmenu.addItem("multiple files")
        self.batchmenu.currentTextChanged.connect(self._model.set_batchmode)
        self.batchmenu.currentTextChanged.connect(self.toggle_options)
        # initialize with default value
        self._model.set_batchmode(self.batchmenu.currentText())
        self.toggle_options(self.batchmenu.currentText())

        # modality selection
        self.modmenulabel = QLabel("modality")
        self.modmenu = QComboBox(self)
        self.modmenu.addItem("ECG")
        self.modmenu.addItem("PPG")
        self.modmenu.addItem("RESP")
        self.modmenu.currentTextChanged.connect(self._model.set_modality)
        self.modmenu.currentTextChanged.connect(self.toggle_options)
        # initialize with default value
        self._model.set_modality(self.modmenu.currentText())
        self.toggle_options(self.modmenu.currentText())

        # segment selection; this widget can be openend / set visible from
        # the menu and closed from within itself (see mapping of segmentermap);
        # it provides utilities to select a segment from the signal
        self.segmentermap = QSignalMapper(self)
        self.segmenter = QDockWidget("select a segment", self)
        # disable closing such that widget can only be closed by confirming
        # selection or custom button
        self.segmenter.setFeatures(QDockWidget.NoDockWidgetFeatures)
        # Limit number of decimals to four.
        regex = QRegExp("[0-9]*\.?[0-9]{4}")
        validator = QRegExpValidator(regex)

        self.startlabel = QLabel("start")
        self.startedit = QLineEdit()
        self.startedit.setValidator(validator)

        self.endlabel = QLabel("end")
        self.endedit = QLineEdit()
        self.endedit.setValidator(validator)

        segmentfromcursor = QAction(QIcon(":/mouse_icon.png"),
                                    "select with mouse",
                                    self)
        segmentfromcursor.triggered.connect(self.enable_segmentedit)
        self.startedit.addAction(segmentfromcursor, QLineEdit.TrailingPosition)
        self.endedit.addAction(segmentfromcursor, QLineEdit.TrailingPosition)

        self.previewedit = QPushButton("preview segment")
        lambdafn = lambda: self._model.set_segment([self.startedit.text(),
                                                    self.endedit.text()])
        self.previewedit.clicked.connect(lambdafn)

        self.confirmedit = QPushButton("confirm segment")
        self.confirmedit.clicked.connect(self._controller.segment_signal)
        self.confirmedit.clicked.connect(self.segmentermap.map)
        self.segmentermap.setMapping(self.confirmedit, 0)

        self.abortedit = QPushButton("abort segmentation")
        self.abortedit.clicked.connect(self.segmentermap.map)
        # reset the segment to None
        self.segmentermap.setMapping(self.abortedit, 2)

        self.segmenterlayout = QFormLayout()
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


        # Set up dialog to gather user input for custom files.

        regex = QRegExp("[1-9][0-9]")
        validator = QRegExpValidator(regex)

        self.signallabel = QLabel("biosignal column")
        self.signaledit = QLineEdit()
        self.signaledit.setValidator(validator)

        self.markerlabel = QLabel("marker column")
        self.markeredit = QLineEdit()
        self.markeredit.setValidator(validator)

        regex = QRegExp("[0-9]{2}")
        validator = QRegExpValidator(regex)

        self.headerrowslabel = QLabel("number of header rows")
        self.headerrowsedit = QLineEdit()
        self.headerrowsedit.setValidator(validator)

        regex = QRegExp("[0-9]{5}")
        validator = QRegExpValidator(regex)

        self.sfreqlabel = QLabel("sampling rate")
        self.sfreqedit = QLineEdit()
        self.sfreqedit.setValidator(validator)

        self.separatorlabel = QLabel("column separator")
        self.separatormenu = QComboBox(self)
        self.separatormenu.addItem("comma")
        self.separatormenu.addItem("tab")
        self.separatormenu.addItem("colon")
        self.separatormenu.addItem("space")

        self.continuecustomfile = QPushButton("continue loading file")
        self.continuecustomfile.clicked.connect(self.set_customheader)

        self.customfiledialog = QDialog()
        self.customfiledialog.setWindowTitle("custom file info")
        self.customfiledialog.setWindowIcon(QIcon(":/file_icon.png"))
        self.customfiledialog.setWindowFlags(Qt.WindowCloseButtonHint)    # remove help button by only setting close button
        self.customfilelayout = QFormLayout()
        self.customfilelayout.addRow(self.signallabel, self.signaledit)
        self.customfilelayout.addRow(self.markerlabel, self.markeredit)
        self.customfilelayout.addRow(self.separatorlabel, self.separatormenu)
        self.customfilelayout.addRow(self.headerrowslabel, self.headerrowsedit)
        self.customfilelayout.addRow(self.sfreqlabel, self.sfreqedit)
        self.customfilelayout.addRow(self.continuecustomfile)
        self.customfiledialog.setLayout(self.customfilelayout)

        # set up menubar
        menubar = self.menuBar()

        # signal menu
        signalmenu = menubar.addMenu("biosignal")

        openSignal = signalmenu.addMenu("load")
        openEDF = QAction("EDF", self)
        openEDF.triggered.connect(lambda: self._model.set_filetype("EDF"))
        openEDF.triggered.connect(self._controller.get_fpaths)
        openSignal.addAction(openEDF)
        openOpenSignals = QAction("OpenSignals", self)
        openOpenSignals.triggered.connect(lambda: self._model.set_filetype("OpenSignals"))
        openOpenSignals.triggered.connect(self._controller.get_fpaths)
        openSignal.addAction(openOpenSignals)
        openCustom = QAction("Custom", self)
        openCustom.triggered.connect(lambda: self._model.set_filetype("Custom"))
        openCustom.triggered.connect(lambda: self.customfiledialog.exec_())
        openSignal.addAction(openCustom)

        segmentSignal = QAction("select segment", self)
        segmentSignal.triggered.connect(self.segmentermap.map)
        self.segmentermap.setMapping(segmentSignal, 1)
        signalmenu.addAction(segmentSignal)

        self.segmentermap.mapped.connect(self.toggle_segmenter)

        saveSignal = QAction("save", self)
        saveSignal.triggered.connect(self._controller.get_wpathsignal)
        signalmenu.addAction(saveSignal)

        # peak menu
        peakmenu = menubar.addMenu("peaks")

        findPeaks = QAction("find", self)
        findPeaks.triggered.connect(self._controller.find_peaks)
        peakmenu.addAction(findPeaks)

        autocorrectPeaks = QAction("autocorrect", self)
        autocorrectPeaks.triggered.connect(self._controller.autocorrect_peaks)
        peakmenu.addAction(autocorrectPeaks)

        savePeaks = QAction("save", self)
        savePeaks.triggered.connect(self._controller.get_wpathpeaks)
        peakmenu.addAction(savePeaks)

        loadPeaks = QAction("load", self)
        loadPeaks.triggered.connect(self._controller.get_rpathpeaks)
        peakmenu.addAction(loadPeaks)

        # stats menu
        statsmenu = menubar.addMenu("statistics")

        calculateStats = QAction("calculate", self)
        calculateStats.triggered.connect(self._controller.calculate_stats)
        statsmenu.addAction(calculateStats)

        saveStats = QAction("save", self)
        saveStats.triggered.connect(self._controller.get_wpathstats)
        statsmenu.addAction(saveStats)

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

        # connect canvas0 to keyboard and mouse input for peak editing;
        # only widgets (e.g. canvas) that currently have focus capture
        # keyboard input: "You must enable keyboard focus for a widget if
        # it processes keyboard events."
        self.canvas0.setFocusPolicy(Qt.ClickFocus)
        self.canvas0.setFocus()
        self.canvas0.mpl_connect("key_press_event",
                                 self._controller.edit_peaks)
        self.canvas0.mpl_connect("button_press_event", self.get_xcursor)

        # arrange the three figure canvases in splitter object
        self.splitter = QSplitter(Qt.Vertical)
        # setting opaque resizing to false is important, since resizing gets
        # very slow otherwise once axes are populated
        self.splitter.setOpaqueResize(False)
        self.splitter.addWidget(self.canvas0)
        self.splitter.addWidget(self.canvas1)
        self.splitter.addWidget(self.canvas2)
        self.splitter.setChildrenCollapsible(False)

        # define GUI layout
        self.vlayout0 = QVBoxLayout(self.centwidget)
        self.vlayout1 = QVBoxLayout()
        self.vlayoutA = QFormLayout()
        self.vlayoutB = QFormLayout()
        self.vlayoutC = QVBoxLayout()
        self.vlayoutD = QVBoxLayout()
        self.hlayout0 = QHBoxLayout()

        self.optionsgroupA = QGroupBox("processing options")
        self.vlayoutA.addRow(self.modmenulabel, self.modmenu)
        self.vlayoutA.addRow(self.batchmenulabel, self.batchmenu)
        self.optionsgroupA.setLayout(self.vlayoutA)

        self.optionsgroupB = QGroupBox("channels")
        self.vlayoutB.addRow(self.sigchanmenulabel, self.sigchanmenu)
        self.vlayoutB.addRow(self.markerchanmenulabel, self.markerchanmenu)
        self.optionsgroupB.setLayout(self.vlayoutB)

        self.optionsgroupC = QGroupBox("peaks")
        self.vlayoutC.addWidget(self.editcheckbox)
        self.vlayoutC.addWidget(self.savecheckbox)
        self.vlayoutC.addWidget(self.correctcheckbox)
        self.optionsgroupC.setLayout(self.vlayoutC)

        self.optionsgroupD = QGroupBox("select statistics for saving")
        self.vlayoutD.addWidget(self.periodcheckbox)
        self.vlayoutD.addWidget(self.ratecheckbox)
        self.vlayoutD.addWidget(self.tidalampcheckbox)
        self.optionsgroupD.setLayout(self.vlayoutD)

        self.vlayout1.addWidget(self.optionsgroupA)
        self.vlayout1.addWidget(self.optionsgroupB)
        self.vlayout1.addWidget(self.optionsgroupC)
        self.vlayout1.addWidget(self.optionsgroupD)
        self.optionsgroupwidget = QWidget()
        self.optionsgroupwidget.setLayout(self.vlayout1)
        self.optionsgroup = QDockWidget("configurations", self)
        self.optionsgroup.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.toggleoptionsgroup = self.optionsgroup.toggleViewAction()
        self.toggleoptionsgroup.setText("show/hide configurations")
        menubar.addAction(self.toggleoptionsgroup)
        self.optionsgroup.setWidget(self.optionsgroupwidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.optionsgroup)


        self.vlayout0.addWidget(self.splitter)

        self.hlayout0.addWidget(self.navitools)
        self.vlayout0.addLayout(self.hlayout0)

        ##############################################
        # connect output widgets to external signals #
        ##############################################
        self._model.signal_changed.connect(self.plot_signal)
        self._model.marker_changed.connect(self.plot_marker)
        self._model.peaks_changed.connect(self.plot_peaks)
        self._model.period_changed.connect(self.plot_period)
        self._model.rate_changed.connect(self.plot_rate)
        self._model.tidalamp_changed.connect(self.plot_tidalamp)
        self._model.path_changed.connect(self.display_path)
        self._model.segment_changed.connect(self.plot_segment)
        self._model.status_changed.connect(self.display_status)
        self._model.progress_changed.connect(self.display_progress)
        self._model.model_reset.connect(self.reset_plot)

    ###########
    # methods #
    ###########

    def plot_signal(self, value):
        self.ax00.clear()
        self.ax00.relim()
        # reset navitools history
        self.navitools.update()
        self.line00 = self.ax00.plot(self._model.sec, value, zorder=1)
        self.ax00.set_xlabel("seconds", fontsize="large", fontweight="heavy")
        self.canvas0.draw()
#        print("plot_signal listening")
#        print(self.ax0.collections, self.ax0.patches, self.ax0.artists)


    def plot_peaks(self, value):
        # self.scat is listed in ax.collections
        if self.ax00.collections:
            self.ax00.collections[0].remove()
        self.scat = self.ax00.scatter(self._model.sec[value],
                                      self._model.signal[value], c="m",
                                      zorder=2)
        self.canvas0.draw()
#        print("plot_peaks listening")
#        print(self.ax0.collections, self.ax0.patches, self.ax0.artists)


    def plot_segment(self, value):
        # If an invalid signal has been selected reset the segmenter interface.
        if value is None:
            self.toggle_segmenter(1)
            return
        if self.ax00.patches:    # self.segementspan is listed in ax.patches
            self.ax00.patches[0].remove()
        self.segmentspan = self.ax00.axvspan(value[0], value[1], color="m",
                                             alpha=0.25)
        self.canvas0.draw()
        self.confirmedit.setEnabled(True)
#        print(self.ax0.collections, self.ax0.patches, self.ax0.artists)


    def plot_marker(self, value):
        self.ax10.clear()
        self.ax10.relim()
        self.line10 = self.ax10.plot(value[0], value[1])
        self.canvas1.draw()
#        print("plot_marker listening")


    def plot_period(self, value):
        self.ax20.clear()
        self.ax20.relim()
        self.navitools.home()
        if self._model.savestats["period"]:
            self.line20 = self.ax20.plot(self._model.sec, value, c="m")
        else:
            self.line20 = self.ax20.plot(self._model.sec, value)
        self.ax20.set_ylim(bottom=min(value), top=max(value))
        self.ax20.set_title("period", pad=0, fontweight="heavy")
        self.ax20.grid(True, axis="y")
        self.navitools.update()
        self.canvas2.draw()
#        print("plot_period listening")


    def plot_rate(self, value):
        self.ax21.clear()
        self.ax21.relim()
        self.navitools.home()
        if self._model.savestats["rate"]:
            self.line21 = self.ax21.plot(self._model.sec, value, c="m")
        else:
            self.line21 = self.ax21.plot(self._model.sec, value)
        self.ax21.set_ylim(bottom=min(value), top=max(value))
        self.ax21.set_title("rate", pad=0, fontweight="heavy")
        self.ax21.grid(True, axis="y")
        self.navitools.update()
        self.canvas2.draw()
#        print("plot_rate listening")


    def plot_tidalamp(self, value):
        self.ax22.clear()
        self.ax22.relim()
        self.navitools.home()
        if self._model.savestats["tidalamp"]:
            self.line22 = self.ax22.plot(self._model.sec, value, c="m")
        else:
            self.line22 = self.ax22.plot(self._model.sec, value)
        self.ax22.set_ylim(bottom=min(value), top=max(value))
        self.ax22.set_title("amplitude", pad=0, fontweight="heavy")
        self.ax22.grid(True, axis="y")
        self.navitools.update()
        self.canvas2.draw()
#        print("plot_tidalamp listening")


    def display_path(self, value):
        self.currentFile.setText(value)


    def display_status(self, status):
        # display status until new status is set
        self.statusBar.showMessage(status)


    def display_progress(self, value):
        # if value is 0, the progressbar indicates a busy state
        self.progressBar.setRange(0, value)


    def toggle_segmenter(self, value):
        if not self._model.loaded:
            return
        # Open segmenter when called from signalmenu or clear segmenter
        # upon selection of invalid segment.
        if value == 1:
            self.segmenter.setVisible(True)
            self.confirmedit.setEnabled(False)
            self.startedit.clear()
            self.endedit.clear()
            if self.ax00.patches:
                self.ax00.patches[0].remove()
                self.canvas0.draw()
        # Close segmenter after segment has been confirmed.
        elif value == 0:
            self.segmenter.setVisible(False)
            if self.ax00.patches:
                self.ax00.patches[0].remove()
                self.canvas0.draw()
        # Close segmenter after segmentation has been aborted (reset
        # segment).
        elif value == 2:
            self._model.set_segment([0, 0])    # This will reset the model to None
            self.segmenter.setVisible(False)
            if self.ax00.patches:
                self.ax00.patches[0].remove()
                self.canvas0.draw()


    def enable_segmentedit(self):
        # disable peak editing to avoid interference
        self.editcheckbox.setChecked(False)
        if self.startedit.hasFocus():
            self.segmentcursor = "start"
        elif self.endedit.hasFocus():
            self.segmentcursor = "end"


    def set_customheader(self):
        """Populate the customheader with inputs from the customfiledialog"""

        # Check if one of the mandatory fields is missing.
        mandatoryfields = self.signaledit.text() and self.headerrowsedit.text() and self.sfreqedit.text()

        if not mandatoryfields:
            self._model.status = ("Please provide values for 'biosignal column'"
                                  ", 'number of header rows' and 'sampling"
                                  " rate'.")
            return

        seps = {"comma": ",", "tab": "\t", "colon": ":", "space": " "}
        self._model.customheader = dict.fromkeys(self._model.customheader, None)    # reset header here since it cannot be reset in controller.get_fpaths()

        self._model.customheader["signalidx"] = int(self.signaledit.text())
        self._model.customheader["skiprows"] = int(self.headerrowsedit.text())
        self._model.customheader["sfreq"] = int(self.sfreqedit.text())
        self._model.customheader["separator"] = seps[self.separatormenu.currentText()]
        if self.markeredit.text():    # not mandatory
            self._model.customheader["markeridx"] = int(self.markeredit.text())

        self.customfiledialog.done(QDialog.Accepted)    # close the dialog window
        self._controller.get_fpaths()    # move on to file selection


    def get_xcursor(self, event):
        # event.button 1 corresponds to left mouse button
        if event.button != 1:
            return
        # limit number of decimal places to two
        if self.segmentcursor == "start":
            self.startedit.selectAll()
            self.startedit.insert("{:.2f}".format(event.xdata))
        elif self.segmentcursor == "end":
            self.endedit.selectAll()
            self.endedit.insert("{:.2f}".format(event.xdata))
        # disable segment cursor again after value has been set
        self.segmentcursor = False


    def select_stats(self, event):
        """
        select or deselect statistics to be saved; toggle boolean with xor
        operator ^=, toggle color with dictionary
        """
        self._model.savestats[event] ^= True
        line = None
        if event == "period":
            if self.line20:
                line = self.line20[0]
        elif event == "rate":
            if self.line21:
                line = self.line21[0]
        elif event == "tidalamp":
            if self.line22:
                line = self.line22[0]
        if line:
            line.set_color(self.togglecolors[line.get_color()])
        self.canvas2.draw()


    def toggle_options(self, event):
        if event in ["ECG", "PPG"]:
            self.tidalampcheckbox.setEnabled(False)
            self.tidalampcheckbox.setChecked(False)
            self.ax22.set_visible(False)
            self.canvas2.draw()
        elif event == "RESP":
            self.tidalampcheckbox.setEnabled(True)
            self.ax22.set_visible(True)
            self.canvas2.draw()
        elif event == "multiple files":
            self.editcheckbox.setEnabled(False)
            self.editcheckbox.setChecked(False)
            self.savecheckbox.setEnabled(True)
            self.correctcheckbox.setEnabled(True)
            self.markerchanmenu.setEnabled(False)
        elif event == "single file":
            self.editcheckbox.setEnabled(True)
            self.markerchanmenu.setEnabled(True)
            self.savecheckbox.setEnabled(False)
            self.savecheckbox.setChecked(False)
            self.correctcheckbox.setEnabled(False)
            self.correctcheckbox.setChecked(False)


    def reset_plot(self):
        self.ax00.clear()
        self.ax00.relim()
        self.line00 = None
        self.scat = None
        self.segmentspan = None
        self.ax10.clear()
        self.ax10.relim()
        self.line10 = None
        self.ax20.clear()
        self.ax20.relim()
        self.line20 = None
        self.ax21.clear()
        self.ax21.relim()
        self.line21 = None
        self.ax22.clear()
        self.ax22.relim()
        self.line22 = None
        self.canvas0.draw()
        self.canvas1.draw()
        self.canvas2.draw()
        self.navitools.update()
        self.currentFile.clear()
