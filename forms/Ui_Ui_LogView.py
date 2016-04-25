# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/dev/qgis/pgversion-plugin/pgversion/forms/Ui_LogView.ui'
#
# Created: Mon Feb 29 17:00:53 2016
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

class Ui_LogView(object):
    def setupUi(self, LogView):
        LogView.setObjectName(_fromUtf8("LogView"))
        LogView.setWindowModality(QtCore.Qt.ApplicationModal)
        LogView.resize(722, 562)
        self.gridLayout = QtGui.QGridLayout(LogView)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.treeWidget = QtGui.QTreeWidget(LogView)
        self.treeWidget.setObjectName(_fromUtf8("treeWidget"))
        self.gridLayout.addWidget(self.treeWidget, 4, 0, 1, 4)
        self.btnRollback = QtGui.QPushButton(LogView)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnRollback.sizePolicy().hasHeightForWidth())
        self.btnRollback.setSizePolicy(sizePolicy)
        self.btnRollback.setMinimumSize(QtCore.QSize(0, 0))
        self.btnRollback.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.btnRollback.setObjectName(_fromUtf8("btnRollback"))
        self.gridLayout.addWidget(self.btnRollback, 3, 0, 1, 4)
        self.btnDiff = QtGui.QPushButton(LogView)
        self.btnDiff.setObjectName(_fromUtf8("btnDiff"))
        self.gridLayout.addWidget(self.btnDiff, 7, 1, 1, 1)
        self.btnCheckout = QtGui.QPushButton(LogView)
        self.btnCheckout.setObjectName(_fromUtf8("btnCheckout"))
        self.gridLayout.addWidget(self.btnCheckout, 7, 0, 1, 1)
        self.btnClose = QtGui.QDialogButtonBox(LogView)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnClose.sizePolicy().hasHeightForWidth())
        self.btnClose.setSizePolicy(sizePolicy)
        self.btnClose.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.gridLayout.addWidget(self.btnClose, 7, 3, 1, 1)
        self.cmbTags = QtGui.QComboBox(LogView)
        self.cmbTags.setObjectName(_fromUtf8("cmbTags"))
        self.cmbTags.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbTags, 7, 2, 1, 1)

        self.retranslateUi(LogView)
        QtCore.QMetaObject.connectSlotsByName(LogView)

    def retranslateUi(self, LogView):
        LogView.setWindowTitle(_translate("LogView", "PG-Version LogView", None))
        self.treeWidget.headerItem().setText(0, _translate("LogView", "Revision", None))
        self.treeWidget.headerItem().setText(1, _translate("LogView", "Date", None))
        self.treeWidget.headerItem().setText(2, _translate("LogView", "User", None))
        self.treeWidget.headerItem().setText(3, _translate("LogView", "Log-Message", None))
        self.btnRollback.setText(_translate("LogView", "rollback to selected revision", None))
        self.btnDiff.setText(_translate("LogView", "diff to HEAD revision", None))
        self.btnCheckout.setText(_translate("LogView", "checkout selected revision", None))
        self.cmbTags.setItemText(0, _translate("LogView", "-- checkout Tag --", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    LogView = QtGui.QDialog()
    ui = Ui_LogView()
    ui.setupUi(LogView)
    LogView.show()
    sys.exit(app.exec_())

