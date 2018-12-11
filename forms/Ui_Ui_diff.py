# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/dev/qgis/pgversion-plugin/pgversion/forms/Ui_diff.ui'
#
# Created: Thu Jul  2 18:03:27 2015
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

class Ui_DiffDlg(object):
    def setupUi(self, DiffDlg):
        DiffDlg.setObjectName(_fromUtf8("DiffDlg"))
        DiffDlg.resize(320, 370)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DiffDlg.sizePolicy().hasHeightForWidth())
        DiffDlg.setSizePolicy(sizePolicy)
        DiffDlg.setMaximumSize(QtCore.QSize(320, 370))
        self.gridLayout_3 = QtGui.QGridLayout(DiffDlg)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.groupBox = QtGui.QGroupBox(DiffDlg)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.radioRevisionRev1 = QtGui.QRadioButton(self.groupBox)
        self.radioRevisionRev1.setObjectName(_fromUtf8("radioRevisionRev1"))
        self.gridLayout.addWidget(self.radioRevisionRev1, 0, 0, 1, 1)
        self.cmbRevision1 = QtGui.QComboBox(self.groupBox)
        self.cmbRevision1.setObjectName(_fromUtf8("cmbRevision1"))
        self.gridLayout.addWidget(self.cmbRevision1, 0, 1, 1, 2)
        self.radioDateRev1 = QtGui.QRadioButton(self.groupBox)
        self.radioDateRev1.setObjectName(_fromUtf8("radioDateRev1"))
        self.gridLayout.addWidget(self.radioDateRev1, 1, 0, 1, 1)
        self.radioHeadRev1 = QtGui.QRadioButton(self.groupBox)
        self.radioHeadRev1.setObjectName(_fromUtf8("radioHeadRev1"))
        self.gridLayout.addWidget(self.radioHeadRev1, 2, 0, 1, 1)
        self.radioBaseRev1 = QtGui.QRadioButton(self.groupBox)
        self.radioBaseRev1.setObjectName(_fromUtf8("radioBaseRev1"))
        self.gridLayout.addWidget(self.radioBaseRev1, 3, 0, 1, 1)
        self.dateEditRev1 = QtGui.QDateEdit(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(200)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dateEditRev1.sizePolicy().hasHeightForWidth())
        self.dateEditRev1.setSizePolicy(sizePolicy)
        self.dateEditRev1.setCalendarPopup(True)
        self.dateEditRev1.setObjectName(_fromUtf8("dateEditRev1"))
        self.gridLayout.addWidget(self.dateEditRev1, 1, 1, 1, 1)
        self.timeEditRev1 = QtGui.QTimeEdit(self.groupBox)
        self.timeEditRev1.setObjectName(_fromUtf8("timeEditRev1"))
        self.gridLayout.addWidget(self.timeEditRev1, 1, 2, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(DiffDlg)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.radioRevisionRev2 = QtGui.QRadioButton(self.groupBox_2)
        self.radioRevisionRev2.setObjectName(_fromUtf8("radioRevisionRev2"))
        self.gridLayout_2.addWidget(self.radioRevisionRev2, 0, 0, 2, 1)
        self.cmbRevision2 = QtGui.QComboBox(self.groupBox_2)
        self.cmbRevision2.setObjectName(_fromUtf8("cmbRevision2"))
        self.gridLayout_2.addWidget(self.cmbRevision2, 0, 1, 1, 2)
        self.radioDateRev2 = QtGui.QRadioButton(self.groupBox_2)
        self.radioDateRev2.setObjectName(_fromUtf8("radioDateRev2"))
        self.gridLayout_2.addWidget(self.radioDateRev2, 2, 0, 1, 1)
        self.radioHeadRev2 = QtGui.QRadioButton(self.groupBox_2)
        self.radioHeadRev2.setObjectName(_fromUtf8("radioHeadRev2"))
        self.gridLayout_2.addWidget(self.radioHeadRev2, 3, 0, 1, 1)
        self.radioBaseRev2 = QtGui.QRadioButton(self.groupBox_2)
        self.radioBaseRev2.setObjectName(_fromUtf8("radioBaseRev2"))
        self.gridLayout_2.addWidget(self.radioBaseRev2, 4, 0, 1, 1)
        self.dateEditRev2 = QtGui.QDateEdit(self.groupBox_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(200)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dateEditRev2.sizePolicy().hasHeightForWidth())
        self.dateEditRev2.setSizePolicy(sizePolicy)
        self.dateEditRev2.setCalendarPopup(True)
        self.dateEditRev2.setObjectName(_fromUtf8("dateEditRev2"))
        self.gridLayout_2.addWidget(self.dateEditRev2, 2, 1, 1, 1)
        self.timeEditRev2 = QtGui.QTimeEdit(self.groupBox_2)
        self.timeEditRev2.setObjectName(_fromUtf8("timeEditRev2"))
        self.gridLayout_2.addWidget(self.timeEditRev2, 2, 2, 1, 1)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.gridLayout_3.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(DiffDlg)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout_3.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(DiffDlg)
        QtCore.QMetaObject.connectSlotsByName(DiffDlg)

    def retranslateUi(self, DiffDlg):
        DiffDlg.setWindowTitle(_translate("DiffDlg", "PgVersion DIFF", None))
        self.groupBox.setTitle(_translate("DiffDlg", "Revision 1", None))
        self.radioRevisionRev1.setText(_translate("DiffDlg", "Number", None))
        self.radioDateRev1.setText(_translate("DiffDlg", "Date", None))
        self.radioHeadRev1.setText(_translate("DiffDlg", "HEAD", None))
        self.radioBaseRev1.setText(_translate("DiffDlg", "BASE", None))
        self.groupBox_2.setTitle(_translate("DiffDlg", "Revision 2", None))
        self.radioRevisionRev2.setText(_translate("DiffDlg", "Number", None))
        self.radioDateRev2.setText(_translate("DiffDlg", "Date", None))
        self.radioHeadRev2.setText(_translate("DiffDlg", "HEAD", None))
        self.radioBaseRev2.setText(_translate("DiffDlg", "BASE", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    DiffDlg = QtGui.QDialog()
    ui = Ui_DiffDlg()
    ui.setupUi(DiffDlg)
    DiffDlg.show()
    sys.exit(app.exec_())

