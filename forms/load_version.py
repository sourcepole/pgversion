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
from PyQt4.QtCore import Qt, QSettings, pyqtSignature
from PyQt4.QtGui import QDialog, QMessageBox, QApplication
from qgis.core import *
from pgversion.dbtools.dbTools import *
from pgversion.pgversion_tools import *
import pgversion.apicompat as pgversion
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'load_version.ui'))

class PgVersionLoadDialog(QDialog, FORM_CLASS):
    
    def __init__(self, parent):
        QDialog.__init__(self,  None)
        self.setupUi(self)
        
        self.getDbSettings()
        self.tools = PgVersionTools(parent)
        self.iface = parent.iface
        self.parent = parent

    
    def getDbSettings(self):
        settings = QSettings()
        settings.beginGroup('PostgreSQL/connections')
        self.cmbServer.addItem('------------')
        self.cmbServer.addItems(settings.childGroups())
        settings.endGroup()
        selectedDb = settings.value(pystring('PostgreSQL/connections/selected'))
        cmbIndex = self.cmbServer.findText(selectedDb, Qt.MatchExactly)
        self.cmbServer.setCurrentIndex(cmbIndex)

    
    def initDB(self, selectedServer):
        if self.cmbServer.currentIndex() == 0:
            return None
        settings = QSettings()    
        mySettings = '/PostgreSQL/connections/' + selectedServer
        DBNAME = pystring(settings.value(mySettings + '/database'))
        DBUSER = pystring(settings.value(mySettings + '/username'))
        DBHOST = pystring(settings.value(mySettings + '/host'))
        DBPORT = pystring(settings.value(mySettings + '/port'))
        DBPASSWD = pystring(settings.value(mySettings + '/password'))
        DBTYPE = 'pg'
        self.lblDBUser.setText(DBUSER)
        
        if DBUSER == '' or DBPASSWD == '':
            connectionInfo = "dbname='" + DBNAME + "' host=" + DBHOST + ' port=' + DBPORT
            (success, user, password) = QgsCredentials.instance().get(connectionInfo, None, None)
            if not success:
                return None
#            self.iface.instance().put(connectionInfo, user, password)
            QgsCredentials.instance().put(connectionInfo, user, password)
            DBUSER = user
            DBPASSWD = password
        
        try:
            self.myDb = DbObj(pluginname = selectedServer, typ = DBTYPE, hostname = DBHOST, port = DBPORT, dbname = DBNAME, username = DBUSER, passwort = DBPASSWD)
        except:
            QMessageBox.information(None, self.tr('Error'), self.tr('No Database Connection Established.'))
            return None

        if not self.tools.check_PGVS_revision(self.myDb):
            self.cmbServer.setCurrentIndex(0)
            return None
        
        query = 'select version_table_id as id, version_table_schema as schema, version_table_name as table \
        from versions.version_tables \
        order by version_table_schema,version_table_name'
        result = self.myDb.read(query)
        self.cmbTables.clear()
        
        if len(result['TABLE']) > 0:
            self.cmbTables.addItem('-------------')
            for i in range(len(result['TABLE'])):
                self.cmbTables.addItem('%s.%s' % (result['SCHEMA'][i],  result['TABLE'][i]), result['ID'][i] )
                

    
    def setDBServer(self, dbServerName):
        settings = QSettings()
        settings.setValue('PostgreSQL/connections/selected', pystring(dbServerName))

    
    def on_cmbTables_currentIndexChanged(self, p0):
        '''
        Slot documentation goes here.
        '''
        version_id = self.cmbTables.itemData(self.cmbTables.currentIndex())
        sql = "select branch_id as id, branch_text as text \
          from versions.version_branch \
          where version_table_id = %s \
          order by branch_id" % (version_id)
#        print sql
        self.cmbBranch.clear()
        
        if version_id != None:
            result = self.myDb.read(sql)
            for i in range(len(result['ID'])):
                self.cmbBranch.addItem(result['TEXT'][i],  result['ID'][i])
            
            

    on_cmbTables_currentIndexChanged = pyqtSignature('QString')(on_cmbTables_currentIndexChanged)
    
    def on_cmbServer_currentIndexChanged(self, p0):
        '''
        Slot documentation goes here.
        '''
        self.setDBServer(p0)
        self.initDB(p0)

    on_cmbServer_currentIndexChanged = pyqtSignature('QString')(on_cmbServer_currentIndexChanged)
    
    def on_buttonBox_accepted(self):
        if self.cmbTables.currentIndex() == 0 or self.cmbServer.currentIndex() == 0:
            QMessageBox.warning(None, self.tr('Error'),  self.tr('Please select a versioned layer'))
        else:
            versionTableList = self.cmbTables.currentText().split('.')
            selected_branch = self.cmbBranch.currentText()
            branch_id = self.cmbBranch.itemData(self.cmbBranch.currentIndex())
            connectionName = self.cmbServer.currentText()
            
#            if selected_branch == 'master':
#                self.loadVersionLayer(connectionName, versionTableList[0], versionTableList[1],  branch_id)
#            else:               
            self.loadVersionLayer(connectionName, versionTableList[0], versionTableList[1], branch_id, '%s - %s' % (versionTableList[1],  selected_branch))
                
    def on_buttonBox_rejected(self):
        '''
        Slot documentation goes here.
        '''
        pass

    on_buttonBox_rejected = pyqtSignature('')(on_buttonBox_rejected)
    
    def loadVersionLayer(self, connectionName, schema, table,  branch_id=None,  layerName=None):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        settings = QSettings()
        mySettings = '/PostgreSQL/connections/' + connectionName
        DBNAME = pystring(settings.value(mySettings + '/database'))
        DBUSER = pystring(settings.value(mySettings + '/username'))
        DBHOST = pystring(settings.value(mySettings + '/host'))
        DBPORT = pystring(settings.value(mySettings + '/port'))
        DBPASSWD = pystring(settings.value(mySettings + '/password'))
        DBTYPE = 'pg'
        
        if DBUSER == '' or DBPASSWD == '':
            connectionInfo = "dbname='" + DBNAME + "' host=" + DBHOST + ' port=' + DBPORT
            (success, user, password) = QgsCredentials.instance().get(connectionInfo, None, None)
            QgsCredentials.instance().put(connectionInfo, user, password)
            DBUSER = user
            DBPASSWD = password
            
        myDb = DbObj(pluginname = connectionName, typ = DBTYPE, hostname = DBHOST, port = DBPORT, dbname = DBNAME, username = DBUSER, passwort = DBPASSWD)
        sql = "select * from versions.version_tables \
        where version_table_schema = '%s' \
          and version_table_name = '%s'" % (schema, table)
          
        layer = myDb.read(sql)
        uri = QgsDataSourceURI()
        uri.setConnection(DBHOST, DBPORT, DBNAME, DBUSER, DBPASSWD)
        uri.setParam('branch_id', str(branch_id))
        
        version_view = '%s#%s' % (layer['VERSION_VIEW_NAME'][0],  branch_id)
            
        uri.setDataSource(layer['VERSION_VIEW_SCHEMA'][0], version_view, '' + layer['VERSION_VIEW_GEOMETRY_COLUMN'][0] + '', '', layer['VERSION_VIEW_PKEY'][0])
        
        if layerName == None:
            layerName = layer['VERSION_TABLE_NAME'][0]
            
        vLayer = QgsVectorLayer(uri.uri(), layerName, 'postgres')
        
        if self.tools.vectorLayerExists(vLayer.name()) or self.tools.vectorLayerExists(vLayer.name() + ' (modified)'):
            QMessageBox.warning(None, '', self.tr('Layer {0} is already loaded').format(table))
            QApplication.restoreOverrideCursor()
            QApplication.setOverrideCursor(Qt.ArrowCursor)
            return None
            
        QgsMapLayerRegistry.instance().addMapLayer(vLayer)
        myDb.close()
        QApplication.restoreOverrideCursor()
        QApplication.setOverrideCursor(Qt.ArrowCursor)
    
