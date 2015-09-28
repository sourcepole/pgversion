# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/dev/pythonlibs/about/ui_about.ui'
#
# Created: Wed Mar 12 11:53:44 2014
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_dlgAbout(object):
    def setupUi(self, dlgAbout):
        dlgAbout.setObjectName(_fromUtf8("dlgAbout"))
        dlgAbout.resize(741, 222)
        self.gridLayout = QtGui.QGridLayout(dlgAbout)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.widget = QtGui.QWidget(dlgAbout)
        self.widget.setMinimumSize(QtCore.QSize(0, 0))
        self.widget.setMaximumSize(QtCore.QSize(180, 16777215))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.lblVersion = QtGui.QLabel(self.widget)
        self.lblVersion.setMaximumSize(QtCore.QSize(16777215, 14))
        self.lblVersion.setObjectName(_fromUtf8("lblVersion"))
        self.verticalLayout.addWidget(self.lblVersion)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(self.widget)
        self.buttonBox.setMaximumSize(QtCore.QSize(200, 16777215))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)
        self.gridLayout.addWidget(self.widget, 0, 0, 1, 1)
        self.tabWidget = QtGui.QTabWidget(dlgAbout)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.gridLayout_2 = QtGui.QGridLayout(self.tab)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.memAbout = QtGui.QTextEdit(self.tab)
        self.memAbout.setUndoRedoEnabled(False)
        self.memAbout.setReadOnly(True)
        self.memAbout.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.memAbout.setObjectName(_fromUtf8("memAbout"))
        self.gridLayout_2.addWidget(self.memAbout, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName(_fromUtf8("tab_3"))
        self.gridLayout_3 = QtGui.QGridLayout(self.tab_3)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.memContrib = QtGui.QTextEdit(self.tab_3)
        self.memContrib.setUndoRedoEnabled(False)
        self.memContrib.setReadOnly(True)
        self.memContrib.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.memContrib.setObjectName(_fromUtf8("memContrib"))
        self.gridLayout_3.addWidget(self.memContrib, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_3, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.gridLayout_4 = QtGui.QGridLayout(self.tab_2)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.memAcknowl = QtGui.QTextEdit(self.tab_2)
        self.memAcknowl.setUndoRedoEnabled(False)
        self.memAcknowl.setReadOnly(True)
        self.memAcknowl.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.memAcknowl.setObjectName(_fromUtf8("memAcknowl"))
        self.gridLayout_4.addWidget(self.memAcknowl, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName(_fromUtf8("tab_4"))
        self.gridLayout_5 = QtGui.QGridLayout(self.tab_4)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.memChangeLog = QtGui.QTextEdit(self.tab_4)
        self.memChangeLog.setUndoRedoEnabled(False)
        self.memChangeLog.setReadOnly(True)
        self.memChangeLog.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.memChangeLog.setObjectName(_fromUtf8("memChangeLog"))
        self.gridLayout_5.addWidget(self.memChangeLog, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_4, _fromUtf8(""))
        self.gridLayout.addWidget(self.tabWidget, 0, 1, 1, 1)

        self.retranslateUi(dlgAbout)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), dlgAbout.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), dlgAbout.reject)
        QtCore.QMetaObject.connectSlotsByName(dlgAbout)

    def retranslateUi(self, dlgAbout):
        dlgAbout.setWindowTitle(QtGui.QApplication.translate("dlgAbout", "About", None, QtGui.QApplication.UnicodeUTF8))
        self.lblVersion.setText(QtGui.QApplication.translate("dlgAbout", "Version:", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("dlgAbout", "About ", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("dlgAbout", "Contributors", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("dlgAbout", "Contact", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QtGui.QApplication.translate("dlgAbout", "Change Log", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    dlgAbout = QtGui.QDialog()
    ui = Ui_dlgAbout()
    ui.setupUi(dlgAbout)
    dlgAbout.show()
    sys.exit(app.exec_())

