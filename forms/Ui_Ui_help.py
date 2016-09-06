# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/.qgis/python/plugins/pgversion/Ui_help.ui'
#
# Created: Sat Nov 27 14:38:14 2010
#      by: PyQt4 UI code generator 4.7
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Ui_Help(object):
    def setupUi(self, Ui_Help):
        Ui_Help.setObjectName("Ui_Help")
        Ui_Help.resize(947, 611)
        self.gridLayout = QtGui.QGridLayout(Ui_Help)
        self.gridLayout.setObjectName("gridLayout")
        self.webView = QtWebKit.QWebView(Ui_Help)
        self.webView.setUrl(QtCore.QUrl("about:blank"))
        self.webView.setObjectName("webView")
        self.gridLayout.addWidget(self.webView, 0, 0, 1, 1)

        self.retranslateUi(Ui_Help)
        QtCore.QMetaObject.connectSlotsByName(Ui_Help)

    def retranslateUi(self, Ui_Help):
        Ui_Help.setWindowTitle(QtGui.QApplication.translate("Ui_Help", "Dialog", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Ui_Help = QtGui.QDialog()
    ui = Ui_Ui_Help()
    ui.setupUi(Ui_Help)
    Ui_Help.show()
    sys.exit(app.exec_())

