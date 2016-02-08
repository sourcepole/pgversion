# -*- coding: utf-8 -*-

"""
Module implementing LogView.
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from Ui_Ui_LogView import Ui_LogView

class LogView(QDialog, Ui_LogView):
    """
    Class documentation goes here.
    """
    rollbackLayer = pyqtSignal(QTreeWidgetItem)
    diffLayer = pyqtSignal()
    checkoutLayer = pyqtSignal(QTreeWidgetItem)
      
    def __init__(self, parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
    
        
    
    @pyqtSignature("QAbstractButton*")
    def on_btnClose_clicked(self, button):
        self.close()
    
    @pyqtSignature("")
    def on_btnRollback_clicked(self):
       self.rollbackLayer.emit(self.treeWidget.currentItem())    
       self.close()
    
    @pyqtSignature("")
    def on_btnDiff_clicked(self):
       self.diffLayer.emit()    
       self.close()
    
    @pyqtSignature("")
    def on_btnCheckout_clicked(self):
       self.checkoutLayer.emit(self.treeWidget.currentItem())    
       self.close()
