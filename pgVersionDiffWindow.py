from qgis.gui import *
from qgis.core import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from pgVersionTools import PgVersionTools
import resources_rc,  sys

class DiffWindow(QMainWindow):
  def __init__(self, myDb,  layer,  majorRevision,  minorRevision,  type='conflict'):
    QMainWindow.__init__(self)

    self.tools = PgVersionTools()    
    self.myDb = myDb
    self.layer = layer
    self.majorRevision = majorRevision
    self.minorRevision = minorRevision
    settings = QSettings()
          
    # Restore Window Settings
    settings = QSettings()
    self.restoreGeometry(settings.value("/pgVersion/geometry").toByteArray())
    self.restoreState(settings.value("/pgVersion/windowState").toByteArray())
    
    settings = QSettings()
    self.canvas = QgsMapCanvas()
    self.canvas.setCanvasColor(Qt.white)
    self.canvas.enableAntiAliasing( settings.value( "/qgis/enable_anti_aliasing", QVariant(False) ).toBool() )
    self.canvas.useImageToRender( settings.value( "/qgis/use_qimage_to_render", QVariant(False) ).toBool() )
    action = settings.value( "/qgis/wheel_action", QVariant(0) ).toInt()[0]
    zoomFactor = settings.value( "/qgis/zoom_factor", QVariant(2) ).toDouble()[0]
    self.canvas.setWheelAction( QgsMapCanvas.WheelAction(action), zoomFactor )

    self.setCentralWidget(self.canvas)

    actionZoomIn = QAction(QIcon(":/plugins/pgversion/icons/ZoomIn.png"), QString("Zoom in"), self)
    actionZoomOut = QAction(QIcon(":/plugins/pgversion/icons/ZoomOut.png"),QString("Zoom out"), self)
    actionZoomFull = QAction(QIcon(":/plugins/pgversion/icons/ZoomFullExtent.png"),QString("Fullextent"), self)
    actionPan = QAction(QIcon(":/plugins/pgversion/icons/Pan.png"),QString("Pan"), self)

    actionZoomIn.setCheckable(True)
    actionZoomOut.setCheckable(True)
    actionPan.setCheckable(True)

    self.connect(actionZoomIn, SIGNAL("triggered()"), self.zoomIn)
    self.connect(actionZoomOut, SIGNAL("triggered()"), self.zoomOut)
    self.connect(actionZoomFull, SIGNAL("triggered()"), self.zoomFull)
    self.connect(actionPan, SIGNAL("triggered()"), self.pan)


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
    self.loadLayer(self.layer)

    QObject.connect(self.tabView, SIGNAL("itemSelectionChanged()"),  self.showDiffObject)    
    self.rBand = QgsRubberBand(self.canvas, False)


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
      settings = QSettings()
      settings.setValue("/pgVersion/windowState", QVariant(self.saveState()))
      settings.setValue("/pgVersion/geometry", QVariant(self.saveGeometry()))
      QMainWindow.closeEvent(self, e)    

  def showDiffs(self):
      pass

  def showDiffObject(self):
      try:
         myAction =  self.tabView.item(self.tabView.currentRow(), 0).text()
         myRevision =  self.tabView.item(self.tabView.currentRow(), 1).text()
         myId =  self.tabView.item(self.tabView.currentRow(), 3).text()
      except: 
         QMessageBox.information(None, '', 'Fehler')
         return
      
      diffLayer = self.tools.diffLayer(self.layer,  self.majorRevision,  self.minorRevision)
      
#      try:
      self.rBand.reset()      
      provider = diffLayer.dataProvider()
      feat = QgsFeature()
      allAttrs = provider.attributeIndexes()
      provider.select(allAttrs)
    
      self.rBand.setColor(QColor(0, 0, 255))
      self.rBand.setWidth(5)
      
      while provider.nextFeature(feat):
         geom = feat.geometry()
         attrs = feat.attributeMap()
         
         if attrs[1].toString() == myId and attrs[3].toString() == myRevision:         
           self.rBand.addGeometry(geom,  None)
#      except:
#        QMessageBox.information(None, '', 'Fehler')
#        return
      
  def manageDiffs(self):
      vLayer = self.tools.diffLayer(self.theLayer,  self.majorRevision,  self.minorRevision) 
      if vLayer == None:
        return
        
      QgsMapLayerRegistry.instance().addMapLayer(vLayer,  False)
      self.vLayerId = vLayer.getLayerID()
      self.canvas.setLayerSet( []  )
      self.canvas.setLayerSet( [QgsMapCanvasLayer(vLayer,  True) , QgsMapCanvasLayer(self.layer,  True)  ]  )
      self.canvas.setExtent(vLayer.extent())
      self.canvas.refresh()
    
      tabData = self.tools.tableRecords(self.layer)

      self.tools.createGridView(self.tabView, tabData[0], tabData[1], 100, 10)



  def loadLayer(self, layer):
      provider = layer.dataProvider()
      uri = provider.dataSourceUri()    
      mySchema = QgsDataSourceURI(uri).schema()
      myHost = QgsDataSourceURI(uri).host()
      myDatabase = QgsDataSourceURI(uri).database()
      myPassword = QgsDataSourceURI(uri).password()
      myPort = QgsDataSourceURI(uri).port()
      myUsername = QgsDataSourceURI(uri).username()
      myGeometryColumn = QgsDataSourceURI(uri).geometryColumn()
      myKeyColumn = QgsDataSourceURI(uri).keyColumn()
      
      if len(mySchema) == 0:
          mySchema = 'public'
      myTable = QgsDataSourceURI(uri).table().remove("_version")     

      sql = "select mykey as "+myKeyColumn+", action, revision, systime, logmsg from versions.pgvsdiff('"+mySchema+"."+myTable+"', "+str(self.majorRevision)+", "+str(self.minorRevision)+")"
      result = self.myDb.read(sql)
      
# Load the LOG-Table for further usage
      layerSql = ''
      for i in range(len(result[str(myKeyColumn.toUpper())])):
        layerSql += "("+myKeyColumn+"="+result[str(myKeyColumn.toUpper())][i]+" and revision="+result['REVISION'][i]+" and systime="+result['SYSTIME'][i]+") or "
        
      layerSql = layerSql[:-4]
      QMessageBox.information(None, '', layerSql)

      logUri = QgsDataSourceURI()
      logUri.setConnection(QgsDataSourceURI(uri).host(), QgsDataSourceURI(uri).port(), QgsDataSourceURI(uri).database(),QgsDataSourceURI(uri).username() , QgsDataSourceURI(uri).password())
      logUri.setDataSource("versions", mySchema+"_"+myTable+"_version_log", QgsDataSourceURI(uri).geometryColumn(), layerSql)
      logUri.setKeyColumn(myKeyColumn)
      logLayer = QgsVectorLayer(logUri.uri(), mySchema+"_"+myTable+"_diff_"+str(self.majorRevision)+"-"+str(self.minorRevision), "postgres")
      logProvider = logLayer.dataProvider()
      QgsMapLayerRegistry.instance().addMapLayer(logLayer,  True)
      
      self.canvas.setExtent(logLayer.extent())
      self.canvas.setLayerSet([QgsMapCanvasLayer(logLayer)])
      self.canvas.refresh()
      
      tabData = self.tools.diffTableRecords(self.layer,  self.majorRevision,  self.minorRevision)
      self.tools.createGridView(self.tabView, tabData[0], tabData[1], 100, 10)      


  def showObjectTab(self, layer):
      try:
        myProject =  self.tabView.item(self.tabView.currentRow(), 0).text()
        myId =  self.tabView.item(self.tabView.currentRow(), 3).text()
      except: 
        return
      
      confLayer = self.tools.conflictLayer(layer)
      self.rBand.reset()      
      provider = confLayer.dataProvider()
      feat = QgsFeature()
      allAttrs = provider.attributeIndexes()
      provider.select(allAttrs)

      self.rBand.setColor(QColor(0, 0, 255))
      self.rBand.setWidth(5)
      
      while provider.nextFeature(feat):
         geom = feat.geometry()
         attrs = feat.attributeMap()
         
         if attrs[0].toString() == myId and attrs[len(attrs)-4].toString() == myProject:         
           self.rBand.addGeometry(geom,  None)
    
