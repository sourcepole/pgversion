# -*- coding: utf-8 -*-

"""
Module implementing CommitMessageDialog.
"""

from PyQt4.QtGui import QDialog
from PyQt4.QtCore import pyqtSignature,  QSettings

from Ui_Ui_CommitMessage import Ui_CommitMessage

class CommitMessageDialog(QDialog, Ui_CommitMessage):
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
