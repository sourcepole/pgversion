from qgis.gui import *
from qgis.core import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from pgVersionTools import PgVersionTools
import apicompat

import resources_rc,  sys

class ConflictWindow(QMainWindow):
    
  mergeCompleted = pyqtSignal()
    
  def __init__(self, layer,  type='conflict',  parent=None):
    QMainWindow.__init__(self)

    self.iface = parent.iface
    self.layer = layer
    self.parent = parent
    self.layer_list = parent.layer_list
    settings = QSettings()
    self.tools = PgVersionTools(self)    
          
    # Restore Window Settings
    settings = QSettings()
    try:
        self.restoreGeometry(pybytearray(settings.value("/pgVersion/geometry")))
        self.restoreState(pybytearray(settings.value("/pgVersion/windowState")))
    except:
        pass
    
    settings = QSettings()
    self.canvas = QgsMapCanvas()
    self.canvas.setCanvasColor(Qt.white)
    self.canvas.enableAntiAliasing(  settings.value( "/qgis/enable_anti_aliasing",True,  type=bool) ) 
    self.canvas.useImageToRender( settings.value( "/qgis/use_qimage_to_render", True,  type=bool) ) 
    action = pyint(settings.value( "/qgis/wheel_action", 0 ) )
    zoomFactor = pyint(settings.value( "/qgis/zoom_factor", 2) ) 
    self.canvas.setWheelAction( QgsMapCanvas.WheelAction(action), zoomFactor )

    QgsMapLayerRegistry.instance().addMapLayer(layer)
    self.canvas.setExtent(layer.extent())
    self.canvas.setLayerSet( [ QgsMapCanvasLayer(layer) ] )
    self.canvas.zoomToFullExtent()
    self.setCentralWidget(self.canvas)
    

    actionZoomIn = QAction(QIcon(":/plugins/pgversion/icons/ZoomIn.png"), pystring("Zoom in"), self)
    actionZoomOut = QAction(QIcon(":/plugins/pgversion/icons/ZoomOut.png"),pystring("Zoom out"), self)
    actionZoomFull = QAction(QIcon(":/plugins/pgversion/icons/ZoomFullExtent.png"),pystring("Fullextent"), self)
    actionPan = QAction(QIcon(":/plugins/pgversion/icons/Pan.png"),pystring("Pan"), self)

    actionZoomIn.setCheckable(True)
    actionZoomOut.setCheckable(True)
    actionPan.setCheckable(True)

    actionZoomIn.triggered.connect(self.zoomIn)
    actionZoomOut.triggered.connect(self.zoomOut)
    actionZoomFull.triggered.connect(self.zoomFull)
    actionPan.triggered.connect(self.pan)


    self.toolbar = self.addToolBar("Canvas actions")
    self.toolbar.addAction(actionPan)
    self.toolbar.addAction(actionZoomIn)
    self.toolbar.addAction(actionZoomOut)
    self.toolbar.addAction(actionZoomFull)

    
    self.dockWidget = QDockWidget()
    self.dockWidget.setWidget(QTableWidget())
    self.addDockWidget(Qt.BottomDockWidgetArea, self.dockWidget)
    self.tabView = self.dockWidget.widget()

    # create the map tools
    self.toolPan = QgsMapToolPan(self.canvas)
    self.toolPan.setAction(actionPan)
    self.toolZoomIn = QgsMapToolZoom(self.canvas, False) # false = in
    self.toolZoomIn.setAction(actionZoomIn)
    self.toolZoomOut = QgsMapToolZoom(self.canvas, True) # true = out
    self.toolZoomOut.setAction(actionZoomOut)

    self.pan()
    
    self.conflictLayerList = []

    if type=='conflict':
      self.cmbMerge = QComboBox()
      self.cmbMerge.addItems(self.tools.confRecords(self.layer))
    
      self.btnMerge = QPushButton()
      self.cmbMerge.currentIndexChanged.connect(self.toggleBtnMerge)
      self.btnMerge.setText(self.tr('solve conflict'))
            
      self.toolbar.addWidget(self.cmbMerge)
      self.toolbar.addWidget(self.btnMerge)
      self.manageConflicts()
      self.btnMerge.clicked.connect(self.runMerge) 

    self.tabView.itemSelectionChanged.connect(self.showConfObject)    
    self.rBand = QgsRubberBand(self.canvas, False)

  def toggleBtnMerge(self):
#      if not self.btnMerge.isEnabled():
#          self.btnMerge.setEnabled(False)
#      else:
#          self.btnMerge.setEnabled(True)
      return
      
  def toggleBtnCommit(self):
#      if not self.btnMerge.isEnabled():
#          self.btnMerge.setEnabled(False)
#      else:
#          self.btnMerge.setEnabled(True)
      return      

  def zoomIn(self):
    self.canvas.setMapTool(self.toolZoomIn)

  def zoomOut(self):
    self.canvas.setMapTool(self.toolZoomOut)

  def zoomFull(self):
      self.canvas.zoomToFullExtent()

  def pan(self):
    self.canvas.setMapTool(self.toolPan)
    

  def closeEvent(self, e):
      """ save window state """
#      settings = QSettings()
#      settings.setValue("/pgVersion/windowState", pybytearray(self.saveState()))
#      settings.setValue("/pgVersion/geometry", pybytearray(self.saveGeometry()))
      QgsMapLayerRegistry.instance().removeMapLayer(self.tools.conflictLayer(self.layer).id())
      self.close()
      

  def showDiffs(self):
      pass

  def showConfObject(self):

        myProject =  self.tabView.item(self.tabView.currentRow(), 0).text()
        myId =  self.tabView.item(self.tabView.currentRow(), 3).text()

        confLayer = self.tools.conflictLayer(self.layer)
        self.conflictLayerList.append(confLayer)
        
        self.rBand.reset()      
        self.rBand.setColor(QColor(0, 0, 255))
        self.rBand.setWidth(5)
        
        if confLayer.isValid():
            iter = confLayer.getFeatures()
            for feature in iter:
               geom = feature.geometry()
               attrs = feature.attributes()
               if str(attrs[0]) == myId and attrs[len(attrs)-5] == myProject:         
                 self.rBand.addGeometry(geom,  None)
    
        return

      
  def manageConflicts(self):
      QApplication.setOverrideCursor(Qt.WaitCursor)
      vLayer = self.tools.conflictLayer(self.layer) 
      if vLayer == None:
        return
      vLayerList = [vLayer,  self.layer]
      QgsMapLayerRegistry.instance().addMapLayers(vLayerList,  False)
      self.vLayerId = vLayer.id()
      self.canvas.setExtent(vLayer.extent())
      self.canvas.refresh()
      vLayer.triggerRepaint()
    
      tabData = self.tools.tableRecords(self.layer)
      
      if tabData <> None:
          self.tools.createGridView(self.tabView, tabData[0], tabData[1], 100, 10)
      else:
          QApplication.restoreOverrideCursor()
          self.mergeCompleted.emit()
          
      QApplication.restoreOverrideCursor()


  def runMerge(self): 
        QApplication.setOverrideCursor(Qt.WaitCursor)
        currentLayer = self.layer
        object = self.cmbMerge.currentText()
        
        if currentLayer == None:
            QMessageBox.information(None, self.tr('Notice'), self.tr('Please select a versioned layer for committing'))
            return
        else:
            myDb = self.tools.layerDB('Merge', currentLayer)
            mySchema = self.tools.layerSchema(currentLayer)
            myTable = self.tools.layerTable(currentLayer).replace("_version", "")     
      
        objectArray = object.split(" - ")
        if len(objectArray)==1:
            return
        elif 'Commit all' in objectArray[0]:
            projectName = objectArray[1].strip()
            sql = "select objectkey from versions.pgvscheck('%s.%s') \
             where myuser = '%s' or conflict_user = '%s' \
             order by objectkey" % (mySchema, myTable,  projectName,  projectName)
             
            result = myDb.read(sql)
            for i in range(len(result['OBJECTKEY'])):
                sql ="select versions.pgvsmerge('%s.%s',%s,'%s')" % (mySchema,  myTable,  result['OBJECTKEY'][i],  projectName)
                myDb.run(sql)
        else:    
            projectName = objectArray[1].strip()
            sql ="select versions.pgvsmerge('%s.%s',%s,'%s')" % (mySchema,  myTable,  objectArray[0],  projectName)
            myDb.run(sql)
            
        self.canvas.refresh()
        self.layer.triggerRepaint()
        self.cmbMerge.clear()
        QApplication.restoreOverrideCursor()
        
        if self.tools.confRecords(self.layer) == None:
            self.tabView.clear()
            self.tools.setModified(self.parent.layer_list)
            self.close()
            
        else:
            self.cmbMerge.addItems(self.tools.confRecords(self.layer))
            tabData = self.tools.tableRecords(self.layer)
            self.tools.createGridView(self.tabView, tabData[0], tabData[1], 100, 10)
        self.manageConflicts()


  def loadLayer(self, layer):
      provider = layer.dataProvider()
      uri = provider.dataSourceUri()    
      mySchema = self.tools.layerSchema(layer)
      myHost = self.tools.layerHost(layer)
      myDatabase = self.tools.layerDB(layer)
      myPassword = self.tools.layerPassword(layer)
      myPort = self.tools.layerPort(layer)
      myUsername = self.tools.layerUsername(layer)
      myGeometryColumn = self.tools.layerGeomCol(layer)

      myTable = myTable.replace("_version", "")     
      
      myUri = QgsDataSourceURI()
      myUri.setConnection(myHost, myPort, myDatabase, myUsername, myPassword)
      myUri.setDataSource(mySchema, myTable, myGeometryColumn)
      
      myLayer = QgsVectorLayer(myUri.uri(), "", "postgres")
      
      QgsMapLayerRegistry.instance().addMapLayer(myLayer, False)
#      self.canvas.setExtent(myLayer.extent())
      self.canvas.setLayerSet([QgsMapCanvasLayer(myLayer)])
      self.canvas.refresh()

    
