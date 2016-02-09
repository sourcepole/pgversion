# -*- coding: utf-8 -*-

"""
Module implementing PgVersionLoadDialog.
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from pgversion.dbtools.dbTools import *
from pgversion.pgVersionTools import  *
from Ui_Ui_pgLoadVersion import Ui_pgLoadVersion
import pgversion.apicompat

class PgVersionLoadDialog(QDialog, Ui_pgLoadVersion):
    def __init__(self,  iface): 
        QDialog.__init__(self)
        self.setupUi(self)
        self.getDbSettings()
        self.tools = PgVersionTools(iface)

    
    def getDbSettings(self):
        settings = QSettings()
        settings.beginGroup("PostgreSQL/connections")
        self.cmbServer.addItem('------------')
        self.cmbServer.addItems(settings.childGroups())
        settings.endGroup()
        selectedDb = settings.value(pystring("PostgreSQL/connections/selected"))
        cmbIndex = self.cmbServer.findText(selectedDb, Qt.MatchExactly)
        self.cmbServer.setCurrentIndex(cmbIndex)    
    
    
    def initDB(self,  selectedServer):    
        if self.cmbServer.currentIndex() == 0:
            return
        settings = QSettings()
        mySettings = "/PostgreSQL/connections/"+selectedServer
        DBNAME = pystring(settings.value(mySettings+"/database"))
        DBUSER = pystring(settings.value(mySettings+"/username"))
        DBHOST = pystring(settings.value(mySettings+"/host"))
        DBPORT = pystring(settings.value(mySettings+"/port"))
        DBPASSWD = pystring(settings.value(mySettings+"/password"))
        DBTYPE = 'pg'

        self.lblDBUser.setText(DBUSER)

        if DBUSER == "" or DBPASSWD == "":
          connectionInfo = "dbname='"+DBNAME+"' host="+DBHOST+" port="+DBPORT 
          (success,  user,  password) =  QgsCredentials.instance().get(connectionInfo, None, None)
          if not success:
              return None
          QgsCredentials.instance().put( connectionInfo, user, password )
          DBUSER = user
          DBPASSWD = password
       
        print DBHOST+" "+DBPORT+" "+DBNAME+" "+DBUSER+" "+DBPASSWD+" "
        try:
            myDb = DbObj(pluginname=selectedServer,typ=DBTYPE,hostname=DBHOST,port=DBPORT,dbname=DBNAME,username=DBUSER, passwort=DBPASSWD)
        except:
            QMessageBox.information(None, QCoreApplication.translate('PgVersionLoadDialog','Error'), QCoreApplication.translate('PgVersionLoadDialog','No Database Connection Established.'))
            return

        if not self.tools.checkPGVSRevision(myDb):
            self.cmbServer.setCurrentIndex(0)
            return
            
        query = "select count(oid) \
        from pg_catalog.pg_proc \
        where proname in ('pgvsinit','pgvscommit','pgvsdrop','pgvsmerge')" 
        
        sysResult  = myDb.read(query)
 
        query =   "select version_table_schema as schema, version_table_name as table \
        from versions.version_tables \
        order by version_table_schema,version_table_name"

        result = myDb.read(query)
        self.cmbTables.clear()

        try:
            if sysResult["COUNT"][0] == "4":
                if len(result["TABLE"]) > 0: 
                  self.cmbTables.addItem("-------------")
                  for i in range(len(result["TABLE"])):
                    self.cmbTables.addItem(result["SCHEMA"][i]+'.'+result["TABLE"][i])
            else:
                self.cmbTables.addItem(QCoreApplication.translate('PgVersionLoadDialog','pgvs not installed in the database'))      
        except:
            QMessageBox.information(None, QCoreApplication.translate('PgVersionLoadDialog','Error'), QCoreApplication.translate('PgVersionLoadDialog','No database connection established.\n Please define a valid database connection and try again.'))
            self.close()
            return            
       
    def setDBServer(self, dbServerName):
        settings = QSettings()
        settings.setValue("PostgreSQL/connections/selected", pystring(dbServerName))  
        pass    
    
    @pyqtSignature("QString")
    def on_cmbTables_currentIndexChanged(self, p0):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        pass
    
    @pyqtSignature("QString")
    def on_cmbServer_currentIndexChanged(self, p0):
        """
        Slot documentation goes here.
        """
        self.setDBServer(p0)
        self.initDB(p0)
    
    
    @pyqtSignature("")
    def on_buttonBox_accepted(self):
            versionTableList= self.cmbTables.currentText().split('.')  
            connectionName = self.cmbServer.currentText()
            self.loadVersionLayer(connectionName,  versionTableList[0],  versionTableList[1]) 
    
    @pyqtSignature("")
    def on_buttonBox_rejected(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        pass
        
    def loadVersionLayer(self, connectionName,  schema,  table):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        settings = QSettings()
        mySettings = "/PostgreSQL/connections/"+connectionName
        DBNAME = pystring(settings.value(mySettings+"/database"))
        DBUSER = pystring(settings.value(mySettings+"/username"))
        DBHOST = pystring(settings.value(mySettings+"/host"))
        DBPORT = pystring(settings.value(mySettings+"/port"))
        DBPASSWD = pystring(settings.value(mySettings+"/password"))
        DBTYPE = 'pg'

        if DBUSER == "" or DBPASSWD == "":
          connectionInfo = "dbname='"+DBNAME+"' host="+DBHOST+" port="+DBPORT 
          (success,  user,  password) =  QgsCredentials.instance().get(connectionInfo, None, None)
          QgsCredentials.instance().put( connectionInfo, user, password )
          DBUSER = user
          DBPASSWD = password
          
        myDb = DbObj(pluginname=connectionName,typ=DBTYPE,hostname=DBHOST,port=DBPORT,dbname=DBNAME,username=DBUSER, passwort=DBPASSWD)

        sql =   "select * from versions.version_tables \
        where version_table_schema = '%s' and version_table_name = '%s'" % (schema,  table)
        layer = myDb.read(sql)    
    
        uri = QgsDataSourceURI()
    
        # set host name, port, database name, username and password
        uri.setConnection(DBHOST, DBPORT, DBNAME, DBUSER, DBPASSWD)    
    
        uri.setDataSource(layer["VERSION_VIEW_SCHEMA"][0], layer["VERSION_VIEW_NAME"][0], ""+layer["VERSION_VIEW_GEOMETRY_COLUMN"][0]+"", "",  layer["VERSION_VIEW_PKEY"][0])
    
        layerName = layer["VERSION_TABLE_NAME"][0]
        vLayer = QgsVectorLayer(uri.uri(), layerName, "postgres")
        vLayer.editingStopped.connect(self.tools.setModified)
        self.tools.setModified(vLayer)
        
        if self.tools.vectorLayerExists(vLayer.name()) or self.tools.vectorLayerExists(vLayer.name()+" (modified)"):
          QMessageBox.warning(None, '', QCoreApplication.translate('PgVersion','Layer {0} is already loaded').formate(table))
          QApplication.restoreOverrideCursor()
          QApplication.setOverrideCursor(Qt.ArrowCursor)      
          return      

        QgsMapLayerRegistry.instance().addMapLayer(vLayer)      
        myDb.close()
        QApplication.restoreOverrideCursor()
        QApplication.setOverrideCursor(Qt.ArrowCursor)                
