# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 18:52:52 2019

@author: John Doe
"""

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton,
                             QFileDialog, QAction, QMainWindow)
from PyQt5.QtGui import QIcon

class Window(QMainWindow):
 
    def __init__(self):
        super().__init__()
        self.initUI()
 
    def initUI(self):
        self.setWindowTitle('biopeaks')
        self.setGeometry(50, 50, 1000, 700)
        self.setWindowIcon(QIcon('python_icon.png'))
        
        openFile = QAction(QIcon('open_icon.png'), 'Open', self)
        openFile.triggered.connect(self.open_dialog)
        
        toolbar = self.addToolBar('File')
        toolbar.addAction(openFile)      
        
        self.show()
    
        
    def open_dialog(self):
#        print('foo')
        fname = QFileDialog.getOpenFileNames(self, 'Open file', '/home')
        print(fname[0])
        
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())
    

    