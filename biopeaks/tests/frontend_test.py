# -*- coding: utf-8 -*-

'''
I want to provide a few functional tests (as opposed to unit tests that cover
every function, or integration tests).

https://codeutopia.net/blog/2015/04/11/what-are-unit-testing-integration-
testing-and-functional-testing/

"you shouldn’t try to make very fine grained functional tests. You don’t want
to test a single function, despite the name “functional” perhaps hinting at it.
Instead, functional tests should be used for testing common user interactions.
If you would manually test a certain flow of your app in a browser, such as
registering an account, you could make that into a functional test"

I won't use a dedicated test framework, but rather implement a test version of
the GUI in which I simulate user interaction by directly interacting
with the controller methods (i.e. the tests won't simulate interaction with
the view, as would be the case in a framework like pytest-qt). I don't use
pytest-qt since it doesn't offer (straightforward) interactions with nested
menus. This approach results in a number of hacks, which isn't pretty but it
does the job.

The tests will be restricted to a few typical, meaningful workflows (i.e.,
sequences of function calls), since testing all possible workflows is
unfeasible and for a majority of workflows meaningless (e.g., saving peaks
before finding peaks etc.).
'''

import sys
import os
import numpy as np
import pandas as pd
from PyQt5.QtTest import QTest, QSignalSpy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from biopeaks.model import Model
from biopeaks.view import View
from biopeaks.controller import Controller


class TestApplication(QApplication):
    def __init__(self, sys_argv):
        super(TestApplication, self).__init__(sys_argv)

        self._model = Model()
        self._controller = Controller(self._model)
        self._view = View(self._model, self._controller)
        self._tests = Tests(self._model, self._view, self._controller)


class MockKeyEvent(object):
    def __init__(self, key, xdata):
        super(MockKeyEvent, self).__init__()
        self.key = key
        self.xdata = xdata


class Tests:
    def __init__(self, model, view, controller):
        super().__init__()
        self._model = model
        self._view = view
        self._controller = controller

    def wait_for_signal(self, signal, value):
        # halt the execution of the test until either only signal (in this
        # case value must be None), or a specific value associated with signal
        # is emitted; spy.wait() runs an event loop until it registers the
        # signal
        spy = QSignalSpy(signal)
        if value is None:
            spy.wait()
        else:
            # wait for x*5 seconds (spy.wait() loops for 5 seconds)
            for i in range(10):
                # if a signal can emit different values, the while loop runs
                # until the signal emits the desired value; every emitted value
                # is appended to spy (last value is most recently emitted one)
                spy.wait()
#                print(len(spy), spy[-1][0])
                if spy[-1][0] == value:
                    break


    def single_file(self, assertion, modality, sigchan, markerchan, mode,
                    sigfnameorig, sigfnameseg, peakfname, statsfname, siglen,
                    siglenseg, markerlen, markerlenseg, peaksum, segment,
                    avgperiod, avgrate, avgtidalamp=None):

        # 1. set options
        ################
        QTest.keyClicks(self._view.modmenu, modality)
        QTest.keyClicks(self._view.sigchanmenu, sigchan)
        QTest.keyClicks(self._view.markerchanmenu, markerchan)
        QTest.keyClicks(self._view.batchmenu, mode)

        # 2. load signal
        ################
        self._controller.read_signal(path=sigfnameorig)
        self.wait_for_signal(self._model.progress_changed, 1)
        # give a human reviewer some time to confirm the execution visually
        QTest.qWait(2000)
        if assertion:
            assert np.size(self._model.signal) == siglen, 'failed to load signal'
            print('loaded signal successfully')
            assert np.size(self._model.marker) == markerlen, 'failed to load marker'
            print('loaded marker successfully')
        else:
            print(f"signal has {np.size(self._model.signal)} samples,"
                  f" marker has {np.size(self._model.marker)} samples")


        # 3. segment signal
        ###################
        # preview segment
        self._model.set_segment(values=segment)
        QTest.qWait(2000)
        # prune signal to segment
        self._controller.segment_signal()
        self.wait_for_signal(self._model.progress_changed, 1)
        seg = int(np.rint((segment[1] - segment[0]) * self._model.sfreq))
        if assertion:
            assert np.allclose(np.size(self._model.signal), seg, atol=1), \
                    'failed to segment signal'
            if self._model.marker is not None:
                seg = int(np.rint((segment[1] - segment[0]) * self._model.sfreqmarker))
                assert np.allclose(np.size(self._model.marker), seg, atol=1), \
                        'failed to segment marker'
            print('segmented signal successfully')
        else:
            print(f"segment has {seg} samples")

        # 4. save segmented signal
        ##########################
        # set path for saving signal
        self._model.wpathsignal = sigfnameseg
        # save signal
        self._controller.save_signal()
        self.wait_for_signal(self._model.progress_changed, 1)
        assert os.path.isfile(sigfnameseg), 'failed to save segmented signal'
        print('saved segmented signal successfully')

        # 5. find peaks
        ###############
        self._controller.find_peaks()
        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        if assertion:
            assert sum(self._model.peaks) == peaksum, 'failed to find peaks'
            print('found peaks successfully')
        else:
            print(f"sum of peaks is {sum(self._model.peaks)}")


        # 6. edit peaks
        ###############
        # enable editing
        self._view.editcheckbox.setCheckState(Qt.Checked)
        # engage editing (click on canvas to give it the focus)
        QTest.mouseClick(self._view.canvas0, Qt.LeftButton)
        # since it is very tedious to map from matplotlib figure canvas
        # coordinates to qt coordinates, the controllers edit_peaks
        # method is called with a mocked KeyEvent; to demonstrate edit_peaks
        # delete the first peak and then add it again
        demopeak = self._model.peaks[0] / self._model.sfreq
        mock_key_event = MockKeyEvent(key='d', xdata=demopeak)
        self._controller.edit_peaks(mock_key_event)
        assert self._model.peaks[0] / self._model.sfreq > demopeak, \
            'failed to delete first peak'
        print('deleted first peak successfully')
        # give user some time to perceive the change
        QTest.qWait(2000)
        mock_key_event = MockKeyEvent(key='a', xdata=demopeak)
        self._controller.edit_peaks(mock_key_event)
        # note that edit_peaks places the peak in the middle of the plateau in
        # case of a flat peak, hence discrepancies of a few msecs can arise;
        # set tolerance for deviation of re-inserted peak to 25 msec
        assert abs(self._model.peaks[0] /
                   self._model.sfreq - demopeak) <= 0.025, 'failed to re-insert first peak'
        print('re-inserted first peaks successfully')

        # 7. save peaks
        ###############
        # set path for saving peaks
        self._model.wpathpeaks = peakfname
        self._controller.save_peaks()
        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        assert os.path.isfile(peakfname), 'failed to save peaks'
        print('saved peaks successfully')

        # 8. load segmented signal
        ##########################
        self._controller.read_signal(path=sigfnameseg)
        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        if assertion:
            assert np.size(self._model.signal) == siglenseg, \
                    'failed to re-load signal'
            print('re-loaded signal successfully')
            assert np.size(self._model.marker) == markerlenseg, \
                    'failed to re-load signal'
            print('re-loaded marker successfully')
        else:
            print(f"re-loaded signal has {np.size(self._model.signal)} samples,"
                  f" re-loaded marker has {np.size(self._model.marker)} samples")

        # 9. load peaks found for segmented signal
        ###########################################
        self._model.rpathpeaks = peakfname
        self._controller.read_peaks()
        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        # For the breathing, after peak editing, the re-inserted peak can
        # be shifted by a few samples. This is not a bug, but inherent in the
        # way extrema are added and deleted in controller.edit_peaks().
        if assertion:
            assert np.allclose(sum(self._model.peaks), peaksum, atol=10), \
                'failed to re-load peaks'
            print('re-loaded peaks successfully')
        else:
            print(f"re-loaded peaks have sum {sum(self._model.peaks)}")


        # 10. calculate stats
        #####################
        self._controller.calculate_stats()

        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        if assertion:
            assert np.around(np.mean(self._model.periodintp), 4) == avgperiod, \
                    'failed to calculate period'

            print('calculated period successfully')
            assert np.around(np.mean(self._model.rateintp), 4) == avgrate, \
                    'failed to calculate rate'
            print('calculated rate successfully')
        else:
            print(f"mean period is {np.around(np.mean(self._model.periodintp), 4)}"
                  f" mean rate is {np.around(np.mean(self._model.rateintp), 4)}")
        if modality == "RESP":
            if assertion:
                assert np.around(np.mean(self._model.tidalampintp), 4) == avgtidalamp, \
                        'failed to calculate tidal amplitude'
                print('calculated tidal amplitude successfully')
            else:
                print(f" mean rate is {np.around(np.mean(self._model.tidalampintp), 4)}")


        # 11. save stats
        ################
        self._view.periodcheckbox.setCheckState(Qt.Checked)
        self._view.ratecheckbox.setCheckState(Qt.Checked)
        if modality == "RESP":
            self._view.tidalampcheckbox.setCheckState(Qt.Checked)
        self._model.wpathstats = statsfname
        self._controller.save_stats()
        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        # load and check content
        stats = pd.read_csv(statsfname)
        if assertion:
            assert np.around(stats["period"].mean(), 4) == avgperiod, \
                    "failed to save period"
            assert np.around(stats["rate"].mean(), 4) == avgrate, \
                    "failed to save rate"
            print('saved statistics successfully')
        else:
            print(f"mean re-loaded period is {np.around(stats['period'].mean(), 4)}"
                  f" mean re-loaded rate is {np.around(stats['rate'].mean(), 4)}")
        if modality == "RESP":
            if assertion:
                assert np.around(stats["tidalamp"].mean(), 4) == avgtidalamp, \
                    "failed to save tidalamplitude}"
            else:
                print(f"mean re-loaded rate is {np.around(stats['tidalamp'].mean(), 4)}")


        # clean-up in case consecutive test are executed
        # reset model
        self._model.reset()
        # disable editing
        self._view.editcheckbox.setCheckState(Qt.Unchecked)
        # unselect stats
        self._view.periodcheckbox.setCheckState(Qt.Unchecked)
        self._view.ratecheckbox.setCheckState(Qt.Unchecked)
        if modality == "RESP":
            self._view.tidalampcheckbox.setCheckState(Qt.Unchecked)

        # remove all files that have been saved during the test
        os.remove(peakfname)
        os.remove(statsfname)
        os.remove(sigfnameseg)


    def batch_file(self, assertion, modality, sigchan, mode, sigfnames,
                   peakdir, statsdir, peaksums, stats):

        # 1. set options and set paths
        ##############################
        QTest.keyClicks(self._view.modmenu, modality)
        QTest.keyClicks(self._view.sigchanmenu, sigchan)
        QTest.keyClicks(self._view.batchmenu, mode)
        self._view.savecheckbox.setCheckState(Qt.Checked)
        self._view.periodcheckbox.setCheckState(Qt.Checked)
        self._view.ratecheckbox.setCheckState(Qt.Checked)
        if modality == "RESP":
            self._view.tidalampcheckbox.setCheckState(Qt.Checked)
        self._model.fpaths = sigfnames

        # 2. process batch
        ##################
        # use a mockup of the controller's batch_processor in order to avoid
        # calls to the controller's get_wpathpeaks and get_wpathstats methods
        self._controller.methodnb = 0
        self._controller.nmethods = 4
        self._controller.filenb = 0
        self._controller.nfiles = len(self._model.fpaths)

        self._model.wdirpeaks = peakdir
        self._model.wdirstats = statsdir

        self._model.status = 'processing files'
        self._model.plotting = False
        self._model.progress_changed.connect(self._controller.dispatcher)

        # initiate processing
        self._controller.dispatcher(1)

        # wait for all files to be processed
        while self._controller.filenb < self._controller.nfiles:
#            print(self._controller.filenb, self._controller.nfiles)
            QTest.qWait(500)

        # 3. check peaks
        ################
        # load each peak file saved during batch processing and assess if
        # peaks have been identified correctly
        for sigfname, peaksum in zip(sigfnames, peaksums):
            # load signal
            self._controller.read_signal(path=sigfname)
            self.wait_for_signal(self._model.progress_changed, 1)
            # load peaks
            fpartname, _ = os.path.splitext(sigfname)
            self._model.rpathpeaks = f"{fpartname}_peaks.csv"
            self._controller.read_peaks()
            self.wait_for_signal(self._model.progress_changed, 1)
            if assertion:
                assert sum(self._model.peaks) == peaksum, \
                        f"failed to load peaks for {sigfname}"
                print(f"loaded peaks for {sigfname} successfully")
            else:
                print(f"sum of peaks is {sum(self._model.peaks)}")
            # remove all files that have been saved during the test
            os.remove(self._model.rpathpeaks)
            self._model.reset()

        # 3. check stats
        ################
        for sigfname, stat in zip(sigfnames, stats):
            fpartname, _ = os.path.splitext(sigfname)
            statsfname = f"{fpartname}_stats.csv"
            stats = pd.read_csv(statsfname)
            if assertion:
                assert np.around(stats["period"].mean(), 4) == stat[0], \
                        f"failed to save period for {sigfname}"
                assert np.around(stats["rate"].mean(), 4) == stat[1], \
                        f"failed to save rate for {sigfname}"
                print('saved statistics successfully')
            else:
                print(f"mean re-loaded period is {np.around(stats['period'].mean(), 4)}"
                      f" mean re-loaded rate is {np.around(stats['rate'].mean(), 4)}")
            if modality == "RESP":
                if assertion:
                    assert np.around(stats["tidalamp"].mean(), 4) == stat[2], \
                        f"failed to save tidalamplitude for {sigfname}"
                else:
                    print(f"mean re-loaded rate is {np.around(stats['tidalamp'].mean(), 4)}")

            # remove all files that have been saved during the test
            os.remove(statsfname)

        # restore original state of optionpanel
        self._view.savecheckbox.setCheckState(Qt.Unchecked)
        self._view.periodcheckbox.setCheckState(Qt.Unchecked)
        self._view.ratecheckbox.setCheckState(Qt.Unchecked)
        if modality == "RESP":
            self._view.tidalampcheckbox.setCheckState(Qt.Unchecked)


def runner(assertion=True):
    """
    Run with assertion=False to only print results and skip assertion.
    """
    testapp = TestApplication(sys.argv)
    testapp._view.show()

    # change from the current directory to testdata directory
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    datapath = os.path.join(THIS_DIR, "testdata")
    os.chdir(datapath)

    # single file with OpenSignals PPG data,
    testapp._tests.single_file(assertion=assertion,
                                modality='PPG',
                                sigchan='A1',
                                markerchan='None',
                                mode='single file',
                                sigfnameorig='OSmontagePPG.txt',
                                sigfnameseg='testdatasegmented.txt',
                                peakfname='testdata_segmented_peaks.csv',
                                statsfname='testdata_segmented_stats.csv',
                                siglen=60001,
                                siglenseg=8750,
                                markerlen=1,
                                markerlenseg=1,
                                peaksum=461362,
                                avgperiod=0.6652,
                                avgrate=90.7158,
                                segment=[20, 90])

    # single file with artificial EDF PPG data,
    testapp._tests.single_file(assertion=assertion,
                                modality='PPG',
                                sigchan='A5',
                                markerchan='A1',
                                mode='single file',
                                sigfnameorig='EDFmontage0.edf',
                                sigfnameseg='testdatasegmented.edf',
                                peakfname='testdata_segmented_peaks.csv',
                                statsfname='testdata_segmented_stats.csv',
                                siglen=45000,
                                siglenseg=3500,
                                markerlen=180000,
                                markerlenseg=14000,
                                peaksum=123270,
                                avgperiod=1.0000,
                                avgrate=60.0000,
                                segment=[11.51, 81.7])

    # single file with OpenSignals ECG data,
    testapp._tests.single_file(assertion=assertion,
                                modality='ECG',
                                sigchan='A3',
                                markerchan='I1',
                                mode='single file',
                                sigfnameorig='OSmontage0J.txt',
                                sigfnameseg='testdatasegmented.txt',
                                peakfname='testdata_segmented_peaks.csv',
                                statsfname='testdata_segmented_stats.csv',
                                siglen=5100000,
                                siglenseg=100000,
                                markerlen=5100000,
                                markerlenseg=100000,
                                peaksum=4572190,
                                avgperiod=1.0921,
                                avgrate=55.1027,
                                segment=[760, 860])

    # single file with artificial EDF ECG data,
    testapp._tests.single_file(assertion=assertion,
                                modality='ECG',
                                sigchan='A3',
                                markerchan='A1',
                                mode='single file',
                                sigfnameorig='EDFmontage0.edf',
                                sigfnameseg='testdatasegmented.edf',
                                peakfname='testdata_segmented_peaks.csv',
                                statsfname='testdata_segmented_stats.csv',
                                siglen=180000,
                                siglenseg=14000,
                                markerlen=180000,
                                markerlenseg=14000,
                                peaksum=1228440,
                                avgperiod=0.4000,
                                avgrate=150.0000,
                                segment=[11.51, 81.7])

    # single file with OpenSignals breathing data
    testapp._tests.single_file(assertion=assertion,
                                modality='RESP',
                                sigchan='A2',
                                markerchan='I1',
                                mode='single file',
                                sigfnameorig='OSmontage0J.txt',
                                sigfnameseg='testdata_segmented.txt',
                                peakfname='testdata_segmented_peaks.csv',
                                statsfname='testdata_segmented_stats.csv',
                                siglen=5100000,
                                siglenseg=200000,
                                markerlen=5100000,
                                markerlenseg=200000,
                                peaksum=13109234,
                                avgperiod=3.3236,
                                avgrate=19.4375,
                                avgtidalamp=131.1297,
                                segment=[3200, 3400])

    # single file with artificial EDF breathing data
    testapp._tests.single_file(assertion=assertion,
                                modality='RESP',
                                sigchan='A5',
                                markerchan='A1',
                                mode='single file',
                                sigfnameorig='EDFmontage0.edf',
                                sigfnameseg='testdata_segmented.edf',
                                peakfname='testdata_segmented_peaks.csv',
                                statsfname='testdata_segmented_stats.csv',
                                siglen=45000,
                                siglenseg=3800,
                                markerlen=180000,
                                markerlenseg=15200,
                                peaksum=288034,
                                avgperiod=1.0002,
                                avgrate=59.9865,
                                avgtidalamp=16350.0000,
                                segment=[602.6, 679.26])

    # batch processing with OpenSignals ECG data
    sigfiles = ['OSmontage1A.txt', 'OSmontage1J.txt', 'OSmontage2A.txt',
                'OSmontage2J.txt', 'OSmontage3A.txt', 'OSmontage3J.txt']
    peaksums = [3808244, 3412308, 2645824, 3523449, 3611836, 3457936]
    stats = [(0.7950, 76.1123), (0.7288, 83.1468), (0.7894, 76.8911),
             (0.7402, 81.7864), (0.7856, 76.9153), (0.7235, 83.6060)]
    testapp._tests.batch_file(assertion=assertion,
                              modality='ECG',
                              sigchan='A3',
                              mode='multiple files',
                              sigfnames=sigfiles,
                              peakdir=datapath,
                              statsdir=datapath,
                              peaksums=peaksums,
                              stats=stats)

    print("tests ran without errors, closing application")
    testapp.closeAllWindows() # QApplication quits once window is closed
