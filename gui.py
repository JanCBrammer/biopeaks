# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 18:52:52 2019

@author: John Doe
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton

class Window(QWidget):
 
    def __init__(self):
        super().__init__()
        self.initUI()
 
    def initUI(self):
        self.setWindowTitle('biopeaks')
        self.setGeometry(50, 50, 1000, 700)
#        self.load_data()
        self.load_button()
        self.show()
    
    def load_button(self):
        btn = QPushButton('Browse', self)
        btn.clicked.connect(self.load_data)
        
    def load_data(self):
        print('foo')  
        
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())
    