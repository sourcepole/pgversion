# -*- coding: utf-8 -*-

"""
Module implementing LogView.
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from Ui_Ui_LogView import Ui_LogView
#from pgversion.dbtools.dbTools import *
from pgversion.pgVersionTools import PgVersionTools

class LogView(QDialog, Ui_LogView):
    """
    Class documentation goes here.
    """
    rollbackLayer = pyqtSignal(QTreeWidgetItem)
    diffLayer = pyqtSignal()
    checkoutLayer = pyqtSignal(str)
    checkoutTag = pyqtSignal(str,  str)
      
    def __init__(self, parent):
        """
        Constructor
        """
        QDialog.__init__(self, None)
        self.setupUi(self)
        
        self.iface = parent.iface
        self.tools = PgVersionTools(parent)
    
        self.myAction = QAction(QIcon(""), self.tr("Set Tag for current revision"),  self)
        self.myAction.setStatusTip(self.tr("Set Tag for current revision"))
        self.myAction.triggered.connect(self.setTag)
        self.treeWidget.addAction(self.myAction)
        self.treeWidget.setContextMenuPolicy(Qt.ActionsContextMenu);    
                
    def setLayer(self,  theLayer):
        self.theLayer = theLayer
        
    def createTagList(self):
        
        self.cmbTags.clear()
        
        # Add tags into tag cmb
        myDb = self.tools.layerDB('tags',self.theLayer)
        sql = "select vtag.tags_id, vtag.version_table_id, vtag.tag_text, vtag.revision \
          from versions.version_tags as vtag,\
               versions.version_tables as vtab \
          where vtab.version_view_schema = '%s' \
            and vtab.version_view_name = '%s' \
            and vtab.version_table_id = vtag.version_table_id \
          order by vtag.tags_id desc " % (self.tools.layerSchema(self.theLayer),  self.tools.layerTable(self.theLayer))
        result = myDb.read(sql)       
        
        try:
            self.version_table_id = result['VERSION_TABLE_ID'][0] 
            
            self.cmbTags.addItem(' ------ ', -1)
            
            for i in range(len(result['TAG_TEXT'])):
                self.cmbTags.addItem(result['TAG_TEXT'][i],  result['REVISION'][i])
        except:
            pass
    
    def setTag(self):
        result, ok = QInputDialog.getText(
            self,
            self.tr("Set Tag for Revision "),
            self.tr(""),
            QLineEdit.Normal)
        
        if ok:

            if self.hasTag():
                QMessageBox.information(None,  self.tr('Warning'),  self.tr('This version is already tagged'))
            else:
                myDb = self.tools.layerDB('tags',self.theLayer)    
                sql = "insert into versions.version_tags (version_table_id, revision,  tag_text) \
                  values \
                  (%s, %s, '%s')" % (self.version_table_id,  self.treeWidget.currentItem().text(0),  result)
                myDb.run(sql)
                
                self.createTagList()

        
    def hasTag(self):
        
        try:
            sql = "select count(revision) \
              from versions.version_tags \
              where version_table_id = %s \
                and revision = %s " % (self.version_table_id,  self.treeWidget.currentItem().text(0))
                
            myDb = self.tools.layerDB('tags',  self.theLayer)
            result = myDb.read(sql)
            if result['COUNT'][0] <> '0':
               return True
            else:
               return False
        except:
            pass
    
    @pyqtSignature("")
    def on_btnRollback_clicked(self):
        try:
            self.rollbackLayer.emit(self.treeWidget.currentItem())    
            self.close()
        except:
            QMessageBox.information(None, self.tr('Warning'),  self.tr('Please select a revision for checkout'))
    
    @pyqtSignature("")
    def on_btnDiff_clicked(self):
       self.diffLayer.emit()    
       self.close()
    
    @pyqtSignature("")
    def on_btnCheckout_clicked(self):
       self.checkoutLayer.emit(self.treeWidget.currentItem().text(0) )   
       self.close()

    
    @pyqtSignature("")
    def on_buttonBox_rejected(self):
        """
        Slot documentation goes here.
        """
        self.close()
    
    @pyqtSignature("int")
    def on_cmbTags_activated(self, index):
        """
        Slot documentation goes here.
        
        @param index DESCRIPTION
        @type int
        """
        
        try:
            self.checkoutTag.emit(self.cmbTags.itemData(index),  self.cmbTags.itemText(index))    
        except:
            pass
