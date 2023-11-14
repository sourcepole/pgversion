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
from pgversion.dbtools.dbtools import *
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
        self.DBSERVICE = settings.value(mySettings + '/service')
        self.DBNAME = settings.value(mySettings + '/database')
        self.DBUSER = settings.value(mySettings + '/username')
        self.DBHOST = settings.value(mySettings + '/host')
        self.DBPORT = settings.value(mySettings + '/port')
        self.DBPASSWD = settings.value(mySettings + '/password')
        self.DBTYPE = 'pg'
#        try:
        if self.DBSERVICE != 'NULL' and self.DBSERVICE != '':
            self.myDb = DbObj(pluginname=selectedServer, service=self.DBSERVICE)     
            self.DBUSER = self.myDb.user()
            self.DBNAME = self.myDb.dbname()
            self.DBPORT = self.myDb.dbport()
        else:
            if self.DBUSER == '':
                connectionInfo = "dbname='%s' host=%s port=%s" % (self.DBNAME,  self.DBHOST,  self.DBPORT)
                (success, user, password) = QgsCredentials.instance().get(connectionInfo, None, None)
                if not success:
                    return None
                QgsCredentials.instance().put(connectionInfo, user, password)
                DBUSER = user
                DBPASSWD = password
            
            self.myDb = DbObj(pluginname=selectedServer, 
                                    typ=self.DBTYPE,
                                    hostname=self.DBHOST, 
                                    port=self.DBPORT,
                                    dbname=self.DBNAME, 
                                    username=self.DBUSER, 
                                    password=self.DBPASSWD)
#        except:
#            QMessageBox.warning(
#                None, self.tr('Error'),
#                self.tr('No Database Connection Established.'))
#            self.cmbServer.setCurrentIndex(0)
#            return None

        if self.DBUSER == '':
            QMessageBox.warning(
                None, self.tr('Error'),
                self.tr("""
In order to work with pgversion properly, the database connection must contain at least one user name! 
Please fix the PostgreSQL database connection."""))
            self.lst_tables.clear()
            return None    

        if not self.myDb.conn:
            self.cmbServer.setCurrentIndex(0)
            self.close()
            return None

        if not self.tools.check_PGVS_revision(self.myDb):
            self.cmbServer.setCurrentIndex(0)
            return None

        self.lblDBUser.setText(self.DBUSER)
        query = 'select 4 as count,  1 as table'
        sysResult,  error = self.myDb.read(query)

        query = 'select version_table_schema as schema, version_table_name as table \
        from versions.version_tables \
        order by version_table_schema,version_table_name'
        result,  error = self.myDb.read(query)
        self.lst_tables.clear()

        if sysResult['COUNT'][0] > 3 or len(result['TABLE']) > 0:
            self.lst_tables.addItem('-------------')
            if result is None:
                return
            for i in range(len(result['TABLE'])):
                self.lst_tables.addItem(result['SCHEMA'][i] + '.' + result[
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
            self.lst_tables.clear()

        self.setDBServer(self.cmbServer.currentText())
        self.initDB(self.cmbServer.currentText())

    def buttonBox_accepted(self):
        
        if len(self.lst_tables.selectedItems()) == 0:
            QMessageBox.warning(None, self.tr('Error'),
                                self.tr('No Layer was selected.'))
            return 0
        else:
            for item in self.lst_tables.selectedItems():
                versionTable = item.text().split('.')
#                connectionName = self.cmbServer.currentText()
                self.loadVersionLayer(versionTable[0], versionTable[1])

    def loadVersionLayer(self, schema, table):
        QApplication.setOverrideCursor(Qt.WaitCursor)

        sql = """select * from versions.version_tables 
        where version_table_schema = '%s' 
          and version_table_name = '%s'""" % (schema, table)

        layer, error = self.myDb.read(sql)
        if error is not None:
            QMessageBox.information(
                None,
                self.tr("DB error"),
                self.tr("The following error came up when loading the layer:"
                        "\n{0}".format(error)))
            return
        uri = QgsDataSourceUri()
        
#        try:
        if self.DBSERVICE != '':
            uri.setConnection(self.DBSERVICE,  self.DBNAME, self.DBUSER, self.DBPASSWD)
        else:
            uri.setConnection(self.DBHOST, self.DBPORT, self.DBNAME, self.DBUSER, self.DBPASSWD)
#        except:
#            uri.setConnection(self.DBHOST, self.DBPORT, self.DBNAME, self.DBUSER, '')
            
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

#        self.myDb.close()
        QApplication.restoreOverrideCursor()
#        QApplication.setOverrideCursor(Qt.ArrowCursor)
