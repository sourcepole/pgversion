# -*- coding: utf-8 -*-
"""
/***************************************************************************
                                 A QGIS plugin
Class for managing Plugin Abouts                              -------------------
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

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog
from .metadata import Metadata
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui_about.ui'))
    
class About( QDialog, FORM_CLASS):
    def __init__( self):
        QDialog.__init__( self)
        self.setupUi( self )
        self.plugin_dir = os.path.dirname(__file__)
        self.metadata = Metadata()
        
        self.setWindowTitle(self.tr('About %s %s' % (self.metadata.name(),  self.metadata.version())))
        self.lblVersion.setText( self.tr( "Version: " )+self.metadata.version() ) 
        self.tabWidget.setTabText(0,  self.metadata.name())
        self.tabWidget.setTabText(1,  self.tr("Author"))
        self.tabWidget.setTabText(2,  self.tr("Contact"))
        self.tabWidget.setTabText(3,  self.tr("Change Log"))
    
        # setup texts
        aboutString = self.metadata.description()
    
        contribString = self.tr("<p><center><b>Author(s):</b></center></p>") 
        contribString += self.tr("<p>%s<br>" % unicode(self.metadata.author())) 
        
        licenseString = self.tr(u"Sourcepole AG - Linux & Open Source Solutions\n")
        licenseString += self.tr(u"Weberstrasse 5, 8004 Zurich, Switzerland\n")
        
        licenseString += "\n"
        licenseString += self.tr(u"Contact:\n")
        licenseString += self.metadata.author()+"\n"
        licenseString +=  self.metadata.email()+"\n"
        licenseString +=  self.metadata.homepage()+"\n"
        licenseString +=  self.metadata.tracker()+"\n"
        licenseString +=  self.metadata.repository()+"\n"
        
        
        # write texts
        self.memAbout.setText( aboutString )
        self.memContrib.setText(contribString )
        self.memAcknowl.setText( licenseString )
        self.memChangeLog.setText( self.metadata.changelog() )
                
