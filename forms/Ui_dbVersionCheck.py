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
        
    def __init__(self, myDb, pgvs_revision, install_path,  type,  parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.myDb = myDb
        self.install_path = install_path
        self.type = type
        self.pgvs_revision = pgvs_revision
        
    @pyqtSignature("bool")
    def on_btnUpdate_clicked(self, checked):

        
        fp = open(self.install_path)
        s = fp.read()
        data = s.decode("utf-8-sig")
        result = self.myDb.runError(data)
        
        if len(result) > 1:
          QMessageBox.information(None, self.tr('Error'), result)
          return False
        else:
            if (self.type == 'install'):
               QMessageBox.information(None, self.tr('Installation'),  self.tr('Installation of pgvs was successful') )    
            else:
               QMessageBox.information(None, self.tr('Upgrade'), self.tr('Upgrade of pgvs was successful'))
            self.close()
            return True
        
    
    @pyqtSignature("bool")
    def on_btnClose_clicked(self, checked):
        self.close()

