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
from PyQt4.QtWebKit import QWebView
from qgis.core import *
from qgis.gui import *
from dbtools.dbTools import *
from forms.Ui_CommitMessage import CommitMessageDialog
from forms.Ui_diff import DiffDlg
from pgVersionConflictWindow import ConflictWindow
    
# Initialize Qt resources from file resources.py
import resources_rc,  traceback,  string
# Import the code for the dialog

from forms.Ui_pgLoadVersion import PgVersionLoadDialog
from forms.Ui_help import HelpDialog
from forms.Ui_LogView import LogView
from pgVersionTools import PgVersionTools
from about.doAbout import  DlgAbout

import apicompat,  tempfile,  os


class PgVersion(QObject): 

  def __init__(self, iface):
    QObject.__init__(self)
    # Save reference to the QGIS interface
    self.iface = iface
    self.w = None
    self.vsCheck = None
    self.layer_list = []
    self.tools = PgVersionTools(self)

    #Initialise thetranslation environment    
    self.plugin_path = os.path.dirname(os.path.realpath(__file__))
    myLocaleName = QLocale.system().name()
    myLocale = myLocaleName[0:2]
    if QFileInfo(self.plugin_path).exists():
        localePath = self.plugin_path+"/i18n/pgVersion_"+myLocale+".qm"
    print localePath
    if QFileInfo(localePath).exists():
        self.translator = QTranslator()
        self.translator.load(localePath)
  
        if qVersion() > '4.3.3':        
            QCoreApplication.installTranslator(self.translator)  

#    self.iface.projectRead.connect(self.layers_init)
    self.iface.projectRead.connect(self.add_layer)
    
    QgsMapLayerRegistry.instance().layerRemoved.connect(self.remove_layer)
    QgsMapLayerRegistry.instance().layersAdded.connect(self.add_layer)
    


  def initGui(self):  

    self.helpDialog = HelpDialog()
    self.LogViewDialog = LogView(self)

    self.toolBar = self.iface.addToolBar("PG Version")
    self.toolBar.setObjectName("PG Version")


    self.actionInit = QAction(QIcon(":/plugins/pgversion/icons/pgversion-init.png"), self.tr("Prepare Layer for Versioning"), self.iface.mainWindow())
    self.actionLoad = QAction(QIcon(":/plugins/pgversion/icons/pgversion-commit.png"), self.tr("Load Versioned Layer"), self.iface.mainWindow())
    self.actionCommit = QAction(QIcon(":/plugins/pgversion/icons/pgversion-load.png"), self.tr("Commit Changes"), self.iface.mainWindow())
    self.actionRevert = QAction(QIcon(":/plugins/pgversion/icons/pgversion-revert.png"), self.tr("Revert to HEAD Revision"), self.iface.mainWindow())
    self.actionLogView = QAction(QIcon(":/plugins/pgversion/icons/pgversion-logview.png"), self.tr("Show Logs"), self.iface.mainWindow())
    self.actionDiff = QAction(QIcon(":/plugins/pgversion/icons/pgversion-diff.png"), self.tr("Show Diffs"), self.iface.mainWindow())
#    self.actionCommit.setEnabled(False)
    self.actionDrop = QAction(QIcon(":/plugins/pgversion/icons/pgversion-drop.png"), self.tr("Drop Versioning from Layer"), self.iface.mainWindow())    
    self.actionHelp = QAction(QIcon(""), self.tr("Help"), self.iface.mainWindow())       
    self.actionAbout = QAction(QIcon(""), self.tr("About"), self.iface.mainWindow())       
    self.actionDelete = QAction(QIcon(":/plugins/pgversion/icons/pgversion-drop.png"), self.tr("Bulk delete directly in the database"), self.iface.mainWindow())       
    self.actionDelete.setEnabled(False)
    

    self.actionList =  [ self.actionInit,self.actionLoad, self.actionCommit, self.actionDiff, self.actionRevert,  self.actionLogView, self.actionDrop, self.actionLogView,  self.actionDelete, self.actionHelp,  self.actionAbout]         
 

#    self.actionList =  [ self.actionInit,self.actionLoad,self.actionCommit,self.actionRevert, self.actionLogView, self.actionDrop, self.actionLogView,  self.actionHelp,  self.actionAbout]         

    self.toolBar.addAction(self.actionInit)
    self.toolBar.addAction(self.actionLoad)
    self.toolBar.addAction(self.actionCommit)
    self.toolBar.addAction(self.actionRevert)
    self.toolBar.addAction(self.actionDiff)
    self.toolBar.addAction(self.actionLogView)
    self.toolBar.addAction(self.actionDelete)


 # Add the Menubar into the new Database Main Menue starting with QGIS1.7
    try:
        for a in self.actionList:
           self.iface.addPluginToDatabaseMenu("PG Version", a)
    except AttributeError:
# For former QGIS Versions use the old Main Menue
       self.menu = QMenu()
       self.menu.setTitle( "PG Version" )  
       self.menu.addActions(self.actionList)    
       self.menuBar = self.iface.mainWindow().menuBar()
       self.menuBar.addMenu(self.menu)  

    # connect the action to the run method
    self.actionInit.triggered.connect(self.doInit) 
    self.actionLoad.triggered.connect(self.doLoad) 
    self.actionDiff.triggered.connect(self.doDiff)     
    self.actionCommit.triggered.connect(self.doCommit) 
    self.actionRevert.triggered.connect(self.doRevert) 
    self.actionLogView.triggered.connect(self.doLogView) 
    self.actionDrop.triggered.connect(self.doDrop) 
    self.actionHelp.triggered.connect(self.doHelp) 
    self.actionAbout.triggered.connect(self.doAbout) 
    self.actionDelete.triggered.connect(self.doDelete) 

    self.LogViewDialog.diffLayer.connect(self.doDiff) 
    self.LogViewDialog.rollbackLayer.connect(self.doRollback) 
    self.LogViewDialog.checkoutLayer.connect(self.doCheckout) 
    self.LogViewDialog.checkoutTag.connect(self.doCheckout) 
    
    for a in self.iface.digitizeToolBar().actions():
        if a.objectName() == 'mActionToggleEditing':
            a.triggered.connect(self.onSelectionChanged)
            
    self.iface.mapCanvas().selectionChanged.connect(self.onSelectionChanged)            

  def onSelectionChanged(self):
        current_layer = self.iface.mapCanvas().currentLayer()
        if current_layer.selectedFeatureCount() == 0:
            self.actionDelete.setEnabled(False)
        else:
            if self.tools.hasVersion(current_layer):
                print current_layer.isEditable()
                if current_layer.isEditable():
                    self.actionDelete.setEnabled(True) # true
                else:
                    self.actionDelete.setEnabled(False)
            else:
                self.actionDelete.setEnabled(False) # true
      
      
  def add_layer(self,  layer):
      
    for l in layer:
        if self.tools.hasVersion(l):
            if l.id not in self.layer_list:
                l.editingStopped.connect(self.tools.setModified)
                l.layerModified.connect(self.tools.setModified)
                self.layer_list.append(l.id())
                self.tools.setModified(l)
            
    self.layers_init()
    

  def remove_layer(self,  id):
        self.layer_list = filter(lambda a: a != id, self.layer_list)
        if len(self.layer_list) > 0:
#            self.layers_init()
            self.tools.setModified(map_layer)
      
  def layers_init(self):
      for i in range(len(self.layer_list)):
          map_layer = QgsMapLayerRegistry.instance().mapLayer(self.layer_list[i])
          
          if map_layer.type() == QgsMapLayer.VectorLayer and map_layer.providerType() == 'postgres':
              self.tools.setModified(map_layer)



  def unload(self):
        # remove menubar
      try:
          for a in self.actionList:
            self.iface.removePluginDatabaseMenu("PG Version", a)
      except:
          del self.menuBar
      del self.toolBar

  def doDelete(self):
      
        res = QMessageBox.question(
         None,
         self.tr("Question"),
         self.tr("Are you sure to delete all selected features. You cannot undo this action!"),
         QMessageBox.StandardButtons(
             QMessageBox.No |
             QMessageBox.Yes))
        
        if res == QMessageBox.Yes:
            QApplication.restoreOverrideCursor()
            canvas = self.iface.mapCanvas()
            currentLayer = canvas.currentLayer()      
            mySchema = self.tools.layerSchema(currentLayer)
            myTable = self.tools.layerTable(currentLayer)
            myPkey = QgsDataSourceURI(currentLayer.dataProvider().dataSourceUri()).keyColumn()
            myDb = self.tools.layerDB('doInit',currentLayer)        
            selectedFeatures = currentLayer.selectedFeatures()
            delete_list = "("
            
            if currentLayer.selectedFeatureCount() > 0:
                for feature in selectedFeatures:
                      delete_list += str(feature.attributes()[0])+", "
                
                delete_list = delete_list[:-2]
                delete_list += ")"
                sql = "delete from %s.%s where %s in %s" % (mySchema,  myTable,  myPkey,  delete_list)
                QApplication.setOverrideCursor(Qt.WaitCursor)
                myDb.run(sql)
                QApplication.restoreOverrideCursor()
                currentLayer.removeSelection()
                currentLayer.triggerRepaint()
                self.tools.setModified()
#                self.actionDelete.setEnabled(false)
        

  def doInit(self):
    canvas = self.iface.mapCanvas()
    currentLayer = canvas.currentLayer()

    if currentLayer == None:
      QMessageBox.information(None, '', self.tr('Please select a layer for versioning'))
      return    
    elif self.tools.hasVersion(currentLayer):
      QMessageBox.warning(None,   self.tr('Warning'),   self.tr('The selected layer is already under versioning!'))
      return
    else:
      mySchema = self.tools.layerSchema(currentLayer)
      myTable = self.tools.layerTable(currentLayer)
      myDb = self.tools.layerDB('doInit',currentLayer)
      if not self.tools.checkPGVSRevision(myDb):
        return

      if not self.tools.versionExists(currentLayer):
        answer = QMessageBox.question(None, '', self.tr('Do you want to create the version environment for the table {0}').format(mySchema+'.'+myTable), self.tr('Yes'), self.tr('No'))
        QApplication.setOverrideCursor(Qt.WaitCursor)
        sql = "select * from versions.pgvsinit('%s.%s')" % (mySchema,  myTable)
        result = myDb.runError(sql)
        if result == ' ':
          QMessageBox. information(None, 'Init', self.tr( 'Init was successful!\n\n\
Please set the user permissions for table {0} and reload it via Database -> PG Version!').format(myTable))

          QgsMapLayerRegistry.instance().removeMapLayer(currentLayer.id())          

          QApplication.restoreOverrideCursor()
      else:
        self.iface.messageBar().pushMessage(self.tr('Init Error'), self.tr('Versioning envoronment for table {0} already exsists!').format(mySchema+"."+myTable), level=QgsMessageBar.CRITICAL, duration=3)


  def doLoad(self): 

     self.dlg = PgVersionLoadDialog(self)
     self.dlg.show()

  def doRollback(self,  item):

      if item == None:
        QMessageBox.information(None, self.tr('Error'),  self.tr('Please select a valid revision'))
        return

      revision = item.text(0)

      canvas = self.iface.mapCanvas()
      currentLayer = canvas.currentLayer()

      if currentLayer == None:
        QMessageBox.information(None, '', self.tr('Please select a versioned layer'))
        return    
      else:
        answer = QMessageBox.question(None, '', self.tr('Are you sure to rollback to revision {0}?').format(revision), self.tr('Yes'),  self.tr('No'))
        if answer == 0:
            if self.tools.isModified(currentLayer):
                answer = QMessageBox.question(None, '', \
                self.tr('Layer {0} has modifications which will be lost after rollback! \
If you want to keep this modifications please commit them. \
Are you sure to rollback to revision {1}?').format(currentLayer.name(),  revision), self.tr('Yes'),  self.tr('No'))                                
                if answer == 1:
                    return

            QApplication.setOverrideCursor(Qt.WaitCursor)
            provider = currentLayer.dataProvider()
            uri = provider.dataSourceUri()    
            myDb = self.tools.layerDB('doRollback',currentLayer)
            if not self.tools.checkPGVSRevision(myDb):
                return
            mySchema = QgsDataSourceURI(uri).schema()

            if len(mySchema) == 0:
                mySchema = 'public'
            myTable = QgsDataSourceURI(uri).table()

            sql = "select * from versions.pgvsrollback('"+mySchema+"."+myTable.replace('_version', '')+"',"+revision+")"

            myDb.run(sql)
            myDb.close()
            self.LogViewDialog.close()
            currentLayer.triggerRepaint()
            QApplication.restoreOverrideCursor()
            self.tools.setModified()
            self.iface.messageBar().pushMessage('INFO', self.tr('Rollback to revision {0} was successful!').format(revision), level=QgsMessageBar.INFO, duration=3)
            return

  def doCommit(self):
      canvas = self.iface.mapCanvas()
      
      if canvas.currentLayer() == None:
          self.iface.messageBar().pushMessage('Error', self.tr('Please select a versioned layer for committing'), level=QgsMessageBar.CRITICAL, duration=3)
          return

      canvas = self.iface.mapCanvas()
      theLayer = canvas.currentLayer()
      mySchema = self.tools.layerSchema(theLayer)
      myTable = self.tools.layerTable(theLayer).replace('_version', '')

      if not self.tools.hasVersion(theLayer):
          QMessageBox.warning(None,   self.tr('Warning'),   self.tr('Please select a versioned layer!'))
      else:
          if self.tools.isModified(theLayer):
              confRecords = self.tools.confRecords(theLayer)            
              if  confRecords == None:
              # show the dialog
                  self.dlgCommitMessage = CommitMessageDialog()
                  self.dlgCommitMessage.show()
                  result = self.dlgCommitMessage.exec_()
    
                  if result == QDialog.Accepted:
                        QApplication.setOverrideCursor(Qt.WaitCursor)                    
                        sql = "select * from versions.pgvscommit('%s.%s','%s')" % (mySchema,  myTable,  self.dlgCommitMessage.textEdit.toPlainText())
                        myDB = self.tools.layerDB('commit',  theLayer)
                        myDB.run(sql)
                        myDB.close()
                        self.tools.layerRepaint()
                        self.iface.messageBar().pushMessage("Info", self.tr('Commit of your changes was successful'), level=QgsMessageBar.INFO, duration=3)            
                        self.tools.setModified()
                        QApplication.restoreOverrideCursor()
              else:
                if self.w != None:
                    self.w = None
                self.w = ConflictWindow(self.iface,  theLayer,  'conflict',  self)
                self.w.mergeCompleted.connect(self.doCommit)
                self.w.show()
    
              self.tools.setModified()
          else:
              self.iface.messageBar().pushMessage('INFO', self.tr('No layer changes for committing, everything is OK'), level=QgsMessageBar.INFO, duration=3)


  def doCheckout(self,  revision,  tag=None):
      print "Revision: %s" % (revision)
      if revision == None:
        QMessageBox.information(None, self.tr('Error'),  self.tr('Please select a valid revision'))
        return

#      revision = item.text(0)

      canvas = self.iface.mapCanvas()
      currentLayer = canvas.currentLayer()


      if currentLayer == None:
        QMessageBox.information(None, '', self.tr('Please select a versioned layer'))
        return    
      else:
        answer = QMessageBox.question(None, '', self.tr('Are you sure to checkout the layer to revision {0}?').format(revision), self.tr('Yes'),  self.tr('No'))
        if answer == 0:

            QApplication.setOverrideCursor(Qt.WaitCursor)
            provider = currentLayer.dataProvider()
            uri = provider.dataSourceUri()    
            uniqueCol = QgsDataSourceURI(uri).keyColumn()
            geomCol = QgsDataSourceURI(uri).geometryColumn()
            geometryType = currentLayer.geometryType()

            mySchema = QgsDataSourceURI(uri).schema()
            myTable = QgsDataSourceURI(uri).table()

            if len(mySchema) == 0:
                mySchema = 'public'


            sql = "select v.* \
            from versions.pgvscheckout('"+mySchema+"."+myTable.replace('_version', '')+"', "+revision+") as c,  \
                 versions."+mySchema+"_"+myTable+"_log as v \
            where c.log_id = v."+uniqueCol+"  \
                         and c.systime = v.systime "
            
            myUri = QgsDataSourceURI(uri)
            myUri.setDataSource("", u"(%s\n)" % (sql), geomCol, "", uniqueCol)

            layer = None
            
            if tag:
                table_ext = " (Tag: %s)" % tag
            else:
                table_ext = " (Revision: %s)" % revision
                
            layer = QgsVectorLayer(myUri.uri(), myTable+table_ext, "postgres")         

            QgsMapLayerRegistry.instance().addMapLayer(layer)
            QApplication.restoreOverrideCursor()
            if layer.isValid():
                self.iface.messageBar().pushMessage('INFO', self.tr('Checkout to revision {0} was successful!').format(revision), level=QgsMessageBar.INFO, duration=3)
                layer.triggerRepaint()
            else:
                self.iface.messageBar().pushMessage('INFO', self.tr('Something went wrong during checkout to revision {0}!').format(revision), level=QgsMessageBar.INFO, duration=3)
            self.LogViewDialog.close()            
            return


  def doRevert(self):
    canvas = self.iface.mapCanvas()
    theLayer = self.iface.activeLayer()
    provider = theLayer.dataProvider()
    uri = provider.dataSourceUri()    
    myDb = self.tools.layerDB('revert', theLayer)
    mySchema = QgsDataSourceURI(uri).schema()
    myTable = QgsDataSourceURI(uri).table()    
    
    if not self.tools.hasVersion(theLayer):
       QMessageBox.warning(None,   self.tr('Warning'),   self.tr('Please select a versioned layer!'))
    else:
        if len(mySchema) == 1:
          mySchema = 'public'
    
        answer = QMessageBox.question(None, '', self.tr('are you sure to revert to the HEAD revision?'), self.tr('Yes'),  self.tr('No'))
    
        if answer == 0:
            sql = "select * from versions.pgvsrevert('"+mySchema+"."+myTable.replace('_version', '')+"')"
            result = myDb.read(sql)
    
            if len(result)>1:
                QMessageBox.information(None, '',result)
            else:
                self.iface.messageBar().pushMessage("Info", self.tr('All changes are set back to the HEAD revision: {0}').format(str(result["PGVSREVERT"][0])), level=QgsMessageBar.INFO, duration=3)            
                
        self.tools.setModified()
        theLayer.triggerRepaint()
        myDb.close()
    pass

  def doLogView(self):
        canvas = self.iface.mapCanvas()
        theLayer = self.iface.activeLayer()

        if theLayer <> None:
            if not self.tools.hasVersion(theLayer):
                QMessageBox.warning(None,   self.tr('Warning'),   self.tr('Please select a versioned layer!'))
            else:
                provider = theLayer.dataProvider()
                uri = provider.dataSourceUri()    
                myDb = self.tools.layerDB('logview', theLayer)
                mySchema = QgsDataSourceURI(uri).schema()
                myTable = QgsDataSourceURI(uri).table()
        
                if len(mySchema) == 0:
                   mySchema = 'public'
        
                sql = "select * from versions.pgvslogview('"+mySchema+"."+myTable.replace('_version', '')+"') order by revision desc"
                result = myDb.read(sql)
        
                logHTML = "<html><head></head><body><Table>"
                
                self.LogViewDialog.setLayer(theLayer)
                self.LogViewDialog.createTagList()
                self.LogViewDialog.treeWidget.clear()
        
                itemList = []
        
                for i in range(len(result["PROJECT"])):
                    myItem = QTreeWidgetItem()
                    myItem.setText(0, result["REVISION"][i])
                    myItem.setText(1, result["DATUM"][i])
                    myItem.setText(2, result["PROJECT"][i])
                    myItem.setText(3, result["LOGMSG"][i])
                    itemList.append(myItem)
        
                self.LogViewDialog.treeWidget.addTopLevelItems(itemList)
        
                self.LogViewDialog.show()        
                myDb.close()
                canvas.refresh()

        if not self.tools.hasVersion(theLayer):
            QMessageBox.warning(None,   self.tr('Warning'),   self.tr('Please select a versioned layer!'))
        else:
            provider = theLayer.dataProvider()
            uri = provider.dataSourceUri()    
            myDb = self.tools.layerDB('logview', theLayer)
            mySchema = QgsDataSourceURI(uri).schema()
            myTable = QgsDataSourceURI(uri).table()
    
            if len(mySchema) == 0:
               mySchema = 'public'
    
            sql = "select * from versions.pgvslogview('"+mySchema+"."+myTable.replace('_version', '')+"') order by revision desc"
            result = myDb.read(sql)
    
            logHTML = "<html><head></head><body><Table>"
            
            self.LogViewDialog.setLayer(theLayer)
            self.LogViewDialog.createTagList()
            self.LogViewDialog.treeWidget.clear()
    
            itemList = []
    
            for i in range(len(result["PROJECT"])):
                myItem = QTreeWidgetItem()
                myItem.setText(0, result["REVISION"][i])
                myItem.setText(1, result["DATUM"][i])
                myItem.setText(2, result["PROJECT"][i])
                myItem.setText(3, result["LOGMSG"][i])
                itemList.append(myItem)
    
            self.LogViewDialog.treeWidget.addTopLevelItems(itemList)
    
            self.LogViewDialog.show()        
            myDb.close()
            canvas.refresh()

        pass

  def doDiff(self):

      canvas = self.iface.mapCanvas()
      currentLayer = canvas.currentLayer()

      myDb = self.tools.layerDB('logview', currentLayer)

      if currentLayer == None:
        QMessageBox.information(None, '', self.tr('Please select a versioned layer'))
        return    
      else:
#        answer = QMessageBox.question(None, '', self.tr('Are you sure to checkout diffs to HEAD revision?'), self.tr('Yes'),  self.tr('No'))
        answer = 0
        if answer == 0:

            QApplication.setOverrideCursor(Qt.WaitCursor)
            uniqueCol = self.tools.layerKeyCol(currentLayer)
            geomCol = self.tools.layerGeomCol(currentLayer)
            geometryType = self.tools.layerGeometryType(currentLayer)
            mySchema = self.tools.layerSchema(currentLayer)
            myTable = self.tools.layerTable(currentLayer)

            if len(mySchema) == 0:
                mySchema = 'public'

            sql = u"select * from \"%s\".\"%s\" limit 0"  % (mySchema,  myTable)
            cols = myDb.cols(sql)
            myCols = ', '.join(cols)+', st_asewkb("'+geomCol+'")'
            
            extent = self.iface.mapCanvas().extent().toString().replace(':',',')
            authority,  crs = currentLayer.crs().authid().split(':')
            geo_idx = '%s && ST_MakeEnvelope(%s,%s)' %  (geomCol,  extent,  crs)

            sql = ("with \
head as (select max(revision) as head from versions.\"{schema}_{table}_log\"), \
checkout as (select v.{cols} \
from versions.pgvscheckout('{schema}.{origin}', (select * from head)) as c, versions.\"{schema}_{table}_log\" as v \
where {geo_idx} \
and c.log_id = v.{uniqueCol}  \
and c.systime = v.systime), \
\
version as (select v.{cols}  \
from \"{schema}\".\"{table}\" as v \
where {geo_idx}) \
\
select row_number() OVER () AS rownum, *  \
from (select *, 'delete'::varchar as action, head as revision from head, ( \
(select * from checkout \
except \
select * from version) \
) as foo \
union all \
select *, 'insert'::varchar as action, head.head as revision \
from head, ( \
select * from version \
except \
select * from checkout) as foo1 \
) as foo ").format(schema = mySchema,  table=myTable,  origin=myTable.replace('_version', ''), cols = myCols,  uniqueCol = uniqueCol,  geo_idx = geo_idx )
            
            myUri = QgsDataSourceURI(self.tools.layerUri(currentLayer))
            myUri.setDataSource("", u"(%s\n)" % sql, geomCol, "", "rownum")
            layer = QgsVectorLayer(myUri.uri(), myTable+" (Diff to HEAD Revision)", "postgres")       
            
#            defult_tmp_dir = tempfile._get_default_tempdir()
#            temp_name = defult_tmp_dir+"/"+next(tempfile._get_candidate_names())+".shp"
#            
#            QgsVectorFileWriter.writeAsVectorFormat(QgsVectorLayer(myUri.uri(), myTable+" (Diff to HEAD Revision)", "postgres") , temp_name, "utf-8", None, "ESRI Shapefile")  
#            layer_ = QgsVectorLayer(temp_name,  myTable+" (Diff to HEAD Revision)",  "ogr")
#            
            
            if not layer.isValid():
                self.iface.messageBar().pushMessage('WARNING', self.tr('No diffs to HEAD detected! Layer could not be loaded.'), level=QgsMessageBar.INFO, duration=3)

            else:                
                userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path()+"/python/plugins/pgversion"  
                layer.setRendererV2(None)
    
                if geometryType == 0:
                    layer.loadNamedStyle(userPluginPath+"/legends/diff_point.qml")             
                elif geometryType == 1:
                    layer.loadNamedStyle(userPluginPath+"/legends/diff_linestring.qml")             
                elif geometryType == 2:
                    layer.loadNamedStyle(userPluginPath+"/legends/diff_polygon.qml")             
    
                QgsMapLayerRegistry.instance().addMapLayer(layer)
                self.iface.messageBar().pushMessage('INFO', self.tr('Diff to HEAD revision was successful!'), level=QgsMessageBar.INFO, duration=3)
                
            QApplication.restoreOverrideCursor()
            self.LogViewDialog.close()            
            return


  def doDrop(self): 

#      try:
      theLayer = self.iface.activeLayer()
      provider = theLayer.dataProvider()
      uri = provider.dataSourceUri()    
      mySchema = QgsDataSourceURI(uri).schema()
      if len(mySchema) == 0:
        mySchema = 'public'
      myTable = QgsDataSourceURI(uri).table()    

      if theLayer == None:
        QMessageBox.information(None, '', self.tr('Please select a layer for versioning'))
        return    
      else:
        answer = QMessageBox.question(None, '', self.tr('are you sure to to drop pgvs from the table {0}?').format(mySchema+"."+myTable.replace('_version', '')), self.tr('Yes'),  self.tr('No'))

        if answer == 0:
            if self.tools.isModified(theLayer):
                QMessageBox.warning(None, self.tr('Warning'), \
                    self.tr('Layer %s has uncommited changes, please commit them or revert to HEAD revision' % (theLayer.name())))
            else:
                myDb = self.tools.layerDB('doDrop',theLayer)
                sql = "select versions.pgvsdrop('"+mySchema+"."+myTable.replace('_version', '')+"')"
                result = myDb.read(sql)                
                myDb.close()

                layer_name = theLayer.name()
                QgsMapLayerRegistry.instance().removeMapLayer(theLayer.id())      
                self.iface.messageBar().pushMessage('INFO', self.tr('Versioning for layer {0} dropped!').format(layer_name), level=QgsMessageBar.INFO, duration=3)
  

  def doHelp(self):
      helpUrl = QUrl()
      helpUrl.setUrl('file://'+self.plugin_path+'/docs/help.html')
      self.helpDialog.webView.load(helpUrl)
      self.helpDialog.show()
      pass  


  def doAbout(self):
      self.about = DlgAbout(self.plugin_path)
      self.about.show()
      
      
      
