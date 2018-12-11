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
 This script initializes the plugin, making it known to QGIS.
"""

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from pgversion.pgVersionTools import PgVersionTools
import os
from qgis.PyQt import uic


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'LogView.ui'))


class LogView(QDialog, FORM_CLASS):
    """
    Class documentation goes here.
    """
    rollbackLayer = pyqtSignal(QTreeWidgetItem)
    diffLayer = pyqtSignal()
    checkoutLayer = pyqtSignal(str)
    checkoutTag = pyqtSignal(str, str)

    def __init__(self, parent):
        """
        Constructor
        """
        QDialog.__init__(self, None)
        self.setupUi(self)

        self.iface = parent.iface
        self.tools = PgVersionTools(parent)

        self.myAction = QAction(QIcon(""), self.tr(
            "Set Tag for current revision"), self)
        self.myAction.setStatusTip(self.tr("Set Tag for current revision"))
        self.myAction.triggered.connect(self.setTag)
        self.treeWidget.addAction(self.myAction)
        self.treeWidget.setContextMenuPolicy(
            Qt.ActionsContextMenu)

        self.btnRollback.clicked.connect(self.btnRollback_clicked)
        self.btnDiff.clicked.connect(self.btnDiff_clicked)
        self.btnCheckout.clicked.connect(self.btnCheckout_clicked)
        self.buttonBox.rejected.connect(self.buttonBox_rejected)
        self.btnTag.clicked.connect(self.btnTag_clicked)

    def setLayer(self, theLayer):
        self.theLayer = theLayer

    def createTagList(self):

        self.cmbTags.clear()

        # Add tags into tag cmb
        myDb = self.tools.layerDB('tags', self.theLayer)
        sql = "select vtag.tags_id, vtag.version_table_id, vtag.tag_text, vtag.revision \
          from versions.version_tags as vtag,\
               versions.version_tables as vtab \
          where vtab.version_view_schema = '%s' \
            and vtab.version_view_name = '%s' \
            and vtab.version_table_id = vtag.version_table_id \
          order by vtag.tags_id desc " % (
              self.tools.layerSchema(self.theLayer), self.tools.layerTable(
                  self.theLayer))
        result,  error = myDb.read(sql)

        try:
            self.version_table_id = result['VERSION_TABLE_ID'][0]

            self.cmbTags.addItem(' ------ ', -1)

            for i in range(len(result['TAG_TEXT'])):
                self.cmbTags.addItem(result['TAG_TEXT'][i],
                                     result['REVISION'][i])
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
                QMessageBox.information(
                    None, self.tr('Warning'),
                    self.tr('This version is already tagged'))
            else:
                myDb = self.tools.layerDB('tags', self.theLayer)
                sql = "insert into versions.version_tags (version_table_id, revision,  tag_text) \
                  values \
                  (%s, %s, '%s')" % (
                      self.version_table_id,
                      self.treeWidget.currentItem().text(0), result)
                success,  error = myDb.run(sql)

                self.createTagList()

    def hasTag(self):

        try:
            sql = """select count(revision) 
              from versions.version_tags 
              where version_table_id = %s 
                and revision = %s """ % (
                self.version_table_id,
                self.treeWidget.currentItem().text(0))

            myDb = self.tools.layerDB('tags', self.theLayer)
            result,  error = myDb.read(sql)
            if result['COUNT'][0] is not 0:
                return True
            else:
                return False
        except:
            pass

    def btnRollback_clicked(self):
        try:
            self.rollbackLayer.emit(self.treeWidget.currentItem())
        except:
            QMessageBox.information(
                None, self.tr('Warning'),
                self.tr('Please select a revision for rollback'))

    def btnDiff_clicked(self):
        self.diffLayer.emit()
        self.close()

    def btnCheckout_clicked(self):
        if self.treeWidget.currentItem() is None:
            return
        self.checkoutLayer.emit(self.treeWidget.currentItem().text(0))
        self.close()

    def buttonBox_rejected(self):
        """
        Slot documentation goes here.
        """
        self.close()

    def btnTag_clicked(self):
        if self.cmbTags.currentIndex() > 0:
            self.checkoutTag.emit(
                str(self.cmbTags.itemData(self.cmbTags.currentIndex())),
                self.cmbTags.itemText(self.cmbTags.currentIndex()))
