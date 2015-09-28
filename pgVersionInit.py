# -*- coding: utf-8 -*-
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
"""
import sys
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog

class PgVersionInit: 

  def __init__(self,db, inTable):
    # Save reference to the QGIS interface
    self.inTable = inTable
    self.db = db

# Divide inTable String into schema and table    
    if self.inTable.find('.')==-1:
        schema = 'public'
        table = self.inTable
    else:
        tabListe = self.inTable.split('.')
        schema = tabListe[0]
        table = tabListe[1]
        
    versionView = schema+"."+table+"_version"
    versionLogTable = versionView+"_log"   
    
# Feststellen ob die Tabelle besteht
    if not self.db.exists('table',inTable):
      QMessageBox.information(None, "", "Table "+inTable+" does not exist!")
      return    
      
# Die grundlegenden Geometrieparameter des Ausgangslayers ermitteln
    query = "select f_geometry_column, coord_dimension, srid, type "
    query += "from geometry_columns "
    query += "where f_table_schema = '"+schema+"' "
    query += "  and f_table_name = '"+table+"'"

    result = self.db.read(query)
    
    geomCol = result["F_GEOMETRY_COLUMN"][0]
    geomDIM = result["COORD_DIMENSION"][0]
    geomSRID = result["SRID"][0]
    geomType = result["TYPE"][0]    
    
# Pruefen ob und welche Spalte der Primarykey der Tabelle ist 
    query = "select col.column_name "
    query += "from information_schema.table_constraints as key, "
    query += "     information_schema.key_column_usage as col "
    query += "where key.table_schema = '"+schema+"' "
    query += "  and key.table_name = '"+table+"' "
    query += "  and key.constraint_type='PRIMARY KEY' "
    query += "  and key.constraint_name = col.constraint_name "
    query += "  and key.table_catalog = col.table_catalog "
    query += "  and key.table_schema = col.table_schema "
    query += "  and key.table_name = col.table_name "	

    result = self.db.read(query)
    
    if len(result["COLUMN_NAME"])==0:
      QMessageBox.information(None, "", "No Primaray Key defined for "+schema+"."+table)
      return
      
    myPkey = result["COLUMN_NAME"][0]

# Feststellen ob die Tabelle bereits besteht
    if self.db.exists("table", inTable+"_version_log"):
       QMessageBox.information(None, "", "Table"+inTable+"_version_log already exists")
       return
