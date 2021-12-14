# -*- coding: utf-8 -*-
"""View component of the MVC application."""

from PySide6.QtWidgets import (QWidget, QComboBox, QMainWindow,
                               QVBoxLayout, QHBoxLayout, QCheckBox,
                               QLabel, QStatusBar, QGroupBox, QDockWidget,
                               QLineEdit, QFormLayout, QPushButton,
                               QProgressBar, QSplitter, QDialog)
from PySide6.QtCore import Qt, QSignalMapper, QRegularExpression
from PySide6.QtGui import QIcon, QRegularExpressionValidator, QAction
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as
                                                FigureCanvas)
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as
                                                NavigationToolbar)
import biopeaks.resources    # noqa


class CustomNavigationToolbar(NavigationToolbar):
    """Matplotlib navigation toolbar.

    Same as superclass except for removed Subplot-configuration and Save
    buttons.

    See Also
    --------
    matplotlib.backends.backend_qt5agg.NavigationToolbar2QT

    """

    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in
                 ("Home", "Pan", "Zoom", "Back", "Forward")]    # only retain desired functionality


class View(QMainWindow):
    """View component of the MVC application.

    Presents the state of the application as well as the available means of
    interaction. Receives updates about the state from the Model and informs
    Controller about user interactions.

    """

    def __init__(self, model, controller):
        """Define GUI elements and their layout.

        Parameters
        ----------
        model : QObject
            Model component of the MVC application.
        controller : QObject
            Controller component of the MVC application.
        """
        super().__init__()

        self._model = model
        self._controller = controller
        self.segmentcursor = False
        self.togglecolors = {"#1f77b4": "m", "m": "#1f77b4"}

        self.setWindowTitle("biopeaks")
        self.setGeometry(50, 50, 1750, 750)
        self.setWindowIcon(QIcon(":/python_icon.png"))

        # Figure for biosignal.
        self.figure0 = Figure()
        self.canvas0 = FigureCanvas(self.figure0)
        # Enforce minimum height, otherwise resizing with self.splitter causes
        # mpl to throw an error because figure is resized to height 0. The
        # widget can still be fully collapsed with self.splitter.
        self.canvas0.setMinimumHeight(1)    # in pixels
        self.ax00 = self.figure0.add_subplot(1, 1, 1)
        self.ax00.set_frame_on(False)
        self.figure0.subplots_adjust(left=0.04, right=0.98, bottom=0.25)
        self.line00 = None
        self.scat = None
        self.segmentspan = None

        # Figure for marker.
        self.figure1 = Figure()
        self.canvas1 = FigureCanvas(self.figure1)
        self.canvas1.setMinimumHeight(1)
        self.ax10 = self.figure1.add_subplot(1, 1, 1, sharex=self.ax00)
        self.ax10.get_xaxis().set_visible(False)
        self.ax10.set_frame_on(False)
        self.figure1.subplots_adjust(left=0.04, right=0.98)
        self.line10 = None

        # Figure for statistics.
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

        self.navitools = CustomNavigationToolbar(self.canvas0, self)

        # Peak editing.
        self.editcheckbox = QCheckBox("editable", self)
        self.editcheckbox.stateChanged.connect(self._model.set_peakseditable)

        # Peak saving during batch processing.
        self.savecheckbox = QCheckBox("save during batch processing", self)
        self.savecheckbox.stateChanged.connect(self._model.set_savebatchpeaks)

        # Peak auto-correction during batch processing.
        self.correctcheckbox = QCheckBox("correct during batch processing",
                                         self)
        self.correctcheckbox.stateChanged.connect(self._model.set_correctbatchpeaks)

        # Selection of stats for saving.
        self.periodcheckbox = QCheckBox("period", self)
        self.periodcheckbox.stateChanged.connect(lambda: self.select_stats("period"))
        self.ratecheckbox = QCheckBox("rate", self)
        self.ratecheckbox.stateChanged.connect(lambda: self.select_stats("rate"))
        self.tidalampcheckbox = QCheckBox("tidal amplitude", self)
        self.tidalampcheckbox.stateChanged.connect(lambda: self.select_stats("tidalamp"))

        # Channel selection.
        self.sigchanmenulabel = QLabel("biosignal")
        self.sigchanmenu = QComboBox(self)
        self.sigchanmenu.addItem("A1")
        self.sigchanmenu.addItem("A2")
        self.sigchanmenu.addItem("A3")
        self.sigchanmenu.addItem("A4")
        self.sigchanmenu.addItem("A5")
        self.sigchanmenu.addItem("A6")
        self.sigchanmenu.currentTextChanged.connect(self._model.set_signalchan)
        self._model.set_signalchan(self.sigchanmenu.currentText())    # initialize with default value

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
        self._model.set_markerchan(self.markerchanmenu.currentText())

        # Processing mode.
        self.batchmenulabel = QLabel("mode")
        self.batchmenu = QComboBox(self)
        self.batchmenu.addItem("single file")
        self.batchmenu.addItem("multiple files")
        self.batchmenu.currentTextChanged.connect(self._model.set_batchmode)
        self.batchmenu.currentTextChanged.connect(self.toggle_options)
        self._model.set_batchmode(self.batchmenu.currentText())
        self.toggle_options(self.batchmenu.currentText())

        # Modality selection.
        self.modmenulabel = QLabel("modality")
        self.modmenu = QComboBox(self)
        self.modmenu.addItem("ECG")
        self.modmenu.addItem("PPG")
        self.modmenu.addItem("RESP")
        self.modmenu.currentTextChanged.connect(self._model.set_modality)
        self.modmenu.currentTextChanged.connect(self.toggle_options)
        self._model.set_modality(self.modmenu.currentText())
        self.toggle_options(self.modmenu.currentText())

        # Segment selection. This widget can be openend / set visible from
        # the menu and closed from within itself (see mapping of segmentermap).
        self.segmentermap = QSignalMapper(self)
        self.segmenter = QDockWidget("select a segment", self)
        self.segmenter.setFeatures(QDockWidget.NoDockWidgetFeatures)    # disable closing such that widget can only be closed by confirming selection or custom button
        regex = QRegularExpression("[0-9]*\.?[0-9]{4}")    # Limit number of decimals to four

        validator = QRegularExpressionValidator(regex)

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
        self.confirmedit.clicked.connect(self._controller.segment_dataset)
        self.confirmedit.clicked.connect(self.segmentermap.map)
        self.segmentermap.setMapping(self.confirmedit, 0)

        self.abortedit = QPushButton("abort segmentation")
        self.abortedit.clicked.connect(self.segmentermap.map)
        self.segmentermap.setMapping(self.abortedit, 2)    # resets the segment to None

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

        # Custom file dialog.
        regex = QRegularExpression("[1-9][0-9]")
        validator = QRegularExpressionValidator(regex)

        self.signallabel = QLabel("biosignal column")
        self.signaledit = QLineEdit()
        self.signaledit.setValidator(validator)

        self.markerlabel = QLabel("marker column")
        self.markeredit = QLineEdit()
        self.markeredit.setValidator(validator)

        regex = QRegularExpression("[0-9]{2}")
        validator = QRegularExpressionValidator(regex)

        self.headerrowslabel = QLabel("number of header rows")
        self.headerrowsedit = QLineEdit()
        self.headerrowsedit.setValidator(validator)

        regex = QRegularExpression("[0-9]{5}")
        validator = QRegularExpressionValidator(regex)

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

        # Layout.
        menubar = self.menuBar()

        signalmenu = menubar.addMenu("biosignal")

        openSignal = signalmenu.addMenu("load")
        openEDF = QAction("EDF", self)
        openEDF.triggered.connect(lambda: self._model.set_filetype("EDF"))
        openEDF.triggered.connect(self._controller.load_channels)
        openSignal.addAction(openEDF)
        openOpenSignals = QAction("OpenSignals", self)
        openOpenSignals.triggered.connect(lambda: self._model.set_filetype("OpenSignals"))
        openOpenSignals.triggered.connect(self._controller.load_channels)
        openSignal.addAction(openOpenSignals)
        openCustom = QAction("Custom", self)
        openCustom.triggered.connect(lambda: self._model.set_filetype("Custom"))
        openCustom.triggered.connect(lambda: self.customfiledialog.exec_())
        openSignal.addAction(openCustom)

        segmentSignal = QAction("select segment", self)
        segmentSignal.triggered.connect(self.segmentermap.map)
        self.segmentermap.setMapping(segmentSignal, 1)
        signalmenu.addAction(segmentSignal)

        self.segmentermap.mappedInt.connect(self.toggle_segmenter)

        saveSignal = QAction("save", self)
        saveSignal.triggered.connect(self._controller.save_channels)
        signalmenu.addAction(saveSignal)

        peakmenu = menubar.addMenu("peaks")

        findPeaks = QAction("find", self)
        findPeaks.triggered.connect(self._controller.find_peaks)
        peakmenu.addAction(findPeaks)

        autocorrectPeaks = QAction("autocorrect", self)
        autocorrectPeaks.triggered.connect(self._controller.autocorrect_peaks)
        peakmenu.addAction(autocorrectPeaks)

        savePeaks = QAction("save", self)
        savePeaks.triggered.connect(self._controller.save_peaks)
        peakmenu.addAction(savePeaks)

        loadPeaks = QAction("load", self)
        loadPeaks.triggered.connect(self._controller.load_peaks)
        peakmenu.addAction(loadPeaks)

        statsmenu = menubar.addMenu("statistics")

        calculateStats = QAction("calculate", self)
        calculateStats.triggered.connect(self._controller.calculate_stats)
        statsmenu.addAction(calculateStats)

        saveStats = QAction("save", self)
        saveStats.triggered.connect(self._controller.save_stats)
        statsmenu.addAction(saveStats)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 1)
        self.statusBar.addPermanentWidget(self.progressBar)
        self.currentFile = QLabel()
        self.statusBar.addPermanentWidget(self.currentFile)

        self.centwidget = QWidget()    # contains figures and navigationtoolbar
        self.setCentralWidget(self.centwidget)

        self.canvas0.setFocusPolicy(Qt.ClickFocus)    # only widgets (e.g. canvas) that currently have focus capture keyboard input
        self.canvas0.setFocus()
        self.canvas0.mpl_connect("key_press_event",
                                 self._controller.edit_peaks)    # connect canvas to keyboard input for peak editing
        self.canvas0.mpl_connect("button_press_event", self.get_xcursor)    # connect canvas to mouse input for peak editing

        self.splitter = QSplitter(Qt.Vertical)    # arrange the three figure canvases in splitter object
        self.splitter.setOpaqueResize(False)    # resizing gets very slow otherwise once axes are populated
        self.splitter.addWidget(self.canvas0)
        self.splitter.addWidget(self.canvas1)
        self.splitter.addWidget(self.canvas2)
        self.splitter.setChildrenCollapsible(False)

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

        # Subscribe to updates from the Model.
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

    def plot_signal(self, signal):
        """Plot the biosignal.

        Receives updates in signal from Model.

        Parameters
        ----------
        signal : ndarray of float
            Vector representing the biosignal.

        See Also
        --------
        model.Model.signal
        """
        self.ax00.clear()
        self.ax00.relim()
        self.navitools.update()    # reset navitools history
        self.line00 = self.ax00.plot(self._model.sec, signal, zorder=1)
        self.ax00.set_xlabel("seconds", fontsize="large", fontweight="heavy")
        self.canvas0.draw()

    def plot_peaks(self, peaks):
        """Plot the extrema.

        Receives updates in peaks from Model.

        Parameters
        ----------
        peaks : ndarray of int
            Vector representing the extrema.

        See Also
        --------
        model.Model.peaks
        """
        if self.ax00.collections:    # self.scat is listed in ax.collections
            self.ax00.collections[0].remove()
        self.scat = self.ax00.scatter(self._model.sec[peaks],
                                      self._model.signal[peaks], c="m",
                                      zorder=2)
        self.canvas0.draw()

    def plot_segment(self, segment):
        """Show preview of segment.

        Receives updates in segment from Model.

        Parameters
        ----------
        segment : list of float
            The start and end of the segment in seconds.

        See Also
        --------
        model.Model.segment
        """
        if segment is None:    # if an invalid segment has been selected reset the segmenter interface
            self.toggle_segmenter(1)
            return
        if self.ax00.patches:    # self.segementspan is listed in ax.patches
            self.ax00.patches[0].remove()
        self.segmentspan = self.ax00.axvspan(segment[0], segment[1], color="m",
                                             alpha=0.25)
        self.canvas0.draw()
        self.confirmedit.setEnabled(True)

    def plot_marker(self, marker):
        """Plot the marker channel.

        Receives updates in marker from Model.

        Parameters
        ----------
        marker : list of ndarray
            Seconds element is vector representing the marker channel and first
            element is a vector representing the seconds associated with each
            sample in the marker channel.

        See Also
        --------
        model.Model.marker
        """
        self.ax10.clear()
        self.ax10.relim()
        self.line10 = self.ax10.plot(marker[0], marker[1])
        self.canvas1.draw()

    def plot_period(self, period):
        """Plot instantaneous period.

        Receives updates in period from Model.

        Parameters
        ----------
        period : ndarray of float
            Vector representing the instantaneous period.

        See Also
        --------
        model.Model.periodintp
        """
        self.ax20.clear()
        self.ax20.relim()
        self.navitools.home()
        if self._model.savestats["period"]:
            self.line20 = self.ax20.plot(self._model.sec, period, c="m")
        else:
            self.line20 = self.ax20.plot(self._model.sec, period)
        self.ax20.set_ylim(bottom=min(period), top=max(period))
        self.ax20.set_title("period", pad=0, fontweight="heavy")
        self.ax20.grid(True, axis="y")
        self.navitools.update()
        self.canvas2.draw()

    def plot_rate(self, rate):
        """Plot instantaneous rate.

        Receives updates in rate from Model.

        Parameters
        ----------
        rate : ndarray of float
            Vector representing the instantaneous rate.

        See Also
        --------
        model.Model.rateintp
        """
        self.ax21.clear()
        self.ax21.relim()
        self.navitools.home()
        if self._model.savestats["rate"]:
            self.line21 = self.ax21.plot(self._model.sec, rate, c="m")
        else:
            self.line21 = self.ax21.plot(self._model.sec, rate)
        self.ax21.set_ylim(bottom=min(rate), top=max(rate))
        self.ax21.set_title("rate", pad=0, fontweight="heavy")
        self.ax21.grid(True, axis="y")
        self.navitools.update()
        self.canvas2.draw()

    def plot_tidalamp(self, tidalamp):
        """Plot instantaneous tidal amplitude.

        Receives updates in tidal amplitude from Model.

        Parameters
        ----------
        tidalamp : ndarray of float
            Vector representing the instantaneous tidal amplitude.

        See Also
        --------
        model.Model.tidalampintp
        """
        self.ax22.clear()
        self.ax22.relim()
        self.navitools.home()
        if self._model.savestats["tidalamp"]:
            self.line22 = self.ax22.plot(self._model.sec, tidalamp, c="m")
        else:
            self.line22 = self.ax22.plot(self._model.sec, tidalamp)
        self.ax22.set_ylim(bottom=min(tidalamp), top=max(tidalamp))
        self.ax22.set_title("amplitude", pad=0, fontweight="heavy")
        self.ax22.grid(True, axis="y")
        self.navitools.update()
        self.canvas2.draw()

    def display_path(self, path):
        """Display the path to the current dataset.

        Receives update in path from Model.

        Parameters
        ----------
        path : str
            The path to the file containing the current dataset.

        See Also
        --------
        model.Model.rpathsignal
        """
        self.currentFile.setText(path)

    def display_status(self, status):
        """Display a status message.

        Receives updates in status message from Model.

        Parameters
        ----------
        status : str
            A status message.

        See Also
        --------
        model.Model.status
        """
        self.statusBar.showMessage(status)

    def display_progress(self, progress):
        """Display task progress.

        Receives updates in progress from Model.

        Parameters
        ----------
        progress : int
            Integer indicating the current task progress.

        See Also
        --------
        model.Model.progress, controller.Worker, controller.threaded
        """
        self.progressBar.setRange(0, progress)    # indicates busy state if progress is 0

    def toggle_segmenter(self, visibility_state):
        """Toggle visibility of segmenter widget.

        Parameters
        ----------
        visibility_state : int
            Update in state of the segmenter widget's visibility.
        """
        if not self._model.loaded:
            return
        if visibility_state == 1:    # open segmenter when called from signalmenu or clear segmenter upon selection of invalid segment
            self.segmenter.setVisible(True)
            self.confirmedit.setEnabled(False)
            self.startedit.clear()
            self.endedit.clear()
        elif visibility_state == 0:    # close segmenter after segment has been confirmed
            self.segmenter.setVisible(False)
        elif visibility_state == 2:    # close segmenter after segmentation has been aborted (reset segment)
            self._model.set_segment([0, 0])
            self.segmenter.setVisible(False)
        if self.ax00.patches:
            self.ax00.patches[0].remove()
            self.canvas0.draw()

    def enable_segmentedit(self):
        """Associate cursor position with a specific segmenter text field.

        Regulate if cursor position is associated with editing the start or
        end of a segment.
        """
        self.editcheckbox.setChecked(False)    # disable peak editing to avoid interference
        if self.startedit.hasFocus():
            self.segmentcursor = "start"
        elif self.endedit.hasFocus():
            self.segmentcursor = "end"

    def get_xcursor(self, mouse_event):
        """Retrieve input to segmenter text fields from cursor position.

        Retrieve the start or end of a segment in seconds from the current
        cursor position.

        Parameters
        ----------
        mouse_event : MouseEvent
            Event containing information about the current cursor position
            in data coordinates.

        See Also
        --------
        matplotlib.backend_bases.MouseEvent
        """
        if mouse_event.button != 1:    # 1 = left mouse button
            return
        if self.segmentcursor == "start":
            self.startedit.selectAll()
            self.startedit.insert("{:.2f}".format(mouse_event.xdata))    # limit number of decimal places to two
        elif self.segmentcursor == "end":
            self.endedit.selectAll()
            self.endedit.insert("{:.2f}".format(mouse_event.xdata))
        self.segmentcursor = False    # disable segment cursor again after value has been set

    def set_customheader(self):
        """Populate the customheader with inputs from the customfiledialog."""
        mandatoryfields = self.signaledit.text() and self.headerrowsedit.text() and self.sfreqedit.text()    # check if one of the mandatory fields is missing

        if not mandatoryfields:
            self._model.status = ("Please provide values for 'biosignal column'"
                                  ", 'number of header rows' and 'sampling"
                                  " rate'.")
            return

        seps = {"comma": ",", "tab": "\t", "colon": ":", "space": " "}
        self._model.customheader = dict.fromkeys(self._model.customheader, None)    # reset header here since it cannot be reset in controller.load_chanels

        self._model.customheader["signalidx"] = int(self.signaledit.text())
        self._model.customheader["skiprows"] = int(self.headerrowsedit.text())
        self._model.customheader["sfreq"] = int(self.sfreqedit.text())
        self._model.customheader["separator"] = seps[self.separatormenu.currentText()]
        if self.markeredit.text():    # not mandatory
            self._model.customheader["markeridx"] = int(self.markeredit.text())

        self.customfiledialog.done(QDialog.Accepted)    # close the dialog window
        self._controller.load_channels()    # move on to file selection

    def select_stats(self, statistic):
        """Select statistics to be saved.

        Parameters
        ----------
        statistic : str
            The selected statistic.
        """
        self._model.savestats[statistic] ^= True    # toggle boolean with xor operator
        line = None
        if statistic == "period":
            if self.line20:
                line = self.line20[0]
        elif statistic == "rate":
            if self.line21:
                line = self.line21[0]
        elif statistic == "tidalamp":
            if self.line22:
                line = self.line22[0]
        if line:
            line.set_color(self.togglecolors[line.get_color()])
        self.canvas2.draw()

    def toggle_options(self, state):
        """Toggle availability of configuration options.

        Based on current state.

        Parameters
        ----------
        state : str
            The aspect of the current state to which the availability of
            configuration options needs to be adapted.
        """
        if state in ["ECG", "PPG"]:
            self.tidalampcheckbox.setEnabled(False)
            self.tidalampcheckbox.setChecked(False)
            self.ax22.set_visible(False)
            self.canvas2.draw()
        elif state == "RESP":
            self.tidalampcheckbox.setEnabled(True)
            self.ax22.set_visible(True)
            self.canvas2.draw()
        elif state == "multiple files":
            self.editcheckbox.setEnabled(False)
            self.editcheckbox.setChecked(False)
            self.savecheckbox.setEnabled(True)
            self.correctcheckbox.setEnabled(True)
            self.markerchanmenu.setEnabled(False)
        elif state == "single file":
            self.editcheckbox.setEnabled(True)
            self.markerchanmenu.setEnabled(True)
            self.savecheckbox.setEnabled(False)
            self.savecheckbox.setChecked(False)
            self.correctcheckbox.setEnabled(False)
            self.correctcheckbox.setChecked(False)

    def reset_plot(self):
        """Reset plot elements associated with the current dataset."""
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
