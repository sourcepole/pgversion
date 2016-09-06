# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/.qgis/python/plugins/pgversion/Ui_dbVersionCheck.ui'
#
# Created: Sat Nov 27 14:38:14 2010
#      by: PyQt4 UI code generator 4.7
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_DbVersionCheck(object):
    def setupUi(self, DbVersionCheck):
        DbVersionCheck.setObjectName("DbVersionCheck")
        DbVersionCheck.resize(400, 300)
        DbVersionCheck.setModal(True)
        self.gridLayout = QtGui.QGridLayout(DbVersionCheck)
        self.gridLayout.setObjectName("gridLayout")
        self.messageTextEdit = QtGui.QTextEdit(DbVersionCheck)
        self.messageTextEdit.setObjectName("messageTextEdit")
        self.gridLayout.addWidget(self.messageTextEdit, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnUpdate = QtGui.QPushButton(DbVersionCheck)
        self.btnUpdate.setObjectName("btnUpdate")
        self.horizontalLayout.addWidget(self.btnUpdate)
        self.btnClose = QtGui.QPushButton(DbVersionCheck)
        self.btnClose.setObjectName("btnClose")
        self.horizontalLayout.addWidget(self.btnClose)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)

        self.retranslateUi(DbVersionCheck)
        QtCore.QMetaObject.connectSlotsByName(DbVersionCheck)

    def retranslateUi(self, DbVersionCheck):
        DbVersionCheck.setWindowTitle(QtGui.QApplication.translate("DbVersionCheck", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.btnUpdate.setText(QtGui.QApplication.translate("DbVersionCheck", "DB-Update", None, QtGui.QApplication.UnicodeUTF8))
        self.btnClose.setText(QtGui.QApplication.translate("DbVersionCheck", "Close", None, QtGui.QApplication.UnicodeUTF8))
        self.btnClose.setShortcut(QtGui.QApplication.translate("DbVersionCheck", "Ctrl+S", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    DbVersionCheck = QtGui.QDialog()
    ui = Ui_DbVersionCheck()
    ui.setupUi(DbVersionCheck)
    DbVersionCheck.show()
    sys.exit(app.exec_())

