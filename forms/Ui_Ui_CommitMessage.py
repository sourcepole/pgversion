# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/.qgis/python/plugins/pgversion/Ui_CommitMessage.ui'
#
# Created: Sat Nov 27 14:38:13 2010
#      by: PyQt4 UI code generator 4.7
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_CommitMessage(object):
    def setupUi(self, CommitMessage):
        CommitMessage.setObjectName("CommitMessage")
        CommitMessage.resize(400, 300)
        self.gridLayout = QtGui.QGridLayout(CommitMessage)
        self.gridLayout.setObjectName("gridLayout")
        self.textEdit = QtGui.QTextEdit(CommitMessage)
        self.textEdit.setObjectName("textEdit")
        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(CommitMessage)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(CommitMessage)
        QtCore.QMetaObject.connectSlotsByName(CommitMessage)

    def retranslateUi(self, CommitMessage):
        CommitMessage.setWindowTitle(QtGui.QApplication.translate("CommitMessage", "Commit Message", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    CommitMessage = QtGui.QDialog()
    ui = Ui_CommitMessage()
    ui.setupUi(CommitMessage)
    CommitMessage.show()
    sys.exit(app.exec_())

