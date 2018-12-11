# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/.qgis/python/plugins/pgversion/Ui_pgVersionAbout.ui'
#
# Created: Thu Jan 20 14:01:41 2011
#      by: PyQt4 UI code generator 4.7
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_PgVersionAbout(object):
    def setupUi(self, PgVersionAbout):
        PgVersionAbout.setObjectName("PgVersionAbout")
        PgVersionAbout.resize(285, 335)
        self.gridlayout = QtGui.QGridLayout(PgVersionAbout)
        self.gridlayout.setObjectName("gridlayout")
        self.txtAbout = QtGui.QTextEdit(PgVersionAbout)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        self.txtAbout.setPalette(palette)
        self.txtAbout.setAutoFillBackground(True)
        self.txtAbout.setFrameShape(QtGui.QFrame.NoFrame)
        self.txtAbout.setFrameShadow(QtGui.QFrame.Plain)
        self.txtAbout.setReadOnly(True)
        self.txtAbout.setObjectName("txtAbout")
        self.gridlayout.addWidget(self.txtAbout, 2, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem, 3, 1, 1, 1)
        self.btnHelp = QtGui.QPushButton(PgVersionAbout)
        self.btnHelp.setObjectName("btnHelp")
        self.gridlayout.addWidget(self.btnHelp, 4, 0, 1, 1)
        self.btnClose = QtGui.QPushButton(PgVersionAbout)
        self.btnClose.setObjectName("btnClose")
        self.gridlayout.addWidget(self.btnClose, 4, 2, 1, 1)
        self.btnWeb = QtGui.QPushButton(PgVersionAbout)
        self.btnWeb.setObjectName("btnWeb")
        self.gridlayout.addWidget(self.btnWeb, 4, 1, 1, 1)
        self.lblVersion = QtGui.QLabel(PgVersionAbout)
        self.lblVersion.setObjectName("lblVersion")
        self.gridlayout.addWidget(self.lblVersion, 1, 0, 1, 2)
        self.lblTitle = QtGui.QLabel(PgVersionAbout)
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setWeight(75)
        font.setBold(True)
        self.lblTitle.setFont(font)
        self.lblTitle.setTextFormat(QtCore.Qt.RichText)
        self.lblTitle.setObjectName("lblTitle")
        self.gridlayout.addWidget(self.lblTitle, 0, 0, 1, 2)

        self.retranslateUi(PgVersionAbout)
        QtCore.QObject.connect(self.btnClose, QtCore.SIGNAL("clicked()"), PgVersionAbout.reject)
        QtCore.QMetaObject.connectSlotsByName(PgVersionAbout)

    def retranslateUi(self, PgVersionAbout):
        PgVersionAbout.setWindowTitle(QtGui.QApplication.translate("PgVersionAbout", "PgVersion About", None, QtGui.QApplication.UnicodeUTF8))
        self.txtAbout.setHtml(QtGui.QApplication.translate("PgVersionAbout", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Sans Serif\'; font-size:9pt;\"></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.btnHelp.setText(QtGui.QApplication.translate("PgVersionAbout", "Help", None, QtGui.QApplication.UnicodeUTF8))
        self.btnClose.setText(QtGui.QApplication.translate("PgVersionAbout", "Close", None, QtGui.QApplication.UnicodeUTF8))
        self.btnWeb.setText(QtGui.QApplication.translate("PgVersionAbout", "Web", None, QtGui.QApplication.UnicodeUTF8))
        self.lblVersion.setText(QtGui.QApplication.translate("PgVersionAbout", "Version x.x-xxxxxx", None, QtGui.QApplication.UnicodeUTF8))
        self.lblTitle.setText(QtGui.QApplication.translate("PgVersionAbout", "PgVersion", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    PgVersionAbout = QtGui.QDialog()
    ui = Ui_PgVersionAbout()
    ui.setupUi(PgVersionAbout)
    PgVersionAbout.show()
    sys.exit(app.exec_())

