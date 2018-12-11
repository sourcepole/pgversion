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
from qgis.core import *
from qgis.gui import *
from ..dbtools.dbtools import *
from ..pgVersionTools import PgVersionTools
import os
from qgis.PyQt import uic


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'diff.ui'))


class DiffDlg(QDialog, FORM_CLASS):
    """
    Class documentation goes here.
    """
    def __init__(self, iface, parent=None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface

        self.tools = PgVersionTools(parent)

        self.dateEditRev1.setDate(QDate.currentDate())
        self.dateEditRev2.setDate(QDate.currentDate())

        theLayer = self.iface.activeLayer()
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()
        myDb = self.tools.layerDB('logview', theLayer)
        mySchema = QgsDataSourceURI(uri).schema()
        myTable = QgsDataSourceURI(uri).table()

        if len(mySchema) == 0:
            mySchema = 'public'

        sql = "select revision from versions.pgvslogview('"
        "" + mySchema + "." + myTable.replace(
            '_version', '') + "') order by revision desc"
        result,  error = myDb.read(sql)

        for i in range(len(result['REVISION'])):
            self.cmbRevision1.addItem(result['REVISION'][i])
            self.cmbRevision2.addItem(result['REVISION'][i])

        self.buttonBox.accepted.connect(self.buttonBox_accepted)
        self.buttonBox.rejected.connect(self.buttonBox_rejected)

    def setDb(self, theLayer):
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()
        self.myDb = self.tools.layerDB('diffDlg', theLayer)
        self.mySchema = QgsDataSourceURI(uri).schema()
        self.myTable = QgsDataSourceURI(uri).table()
        self.myKeyColumn = QgsDataSourceURI(uri).keyColumn()

        if len(self.mySchema) == 0:
            self.mySchema = 'public'

        return

    def buttonBox_accepted(self):

        if self.radioRevisionRev1.isChecked():
            if self.cmbRevisionRev1.currentText() != '-----':
                myRevision1 = self.cmbRevisionRev1.currentText()

        if self.radioRevisionRev2.isChecked():
            if self.cmbRevisionRev2.currentText() != '-----':
                myRevision2 = self.cmbRevisionRev2.currentText()

        if self.radioDateRev1.isChecked():
            myDate = self.dateEditRev1.date().toString(Qt.ISODate)

            sql = 'select revision from versions."\
            ' + self.mySchema + '_' + self.myTable + '_log" '
            sql += 'where systime <= (date_part(\'epoch\'::text, \'\
            ' + myDate + '\'::timestamp without time zone) * (1000)::double \
            precision)::bigint '
            sql += 'order by systime desc limit 1 '

            result,  error = self.myDb.read(sql)
            myRevision1 = str(result['REVISION'][0])

        if self.radioDateRev2.isChecked():
            myDate = self.dateEditRev2.date().toString(Qt.ISODate)

            sql = 'select revision from versions."\
            ' + self.mySchema + '_' + self.myTable + '_log" '
            sql += 'where systime <= (date_part(\'epoch\'::text, \'\
            ' + myDate + '\'::timestamp without time zone) * (1000)::double \
            precision)::bigint '
            sql += 'order by systime desc limit 1 '

            result,  error = self.myDb.read(sql)
            myRevision2 = str(result['REVISION'][0])

        if self.radioHeadRev1.isChecked():
            sql = 'select max(revision) as revision from versions."\
            ' + self.mySchema + '_' + self.myTable + '_log" '
            result,  error = self.myDb.read(sql)
            myRevision1 = str(result['REVISION'][0])

        if self.radioHeadRev2.isChecked():
            sql = 'select max(revision) as revision from versions."\
            ' + self.mySchema + '_' + self.myTable + '_log" '
            result,  error = self.myDb.read(sql)
            myRevision2 = str(result['REVISION'][0])

        if self.radioBaseRev1.isChecked():
            sql = 'select min(revision) as revision from versions."\
            ' + self.mySchema + '_' + self.myTable + '_log" '
            result,  error = self.myDb.read(sql)
            myRevision1 = str(result['REVISION'][0])

        if self.radioBaseRev2.isChecked():
            sql = 'select min(revision) as revision from versions."\
            ' + self.mySchema + '_' + self.myTable + '_log" '
            result,  error = self.myDb.read(sql)
            myRevision2 = str(result['REVISION'][0])

        try:
            self.diffExecute.emit(myRevision1, myRevision2)
            self.close()
        except:
            QMessageBox.information(
                None, self.tr('Message'), self.tr(
                    'This combination is not implemented yet'))

    def buttonBox_rejected(self):
        self.close()
