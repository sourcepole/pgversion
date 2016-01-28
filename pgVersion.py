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
from qgis.gui import *
from dbtools.dbTools import *
from forms.Ui_CommitMessage import CommitMessageDialog
from forms.Ui_diff import DiffDlg
from pgVersionConflictWindow import ConflictWindow

# Initialize Qt resources from file resources.py
import resources_rc,  traceback
# Import the code for the dialog

from forms.Ui_pgLoadVersion import PgVersionLoadDialog
from pgVersionInit import PgVersionInit
from forms.Ui_help import HelpDialog
from forms.Ui_LogView import LogView
from pgVersionTools import PgVersionTools
from about.doAbout import  DlgAbout

import apicompat


class PgVersion: 

  def __init__(self, iface):
    # Save reference to the QGIS interface
    self.iface = iface
    self.dlgCommitMessage = CommitMessageDialog()
    self.tools = PgVersionTools(self.iface)
    self.w = None
    self.vsCheck = None
      
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
    
    self.plugin_dir = pystring(QFileInfo(QgsApplication.qgisUserDbFilePath()).path()) + "/python/plugins/pgversion"      
    
    self.iface.projectRead.connect(self.layersInit)


  def initGui(self):  

    self.helpDialog = HelpDialog()
    self.LogViewDialog = LogView()
    
    self.toolBar = self.iface.addToolBar("PG Version")
    self.toolBar.setObjectName("PG Version")
    
    
    self.actionInit = QAction(QIcon(":/plugins/pgversion/icons/pgversion-init.png"), QCoreApplication.translate("PgVersion","Prepare Layer for Versioning"), self.iface.mainWindow())
    self.actionLoad = QAction(QIcon(":/plugins/pgversion/icons/pgversion-commit.png"), QCoreApplication.translate("PgVersion","Load Versioned Layer"), self.iface.mainWindow())
    self.actionCommit = QAction(QIcon(":/plugins/pgversion/icons/pgversion-load.png"), QCoreApplication.translate("PgVersion","Commit Changes"), self.iface.mainWindow())
    self.actionRevert = QAction(QIcon(":/plugins/pgversion/icons/pgversion-revert.png"), QCoreApplication.translate("PgVersion","Revert to HEAD Revision"), self.iface.mainWindow())
    self.actionLogView = QAction(QIcon(":/plugins/pgversion/icons/pgversion-logview.png"), QCoreApplication.translate("PgVersion","Show Logs"), self.iface.mainWindow())
    self.actionDiff = QAction(QIcon(":/plugins/pgversion/icons/pgversion-diff.png"), QCoreApplication.translate("PgVersion","Show Diffs"), self.iface.mainWindow())
#    self.actionCommit.setEnabled(False)
    self.actionDrop = QAction(QIcon(":/plugins/pgversion/icons/pgversion-drop.png"), QCoreApplication.translate("PgVersion","Drop Versioning from Layer"), self.iface.mainWindow())    
    self.actionHelp = QAction(QIcon(""), QCoreApplication.translate("PgVersion","Help"), self.iface.mainWindow())       
    self.actionAbout = QAction(QIcon(""), QCoreApplication.translate("PgVersion","About"), self.iface.mainWindow())       
 
#    self.actionList =  [ self.actionInit,self.actionLoad, self.actionCommit, self.actionDiff, self.actionRevert, self.actionLogView, self.actionDrop, self.actionLogView,  self.actionHelp]         
    self.actionList =  [ self.actionInit,self.actionLoad,self.actionCommit,self.actionRevert, self.actionLogView, self.actionDrop, self.actionLogView,  self.actionHelp,  self.actionAbout]         
 
    self.toolBar.addAction(self.actionInit)
    self.toolBar.addAction(self.actionLoad)
    self.toolBar.addAction(self.actionCommit)
    self.toolBar.addAction(self.actionRevert)
#    self.toolBar.addAction(self.actionDiff)
    self.toolBar.addAction(self.actionLogView)

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
    
    self.LogViewDialog.rollbackLayer.connect(self.doRollback) 
    self.LogViewDialog.checkoutLayer.connect(self.doCheckout) 


  def layersInit(self):
      canvas = self.iface.mapCanvas()
      layerList = canvas.layers()
      
      for l in layerList:
          
          if l.type() == QgsMapLayer.VectorLayer and l.providerType() == 'postgres':
              self.tools.setModified(l)
              l.editingStopped.connect(self.tools.setModified)
          

  def unload(self):
        # remove menubar
      try:
          for a in self.actionList:
            self.iface.removePluginDatabaseMenu("PG Version", a)
      except:
          del self.menuBar
      del self.toolBar



      
  def doInit(self):
    canvas = self.iface.mapCanvas()
    currentLayer = canvas.currentLayer()
    
    if currentLayer == None:
      QMessageBox.information(None, '', QCoreApplication.translate('PgVersion','Please select a layer for versioning'))
      return    
    else:
      provider = currentLayer.dataProvider()
      uri = provider.dataSourceUri()    
      myDb = self.tools.layerDB('doInit',currentLayer)
      if not self.tools.checkPGVSRevision(myDb):
        return
      mySchema = QgsDataSourceURI(uri).schema()
      
      if len(mySchema) == 0:
        mySchema = 'public'
      myTable = QgsDataSourceURI(uri).table()
      if not self.tools.versionExists(currentLayer):
        myExtent = canvas.extent()
        answer = QMessageBox.question(None, '', QCoreApplication.translate('PgVersion','Do you want to create the version environment for the table {0}').format(mySchema+'.'+myTable), QCoreApplication.translate('PgVersion','Yes'), QCoreApplication.translate('PgVersion','No'))
        
        QApplication.setOverrideCursor(Qt.WaitCursor)

        if answer == 0:
          sql = "select * from versions.pgvsinit('"+mySchema+"."+myTable+"')"
          result = myDb.runError(sql)              
          myDb.close()
          
          QMessageBox. information(None, 'Init', QCoreApplication.translate('PgVersion', 'Init was successful!\n\n\
Please set the user permissions for table {0} and reload it via Database -> PG Version!').format(myTable))
          
#          vUri = QgsDataSourceURI(provider.dataSourceUri() )
#          vUri.setDataSource(mySchema, myTable+'_version', QgsDataSourceURI(uri).geometryColumn())
#
#          vLayer = QgsVectorLayer(vUri.uri(),  myTable+'_version',  'postgres')
          QgsMapLayerRegistry.instance().removeMapLayer(currentLayer.id())          
#          QgsMapLayerRegistry.instance().addMapLayer(vLayer)
#          canvas.setExtent(myExtent)
#          canvas.zoomToPreviousExtent()

          QApplication.restoreOverrideCursor()
      else:
        self.iface.messageBar().pushMessage(QCoreApplication.translate('PgVersion','Init Error'), QCoreApplication.translate('PgVersion','Versioning envoronment for table {0} already exsists!').format(mySchema+"."+myTable), level=QgsMessageBar.CRITICAL, duration=3)


  def doLoad(self): 

    self.dlg = PgVersionLoadDialog(self.iface)
    self.dlg.show()

  def doRollback(self,  item):
      
      if item == None:
        QMessageBox.information(None, QCoreApplication.translate('PgVersion','Error'),  QCoreApplication.translate('PgVersion','Please select a valid revision'))
        return

      revision = item.text(0)

      canvas = self.iface.mapCanvas()
      currentLayer = canvas.currentLayer()
    
      if currentLayer == None:
        QMessageBox.information(None, '', QCoreApplication.translate('PgVersion','Please select a versioned layer'))
        return    
      else:
        answer = QMessageBox.question(None, '', QCoreApplication.translate('PgVersion','Are you sure to rollback to revision {0}?').format(revision), QCoreApplication.translate('PgVersion','Yes'),  QCoreApplication.translate('PgVersion','No'))
        if answer == 0:
            if self.tools.isModified(currentLayer):
                answer = QMessageBox.question(None, '', \
                QCoreApplication.translate('PgVersion','Layer {0} has modifications which will be lost after rollback! \
If you want to keep this modifications please commit them. \
Are you sure to rollback to revision {1}?').format(currentLayer.name(),  revision), QCoreApplication.translate('PgVersion','Yes'),  QCoreApplication.translate('PgVersion','No'))                                
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
            canvas.refresh()
            QApplication.restoreOverrideCursor()
            self.tools.setModified(currentLayer)
            self.iface.messageBar().pushMessage('INFO', QCoreApplication.translate('PgVersion','Rollback to revision {0} was successful!').format(revision), level=QgsMessageBar.INFO, duration=3)
            return

  def doCommit(self):
      canvas = self.iface.mapCanvas()
      if canvas.currentLayer() == None:
          self.iface.messageBar().pushMessage('Error', QCoreApplication.translate('PgVersion','Please select a versioned layer for committing'), level=QgsMessageBar.CRITICAL, duration=3)
          return
      
      canvas = self.iface.mapCanvas()
      theLayer = canvas.currentLayer()
      provider = theLayer.dataProvider()
      uri = provider.dataSourceUri()    
      myDb = self.tools.layerDB('commit',  theLayer)
      mySchema = QgsDataSourceURI(uri).schema()
      if len(mySchema) == 0:
         mySchema = 'public'
      myTable = QgsDataSourceURI(uri).table()    
      
#                if theLayer == None:
#            self.iface.messageBar().pushMessage('Error', QCoreApplication.translate('PgVersion','Please select a versioned layer for committing'), level=QgsMessageBar.ERROR, duration=3)
#            return

      if self.tools.isModified(theLayer):
          confRecords = self.tools.confRecords(theLayer)            
          if  confRecords == None:
          # show the dialog
              self.dlgCommitMessage.show()
              result = self.dlgCommitMessage.exec_()
    
              if result == QDialog.Accepted:
                    QApplication.setOverrideCursor(Qt.WaitCursor)                    
                    sql = "select * from versions.pgvscommit('"+mySchema+"."+myTable.replace('_version', '')+"','"+self.dlgCommitMessage.textEdit.toPlainText()+"')"
                    myDb.run(sql)
                    canvas.refresh()
                    self.iface.messageBar().pushMessage("Info", QCoreApplication.translate('PgVersion','Commit of your changes was successful'), level=QgsMessageBar.INFO, duration=3)            
                    self.tools.setModified()
                    QApplication.restoreOverrideCursor()
          else:
            if self.w != None:
                self.w = None
            self.w = ConflictWindow(self.iface,  theLayer,  'conflict',  self)
            self.w.mergeCompleted.connect(self.doCommit)
            self.w.show()
            
          myDb.close()
          self.tools.setModified()
      else:
          self.iface.messageBar().pushMessage('INFO', QCoreApplication.translate('PgVersion','No layer changes for committing, everything is OK'), level=QgsMessageBar.INFO, duration=3)

    
  def doCheckout(self,  item):
      revision = item.text(0)
      self.LogViewDialog.btnClose.setEnabled(False)
      QApplication.setOverrideCursor(Qt.WaitCursor)
      
      if revision == '-----':
        QMessageBox.information(None, 'Error',  'Please select a valid revision')
        return
        
      theLayer = self.iface.activeLayer()
      provider = theLayer.dataProvider()
      myCrs = provider.crs()
      uri = provider.dataSourceUri()    
      myDb = self.tools.layerDB('checkout', theLayer)
      mySchema = QgsDataSourceURI(uri).schema()
      myTable = QgsDataSourceURI(uri).table() 
      myKeyColumn = QgsDataSourceURI(uri).keyColumn()
      numFeat = provider.featureCount()
      
      if len(mySchema) == 0:
          mySchema = 'public'

      sql = "  select "+myKeyColumn+", revision, action \
           from versions."+mySchema+"_"+myTable+"_log \
           where revision > "+revision+" \
           order by revision desc "
      QMessageBox.information(None, '', sql)
      pass
      result = myDb.read(sql)
      
# Load the LOG-Table for further usage
      logUri = QgsDataSourceURI()
      logUri.setConnection(QgsDataSourceURI(uri).host(), QgsDataSourceURI(uri).port(), QgsDataSourceURI(uri).database(),QgsDataSourceURI(uri).username() , QgsDataSourceURI(uri).password())
      logUri.setDataSource("versions", mySchema+"_"+myTable+"_log", QgsDataSourceURI(uri).geometryColumn(), "revision > "+revision)
      logUri.setKeyColumn(QgsDataSourceURI(uri).keyColumn())
      logLayer = QgsVectorLayer(logUri.uri(), "dummy", "postgres")
      logProvider = logLayer.dataProvider()
         
      if theLayer.geometryType() == 0:
          myGeometry = "Point"
      elif theLayer.geometryType() == 1:
          myGeometry = "Linestring"
      elif theLayer.geometryType() == 2:
          myGeometry = "Polygon"
      
      revLayer = QgsVectorLayer(myGeometry, myTable.replace('_version', '')+"_rev_"+revision, "memory")
      revLayer.setCrs(myCrs)
      revProvider = revLayer.dataProvider()

      mLogLayer = QgsVectorLayer(myGeometry,  myTable.replace('_version', '')+"_rev_"+revision, "memory")
      mLogLayer.setCrs(myCrs)
      mLogProvider = mLogLayer.dataProvider()
      myFieldList = self.tools.getFieldList(logLayer)
      myFieldDefList = []

#      for (k,  attr) in myFieldList.iteritems():
#          myFieldDefList.append(attr)
          
      for attr in mLogProvider.fields():
          myFieldDefList.append(attr)          
    
      mLogProvider.addAttributes( myFieldDefList)
      
      feat = QgsFeature()
      allAttrs = logProvider.attributeIndexes()
#      logProvider.select(allAttrs)
      numFeat = numFeat + logProvider.featureCount()
      self.LogViewDialog.progressBar.setMinimum(0)
      self.LogViewDialog.progressBar.setRange(0, 100)
      self.LogViewDialog.progressBar.setValue(50)
      
      count = 1
      mIter = mLogLayer.getFeatures()
      for feat in mIter:
           mFeat = QgsFeature()
           mFeat.setGeometry(feat.geometry())
           mFeat.setAttributeMap(feat.attributeMap())
           mLogProvider.addFeatures( [mFeat] ) 
           self.LogViewDialog.progressBar.setValue(float(count)/float(numFeat)*100.0)
           count = count + 1
      
      
      mLogLayer.startEditing()
      numFields = mLogProvider.fields().count()
      for i in range(numFields-1):
        mLogLayer.deleteAttribute(numFields-i)

      mLogLayer.commitChanges()
      QgsMapLayerRegistry.instance().addMapLayer(revLayer)
      

#      myFieldList = self.tools.getFieldList(theLayer)
      
      myFieldDefList = []

      for attr in provider.fields():
          myFieldDefList.append(attr)
    
      revProvider.addAttributes( myFieldDefList)

      myFeatList = []

      feat = QgsFeature()
#      allAttrs = provider.attributeIndexes()
    
    # start data retreival: fetch geometry and all attributes for each feature
#      provider.select(allAttrs)
#      attrs = feat.attributeMap()
      iter = theLayer.getFeatures()
      for feat in iter:
         if str(feat.id()) not in result[str(myKeyColumn.upper())]:
             revFeat = QgsFeature()
             revFeat.setGeometry(feat.geometry())
             revFeat.setAttributes(feat.attributes())
             myFeatList.append(revFeat)
             revProvider.addFeatures( [revFeat] ) 
             self.LogViewDialog.progressBar.setValue(float(count)/float(numFeat)*100.0)
             count = count + 1



      for feat in mIter:
           attrs = feat.attributeMap()
           actionFieldId = len(attrs)-5
           if attrs[actionFieldId].toString() == 'delete':
             revFeat = QgsFeature()
             revFeat.setGeometry(feat.geometry())
             revFeat.setAttributes(feat.attributeMap())
             myFeatList.append(revFeat)
             revProvider.addFeatures( [revFeat] ) 
             self.LogViewDialog.progressBar.setValue(float(count)/float(numFeat)*100.0)
             count = count + 1

             
      revLayer.startEditing()
      revLayer.commitChanges()
      self.LogViewDialog.progressBar.setValue(100.0)      
      self.LogViewDialog.btnClose.setEnabled(True)
      QApplication.restoreOverrideCursor()
      QApplication.setOverrideCursor(Qt.ArrowCursor)        
      self.iface.mapCanvas().refresh()
      pass  

  
  def doRevert(self):
    try:
        canvas = self.iface.mapCanvas()
        theLayer = self.iface.activeLayer()
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()    
        myDb = self.tools.layerDB('revert', theLayer)
        mySchema = QgsDataSourceURI(uri).schema()
        myTable = QgsDataSourceURI(uri).table()    
    
        if len(mySchema) == 1:
          mySchema = 'public'
    except:
        self.iface.messageBar().pushMessage('Error', QCoreApplication.translate('PgVersion','Please select a versioned layer for reverting'), level=QgsMessageBar.CRITICAL, duration=3)
        return
    answer = QMessageBox.question(None, '', QCoreApplication.translate('PgVersion','are you sure to revert to the HEAD revision?'), QCoreApplication.translate('PgVersion','Yes'),  QCoreApplication.translate('PgVersion','No'))
    
    if answer == 0:
        sql = "select * from versions.pgvsrevert('"+mySchema+"."+myTable.replace('_version', '')+"')"
        result = myDb.read(sql)
                
        if len(result)>1:
            QMessageBox.information(None, '',result)
        else:
            self.iface.messageBar().pushMessage("Info", QCoreApplication.translate('PgVersion','All changes are set back to the HEAD revision: {0}').format(str(result["PGVSREVERT"][0])), level=QgsMessageBar.INFO, duration=3)            
        self.tools.setModified()
    canvas.refresh()
    myDb.close()
    pass
  
  def doLogView(self):
#    try:
        canvas = self.iface.mapCanvas()
        theLayer = self.iface.activeLayer()
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
        
#    except:
#        return
          
        
        pass
    
  def doDiff(self):
#      QMessageBox.information(None, 'Message', 'Diff is not implemented yet!')
#    try:
        canvas = self.iface.mapCanvas()
        theLayer = canvas.currentLayer()
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()    
#        myDb = self.tools.layerDB('commit',  theLayer)

        type='diff'
        self.diff = DiffDlg(self.iface)
        self.diff.show()
#    except:
#        QMessageBox.information(None, '', QCoreApplication.translate('PgVersion','Please select a layer to show the diffs to HEAD'))

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
        QMessageBox.information(None, '', QCoreApplication.translate('PgVersion','Please select a layer for versioning'))
        return    
      else:
        answer = QMessageBox.question(None, '', QCoreApplication.translate('PgVersion','are you sure to to drop pgvs from the table {0}?').format(mySchema+"."+myTable.replace('_version', '')), QCoreApplication.translate('PgVersion','Yes'),  QCoreApplication.translate('PgVersion','No'))

        if answer == 0:
            myDb = self.tools.layerDB('doDrop',theLayer)
            sql = "select * from versions.pgvsdrop('"+mySchema+"."+myTable.replace('_version', '')+"')"
            result = myDb.read(sql)
            myDb.close()
            QgsMapLayerRegistry.instance().removeMapLayer(theLayer.id())      
              

#      except:
#          QMessageBox.information(None, QCoreApplication.translate('PgVersion','Error'), QCoreApplication.translate('PgVersion','Please select a versionied layer for dropping'))
        else:
            QMessageBox.information(None, '',  'hallo')
        
        

  def doHelp(self):
      helpUrl = QUrl()
      helpUrl.setUrl('file://'+self.plugin_dir+'/docs/help.html')
      self.helpDialog.webView.load(helpUrl)
      self.helpDialog.show()
      pass  


    
  def doMessage(self):
      QMessageBox.information(None, '', 'Hallo')    
      
  
  def doAbout(self):
      self.about = DlgAbout(self.plugin_dir)
      self.about.show()
