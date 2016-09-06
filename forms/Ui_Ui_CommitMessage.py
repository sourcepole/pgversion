# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/dev/qgis/pgversion-plugin/pgversion/forms/Ui_CommitMessage.ui'
#
# Created: Tue Sep  6 15:29:13 2016
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

class Ui_CommitMessage(object):
    def setupUi(self, CommitMessage):
        CommitMessage.setObjectName(_fromUtf8("CommitMessage"))
        CommitMessage.resize(400, 300)
        self.gridLayout = QtGui.QGridLayout(CommitMessage)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.textEdit = QtGui.QTextEdit(CommitMessage)
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(CommitMessage)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 1)
        self.cmbMessages = QtGui.QComboBox(CommitMessage)
        self.cmbMessages.setObjectName(_fromUtf8("cmbMessages"))
        self.gridLayout.addWidget(self.cmbMessages, 2, 0, 1, 1)
        self.label = QtGui.QLabel(CommitMessage)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.retranslateUi(CommitMessage)
        QtCore.QMetaObject.connectSlotsByName(CommitMessage)

    def retranslateUi(self, CommitMessage):
        CommitMessage.setWindowTitle(_translate("CommitMessage", "Commit Message", None))
        self.label.setText(_translate("CommitMessage", "Recent commit messages:", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    CommitMessage = QtGui.QDialog()
    ui = Ui_CommitMessage()
    ui.setupUi(CommitMessage)
    CommitMessage.show()
    sys.exit(app.exec_())

