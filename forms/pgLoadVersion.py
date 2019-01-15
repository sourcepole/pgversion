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
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
from pgversion.dbtools import *
from pgversion.pgVersionTools import *
import os
from qgis.PyQt import uic


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'pgLoadVersion.ui'))


class PgVersionLoadDialog(QDialog, FORM_CLASS):

    def __init__(self, parent):
        QDialog.__init__(self)
        self.setupUi(self)
        self.getDbSettings()
        self.tools = PgVersionTools(parent)
        self.iface = parent.iface
        self.parent = parent

        self.cmbServer.currentIndexChanged.connect(
            self.cmbServer_currentIndexChanged)
        self.buttonBox.accepted.connect(self.buttonBox_accepted)
        self.buttonBox.rejected.connect(self.close)

    def getDbSettings(self):
        settings = QSettings()
        settings.beginGroup('PostgreSQL/connections')
        self.cmbServer.addItem('------------')
        self.cmbServer.addItems(settings.childGroups())
        settings.endGroup()
        self.cmbServer.setCurrentText('------------')

    def initDB(self, selectedServer):
        if self.cmbServer.currentIndex() == 0:
            return None
        settings = QSettings()
        mySettings = '/PostgreSQL/connections/' + selectedServer
        DBNAME = settings.value(mySettings + '/database')
        DBUSER = settings.value(mySettings + '/username')
        DBHOST = settings.value(mySettings + '/host')
        DBPORT = settings.value(mySettings + '/port')
        DBPASSWD = settings.value(mySettings + '/password')
        DBTYPE = 'pg'

        if DBUSER == '' or DBPASSWD == '':
            connectionInfo = "dbname='" + DBNAME + "' host=" + DBHOST + ' port=' + DBPORT
            (success, user, password) = QgsCredentials.instance().get(
                connectionInfo, None, None)
            if not success:
                return None
            QgsCredentials.instance().put(connectionInfo, user, password)
            DBUSER = user
            DBPASSWD = password

        try:
            myDb = DbObj(pluginname=selectedServer, typ=DBTYPE,
                         hostname=DBHOST, port=DBPORT,
                         dbname=DBNAME, username=DBUSER, password=DBPASSWD)
        except:
            QMessageBox.information(
                None, self.tr('Error'),
                self.tr('No Database Connection Established.'))
            self.cmbServer.setCurrentIndex(0)
            return None

        if not myDb.conn:
            self.cmbServer.setCurrentIndex(0)
            self.close()
            return None

        if not self.tools.check_PGVS_revision(myDb):
            self.cmbServer.setCurrentIndex(0)
            return None

        self.lblDBUser.setText(DBUSER)
        query = 'select 4 as count,  1 as table'
        sysResult,  error = myDb.read(query)

        query = 'select version_table_schema as schema, version_table_name as table \
        from versions.version_tables \
        order by version_table_schema,version_table_name'
        result,  error = myDb.read(query)
        self.cmbTables.clear()

        if sysResult['COUNT'][0] > 3 or len(result['TABLE']) > 0:
            self.cmbTables.addItem('-------------')
            if result is None:
                return
            for i in range(len(result['TABLE'])):
                self.cmbTables.addItem(result['SCHEMA'][i] + '.' + result[
                    'TABLE'][i])

    def setDBServer(self, dbServerName):
        settings = QSettings()
        settings.setValue('PostgreSQL/connections/selected',
                          dbServerName)

    def cmbServer_currentIndexChanged(self):
        '''
        Slot documentation goes here.
        '''
        if self.cmbServer.currentIndex() == 0:
            self.lblDBUser.setText("")
            self.cmbTables.clear()

        self.setDBServer(self.cmbServer.currentText())
        self.initDB(self.cmbServer.currentText())

    def buttonBox_accepted(self):
        if self.cmbTables.currentIndex() == 0 or self.cmbServer.currentIndex() == 0:
            QMessageBox.warning(None, self.tr('Error'),
                                self.tr('No Layer was selected.'))
        else:
            versionTableList = self.cmbTables.currentText().split('.')
            connectionName = self.cmbServer.currentText()
            self.loadVersionLayer(connectionName, versionTableList[0],
                                  versionTableList[1])

    def loadVersionLayer(self, connectionName, schema, table):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        settings = QSettings()
        mySettings = '/PostgreSQL/connections/' + connectionName
        DBNAME = settings.value(mySettings + '/database')
        DBUSER = settings.value(mySettings + '/username')
        DBHOST = settings.value(mySettings + '/host')
        DBPORT = settings.value(mySettings + '/port')
        DBPASSWD = settings.value(mySettings + '/password')
        DBTYPE = 'pg'

        if DBUSER == '' or DBPASSWD == '':
            connectionInfo = "dbname='" + DBNAME + "' host=" + DBHOST + ' port=' + DBPORT
            (success, user, password) = QgsCredentials.instance().get(
                connectionInfo, None, None)
            QgsCredentials.instance().put(connectionInfo, user, password)
            DBUSER = user
            DBPASSWD = password

        myDb = DbObj(pluginname=connectionName, typ=DBTYPE, hostname=DBHOST,
                     port=DBPORT, dbname=DBNAME, username=DBUSER,
                     password=DBPASSWD)
        sql = "select * from versions.version_tables \
        where version_table_schema = '%s' \
          and version_table_name = '%s'" % (schema, table)

        layer, error = myDb.read(sql)
        if error is not None:
            QMessageBox.information(
                None,
                self.tr("DB error"),
                self.tr("The following error came up when loading the layer:"
                        "\n{0}".format(error)))
            return
        uri = QgsDataSourceUri()
        uri.setConnection(DBHOST, DBPORT, DBNAME, DBUSER, DBPASSWD)
        uri.setDataSource(layer['VERSION_VIEW_SCHEMA'][0], layer[
            'VERSION_VIEW_NAME'][0], '' + layer[
                'VERSION_VIEW_GEOMETRY_COLUMN'][0] + '', '', layer[
                    'VERSION_VIEW_PKEY'][0])
        layerName = layer['VERSION_TABLE_NAME'][0]
        vLayer = QgsVectorLayer(uri.uri(), layerName, 'postgres')

        if self.tools.vectorLayerExists(vLayer.name()) or self.tools.vectorLayerExists(vLayer.name() + ' (modified)'):
            QMessageBox.warning(
                None, '', self.tr('Layer {0} is already loaded').format(table))
            QApplication.restoreOverrideCursor()
            QApplication.setOverrideCursor(Qt.ArrowCursor)
            return None

        QgsProject().instance().addMapLayer(vLayer)

        myDb.close()
        QApplication.restoreOverrideCursor()
        QApplication.setOverrideCursor(Qt.ArrowCursor)
