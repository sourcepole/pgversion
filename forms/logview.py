# -*- coding: utf-8 -*-
"""
/***************************************************************************
Plugin for the Postgres Versioning System
-----------------------------------------------------------------------------------------------------------------
begin                : 2010-07-31
copyright          : (C) 2010 by Dr. Horst Duester
email                : horst.duester@sourcepole.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4 import uic
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from pgversion.pgversion_tools import PgVersionTools
from create_branch import DlgCreateBranch
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'logview.ui'))

class LogView(QDialog, FORM_CLASS):
    """
    Class documentation goes here.
    """
    rollbackLayer = pyqtSignal(QTreeWidgetItem)
    diffLayer = pyqtSignal()
    checkoutLayer = pyqtSignal(str)
    checkoutTag = pyqtSignal(str,  str)
    createBranch = pyqtSignal(str)    

      
    def __init__(self, parent):
        """
        Constructor
        """
        QDialog.__init__(self, None)
        self.setupUi(self)
        
        self.iface = parent.iface
        self.tools = PgVersionTools(parent)
    
        self.tagAction = QAction(QIcon(""), self.tr("Set Tag for current revision"),  self)
        self.tagAction.setStatusTip(self.tr("Set Tag for current revision"))
        self.tagAction.triggered.connect(self.setTag)
        self.treeWidget.addAction(self.tagAction)
        
        self.branchAction = QAction(QIcon(""), self.tr("Branch the current revision"),  self)
        self.branchAction.setStatusTip(self.tr("Create branch for current revision"))
        self.branchAction.triggered.connect(self.create_branch)
        self.treeWidget.addAction(self.branchAction)        
        
        self.treeWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
                        
    def set_version_table_id(self,  id):
        self.version_table_id = id
        
    def setLayer(self,  theLayer):
        self.theLayer = theLayer
        self.setWindowTitle(self.tr('Logview for layer %s' % (self.theLayer.name())))
        
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
        
        self.version_table_id = result['VERSION_TABLE_ID'][0] 
        self.cmbTags.addItem(' ------ ', -1)
        for i in range(len(result['TAG_TEXT'])):
            self.cmbTags.addItem(result['TAG_TEXT'][i],  result['REVISION'][i])

    
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

    def create_branch(self):
        result, ok = QInputDialog.getText(
            self,
            self.tr("Create branch for Revision "),
            self.tr(""),
            QLineEdit.Normal)        
            
        if ok:
            if self.branchExists():
                QMessageBox.information(None,  self.tr('Warning'),  self.tr('Branch already exists'))
            else:
                myDb = self.tools.layerDB('tags',self.theLayer)    
                sql = "select versions.pgvsmakebranch(%s, '%s')" % (self.version_table_id,  result)
                myDb.run(sql)
        
    def branchExists(self):
        return False
        
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
    
    @pyqtSignature("")
    def on_btnTag_clicked(self):
        if self.cmbTags.currentIndex() > 0:
            self.checkoutTag.emit(self.cmbTags.itemData(self.cmbTags.currentIndex()),  self.cmbTags.itemText(self.cmbTags.currentIndex()))    

