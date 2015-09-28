# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/dev/qgis/pgversion-plugin/pgversion/dbtools/login.ui'
#
# Created: Tue Aug 18 17:04:34 2015
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

class Ui_Login(object):
    def setupUi(self, Login):
        Login.setObjectName(_fromUtf8("Login"))
        Login.resize(427, 161)
        Login.setSizeGripEnabled(True)
        self.gridLayout = QtGui.QGridLayout(Login)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(Login)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.lneUserName = QtGui.QLineEdit(Login)
        self.lneUserName.setObjectName(_fromUtf8("lneUserName"))
        self.gridLayout.addWidget(self.lneUserName, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(Login)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.lnePassWord = QtGui.QLineEdit(Login)
        self.lnePassWord.setEchoMode(QtGui.QLineEdit.Password)
        self.lnePassWord.setObjectName(_fromUtf8("lnePassWord"))
        self.gridLayout.addWidget(self.lnePassWord, 1, 1, 1, 1)
        self.btnBoxLogin = QtGui.QDialogButtonBox(Login)
        self.btnBoxLogin.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.btnBoxLogin.setObjectName(_fromUtf8("btnBoxLogin"))
        self.gridLayout.addWidget(self.btnBoxLogin, 2, 1, 1, 1)

        self.retranslateUi(Login)
        QtCore.QMetaObject.connectSlotsByName(Login)

    def retranslateUi(self, Login):
        Login.setWindowTitle(_translate("Login", "Database-Login", None))
        self.label.setText(_translate("Login", "Username:", None))
        self.label_2.setText(_translate("Login", "Password:", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Login = QtGui.QDialog()
    ui = Ui_Login()
    ui.setupUi(Login)
    Login.show()
    sys.exit(app.exec_())

