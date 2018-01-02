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
from PyQt4.QtCore import pyqtSignature,  QSettings
from PyQt4.QtGui import QDialog

import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'commit_message.ui'))

class CommitMessageDialog(QDialog, FORM_CLASS):
    """
    Class documentation goes here.
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.settings = QSettings()
        self.messages = []
        self.messages = self.settings.value("/pgVersion/commit_messages",  [],  str)
        list(set(self.messages))
        self.cmbMessages.addItems(self.messages)
        self.textEdit.setText('')
    
    @pyqtSignature("")
    def on_buttonBox_accepted(self):
        """
        Slot documentation goes here.
        """
        if  self.textEdit.toPlainText() not in self.messages:
            self.messages.insert(0, self.textEdit.toPlainText())
            list(set(self.messages))
            self.settings.setValue("/pgVersion/commit_messages",  self.messages)
            
        self.done(1)
    
    @pyqtSignature("")
    def on_buttonBox_rejected(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.done(0)
        self.close()
    
    @pyqtSignature("QString")
    def on_cmbMessages_highlighted(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type QString
        """
        # TODO: not implemented yet
        pass
    
    @pyqtSignature("QString")
    def on_cmbMessages_activated(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type QString
        """
        # TODO: not implemented yet
        self.textEdit.setText(p0)
    
    @pyqtSignature("QString")
    def on_cmbMessages_textChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type QString
        """
        # TODO: not implemented yet
        raise NotImplementedError
