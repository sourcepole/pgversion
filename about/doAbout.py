# -*- coding: latin1 -*-
"""
/***************************************************************************
 LnfSchwyz
                                 A QGIS plugin
 Plugin for checking quality rules when data are captured
                              -------------------
        begin                : 2014-01-15
        copyright            : (C) 2014 by Dr. Horst Duester / Sourcepole AG
        email                : horst.duester@sourcepole.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
import os
from qgis.PyQt import uic


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'about.ui'))


class DlgAbout(QDialog, FORM_CLASS):
    def __init__(self, plugindir):
        QDialog.__init__(self)
        self.setupUi(self)
        self.plugindir = plugindir
        result = self.metadata()

        self.setWindowTitle(self.tr(
            'About ') + result['name'] + " " + result['version'])
        self.lblVersion.setText(self.tr("Version: ") + result['version'])
        self.tabWidget.setTabText(0, result['name'])
        self.tabWidget.setTabText(1, self.tr("Author"))
        self.tabWidget.setTabText(2, self.tr("Contact"))
        self.tabWidget.setTabText(3, self.tr("Sponsors"))
        self.tabWidget.setTabText(4, self.tr("Change Log"))

        aboutString = result['description']

        contribString = self.tr("<p><center><b>Author(s):</b></center></p>")
        contribString += self.tr(u"<p>{0}<br><br>".format(result['author']))

        sponsorString = self.tr(
            u"<b>The development of PgVersion was funded by:</b><br><br>")
        sponsorString += self.tr(
            u"- Sourcepole AG, Weberstrasse 5, CH-8004 Zurich<br>")
        sponsorString += self.tr(u"- Canton of Glarus / Switzerland<br>")
        sponsorString += self.tr(
            u"- Lower Saxony Ministry of Food, Agriculture and consumer\
             protection / Germany<br>")

        licenseString = self.tr(
            u"Sourcepole AG - Linux & Open Source Solutions\n")
        licenseString += self.tr(
            u"Weberstrasse 5, 8004 Z�rich, Switzerland\n")

        licenseString += "\n"
        licenseString += self.tr(u"Contact:\n")
        licenseString += result['author'] + "\n"
        licenseString += result['email'] + "\n"
        licenseString += result['homepage'] + "\n"
        licenseString += result['tracker'] + "\n"
        licenseString += result['repository'] + "\n"

        # write texts
        self.memAbout.setText(aboutString)
        self.memContrib.setText(contribString)
        self.memSponsor.setText(sponsorString)
        self.memAcknowl.setText(licenseString)
        self.memChangeLog.setText(result['changelog'])

    def metadata(self):
        mdFile = QFile(self.plugindir + "/metadata.txt")
        mdFile.open(QIODevice.ReadOnly | QIODevice.Text)
        inFile = QTextStream(mdFile)

        changeLog = ''
        result = {}

        result['version'] = ''
        result['description'] = ''
        result['name'] = ''
        result['qgisMinimumVersion'] = ''
        result['qgisMaximumVersion'] = ''
        result['author'] = ''
        result['email'] = ''
        result['date'] = ''
        result['homepage'] = ''
        result['tracker'] = ''
        result['repository'] = ''
        result['changelog'] = ''

        while (not inFile.atEnd()):
            line = inFile.readLine()
            lineArr = line.split("=")

            if lineArr[0] == 'version':
                result['version'] = lineArr[1]
            elif lineArr[0] == 'description':
                result['description'] = lineArr[1]
            elif lineArr[0] == 'name':
                result['name'] = lineArr[1]
            elif lineArr[0] == 'qgisMinimumVersion':
                result['qgisMinimumVersion'] = lineArr[1]
            elif lineArr[0] == 'qgisMaximumVersion':
                result['qgisMaximumVersion'] = lineArr[1]
            elif lineArr[0] == 'author':
                result['author'] = lineArr[1]
            elif lineArr[0] == 'date':
                result['author'] = lineArr[1]
            elif lineArr[0] == 'email':
                result['email'] = lineArr[1]
            elif lineArr[0] == 'homepage':
                result['homepage'] = lineArr[1]
            elif lineArr[0] == 'tracker':
                result['tracker'] = lineArr[1]
            elif lineArr[0] == 'repository':
                result['repository'] = lineArr[1]

            elif lineArr[0] == 'changelog':
                line = inFile.readLine()
                while len(line.split("=")) == 1:
                    if line[0:1] != '#':
                        changeLog += line + "\n"
                    line = inFile.readLine()

                result['changelog'] = changeLog
        return result
