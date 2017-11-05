# -*- coding: utf-8 -*-

"""
Module implementing Ui_Help.
"""
from PyQt4 import uic
from PyQt4.QtGui import QDialog
from PyQt4.QtCore import pyqtSignature
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'help.ui'))

class HelpDialog(QDialog, FORM_CLASS):
    """
    Class documentation goes here.
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
 
