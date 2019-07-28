# -*- coding: utf-8 -*-
"""
Created on Sun Jul 28 14:13:03 2019

@author: John Doe
"""

'''
What I want to provide are a few functional tests (as opposed to unit tests
covering every function, or integration tests);

https://codeutopia.net/blog/2015/04/11/what-are-unit-testing-integration-
testing-and-functional-testing/

"you shouldn’t try to make very fine grained functional tests. You don’t want
to test a single function, despite the name “functional” perhaps hinting at it.
Instead, functional tests should be used for testing common user interactions.
If you would manually test a certain flow of your app in a browser, such as
registering an account, you could make that into a functional test"

what's the correct level of granularity? check outcome of each step of a
workflow, or only the end result of a workflow?
	try and check outcome of every step

how to assert correctness / passing of tests? what is the criterion?
	assert correctness based on model attributes, e.g., make sure that the
	signal is of a certain length
'''

# single file: load signal

import sys
from PyQt5.QtWidgets import QApplication
from model import Model
from view import View
from controller import Controller

import numpy as np


class TestApplication(QApplication):
    def __init__(self, sys_argv):
        super(TestApplication, self).__init__(sys_argv)
        
        self._model = Model()
        self._controller = Controller(self._model)
        self._view = View(self._model, self._controller)
        self._view.show()
        
    def test_loadsignal(self):
        def assert_signal():
            assert np.size(self._model.signal) == 24481, ('failed to load '
                          'signal')
            print('loaded signal successfully')
        # once the thread finished, the test condition will be asserted
        self._model.progress_changed.connect(assert_signal)
        self._controller.threader(status='loading file',
                                  fn=self._controller.read_chan,
                                  path='ECG_testdata.txt', chantype='signal')


if __name__ == '__main__':
    app = TestApplication(sys.argv)
    
    # run tests
    app.test_loadsignal()

    sys.exit(app.exec_())
    
    
    
    
