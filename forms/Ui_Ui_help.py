# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/dev/qgis/pgversion-plugin/pgversion/forms/Ui_help.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
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

class Ui_Ui_Help(object):
    def setupUi(self, Ui_Help):
        Ui_Help.setObjectName(_fromUtf8("Ui_Help"))
        Ui_Help.resize(947, 611)
        self.gridLayout = QtGui.QGridLayout(Ui_Help)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.webView = QtWebKit.QWebView(Ui_Help)
        self.webView.setProperty("url", QtCore.QUrl(None))
        self.webView.setObjectName(_fromUtf8("webView"))
        self.gridLayout.addWidget(self.webView, 0, 0, 1, 1)

        self.retranslateUi(Ui_Help)
        QtCore.QMetaObject.connectSlotsByName(Ui_Help)

    def retranslateUi(self, Ui_Help):
        Ui_Help.setWindowTitle(_translate("Ui_Help", "Dialog", None))

from PyQt4 import QtWebKit

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Ui_Help = QtGui.QDialog()
    ui = Ui_Ui_Help()
    ui.setupUi(Ui_Help)
    Ui_Help.show()
    sys.exit(app.exec_())

