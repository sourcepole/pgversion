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
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QDialog, QMessageBox
from qgis.core import *

import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'db_version_check.ui'))
    
class DbVersionCheckDialog(QDialog, FORM_CLASS):
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
        
    @pyqtSlot()
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
        
    
    @pyqtSlot()
    def on_btnClose_clicked(self, checked):
        self.close()

