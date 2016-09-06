# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/dev/qgis/pgversion-plugin/pgversion/forms/Ui_pgLoadVersion.ui'
#
# Created: Tue Sep  6 13:05:06 2016
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_pgLoadVersion(object):
    def setupUi(self, pgLoadVersion):
        pgLoadVersion.setObjectName(_fromUtf8("pgLoadVersion"))
        pgLoadVersion.resize(533, 155)
        pgLoadVersion.setLocale(QtCore.QLocale(QtCore.QLocale.German, QtCore.QLocale.Switzerland))
        self.gridLayout_2 = QtGui.QGridLayout(pgLoadVersion)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(pgLoadVersion)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.cmbTables = QtGui.QComboBox(pgLoadVersion)
        self.cmbTables.setObjectName(_fromUtf8("cmbTables"))
        self.gridLayout.addWidget(self.cmbTables, 2, 1, 1, 1)
        self.label_2 = QtGui.QLabel(pgLoadVersion)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.label_3 = QtGui.QLabel(pgLoadVersion)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.lblDBUser = QtGui.QLabel(pgLoadVersion)
        self.lblDBUser.setText(_fromUtf8(""))
        self.lblDBUser.setObjectName(_fromUtf8("lblDBUser"))
        self.gridLayout.addWidget(self.lblDBUser, 1, 1, 1, 1)
        self.cmbServer = QtGui.QComboBox(pgLoadVersion)
        self.cmbServer.setObjectName(_fromUtf8("cmbServer"))
        self.gridLayout.addWidget(self.cmbServer, 0, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(pgLoadVersion)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout_2.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(pgLoadVersion)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), pgLoadVersion.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), pgLoadVersion.reject)
        QtCore.QMetaObject.connectSlotsByName(pgLoadVersion)

    def retranslateUi(self, pgLoadVersion):
        pgLoadVersion.setWindowTitle(_translate("pgLoadVersion", "PostGIS Versioning System", None))
        self.label.setText(_translate("pgLoadVersion", "select versioned layer for loading into canvas:", None))
        self.label_2.setText(_translate("pgLoadVersion", "Current Database Connection Name:", None))
        self.label_3.setText(_translate("pgLoadVersion", "Current Database User:", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    pgLoadVersion = QtGui.QDialog()
    ui = Ui_pgLoadVersion()
    ui.setupUi(pgLoadVersion)
    pgLoadVersion.show()
    sys.exit(app.exec_())

