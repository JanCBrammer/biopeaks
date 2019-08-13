# -*- coding: utf-8 -*-
"""
Created on Sun Jul 28 14:13:03 2019

@author: John Doe
"""

'''
What I want to provide are a few functional tests (as opposed to unit tests
that cover every function, or integration tests); 

https://codeutopia.net/blog/2015/04/11/what-are-unit-testing-integration-
testing-and-functional-testing/

"you shouldn’t try to make very fine grained functional tests. You don’t want
to test a single function, despite the name “functional” perhaps hinting at it.
Instead, functional tests should be used for testing common user interactions.
If you would manually test a certain flow of your app in a browser, such as
registering an account, you could make that into a functional test"

I won't use a dedicated test framework, but rather implement a test version of
the qt application in which I simulate user interaction by directly interacting
with the controller's methods (i.e. the tests won't simulate interaction with
the view, as would be the case in a framework like pytest-qt); I don't use
pytest-qt since it doesn't offer (straightforward) interactions with nested
menus;

The tests will be restricted to a few typical, meaningful workflows (i.e., 
sequences of function calls), since testing all possible workflows is
unfeasible and for a majority of workflows meaningless (e.g., saving peaks
before finding peaks etc.)

what's the correct level of granularity? check outcome of each step of a
workflow, or only the end result of a workflow?
	try and check outcome of every step

how to assert correctness / passing of tests? what is the criterion?
	assert correctness based on model attributes, e.g., make sure that the
	signal is of a certain length
'''

import sys
import os
import numpy as np
from PyQt5.QtTest import QTest, QSignalSpy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from model import Model
from view import View
from controller import Controller


class TestApplication(QApplication):
    def __init__(self, sys_argv):
        super(TestApplication, self).__init__(sys_argv)
        
        self._model = Model()
        self._controller = Controller(self._model)
        self._view = View(self._model, self._controller)
        self._tests = Tests(self._model, self._view, self._controller)
        self._view.show()
        self._tests.run()
        
        
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
        if value == None:
            spy.wait()
        else:
            while True:
                # if a signal can emit different values, the while loop runs
                # until the signal emits the desired value; every emitted value
                # is appended to spy (last value is most recently emitted one)
                spy.wait()
#                print(len(spy), spy[-1][0])
                if spy[-1][0] == value:
                    break
        
    def run(self):
        # single file ECG #####################################################
        #######################################################################
        
        # 1. change signal channel and marker channel
        QTest.keyClicks(self._view.sigchanmenu, 'A1')
        QTest.keyClicks(self._view.markerschanmenu, 'A3')
        
        # 2. load signal
        ################
        self._controller.threader(status='loading file',
                                  fn=self._controller.read_chan,
                                  path='ECG_testdata_long.txt',
                                  chantype='signal')
        self.wait_for_signal(self._model.progress_changed, 1)
        # give a human reviewer some time to confirm the execution visually
        QTest.qWait(2000)
        assert np.size(self._model.signal) == 7925550, \
                'failed to load signal'
        print('loaded signal successfully')
        
        # 3. load markers
        #################
        self._controller.open_markers()
        # open_markers starts thread
        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        assert np.size(self._model.markers) == 7925550, \
                'failed to load markers'
        print('loaded markers successfully')
        
        # 4. segment signal
        ###################
        # preview segment
        segment = [1, 60]
        self._controller.threader(status='changing segment',
                                  fn=self._controller.change_segment,
                                  values = segment)
        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        # prune signal to segment
        self._controller.threader(status='segmenting signal',
                                  fn=self._controller.segment_signal)
        self.wait_for_signal(self._model.progress_changed, 1)
        assert np.size(self._model.signal) == int((segment[1] - segment[0]) *
                       self._model.sfreq), ('failed to load signal')
        print('segmented signal successfully')
#        # give a human reviewer some time to confirm the execution visually
#        QTest.qWait(1000)
        
        # 5. save segmented signal
        ##########################
        # set path for saving signal
        self._controller.wpathsignal = './ECG_testdata_long_segmented.txt'
        # save signal
        self._controller.threader(status='saving signal',
                                  fn=self._controller.save_signal)
        self.wait_for_signal(self._model.progress_changed, 1)
        assert os.path.isfile('./ECG_testdata_long_segmented.txt'), \
                'failed to save segmented signal'
        print('segmented signal successfully')

        # 6. find peaks
        ###############
        self._controller.threader(status='finding peaks',
                                  fn=self._controller.find_peaks)
        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        assert np.size(self._model.peaks) == 66, 'failed to find peaks'
        print('found peaks successfully')
        
        # 7. edit peaks
        ###############
        # enable editing
        QTest.mouseClick(self._view.editcheckbox, Qt.LeftButton)
        # engage editing (click on canvas to give it the focus)
        QTest.mouseClick(self._view.canvas, Qt.LeftButton)
        # since it is very tedious to map from matplotlib figure canvas
        # coordinates to qt coordinates, the controllers edit_peaks 
        # method is called with a mocked KeyEvent; to demonstrate edit_peaks
        # delete the first peak and then add it again
        demopeak = self._model.peaks[0][0] / self._model.sfreq
        mock_key_event = MockKeyEvent(key='d', xdata=demopeak)
        self._controller.edit_peaks(mock_key_event)
        assert self._model.peaks[0][0] / self._model.sfreq > demopeak, \
            'failed to delete first peak'
        print('deleted first peak successfully')
        # give user some time to perceive the change
        QTest.qWait(2000)
        mock_key_event = MockKeyEvent(key='a', xdata=demopeak)
        self._controller.edit_peaks(mock_key_event)
        print(self._model.peaks[0][0] / self._model.sfreq, self._model.peaks[0][0] / self._model.sfreq == demopeak)
        # note that edit_peaks places the peak in the middle of the plateau in
        # case of a flat peak, hence discrepancies of a few msecs can arise;
        # set tolerance for deviation of re-inserted peak to 10 msec
        assert abs(self._model.peaks[0][0] / self._model.sfreq - 
                   demopeak) <= 0.010, 'failed to re-insert first peak'
        print('re-inserted first peaks successfully')
        
        # 8. save peaks
        ###############
        # set path for saving peaks
        self._controller.wpathpeaks = './ECG_testdata_long_segmented_peaks.txt'
        # save signal
        self._controller.threader(status='saving peaks',
                                  fn=self._controller.save_peaks)
        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        assert os.path.isfile('./ECG_testdata_long_segmented_peaks.txt'), \
                'failed to save peaks'
        print('saved peaks successfully')
        
        # 9. load segmented signal
        ##########################
        self._controller.threader(status='loading file',
                                  fn=self._controller.read_chan,
                                  path='ECG_testdata_long_segmented.txt',
                                  chantype='signal')
        self.wait_for_signal(self._model.progress_changed, 1)
        QTest.qWait(2000)
        assert np.size(self._model.signal) == 59000, 'failed to load signal'
        print('re-loaded signal successfully')
        
        # 10. load peaks found for segmented signal
        ##########################################
        self._controller.rpathpeaks = './ECG_testdata_long_segmented_peaks.txt'
        self._controller.threader(status='loading peaks',
                                  fn=self._controller.read_peaks)
        assert np.size(self._model.peaks) == 66, 'failed to re-load peaks'
        print('re-loaded peaks successfully')
        
        
        # single file respiration #############################################
        #######################################################################
        
        
        
        
        # batch processing ECG ################################################
        #######################################################################
        
        
        
        # batch processing respiration ########################################
        #######################################################################


if __name__ == '__main__':
    app = TestApplication(sys.argv)
    sys.exit(app.exec_())
