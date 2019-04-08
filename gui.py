# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 18:52:52 2019

@author: John Doe
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QIcon
 
class Window(QWidget):
 
    def __init__(self):
        super().__init__()
        self.setWindowTitle('biopeaks')
        self.show()
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())