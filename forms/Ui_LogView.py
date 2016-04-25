# -*- coding: utf-8 -*-

"""
Module implementing LogView.
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from Ui_Ui_LogView import Ui_LogView
from pgversion.dbtools.dbTools import *
from pgversion.pgVersionTools import PgVersionTools

class LogView(QDialog, Ui_LogView):
    """
    Class documentation goes here.
    """
    rollbackLayer = pyqtSignal(QTreeWidgetItem)
    diffLayer = pyqtSignal()
    checkoutLayer = pyqtSignal(QTreeWidgetItem)
      
    def __init__(self, iface,  parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.iface = iface
        
        self.tools = PgVersionTools(self.iface)
    
        self.myAction = QAction(QIcon(""), self.tr("Set Tag for current revision"),  self)
        self.myAction.setStatusTip(self.tr("Set Tag for current revision"))
        self.myAction.triggered.connect(self.setTag)
        self.treeWidget.addAction(self.myAction)
        self.treeWidget.setContextMenuPolicy(Qt.ActionsContextMenu);    
    
    def setTag(self):
        result, ok = QInputDialog.getText(
            self,
            self.tr("Set Tag for Revision "),
            self.tr(""),
            QLineEdit.Normal)
        
        
        
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
    
    @pyqtSignature("int")
    def on_cmbTags_currentIndexChanged(self, index):
        """
        Slot documentation goes here.
        
        @param index DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        myDb = self.tools.layerDB('tags',currentLayer)
        sql = "select version_id, tag_text \
          from versions.version_tags \
          where "
        result = myDb(sql)
