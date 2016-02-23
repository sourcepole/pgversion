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
import resources_rc,  traceback,  string
# Import the code for the dialog

from forms.Ui_pgLoadVersion import PgVersionLoadDialog
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

    self.actionList =  [ self.actionInit,self.actionLoad, self.actionCommit, self.actionDiff, self.actionRevert, self.actionLogView, self.actionDrop, self.actionLogView,  self.actionHelp,  self.actionAbout]         
#    self.actionList =  [ self.actionInit,self.actionLoad,self.actionCommit,self.actionRevert, self.actionLogView, self.actionDrop, self.actionLogView,  self.actionHelp,  self.actionAbout]         

    self.toolBar.addAction(self.actionInit)
    self.toolBar.addAction(self.actionLoad)
    self.toolBar.addAction(self.actionCommit)
    self.toolBar.addAction(self.actionRevert)
    self.toolBar.addAction(self.actionDiff)
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

    self.LogViewDialog.diffLayer.connect(self.doDiff) 
    self.LogViewDialog.rollbackLayer.connect(self.doRollback) 
    self.LogViewDialog.checkoutLayer.connect(self.doCheckout) 


  def layersInit(self):
      canvas = self.iface.mapCanvas()
      layerList = canvas.layers()

      for l in layerList:

          if l.type() == QgsMapLayer.VectorLayer and l.providerType() == 'postgres':
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
    elif self.tools.hasVersion(currentLayer):
      QMessageBox.warning(None,   QCoreApplication.translate('PgVersion','Warning'),   QCoreApplication.translate('PgVersion','The selected layer is already under versioning!'))
      return
    else:
      mySchema = self.tools.layerSchema(currentLayer)
      myTable = self.tools.layerTable(currentLayer)
      myDb = self.tools.layerDB('doInit',currentLayer)
      if not self.tools.checkPGVSRevision(myDb):
        return

      if not self.tools.versionExists(currentLayer):
        answer = QMessageBox.question(None, '', QCoreApplication.translate('PgVersion','Do you want to create the version environment for the table {0}').format(mySchema+'.'+myTable), QCoreApplication.translate('PgVersion','Yes'), QCoreApplication.translate('PgVersion','No'))
        QApplication.setOverrideCursor(Qt.WaitCursor)
        sql = "select * from versions.pgvsinit('%s.%s')" % (mySchema,  myTable)
        result = myDb.runError(sql)
        if result == ' ':
          QMessageBox. information(None, 'Init', QCoreApplication.translate('PgVersion', 'Init was successful!\n\n\
Please set the user permissions for table {0} and reload it via Database -> PG Version!').format(myTable))

          QgsMapLayerRegistry.instance().removeMapLayer(currentLayer.id())          

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
      mySchema = self.tools.layerSchema(theLayer)
      myTable = self.tools.layerTable(theLayer).replace('_version', '')

      if not self.tools.hasVersion(theLayer):
          QMessageBox.warning(None,   QCoreApplication.translate('PgVersion','Warning'),   QCoreApplication.translate('PgVersion','Please select a versioned layer!'))
      else:
          if self.tools.isModified(theLayer):
              confRecords = self.tools.confRecords(theLayer)            
              if  confRecords == None:
              # show the dialog
                  self.dlgCommitMessage.show()
                  result = self.dlgCommitMessage.exec_()
    
                  if result == QDialog.Accepted:
                        QApplication.setOverrideCursor(Qt.WaitCursor)                    
                        sql = "select * from versions.pgvscommit('%s.%s','%s')" % (mySchema,  myTable,  self.dlgCommitMessage.textEdit.toPlainText())
                        myDB = self.tools.layerDB('commit',  theLayer)
                        myDB.run(sql)
                        myDB.close()
                        canvas.refresh()
                        self.iface.messageBar().pushMessage("Info", QCoreApplication.translate('PgVersion','Commit of your changes was successful'), level=QgsMessageBar.INFO, duration=3)            
                        self.tools.setModified(None,  True)
                        QApplication.restoreOverrideCursor()
              else:
                if self.w != None:
                    self.w = None
                self.w = ConflictWindow(self.iface,  theLayer,  'conflict',  self)
                self.w.mergeCompleted.connect(self.doCommit)
                self.w.show()
    
              self.tools.setModified(None,  True)
          else:
              self.iface.messageBar().pushMessage('INFO', QCoreApplication.translate('PgVersion','No layer changes for committing, everything is OK'), level=QgsMessageBar.INFO, duration=3)


  def doCheckout(self,  item):
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
        answer = QMessageBox.question(None, '', QCoreApplication.translate('PgVersion','Are you sure to checkout the layer to revision {0}?').format(revision), QCoreApplication.translate('PgVersion','Yes'),  QCoreApplication.translate('PgVersion','No'))
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
            myUri.setDataSource("", u"(%s\n)" % sql, geomCol, "", uniqueCol)

            layer = None
            layer = QgsVectorLayer(myUri.uri(), myTable+" (Revision "+revision+")", "postgres")         
            userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path()+"/python/plugins/pgversion"         

            QgsMapLayerRegistry.instance().addMapLayer(layer)
            QApplication.restoreOverrideCursor()
            self.iface.messageBar().pushMessage('INFO', QCoreApplication.translate('PgVersion','Checkout to revision {0} was successful!').format(revision), level=QgsMessageBar.INFO, duration=3)
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
       QMessageBox.warning(None,   QCoreApplication.translate('PgVersion','Warning'),   QCoreApplication.translate('PgVersion','Please select a versioned layer!'))
    else:
        if len(mySchema) == 1:
          mySchema = 'public'
    
        answer = QMessageBox.question(None, '', QCoreApplication.translate('PgVersion','are you sure to revert to the HEAD revision?'), QCoreApplication.translate('PgVersion','Yes'),  QCoreApplication.translate('PgVersion','No'))
    
        if answer == 0:
            sql = "select * from versions.pgvsrevert('"+mySchema+"."+myTable.replace('_version', '')+"')"
            result = myDb.read(sql)
    
            if len(result)>1:
                QMessageBox.information(None, '',result)
            else:
                self.iface.messageBar().pushMessage("Info", QCoreApplication.translate('PgVersion','All changes are set back to the HEAD revision: {0}').format(str(result["PGVSREVERT"][0])), level=QgsMessageBar.INFO, duration=3)            
            self.tools.setModified(None,  True)
        canvas.refresh()
        myDb.close()
    pass

  def doLogView(self):
        canvas = self.iface.mapCanvas()
        theLayer = self.iface.activeLayer()
        
        if not self.tools.hasVersion(theLayer):
            QMessageBox.warning(None,   QCoreApplication.translate('PgVersion','Warning'),   QCoreApplication.translate('PgVersion','Please select a versioned layer!'))
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
        QMessageBox.information(None, '', QCoreApplication.translate('PgVersion','Please select a versioned layer'))
        return    
      else:
        answer = QMessageBox.question(None, '', QCoreApplication.translate('PgVersion','Are you sure to checkout diffs to HEAD revision?'), QCoreApplication.translate('PgVersion','Yes'),  QCoreApplication.translate('PgVersion','No'))
        if answer == 0:

            QApplication.setOverrideCursor(Qt.WaitCursor)
            uniqueCol = self.tools.layerKeyCol(currentLayer)
            geomCol = self.tools.layerGeomCol(currentLayer)
            geometryType = self.tools.layerGeometryType(currentLayer)
            mySchema = self.tools.layerSchema(currentLayer)
            myTable = self.tools.layerTable(currentLayer)

            if len(mySchema) == 0:
                mySchema = 'public'

            sql = u"select * from %s.%s limit 0"  % (mySchema,  myTable)
            cols = myDb.cols(sql)
            myCols = ', '.join(cols)+', st_astext("'+geomCol+'")'
#            myCols = string.replace(', '.join(cols),'"'+geomCol+'"',  'st_astext("'+geomCol+'")')
#            QMessageBox.information(None, '',  myCols)
            

            sql = ("select row_number() OVER () AS rownum, * \
from (select *, 'delete'::varchar as action, head.head as revision \
from (select max(revision) as head from versions.{schema}_{table}_log) as head, \
((select v.{cols} \
from versions.pgvscheckout('{schema}.{origin}', (select max(revision) as head from versions.{schema}_{table}_log)) as c,  \
versions.{schema}_{table}_log as v \
where c.log_id = v.{uniqueCol}  \
and c.systime = v.systime \
except \
select v.{cols}  \
from {schema}.{table} as v)) as foo \
union \
select *, 'insert'::varchar as action, head.head as revision \
from (select max(revision) as head from versions.{schema}_{table}_log) as head, \
(select v.{cols} \
from {schema}.{table} as v \
except \
select v.{cols} \
from versions.pgvscheckout('{schema}.{origin}', (select max(revision) as head from versions.{schema}_{table}_log)) as c, \
versions.{schema}_{table}_log as v \
where c.log_id = v.{uniqueCol} and c.systime = v.systime) as foo1) as foo ").format(schema = mySchema,  table=myTable,  origin=myTable.replace('_version', ''), cols = myCols,  uniqueCol = uniqueCol )

#            QMessageBox.information(None, '', sql)
            myUri = QgsDataSourceURI(self.tools.layerUri(currentLayer))
            myUri.setDataSource("", u"(%s\n)" % sql, geomCol, "", "rownum")

            layer = QgsVectorLayer(myUri.uri(), myTable+" (Diff to HEAD Revision)", "postgres")         
            
            if not layer.isValid():
                self.iface.messageBar().pushMessage('WARNING', QCoreApplication.translate('PgVersion','No diffs to HEAD detected! Layer could not be loaded.'), level=QgsMessageBar.INFO, duration=3)

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
                self.iface.messageBar().pushMessage('INFO', QCoreApplication.translate('PgVersion','Diff to HEAD revision was successful!'), level=QgsMessageBar.INFO, duration=3)
                
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
        QMessageBox.information(None, '', QCoreApplication.translate('PgVersion','Please select a layer for versioning'))
        return    
      else:
        answer = QMessageBox.question(None, '', QCoreApplication.translate('PgVersion','are you sure to to drop pgvs from the table {0}?').format(mySchema+"."+myTable.replace('_version', '')), QCoreApplication.translate('PgVersion','Yes'),  QCoreApplication.translate('PgVersion','No'))

        if answer == 0:
            if self.tools.isModified(theLayer):
                QMessageBox.warning(None, QCoreApplication.translate('PgVersion','Warning'), \
                    QCoreApplication.translate('PgVersion','Layer %s has uncommited changes, please commit them or revert to HEAD revision' % (theLayer.name())))
            else:
                myDb = self.tools.layerDB('doDrop',theLayer)
                sql = "select versions.pgvsdrop('"+mySchema+"."+myTable.replace('_version', '')+"')"
                result = myDb.read(sql)                
                myDb.close()
                QgsMapLayerRegistry.instance().removeMapLayer(theLayer.id())      
                self.iface.messageBar().pushMessage('INFO', QCoreApplication.translate('PgVersion','Versioning for layer {0} dropped!').format(theLayer.name()), level=QgsMessageBar.INFO, duration=3)



  def doHelp(self):
      helpUrl = QUrl()
      helpUrl.setUrl('file://'+self.plugin_dir+'/docs/help.html')
      self.helpDialog.webView.load(helpUrl)
      self.helpDialog.show()
      pass  


  def doAbout(self):
      self.about = DlgAbout(self.plugin_dir)
      self.about.show()
