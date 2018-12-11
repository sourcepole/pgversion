# -*- coding: utf-8 -*-

"""
Module implementing Ui_Help.
"""

from PyQt4.QtGui import QDialog
from PyQt4.QtCore import pyqtSignature

from Ui_Ui_help import Ui_Ui_Help

class HelpDialog(QDialog, Ui_Ui_Help):
    """
    Class documentation goes here.
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
 
