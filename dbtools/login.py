# -*- coding: utf-8 -*-

"""
Module implementing Login.
"""

from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QDialog

from .Ui_login import Ui_Login


class Login(QDialog, Ui_Login):
    """
    Class documentation goes here.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
    
    @pyqtSignature("")
    def on_btnBoxLogin_accepted(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSignature("")
    def on_btnBoxLogin_rejected(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
