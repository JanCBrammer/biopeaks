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
the view, as would be the case in a framework like pytest-qt);

what's the correct level of granularity? check outcome of each step of a
workflow, or only the end result of a workflow?
	try and check outcome of every step

how to assert correctness / passing of tests? what is the criterion?
	assert correctness based on model attributes, e.g., make sure that the
	signal is of a certain length
'''

import sys
import numpy as np
from PyQt5.QtTest import QTest, QSignalSpy
from PyQt5.QtWidgets import QApplication
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
        
        
class Tests:
    def __init__(self, model, view, controller):
        super().__init__()
        self._model = model
        self._view = view
        self._controller = controller
        
    
    def wait_for_signal(self, signal, value):
        # halt the execution of the test until either only signal (in this
        # value must be None), or a specific value associated with signal
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
        
        # 1. change signal channel
        QTest.keyClicks(self._view.sigchanmenu, 'A1')
        # 2. load signal
        ################
        self._controller.threader(status='loading file',
                                  fn=self._controller.read_chan,
                                  path='ECG_testdata_long.txt',
                                  chantype='signal')
        self.wait_for_thread(self._model.progress_changed, 1)
#        # give a human reviewer some time to confirm the execution visually
#        QTest.qWait(1000)
        assert np.size(self._model.signal) == 7925550, ('failed to load '
                                                          'signal')
        print('loaded signal successfully')
        # 3. segment signal
        ###################
        # preview segment
        self._controller.threader(status='changing segment',
                                  fn=self._controller.change_segment,
                                  values = [1, 1000])
        self.wait_for_thread(self._model.progress_changed, 1)
        # give a human reviewer some time to confirm the execution visually
#        QTest.qWait(2000)
        # prune signal to segment
        self._controller.threader(status='segmenting signal',
                                  fn=self._controller.segment_signal)
        self.wait_for_thread(self._model.progress_changed, 1)
#        # give a human reviewer some time to confirm the execution visually
##        QTest.qWait(1000)
        # 4. find peaks
        ###############
        self._controller.threader(status='finding peaks',
                                  fn=self._controller.find_peaks)
        self.wait_for_thread(self._model.progress_changed, 1)


if __name__ == '__main__':
    app = TestApplication(sys.argv)
    sys.exit(app.exec_())




    
    
    
    
