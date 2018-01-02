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
from PyQt4.QtGui import QDialog
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'create_branch.ui'))


class DlgCreateBranch(QDialog, FORM_CLASS):
    """
    Class documentation goes here.
    """
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
    
    @pyqtSlot()
    def on_btn_box_create_branch_accepted(self):
        """
        Slot documentation goes here.
        """
        self.setResult(1)
        self.close()
    
    @pyqtSlot()
    def on_btn_box_create_branch_rejected(self):
        """
        Slot documentation goes here.
        """
        self.setResult(0)
        self.close()
