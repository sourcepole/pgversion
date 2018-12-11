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
from qgis.core import *
import os
from qgis.PyQt import uic


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dbVersionCheck.ui'))


class DbVersionCheckDialog(QDialog, FORM_CLASS):
    """
    Class documentation goes here.
    """

    def __init__(self, myDb, pgvs_revision, install_path, type, parent=None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.myDb = myDb
        self.install_path = install_path
        self.type = type
        self.pgvs_revision = pgvs_revision

        self.messageTextEdit.setReadOnly(True)
        self.btnUpdate.clicked.connect(self.btnUpdate_clicked)
        self.btnClose.clicked.connect(self.btnClose_clicked)

    def btnUpdate_clicked(self):
        fp = open(self.install_path)
        s = fp.read()
        success, error = self.myDb.run(s)

        if error is not None:
            QMessageBox.information(
                None,
                self.tr("DB error"),
                self.tr("The following error came up when initializing the DB:"
                        "\n{0}".format(error)))
            return

        if self.type == 'install':
            QMessageBox.information(
                None, self.tr('Installation'),
                self.tr('Installation of pgvs was successful'))
        else:
            QMessageBox.information(
                None, self.tr('Upgrade'),
                self.tr('Upgrade of pgvs was successful'))
        self.close()

    def btnClose_clicked(self):
        self.close()
