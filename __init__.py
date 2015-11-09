"""
/***************************************************************************
Plugin for the Postgres Versioning System
-----------------------------------------------------------------------------------------------------------------
begin                : 2010-07-31
copyright          : (C) 2010 by Dr. Horst Duester
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
 This script initializes the plugin, making it known to QGIS.
"""
from pgVersion import PgVersion
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
import os

#Initialise thetranslation environment    
userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path()+"/python/plugins/pgversion"  
systemPluginPath = QgsApplication.prefixPath()+"/share/qgis/python/plugins/pgversion"
myLocaleName = QLocale.system().name()
myLocale = myLocaleName[0:2]
if QFileInfo(userPluginPath).exists():
    pluginPath = userPluginPath
    localePath = userPluginPath+"/i18n/pgVersion_"+myLocale+".qm"
    
elif QFileInfo(systemPluginPath).exists():
    pluginPath = systemPluginPath
    localePath = systemPluginPath+"/i18n/pgVersion_"+myLocale+".qm"

if QFileInfo(localePath).exists():
    translator = QTranslator()
    translator.load(localePath)
      
    if qVersion() > '4.3.3':        
        QCoreApplication.installTranslator(translator)      
  
def classFactory(iface): 
  # load pgVersion class from file pgVersion
  from pgVersion import PgVersion 
  return PgVersion(iface)


