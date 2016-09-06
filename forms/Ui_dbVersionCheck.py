# -*- coding: utf-8 -*-

"""
Module implementing DbVersionCheck.
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from Ui_Ui_dbVersionCheck import Ui_DbVersionCheck

class DbVersionCheckDialog(QDialog, Ui_DbVersionCheck):
    """
    Class documentation goes here.
    """
        
    def __init__(self, myDb, pgvsRevision, parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.myDb = myDb
        self.pgvsRevision = pgvsRevision
    
    @pyqtSignature("bool")
    def on_btnUpdate_clicked(self, checked):

        btnText = self.btnUpdate.text()

        userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path()+"/python/plugins/pgversion"  
        systemPluginPath = QgsApplication.prefixPath()+"/share/qgis/python/plugins/pgversion"

        if QFileInfo(userPluginPath).exists():
          self.pluginPath = userPluginPath
          if (btnText == 'Install pgvs'):
              self.functionsPath = userPluginPath+"/docs/create_versions_schema.sql"
#          else:
#              self.functionsPath = userPluginPath+"/tools/updateFunctions.sql"
        elif QFileInfo(systemPluginPath).exists():
          self.pluginPath = systemPluginPath
          if (btnText == 'Install pgvs'):
              self.functionsPath = systemPluginPath+"/docs/create_versions_schema.sql"              
#          else:
#              self.functionsPath = systemPluginPath+"/tools/updateFunctions.sql"
        
        fp = open(self.functionsPath)
        s = fp.read()
        data = s.decode("utf-8-sig")
#        sqlFile = QFile(self.functionsPath)
#        sqlFile.open(QIODevice.ReadOnly)
#        data = sqlFile.read(QFileInfo(sqlFile).size())
        result = self.myDb.runError(data)
#        result = self.myDb.runError("select versions.pgvsupdatecheck('"+self.pgvsRevision+"')")
        
        if len(result) > 1:
          QMessageBox.information(None, QCoreApplication.translate('dbVersionCheckDialog','Error'), result)
          return 1
        else:
            if (btnText == 'Install pgvs'):
               QMessageBox.information(None, QCoreApplication.translate('dbVersionCheckDialog',''), QCoreApplication.translate('dbVersionCheckDialog','installation was successful'))    
            else:
               QMessageBox.information(None, QCoreApplication.translate('dbVersionCheckDialog',''), QCoreApplication.translate('dbVersionCheckDialog','upgrade successful'))
            self.close()
            return 0
        
    
    @pyqtSignature("bool")
    def on_btnClose_clicked(self, checked):
        self.close()

