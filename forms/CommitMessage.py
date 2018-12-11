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
 This script initializes the plugin, making it known to QGIS.
"""

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

import os
from qgis.PyQt import uic


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'CommitMessage.ui'))


class CommitMessageDialog(QDialog, FORM_CLASS):
    """
    Class documentation goes here.
    """
    def __init__(self, parent=None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.settings = QSettings()
        self.messages = []
        self.messages = self.settings.value(
            "/pgVersion/commit_messages", [], str)
        self.messages = list(set(self.messages))
        self.cmbMessages.addItems(self.messages)
        self.textEdit.setText('')

        self.buttonBox.accepted.connect(self.buttonBox_accepted)
        self.buttonBox.rejected.connect(self.buttonBox_rejected)
        self.cmbMessages.activated.connect(self.cmbMessages_activated)

    def buttonBox_accepted(self):
        """
        Slot documentation goes here.
        """
        if self.textEdit.toPlainText() not in self.messages:
            self.messages.insert(0, self.textEdit.toPlainText())
            self.messages = list(set(self.messages))
            self.settings.setValue("/pgVersion/commit_messages", self.messages)
        if not self.textEdit.toPlainText():
            QMessageBox.critical(None, self.tr("Error"),
                                 self.tr("Please write a commit message"))
            return
        self.done(1)

    def buttonBox_rejected(self):
        """
        Slot documentation goes here.
        """
        self.done(0)
        self.close()

    def cmbMessages_activated(self):
        """
        Slot documentation goes here.

        @param p0 DESCRIPTION
        @type QString
        """
        self.textEdit.setText(self.cmbMessages.currentText())
