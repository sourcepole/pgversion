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
from qgis.gui import *
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from .pgVersionTools import PgVersionTools

from . import resources_rc


class ConflictWindow(QMainWindow):

    def __init__(self, layer, type='conflict', parent=None):
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
            self.restoreGeometry(pybytearray(
                settings.value("/pgVersion/geometry")))
            self.restoreState(pybytearray(
                settings.value("/pgVersion/windowState")))
        except:
            pass

        settings = QSettings()
        self.canvas = QgsMapCanvas()
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(settings.value(
            "/qgis/enable_anti_aliasing", True, type=bool))
        action = settings.value("/qgis/wheel_action", 0)
        zoomFactor = settings.value("/qgis/zoom_factor", 2)

        QgsProject.instance().addMapLayer(layer)
        self.canvas.setExtent(layer.extent())
        self.canvas.setLayers([layer])
        self.canvas.zoomToFullExtent()
        self.setCentralWidget(self.canvas)

        actionZoomIn = QAction(QIcon(
            ":/plugins/pgversion/icons/ZoomIn.png"), "Zoom in", self)
        actionZoomOut = QAction(QIcon(
            ":/plugins/pgversion/icons/ZoomOut.png"), "Zoom out",
            self)
        actionZoomFull = QAction(QIcon(
            ":/plugins/pgversion/icons/ZoomFullExtent.png"), "Fullextent", self)
        actionPan = QAction(QIcon(":/plugins/pgversion/icons/Pan.png"), "Pan", self)

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
        self.toolZoomIn = QgsMapToolZoom(self.canvas, False)
        self.toolZoomIn.setAction(actionZoomIn)
        self.toolZoomOut = QgsMapToolZoom(self.canvas, True)
        self.toolZoomOut.setAction(actionZoomOut)

        self.pan()

        self.conflictLayerList = []

        if type is 'conflict':
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
        return

    def toggleBtnCommit(self):
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
        self.close()

    def showDiffs(self):
        pass

    def showConfObject(self):

        myProject = self.tabView.item(self.tabView.currentRow(), 0).text()
        myId = self.tabView.item(self.tabView.currentRow(), 3).text()

        confLayer = self.tools.conflictLayer(self.layer)
        self.conflictLayerList.append(confLayer)

        self.rBand.reset()
        self.rBand.setColor(QColor(0, 0, 255))
        self.rBand.setWidth(5)

        if confLayer != None:
            iter = confLayer.getFeatures()
            for feature in iter:
                geom = feature.geometry()
                attrs = feature.attributes()
                if str(attrs[0]) == myId and attrs[len(attrs) - 5] == myProject:
                    self.rBand.addGeometry(geom, None)

        return

    def manageConflicts(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        vLayer = self.tools.conflictLayer(self.layer)
        if vLayer is None:
            QApplication.restoreOverrideCursor()
            self.parent.doCommit()
            return
        vLayerList = [vLayer, self.layer]
        QgsProject.instance().addMapLayers(vLayerList, False)
        self.vLayerId = vLayer.id()
        self.canvas.setExtent(vLayer.extent())
        self.canvas.refresh()
        vLayer.triggerRepaint()

        tabData = self.tools.tableRecords(self.layer)
        
        if tabData is not None:
            self.tools.createGridView(
                self.tabView, tabData[0], tabData[1], 100, 10)
        else:
            self.tools.setModified([vLayer])
            QApplication.restoreOverrideCursor()
            self.parent.doCommit()

        QApplication.restoreOverrideCursor()

    def runMerge(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        currentLayer = self.layer
        object = self.cmbMerge.currentText()

        if currentLayer is None:
            QMessageBox.information(
                None, self.tr('Notice'),
                self.tr('Please select a versioned layer for committing'))
            return
        else:
            myDb = self.tools.layerDB('Merge', currentLayer)
            mySchema = self.tools.layerSchema(currentLayer)
            myTable = self.tools.layerTable(currentLayer).replace("_version", "")

        objectArray = object.split(" - ")
        if len(objectArray) is 1:
            self.parent.doCommit()
            return
        elif 'Commit all' in objectArray[0]:
            projectName = objectArray[1].strip()
            sql = """
                        select objectkey from versions.pgvscheck('%s.%s') 
                        where myuser = '%s' or conflict_user = '%s' 
                        order by objectkey""" % (
                mySchema, myTable, projectName, projectName)
            result,  error = myDb.read(sql)
            for i in range(len(result['OBJECTKEY'])):
                sql = "select versions.pgvsmerge('%s.%s',%s,'%s')" % (
                    mySchema, myTable, result['OBJECTKEY'][i], projectName)
                success,  error = myDb.run(sql)
        else:
            projectName = objectArray[1].strip()
            sql = "select versions.pgvsmerge('%s.%s',%s,'%s')" % (
                mySchema, myTable, objectArray[0], projectName)
            success,  error= myDb.run(sql)

        self.canvas.refresh()
        self.layer.triggerRepaint()
        self.cmbMerge.clear()
        QApplication.restoreOverrideCursor()
        if self.tools.confRecords(self.layer) is None:
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

        QgsProject.instance().addMapLayer(myLayer, False)
        self.canvas.setLayerSet([QgsMapCanvasLayer(myLayer)])
        self.canvas.refresh()
