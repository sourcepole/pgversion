# -*- coding: utf-8 -*-
"""
/***************************************************************************
Tools for Database Management
------------------------------------------------------------------------------------------------------------------
begin                 : 2010-07-31
copyright           : (C) 2010 by Dr. Horst Duester
email                 :  horst.duester@sourcepole.ch
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
from qgis.gui import *
from qgis.core import *
from forms.Ui_dbVersionCheck import DbVersionCheckDialog 
from datetime import datetime
from .dbtools.dbTools import *
import time,  sys,  os
import apicompat

class PgVersionTools(QObject):

# Konstruktor 
  def __init__(self,  parent):
      QObject.__init__(self,  parent)
      self.pgvsRevision = '2.1.3'
      self.parent = parent
      self.iface = parent.iface
      self.layer_list = parent.layer_list
      pass

  def layerRepaint(self):
        for layer in self.iface.mapCanvas().layers():
            layer.triggerRepaint()

  def layerDB(self, connectionName,  layer):

      myUri = QgsDataSourceURI(layer.source())

      # If username and password are not saved in the DB settings
      if myUri.username() == '':
          connectionInfo = myUri.connectionInfo()
          (success,  user,  password) =  QgsCredentials.instance().get(connectionInfo, None, None)
          QgsCredentials.instance().put( connectionInfo, user, password )
          myUri.setPassword(password)
          myUri.setUsername(user)

      try:
          myDb = DbObj(pluginname=connectionName,typ='pg',hostname=myUri.host(),port=myUri.port(),dbname=myUri.database(),username=myUri.username(), passwort=myUri.password())
          return myDb
      except:
          QMessageBox.information(None, self.tr('Error'), self.tr('No Database Connection Established.'))
          return None

      if not self.tools.checkPGVSRevision(myDb):
        return


  def setConfTable(self,  theLayer):
      provider = theLayer.dataProvider()
      uri = provider.dataSourceUri() 
      myDb = layerDB('setConfTable',  theLayer)
      mySchema = QgsDataSourceURI(uri).schema()
      myTable = QgsDataSourceURI(uri).table()
      if len(mySchema) == 0:
          mySchema = 'public'

      myTable = myTable.remove("_version")
      sql = "select versions.pgvscommit('"+mySchema+"."+myTable+"')"
      result = myDb.read(sql)
      myDb.close()

  def hasVersion(self,  theLayer):
        
        try:
            myLayerUri = QgsDataSourceURI(theLayer.source())
    
            myDb = self.layerDB('hasVersion',  theLayer)
    
            if myDb == None:
                return None
    
            if len(myLayerUri.schema()) == 1:
              schema = 'public'
            else:
              schema = myLayerUri.schema()
    
    
            sql = "select count(version_table_name) \
              from versions.version_tables import \
              where version_view_schema = '%s' and version_view_name = '%s'" % (schema,  myLayerUri.table())
              
            result = myDb.read(sql)
            myDb.close()
            try:
                if result['COUNT'][0] == '1':
                    return True
                else:
                    return False
            except:
                return False
        except:
            pass
      
  def isModified(self, myLayer=None):

        myLayerUri = QgsDataSourceURI(myLayer.source())

        myDb = self.layerDB('isModified',  myLayer)

        if myDb == None:
            return None

        if len(myLayerUri.schema()) == 0:
          schema = 'public'
        else:
          schema = myLayerUri.schema()


        sql = 'select count(project) \
          from versions.\"'+schema+'_'+myLayerUri.table()+'_log\" \
          where project = \''+myDb.dbUser()+'\' and not commit'

        result = myDb.read(sql)
        myDb.close()

        if int(result["COUNT"][0]) == 0:
          return False
        else:
          return True      


  def setModified(self, unsetModified=False):

    for i in range(len(self.layer_list)):
        map_layer = QgsMapLayerRegistry.instance().mapLayer(self.layer_list[i])
        if self.isModified(map_layer):
          if '(modified)' not in map_layer.name():
            map_layer.setLayerName(map_layer.name()+' (modified)')
        else:
          map_layer.setLayerName(map_layer.name().replace(' (modified)', ''))      
    
    
    
    # Return QgsVectorLayer from a layer name ( as string )
  def vectorLayerExists(self,   myName ):
     layermap = QgsMapLayerRegistry.instance().mapLayers()
     for name, layer in layermap.iteritems():
         if layer.type() == QgsMapLayer.VectorLayer and layer.name() == myName:
             if layer.isValid():
                 return True
             else:
                 return False



  def versionExists(self,layer):

      myDb = self.layerDB('versionExists',  layer)
      provider = layer.dataProvider()
      uri = provider.dataSourceUri()    

      try: 
          myTable = QgsDataSourceURI(uri).table()       
          mySchema = QgsDataSourceURI(uri).schema()

          if mySchema == '':
              mySchema = 'public'

          sql = ("select version_table_schema as schema, version_table_name as table \
           from versions.version_tables \
           where (version_view_schema = '{schema}' and version_view_name = '{table}') \
              or (version_table_schema = '{schema}' and version_table_name = '{table}')").format(schema=mySchema,  table=myTable)

          result  = myDb.read(sql)
          myDb.close()

          if len(result["SCHEMA"]) > 1:
            QMessageBox.information(None, '', self.tr('Table {schema}.{table} is already versionized').format(schema=mySchema,  table=myTable))
            return True
          else:
            return False
      except:
            QMessageBox.information(None, '', \
            self.tr('pgvs is not installed in your database. \n\n Please install the pgvs functions from file \n\n {createVersionPath}\n\n as mentioned in help') .format(createVersionPath=self.createVersionPath))
            return True

  def createGridView(self, tabView, tabData, headerText, colWidth, rowHeight):

    numCols = len(headerText)
    startVal = 0

    numRows = len(tabData[headerText[0].upper()])

    tabView.clear()
    tabView.setColumnCount(numCols)

    tabView.setRowCount(numRows)

    tabView.sortItems(2)
    col = startVal

    i = 0
    for text in headerText:
      headerItem = QTableWidgetItem()
      headerItem.setData(Qt.DisplayRole,pystring(text))
      tabView.setHorizontalHeaderItem(i,headerItem)
      i = i+1


    for i in range(0,numRows):

      col = startVal


      for text in headerText:
        myItem = QTableWidgetItem()
        myItem.setData(Qt.DisplayRole,pystring(tabData[text.upper()][i]))   
        tabView.setItem(i,col,myItem)
        myItem.setSelected(False)
        col = col + 1
    return

  def confRecords(self, theLayer):
      confRecords = []
      myDb = self.layerDB('commit',theLayer)
      mySchema = self.layerSchema(theLayer)
      myTable = self.layerTable(theLayer).replace('_version', '')

      sql =    "select version_table_schema as schema, version_table_name as table "
      sql += "from versions.version_tables "
      sql += "where version_view_schema = '"+mySchema+"' and version_view_name = '"+myTable+"'"
      result  = myDb.read(sql)

      if len(result["SCHEMA"]) == 0:
        QMessageBox.information(None, '', self.tr('Table {0} is not versionized').format(self.mySchema+'.'+self.myTable))
        return None
      else:
        sql = "select count(myuser) from versions.pgvscheck('%s.%s')" % (mySchema, myTable)
#        QMessageBox.information(None, '',  sql)
        check = myDb.read(sql)

      if check["COUNT"][0] <> "0":    
          sql = "select * from versions.pgvscheck('%s.%s') order by objectkey" % (mySchema, myTable)
#          QMessageBox.information(None, '',  sql)
          result = myDb.read(sql)
          myDb.close()        
          
          for i in range(len(result["CONFLICT_USER"])):
              confRecords.append("Commit all changes of - %s" % (result['MYUSER'][i]))
              confRecords.append("Commit all changes of - %s" % (result['CONFLICT_USER'][i]))
          
          confRecords = list(set(confRecords))

          for i in range(len(result["CONFLICT_USER"])):
              resString = result["OBJECTKEY"][i]+" - "+result["MYUSER"][i].strip()+" - "+datetime.strftime(datetime.fromtimestamp(float(result["MYSYSTIME"][i])/1000.0), "%x %H:%M:%S")
              confRecords.append(resString)
              resString = result["OBJECTKEY"][i]+" - "+result["CONFLICT_USER"][i].strip()+" - "+datetime.strftime(datetime.fromtimestamp(float(result["CONFLICT_SYSTIME"][i])/1000.0), "%x %H:%M:%S")
              confRecords.append(resString)
          confRecords.insert(0, self.tr('select Candidate'))          
          return confRecords
      else:
          return None

  def tableRecords(self,  theLayer):      
      myDb = self.layerDB('tableRecords',  theLayer)
      mySchema = self.layerSchema(theLayer)
      myTable = self.layerTable(theLayer)
      geomCol = self.layerGeomCol(theLayer)

      sql =   "select * from versions.version_tables \
          where version_view_schema = '%s' and version_view_name = '%s'" %(mySchema,  myTable)
      layer = myDb.read(sql)              
            
      sql = "select objectkey, myversion_log_id, conflict_version_log_id \
          from versions.pgvscheck('%s.%s')" % (mySchema,  myTable.replace("_version", ""))
                    
      result = myDb.read(sql)          
      timeListString = ''
      keyString = ''

      for i in range(len(result["OBJECTKEY"])):
          timeListString += result["MYVERSION_LOG_ID"][i]+","+result["CONFLICT_VERSION_LOG_ID"][i]+","
          keyString += result["OBJECTKEY"][i]+","

      timeListString = timeListString[0:len(timeListString)-1]
      keyString = keyString[0:len(keyString)-1]

      sql = 'select * from versions."%s_%s_log" \
           where version_log_id in (%s)\
           order by "%s"' % (mySchema,  myTable,  timeListString,  layer["VERSION_VIEW_PKEY"][0])
           

      result = myDb.read(sql)
      try:
          cols = myDb.cols(sql)
          cols.remove('action')
          cols.remove('systime')
          cols.remove('commit')
          cols.remove(geomCol)
    
          cols.insert(0, cols.pop(-1))
          cols.insert(0, cols.pop(-1))
          cols.insert(0, cols.pop(-1))
    
          resultArray = []
          resultArray.append(result)
          resultArray.append(cols)
          
          myDb.close()
          return resultArray
      except:
          return None

  def conflictLayer(self,  theLayer):
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()    
        myDb = self.layerDB('getConflictLayer',  theLayer)
        mySchema = QgsDataSourceURI(uri).schema()
        myTable = QgsDataSourceURI(uri).table()
        if len(mySchema) == 0:
          mySchema = 'public'

        sql =   "select * from versions.version_tables "
        sql += "where version_view_schema = '%s' and version_view_name = '%s'" % (mySchema,  myTable)
        layer = myDb.read(sql)    

        uri = QgsDataSourceURI()

#        # set host name, port, database name, username and password
        uri.setConnection(myDb.dbHost(), str(myDb.dbPort()), myDb.dbName(), myDb.dbUser(), myDb.dbPasswd())    

        sql = "select * from versions.pgvscheck('"+mySchema+"."+myTable.replace("_version", '')+"')"
        result = myDb.read(sql)
        myFilter = ''
        for i in range(len(result["OBJECTKEY"])):
            key = result["OBJECTKEY"][i]
            myproject = result["MYUSER"][i]
            mysystime = result["MYSYSTIME"][i]
            project = result["CONFLICT_USER"][i]
            systime = result["CONFLICT_SYSTIME"][i]
            myFilter += "("+layer["VERSION_VIEW_PKEY"][0]+"="+key+" and systime = "+systime+") or ("+layer["VERSION_VIEW_PKEY"][0]+"="+key+" and systime = "+mysystime+") or "

        if len(myFilter) > 0:
           myFilter = myFilter[0:len(myFilter)-4]  
           uri.setDataSource("versions", mySchema+"_"+myTable+"_log", layer["VERSION_VIEW_GEOMETRY_COLUMN"][0], myFilter,  layer["VERSION_VIEW_PKEY"][0])
           layerName = myTable+"_conflicts"
           vLayer = QgsVectorLayer(uri.uri(), layerName, "postgres")
           userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path()+"/python/plugins/pgversion/"  
           vLayer.setRendererV2(None)
           vLayer.loadNamedStyle(userPluginPath+"/legends/conflict.qml")   
           myDb.close()
           if vLayer.isValid():
               return vLayer    
           else:
               return None


  def createPolygon(self, geometry, geometryType):      

    self.mRubberBand.reset()
#    project = QgsProject.instance()

    color = QColor(255,0,0)
    self.mRubberBand.setColor(color)
    self.mRubberBand.setWidth(5)
    self.mRubberBand.show()

    g = QgsGeometry.fromWkt(geometry)

#    self.mRubberBand.setToGeometry(g,  None)

    if geometryType == "MULTIPOLYGON":
      for i in g.asMultiPolygon():
        index = 0
        for n in i:
          for k in n: 
            self.mRubberBand.addPoint(k,  False,  index)
          index = index + 1

#    if geometryType == "MULTILINESTRING":
#      for i in g.asPolyline():
#        for k in i: 
#          self.mRubberBand.addPoint(k)

    elif geometryType == "POLYGON":
      for i in g.asPolygon():
        for k in i: 
          self.mRubberBand.addPoint(k,  False)


    elif geometryType == "POINT":
      gBuffer = g.buffer(25, 100)
      for i in gBuffer.asPolygon():
        for k in i: 
          self.mRubberBand.addPoint(k)

    return 0                      


  def file_path(name, base_path=None):
    if not base_path:
      base_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_path, name)


# Check the revision of the DB-Functions
  def checkPGVSRevision(self,    myDb):          
        create_version_path = '%s/docs/create_pgversion_schema.sql' % (self.parent.plugin_path)
        upgrade_version_path = '%s/docs/upgrade_pgversion_schema.sql' % (self.parent.plugin_path)
        check = pystring(myDb.runError('select pgvsrevision from versions.pgvsrevision()'))
          
        if len(check) > 1:
            self.vsCheck = DbVersionCheckDialog(myDb,  '',  create_version_path,  'install')
            revisionMessage = self.tr("pgvs is not installed in the selected DB.\n\n\
Please contact your DB-administrator to install the DB-functions from the file:\n\n%s\n\n \
If you have appropriate DB permissions you can install the DB \
functions directly with click on Install pgvs." %(create_version_path))
            self.vsCheck.messageTextEdit.setText(revisionMessage)
            self.vsCheck.btnUpdate.setText('Install pgvs')
            self.vsCheck.show()
            return False
        else:  
            result = myDb.read('select pgvsrevision from versions.pgvsrevision()')
            
            my_major_revision = self.pgvsRevision.split('.')[1]
            my_minor_revision = self.pgvsRevision.split('.')[2]
            db_major_revision = result["PGVSREVISION"][0].split('.')[1]
            db_minor_revision = result["PGVSREVISION"][0].split('.')[2]
            
            for i in range(int(db_minor_revision), int(my_minor_revision)):
            
                if my_major_revision+"."+my_minor_revision != db_major_revision+"."+db_minor_revision:
                    upgrade_version_path = '%s/docs/upgrade_pgversion_schema-2.%s.%s.sql' % (self.parent.plugin_path,  db_major_revision,  i)
                    self.vsCheck = DbVersionCheckDialog(myDb,  result["PGVSREVISION"][0],  upgrade_version_path,  'upgrade')              
                    revisionMessage =self.tr('The Plugin expects pgvs revision %s but DB-functions revision %s are installed.\n\n \
    Please contact your DB-administrator to upgrade the DB-functions from the file:\n\n %s\n\n \
    If you have appropriate DB permissions you can update the DB directly with click on DB-Update.') % (self.pgvsRevision,  result["PGVSREVISION"][0],  upgrade_version_path)
                    
                    self.vsCheck.messageTextEdit.setText(revisionMessage)
                    self.vsCheck.btnUpdate.setText(self.tr('Upgrade pgvs to Revision %s.%s.%s') % (2,  my_major_revision,  i+1))
                    self.vsCheck.show()
                    return False       
        return True


#Get the Fieldnames of a Vector Layer
#Return: List of Fieldnames
  def getFieldNames(self, vLayer):
    myList = self.getFieldList(vLayer)

    fieldList = []    
    for (k,attr) in myList.iteritems():
       fieldList.append(unicode(attr.name(),'latin1'))

    return fieldList

#Get the List of Fields
#Return: QGsFieldMap
  def getFieldList(self, vlayer):
    fProvider = vlayer.dataProvider()

# retrieve every feature with its attributes
    myFields = fProvider.fields().toList()

    return myFields

  def layerGeomCol(self,  layer):
      return QgsDataSourceURI(self.layerUri(layer)).geometryColumn()
      
  def layerSchema(self,  layer):
      mySchema = QgsDataSourceURI(self.layerUri(layer)).schema()
      if len(mySchema) == 0:
          mySchema = 'public'
      return mySchema
      
  def layerTable(self,  layer):  
      return QgsDataSourceURI(self.layerUri(layer)).table()
      
  def layerName(self,  layer):  
      return QgsDataSourceURI(layer.name())

  def layerKeyCol(self,  layer):
      return QgsDataSourceURI(self.layerUri(layer)).keyColumn()
      
  def layerUri(self,  layer):
      provider = layer.dataProvider()
      return provider.dataSourceUri()
      
  def layerGeometryType(self,  layer):
      return layer.geometryType()      
      
  def layerHost(self,  layer):
      return QgsDataSourceURI(self.layerUri(layer)).host()
      
  def layerPassword(self,  layer):
      return QgsDataSourceURI(self.layerUri(layer)).password()
      
  def layerPort(self,  layer):
      return QgsDataSourceURI(self.layerUri(layer)).port()
      
  def layerUsername(self,  layer):
      return QgsDataSourceURI(self.layerUri(layer)).username()      
