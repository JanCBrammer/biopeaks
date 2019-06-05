# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 18:47:10 2019

@author: John Doe
"""

import sys
from PyQt5.QtWidgets import QApplication
from model import Model
from controller import Controller
from view import View


class Application(QApplication):
    def __init__(self, sys_argv):
        super(Application, self).__init__(sys_argv)
        self._model = Model()
        self._controller = Controller(self._model)
        self._view = View(self._model, self._controller)
        self._view.show()


if __name__ == '__main__':
    app = Application(sys.argv)
    sys.exit(app.exec_())