# -*- coding: utf-8 -*-

'''
Test GUI with a few functional tests (as opposed to unit tests that cover every
function, or integration tests):

https://codeutopia.net/blog/2015/04/11/what-are-unit-testing-integration-
testing-and-functional-testing/

"You shouldn’t try to make very fine grained functional tests. You don’t want
to test a single function, despite the name “functional” perhaps hinting at it.
Instead, functional tests should be used for testing common user interactions.
If you would manually test a certain flow of your app in a browser, such as
registering an account, you could make that into a functional test."

The tests will be restricted to a few typical, meaningful workflows (i.e.,
sequences of function calls), since testing all possible workflows is
unfeasible and for a majority of workflows meaningless (e.g., saving peaks
before finding peaks etc.).

Note that the timeouts used in qtbot.waitSignal(s) might cause flaky tests
depending on which machine runs the tests.
'''

import pytest
from pathlib import Path
import numpy as np
import pandas as pd
from PySide2.QtCore import Qt
from biopeaks.model import Model
from biopeaks.view import View
from biopeaks.controller import Controller


class MockKeyEvent(object):
    def __init__(self, key, xdata):
        super(MockKeyEvent, self).__init__()
        self.key = key
        self.xdata = xdata


datadir = Path(__file__).parent.resolve().joinpath("testdata")

ppg_os = {"modality": "PPG",
          "sigchan": "A1",
          "markerchan": "I1",
          "mode": "single file",
          "sigpathorig": datadir.joinpath("OSmontagePPG.txt"),
          "sigfnameseg": "testdata_segmented.txt",
          "peakfname": "testdata_segmented_peaks.csv",
          "statsfname": "testdata_segmented_stats.csv",
          "sfreq": 125,
          "siglen": 60001,
          "siglenseg": 8750,
          "markerlen": 60001,
          "markerlenseg": 8750,
          "peaksum": 461362,
          "avgperiod": 0.6652,
          "avgrate": 90.7158,
          "segment": [20, 90],
          "filetype": "OpenSignals"}

ppg_custom = {"modality": "PPG",
              "header": {"signalidx": 6, "markeridx": 1, "skiprows": 3,
                         "sfreq": 125, "separator": "\t"},
              "mode": "single file",
              "sigpathorig": datadir.joinpath("OSmontagePPG.txt"),
              "sigfnameseg": "testdata_segmented.txt",
              "peakfname": "testdata_segmented_peaks.csv",
              "statsfname": "testdata_segmented_stats.csv",
              "siglen": 60001,
              "siglenseg": 8750,
              "markerlen": 60001,
              "markerlenseg": 8750,
              "peaksum": 461362,
              "avgperiod": 0.6652,
              "avgrate": 90.7158,
              "segment": [20, 90],
              "filetype": "Custom"}

ppg_edf = {"modality": "PPG",
           "sigchan": "A5",
           "markerchan": "A1",
           "mode": "single file",
           "sigpathorig": datadir.joinpath("EDFmontage0.edf"),
           "sigfnameseg": "testdata_segmented.edf",
           "peakfname": "testdata_segmented_peaks.csv",
           "statsfname": "testdata_segmented_stats.csv",
           "sfreq": 50,
           "siglen": 45000,
           "siglenseg": 3500,
           "markerlen": 180000,
           "markerlenseg": 14000,
           "peaksum": 123270,
           "avgperiod": 1.0000,
           "avgrate": 60.0000,
           "segment": [11.51, 81.7],
           "filetype": "EDF"}

ecg_os = {"modality": "ECG",
          "sigchan": "A3",
          "markerchan": "I1",
          "mode": "single file",
          "sigpathorig": Path(datadir).joinpath("OSmontage0J.txt"),
          "sigfnameseg": "testdata_segmented.txt",
          "peakfname": "testdata_segmented_peaks.csv",
          "statsfname": "testdata_segmented_stats.csv",
          "sfreq": 1000,
          "siglen": 5100000,
          "siglenseg": 100000,
          "markerlen": 5100000,
          "markerlenseg": 100000,
          "peaksum": 4572190,
          "avgperiod": 1.0921,
          "avgrate": 55.1027,
          "segment": [760, 860],
          "filetype": "OpenSignals"}

ecg_custom = {"modality": "ECG",
              "header": {"signalidx": 7, "markeridx": 1, "skiprows": 3,
                         "sfreq": 1000, "separator": "\t"},
              "mode": "single file",
              "sigpathorig": Path(datadir).joinpath("OSmontage0J.txt"),
              "sigfnameseg": "testdata_segmented.txt",
              "peakfname": "testdata_segmented_peaks.csv",
              "statsfname": "testdata_segmented_stats.csv",
              "siglen": 5100000,
              "siglenseg": 100000,
              "markerlen": 5100000,
              "markerlenseg": 100000,
              "peaksum": 4572190,
              "avgperiod": 1.0921,
              "avgrate": 55.1027,
              "segment": [760, 860],
              "filetype": "Custom"}

ecg_edf = {"modality": "ECG",
           "sigchan": "A3",
           "markerchan": "A1",
           "mode": "single file",
           "sigpathorig": datadir.joinpath("EDFmontage0.edf"),
           "sigfnameseg": "testdata_segmented.edf",
           "peakfname": "testdata_segmented_peaks.csv",
           "statsfname": "testdata_segmented_stats.csv",
           "sfreq": 200,
           "siglen": 180000,
           "siglenseg": 14000,
           "markerlen": 180000,
           "markerlenseg": 14000,
           "peaksum": 1228440,
           "avgperiod": 0.4000,
           "avgrate": 150.0000,
           "segment": [11.51, 81.7],
           "filetype": "EDF"}

rsp_os = {"modality": "RESP",
          "sigchan": "A2",
          "markerchan": "I1",
          "mode": "single file",
          "sigpathorig": datadir.joinpath("OSmontage0J.txt"),
          "sigfnameseg": "testdata_segmented.txt",
          "peakfname": "testdata_segmented_peaks.csv",
          "statsfname": "testdata_segmented_stats.csv",
          "sfreq": 1000,
          "siglen": 5100000,
          "siglenseg": 200000,
          "markerlen": 5100000,
          "markerlenseg": 200000,
          "peaksum": 13355662,
          "avgperiod": 3.2676,
          "avgrate": 19.7336,
          "avgtidalamp": 129.722,
          "segment": [3200, 3400],
          "filetype": "OpenSignals"}

rsp_custom = {"modality": "RESP",
              "header" : {"signalidx": 6, "markeridx": 1, "skiprows": 3,
                          "sfreq": 1000, "separator": "\t"},
              "mode": "single file",
              "sigpathorig": datadir.joinpath("OSmontage0J.txt"),
              "sigfnameseg": "testdata_segmented.txt",
              "peakfname": "testdata_segmented_peaks.csv",
              "statsfname": "testdata_segmented_stats.csv",
              "siglen": 5100000,
              "siglenseg": 200000,
              "markerlen": 5100000,
              "markerlenseg": 200000,
              "peaksum": 13355662,
              "avgperiod": 3.2676,
              "avgrate": 19.7336,
              "avgtidalamp": 129.722,
              "segment": [3200, 3400],
              "filetype": "Custom"}

rsp_edf = {"modality": "RESP",
           "sigchan": "A5",
           "markerchan": "A1",
           "mode": "single file",
           "sigpathorig": datadir.joinpath("EDFmontage0.edf"),
           "sigfnameseg": "testdata_segmented.edf",
           "peakfname": "testdata_segmented_peaks.csv",
           "statsfname": "testdata_segmented_stats.csv",
           "sfreq": 50,
           "siglen": 45000,
           "siglenseg": 3800,
           "markerlen": 180000,
           "markerlenseg": 15200,
           "peaksum": 276760,
           "avgperiod": 1.0000,
           "avgrate": 60.0003,
           "avgtidalamp": 16350.0000,
           "segment": [602.6, 679.26],
           "filetype": "EDF"}


def idcfg_single(cfg):
    """Generate a test ID."""
    modality = cfg["modality"]
    filetype = cfg["filetype"]

    return f"{modality}:{filetype}"


@pytest.fixture(params=[ppg_os, ppg_custom, ppg_edf,
                        ecg_os, ecg_custom, ecg_edf,
                        rsp_os, rsp_custom, rsp_edf],
                ids=idcfg_single)    # automatically runs the test(s) using this fixture with all values of params
def cfg_single(request):
    return request.param


def test_singlefile(qtbot, tmpdir, cfg_single):

    # Set up application.
    model = Model()
    controller = Controller(model)
    view = View(model, controller)
    qtbot.addWidget(view)
    view.show()

    # Configure options.
    if cfg_single["filetype"] == "Custom":
        model.customheader = cfg_single["header"]
    else:
        qtbot.keyClicks(view.sigchanmenu, cfg_single["sigchan"])
        qtbot.keyClicks(view.markerchanmenu, cfg_single["markerchan"])
    qtbot.keyClicks(view.modmenu, cfg_single["modality"])
    qtbot.keyClicks(view.batchmenu, cfg_single["mode"])
    model.set_filetype(cfg_single["filetype"])

    # 1. load signal #########################################################
    model.fpaths = [cfg_single["sigpathorig"]]
    with qtbot.waitSignals([model.signal_changed, model.marker_changed],
                           timeout=10000):
        controller.read_channels()
    assert np.size(model.signal) == cfg_single["siglen"]
    assert np.size(model.sec) == cfg_single["siglen"]
    assert np.size(model.marker) == cfg_single["markerlen"]
    sfreq = cfg_single["header"]["sfreq"] if cfg_single["filetype"] == "Custom" else cfg_single["sfreq"]
    assert model.sfreq == sfreq
    assert model.loaded

    # 2. segment signal ######################################################
    with qtbot.waitSignal(model.segment_changed, timeout=5000):
        model.set_segment(values=cfg_single["segment"])
    assert model.segment == cfg_single["segment"]
    with qtbot.waitSignal(model.signal_changed, timeout=5000):
        controller.segment_signal()
    seg = int(np.rint((cfg_single["segment"][1] - cfg_single["segment"][0]) *
                      model.sfreq))
    assert np.allclose(np.size(model.signal), seg, atol=1)
    assert np.allclose(np.size(model.sec), seg, atol=1)

    # 3. save segment ########################################################
    model.wpathsignal = tmpdir.join(cfg_single["sigfnameseg"])
    with qtbot.waitSignals([model.progress_changed] * 2, timeout=10000):
        controller.save_channels()

    # 4. find extrema #########################################################
    with qtbot.waitSignal(model.peaks_changed, timeout=5000):
        controller.find_peaks()
    assert sum(model.peaks) == cfg_single["peaksum"]

    # 5. edit extrema #########################################################
    view.editcheckbox.setCheckState(Qt.Checked)
    # Engage editing (click on canvas to give it the focus).
    qtbot.mouseClick(view.canvas0, Qt.LeftButton)
    # Since it is very tedious to map from matplotlib figure canvas
    # coordinates to qt coordinates, the controllers edit_peaks method is
    # called with a mocked KeyEvent. To test edit_peaks delete the first peak
    # and then add it again.
    demopeak = model.peaks[0] / model.sfreq
    mock_key_event = MockKeyEvent(key='d', xdata=demopeak)
    controller.edit_peaks(mock_key_event)
    assert model.peaks[0] / model.sfreq > demopeak
    mock_key_event = MockKeyEvent(key='a', xdata=demopeak)
    controller.edit_peaks(mock_key_event)
    # Note that edit_peaks places the peak in the middle of the plateau in
    # case of a flat peak, hence discrepancies of a few msecs can arise. Set
    # tolerance for deviation of re-inserted peak to 25 msec.
    assert abs(model.peaks[0] / model.sfreq - demopeak) <= .025
    view.editcheckbox.setCheckState(Qt.Unchecked)

    # 6. save peaks ###########################################################
    model.wpathpeaks = tmpdir.join(cfg_single["peakfname"])
    with qtbot.waitSignals([model.progress_changed] * 2, timeout=10000):
        controller.save_peaks()

    # 7. re-load signal #######################################################
    model.fpaths = [tmpdir.join(cfg_single["sigfnameseg"])]
    with qtbot.waitSignals([model.signal_changed, model.marker_changed],
                           timeout=10000):
        controller.read_channels()
    sfreq = cfg_single["header"]["sfreq"] if cfg_single["filetype"] == "Custom" else cfg_single["sfreq"]
    assert model.sfreq == sfreq
    assert model.loaded
    # Increase tolerance to 38, since for EDF files data needs to be saved as
    # epochs of fixed size which can lead to deviations from original segment
    # length.
    assert np.allclose(np.size(model.signal), seg, atol=38)
    assert np.allclose(np.size(model.sec), seg, atol=38)
    assert np.size(model.signal) == np.size(model.sec)

    # 8. load peaks ###########################################################
    model.rpathpeaks = tmpdir.join(cfg_single["peakfname"])
    with qtbot.waitSignal(model.peaks_changed, timeout=5000):
        controller.read_peaks()
    # For the breathing, after peak editing, the re-inserted peak can
    # be shifted by a few samples. This is not a bug, but inherent in the
    # way extrema are added and deleted in controller.edit_peaks().
    assert np.allclose(sum(model.peaks), cfg_single["peaksum"], atol=10)

    # 9. calculate stats ######################################################
    signals = ([model.period_changed, model.rate_changed,
                model.tidalamp_changed] if model.modality == "RESP"
               else [model.period_changed, model.rate_changed])
    with qtbot.waitSignals(signals, timeout=5000):
        controller.calculate_stats()
    assert np.around(np.mean(model.periodintp), 4) == cfg_single["avgperiod"]
    assert np.around(np.mean(model.rateintp), 4) == cfg_single["avgrate"]
    if model.modality == "RESP":
        assert np.around(np.mean(model.tidalampintp),
                         4) == cfg_single["avgtidalamp"]

    # 10. save stats ##########################################################
    view.periodcheckbox.setCheckState(Qt.Checked)
    view.ratecheckbox.setCheckState(Qt.Checked)
    if model.modality == "RESP":
        view.tidalampcheckbox.setCheckState(Qt.Checked)
    model.wpathstats = tmpdir.join(cfg_single["statsfname"])
    with qtbot.waitSignals([model.progress_changed] * 2, timeout=10000):
        controller.save_stats()
    # load and check content
    stats = pd.read_csv(tmpdir.join(cfg_single["statsfname"]))
    assert np.around(stats["period"].mean(), 4) == cfg_single["avgperiod"]
    assert np.around(stats["rate"].mean(), 4) == cfg_single["avgrate"]
    if model.modality == "RESP":
        assert np.around(stats["tidalamp"].mean(),
                         4) == cfg_single["avgtidalamp"]


ecg_batch_os = {"modality": "ECG",
                "sigchan": "A3",
                "mode": "multiple files",
                "filetype": "OpenSignals",
                "sigfnames": ["OSmontage1A.txt", "OSmontage1J.txt",
                              "OSmontage2A.txt", "OSmontage2J.txt",
                              "OSmontage3A.txt", "OSmontage3J.txt"],
                "peaksums": [3808244, 3412308, 2645824, 3523449, 3611836,
                             3457936],
                "stats": [(0.7950, 76.1123), (0.7288, 83.1468),
                          (0.7894, 76.8911), (0.7402, 81.7864),
                          (0.7856, 76.9153), (0.7235, 83.6060)],
                "correctpeaks": False}

ecg_batch_custom = {"modality": "ECG",
                    "header": {"signalidx": 7, "markeridx": None, "skiprows": 3,
                               "sfreq": 100, "separator": "\t"},
                    "mode": "multiple files",
                    "filetype": "Custom",
                    "sigfnames": ["OSmontage1A.txt", "OSmontage1J.txt",
                                  "OSmontage2A.txt", "OSmontage2J.txt",
                                  "OSmontage3A.txt", "OSmontage3J.txt"],
                    "peaksums": [3808244, 3412308, 2645824, 3523449, 3611836,
                                 3457936],
                    "stats": [(0.7950, 76.1123), (0.7288, 83.1468),
                              (0.7894, 76.8911), (0.7402, 81.7864),
                              (0.7856, 76.9153), (0.7235, 83.6060)],
                    "correctpeaks": False}

ecg_batch_autocorrect = {"modality": "ECG",
                         "sigchan": 'A3',
                         "mode": "multiple files",
                         "filetype": "OpenSignals",
                         "sigfnames": ["OSmontage1A.txt", "OSmontage1J.txt",
                                       "OSmontage2A.txt", "OSmontage2J.txt",
                                       "OSmontage3A.txt", "OSmontage3J.txt"],
                         "peaksums": [3808199, 3394481, 2626449, 3511241,
                                      3611833, 3457931],
                         "stats": [(0.7944, 76.0973), (0.7308, 82.8572),
                                   (0.7934, 76.2351), (0.7418, 81.5011),
                                   (0.7856, 76.9152), (0.7235, 83.5973)],
                         "correctpeaks": True}


def idcfg_batch(cfg):
    """Generate a test ID."""
    modality = cfg["modality"]
    filetype = cfg["filetype"]
    if cfg["correctpeaks"]:
        correction = "autocorrection"
    else:
        correction = "uncorrected"
    return f"{modality}:{correction}:{filetype}"


@pytest.fixture(params=[ecg_batch_os, ecg_batch_custom, ecg_batch_autocorrect],
                ids=idcfg_batch)
def cfg_batch(request):
    return request.param


def test_batchfile(qtbot, tmpdir, cfg_batch):

    # Set up application.
    model = Model()
    controller = Controller(model)
    view = View(model, controller)
    qtbot.addWidget(view)
    view.show()

    # Configure options.
    qtbot.keyClicks(view.modmenu, cfg_batch["modality"])
    if cfg_batch["filetype"] == "Custom":
        model.customheader = cfg_batch["header"]
    else:
        qtbot.keyClicks(view.sigchanmenu, cfg_batch["sigchan"])
    qtbot.keyClicks(view.batchmenu, cfg_batch["mode"])
    view.savecheckbox.setCheckState(Qt.Checked)
    if cfg_batch["correctpeaks"]:
        view.correctcheckbox.setCheckState(Qt.Checked)
    view.periodcheckbox.setCheckState(Qt.Checked)
    view.ratecheckbox.setCheckState(Qt.Checked)
    model.fpaths = [datadir.joinpath(p) for p in cfg_batch["sigfnames"]]
    model.set_filetype(cfg_batch["filetype"])

    # Mock the controller's batch_processor in order to avoid
    # calls to the controller's get_wpathpeaks and get_wpathstats methods.
    model.wdirpeaks = tmpdir
    model.wdirstats = tmpdir

    model.status = 'processing files'
    model.plotting = False

    controller.batchmethods = [controller.read_channels, controller.find_peaks,
                               controller.autocorrect_peaks,
                               controller.calculate_stats,
                               controller.save_stats,
                               controller.save_peaks]
    controller.iterbatchmethods = iter(controller.batchmethods)

    model.progress_changed.connect(controller.dispatcher)

    # Initiate batch processing.
    controller.dispatcher(1)

    # Wait for all files to be processed.
    while not model.plotting:    # dispatcher enables plotting once all files are processed
        qtbot.wait(1000)

    # Load each peak file saved during batch processing and assess if
    # peaks have been identified correctly.
    for sigfname, peaksum in zip(cfg_batch["sigfnames"],
                                 cfg_batch["peaksums"]):
        with qtbot.waitSignal(model.signal_changed, timeout=5000):
            model.fpaths = [datadir.joinpath(sigfname)]
            controller.read_channels()
        fname = Path(sigfname).stem
        model.rpathpeaks = tmpdir.join(f"{fname}_peaks.csv")
        with qtbot.waitSignal(model.peaks_changed, timeout=5000):
            controller.read_peaks()
        assert sum(model.peaks) == peaksum
        model.reset()

    # Load each stats file saved during batch processing and assess if
    # stats have been caclualted correctly.
    for sigfname, stat in zip(cfg_batch["sigfnames"], cfg_batch["stats"]):
        fname = Path(sigfname).stem
        statsfname = tmpdir.join(f"{fname}_stats.csv")
        stats = pd.read_csv(statsfname)
        assert np.around(stats["period"].mean(), 4) == stat[0]
        assert np.around(stats["rate"].mean(), 4) == stat[1]
