# -*- coding: utf-8 -*-

"""
Module implementing PgVersionAbout.
"""

from PyQt4.QtGui import QDialog
from PyQt4.QtCore import pyqtSignature

from Ui_Ui_pgVersionAbout import Ui_PgVersionAbout

class PgVersionAbout(QDialog, Ui_PgVersionAbout):
    """
    Class documentation goes here.
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
    
    @pyqtSignature("bool")
    def on_btnClose_clicked(self, checked):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
