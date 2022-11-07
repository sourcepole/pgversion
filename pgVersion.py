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
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *
from qgis.gui import *
from .dbtools.dbtools import *
from .forms.CommitMessage import CommitMessageDialog
from .pgVersionConflictWindow import ConflictWindow

from .forms.pgLoadVersion import PgVersionLoadDialog
from .forms.help import HelpDialog
from .forms.LogView import LogView
from .pgVersionTools import PgVersionTools
from .about.doAbout import DlgAbout
import os


class PgVersion(QObject):

    def __init__(self, iface):
        QObject.__init__(self)
        # Save reference to the QGIS interface
        self.iface = iface
        self.w = None
        self.vsCheck = None
        self.layer_list = []
        self.tools = PgVersionTools(self)

        # Initialise thetranslation environment
        self.plugin_path = os.path.dirname(__file__)
        self.locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_path,
            'i18n',
            'pgVersion_{}.qm'.format(self.locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def initGui(self):

        self.helpDialog = HelpDialog()
        self.LogViewDialog = LogView(self)

        self.toolBar = self.iface.addToolBar("PG Version")
        self.toolBar.setObjectName("PG Version")

        self.actionInit = QAction(
            QIcon(":/plugins/pgversion/icons/pgversion-init.png"),
            self.tr("Prepare Layer for Versioning"),
            self.iface.mainWindow())
        self.actionLoad = QAction(
            QIcon(":/plugins/pgversion/icons/pgversion-commit.png"),
            self.tr("Load Versioned Layer"), self.iface.mainWindow())
        self.actionCommit = QAction(
            QIcon(":/plugins/pgversion/icons/pgversion-load.png"),
            self.tr("Commit Changes"), self.iface.mainWindow())
        self.actionRevert = QAction(
            QIcon(":/plugins/pgversion/icons/pgversion-revert.png"),
            self.tr("Revert to HEAD Revision"), self.iface.mainWindow())
        self.actionLogView = QAction(
            QIcon(":/plugins/pgversion/icons/pgversion-logview.png"),
            self.tr("Show Logs"), self.iface.mainWindow())
        self.actionDiff = QAction(
            QIcon(":/plugins/pgversion/icons/pgversion-diff.png"),
            self.tr("Show Diffs"), self.iface.mainWindow())
        self.actionDrop = QAction(
            QIcon(":/plugins/pgversion/icons/pgversion-drop.png"),
            self.tr("Drop Versioning from Layer"), self.iface.mainWindow())
        self.actionHelp = QAction(
            QIcon(":/plugins/pgversion/icons/pgversion-help.png"), 
            self.tr("Help"),
            self.iface.mainWindow())
        self.actionAbout = QAction(QIcon(""), self.tr("About"),
                                   self.iface.mainWindow())
        self.actionDelete = QAction(
            QIcon(":/plugins/pgversion/icons/pgversion-drop.png"),
            self.tr("Bulk delete directly in the database"),
            self.iface.mainWindow())
            
        self.actionDelete.setEnabled(False)
        self.set_actions(False)
        
        self.actionList = [self.actionInit, self.actionLoad, self.actionCommit,
                           self.actionDiff, self.actionRevert,
                           self.actionLogView, self.actionDrop,
                           self.actionLogView, self.actionDelete,
                           self.actionHelp, self.actionAbout]

        self.toolBar.addAction(self.actionInit)
        self.toolBar.addAction(self.actionLoad)
        self.toolBar.addAction(self.actionCommit)
        self.toolBar.addAction(self.actionRevert)
        self.toolBar.addAction(self.actionDiff)
        self.toolBar.addAction(self.actionLogView)
        self.toolBar.addAction(self.actionDelete)
        self.toolBar.addAction(self.actionHelp)

        try:
            for a in self.actionList:
                self.iface.addPluginToDatabaseMenu("PG Version", a)
        except AttributeError:
            self.menu = QMenu()
            self.menu.setTitle("PG Version")
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
                a.triggered.connect(self.SelectionChanged)

        self.iface.mapCanvas().selectionChanged.connect(self.SelectionChanged)
        self.iface.currentLayerChanged.connect(self.layer_changed)
        QgsProject().instance().layerWasAdded.connect(self.add_layer)
        QgsProject().instance().layerWillBeRemoved.connect(
            self.remove_layer)

    def layer_changed(self):
        if self.tools.hasVersion(self.iface.activeLayer()):
            self.set_actions(True)
        else:
            self.set_actions(False)

    def SelectionChanged(self):
        current_layer = self.iface.activeLayer()
        if current_layer is not None:
            if (current_layer.type() == QgsMapLayer.VectorLayer) and current_layer.selectedFeatureCount() == 0:
                self.actionDelete.setEnabled(False)
            else:
                if self.tools.hasVersion(current_layer):
                    if current_layer.isEditable():
                        self.actionDelete.setEnabled(True)
                    else:
                        self.actionDelete.setEnabled(False)
                else:
                    self.actionDelete.setEnabled(False)
                    
    def set_actions(self,  isActive):
#        self.actionDelete.setEnabled(isActive)
#        self.actionLoad.setEnabled(isActive)
        self.actionCommit.setEnabled(isActive)
        self.actionRevert.setEnabled(isActive)
        self.actionDiff.setEnabled(isActive)
        self.actionLogView.setEnabled(isActive)               

    def add_layer(self, l):
        if self.tools.hasVersion(l):
            if l.id not in self.layer_list:
                l.editingStopped.connect(
                    lambda my_list=self.layer_list: self.tools.setModified(
                        my_list))
                self.layer_list.append(l.id())
                self.tools.setModified(self.layer_list)

    def remove_layer(self, id):
        self.layer_list = list(set(self.layer_list))
        if id in set(self.layer_list):
            self.layer_list.remove(id)

    def unload(self):
        QSettings().setValue("/pgVersion/commit_messages", "")
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
            self.tr(
                "Are you sure to delete all selected features. "
                "You cannot undo this action!"),
            QMessageBox.No | QMessageBox.Yes)

        if res == QMessageBox.Yes:
            QApplication.restoreOverrideCursor()
            canvas = self.iface.mapCanvas()
            currentLayer = canvas.currentLayer()
            mySchema = self.tools.layerSchema(currentLayer)
            myTable = self.tools.layerTable(currentLayer)
            myPkey = QgsDataSourceUri(
                currentLayer.dataProvider().dataSourceUri()).keyColumn()
            myDb = self.tools.layerDB('doInit', currentLayer)
            selectedFeatures = currentLayer.selectedFeatures()
            delete_list = "("

            if currentLayer.selectedFeatureCount() > 0:
                for feature in selectedFeatures:
                    delete_list += str(feature.attributes()[0]) + ", "

                delete_list = delete_list[:-2]
                delete_list += ")"
                sql = "delete from \"%s\".\"%s\" where \"%s\" in %s" % (
                    mySchema, myTable, myPkey, delete_list)
                QApplication.setOverrideCursor(Qt.WaitCursor)
                success,  error = myDb.run(sql)
                QApplication.restoreOverrideCursor()
                currentLayer.removeSelection()
                currentLayer.triggerRepaint()
                self.tools.setModified(self.layer_list)

    def doInit(self):
        currentLayer = self.iface.activeLayer()
        if currentLayer is None:
            QMessageBox.warning(
                None, '', self.tr('Please select a layer for versioning'))
            return
        elif currentLayer.dataProvider().name() != 'postgres':
                QMessageBox.warning(
                    None, '', self.tr('Please select a postgres layer '
                                      'for versioning'))
                return
        elif self.tools.hasVersion(currentLayer):
            QMessageBox.warning(
                None, self.tr('Warning'),
                self.tr('The selected layer is already under versioning!'))
            return
        else:
            mySchema = self.tools.layerSchema(currentLayer)
            myTable = self.tools.layerTable(currentLayer)
            myDb = self.tools.layerDB('doInit', currentLayer)
            if not self.tools.check_PGVS_revision(myDb):
                return

            if not self.tools.versionExists(currentLayer):
                answer = QMessageBox.question(
                    None, '', self.tr(
                        'Do you want to create the version environment\
                         for the table {0}?').format(
                            mySchema + '.' + myTable),
                    QMessageBox.Yes | QMessageBox.No)
                if answer == QMessageBox.No:
                    return
                QApplication.setOverrideCursor(Qt.WaitCursor)
                sql = "select * from versions.pgvsinit('%s.%s')" % (
                    mySchema, myTable)
                result, error = myDb.run(sql)

                QApplication.restoreOverrideCursor()
                
                if result is True:
                    QMessageBox. information(None, 'Init', self.tr(
                        """
Init was successful!

Please set the user permissions for table {0} and reload it via Database -> PG Version!

Further information on rights management can be found in the help in section 1.3.3""").format(myTable))

                    QgsProject().instance().removeMapLayer(
                        currentLayer.id())
                    self.iface.mapCanvas().refreshAllLayers()

                else:
                    QMessageBox.warning(None, 
                        self.tr('Init Error'),
                        self.tr("""
Initialisation of table {0} failed!
                              
Error:
{1}
                        """).format(
                            mySchema + "." + myTable, 
                            error))
            else:
                QMessageBox.information(
                    None,
                    "",
                    self.tr("""
The layer: {0} was already versioned.
If you want to use the versioned layer, then add the
following table from the DB: {0}_version or 
add the layer through the Load Versioned Layer button""".format(self.iface.activeLayer().name())))

    def doLoad(self):

        self.dlg = PgVersionLoadDialog(self)
        result = self.dlg.exec_()
        
        if result == 1:
            self.set_actions(True)
            
            
    def doRollback(self, item):

        if item is None:
            QMessageBox.information(None, self.tr('Error'),
                                    self.tr('Please select a valid revision'))
            return

        revision = item.text(0)

        canvas = self.iface.mapCanvas()
        currentLayer = canvas.currentLayer()

        if currentLayer is None:
            QMessageBox.information(
                None, '', self.tr('Please select a versioned layer'))
            return
        else:
            answer = QMessageBox.question(
                None, '', self.tr(
                    'Are you sure to rollback to revision {0}?').format(
                        revision), QMessageBox.Yes | QMessageBox.Cancel)

            if answer == QMessageBox.Cancel:
                return

            if self.tools.isModified(currentLayer):
                answer = QMessageBox.question(
                    None, '',
                    self.tr("""Layer {0} has modifications which will be lost after rollback! If you want to keep this modifications please commit them before you execute the rollback. 

Are you sure to rollback to revision {1}?""").format(currentLayer.name(), revision),QMessageBox.Yes | QMessageBox.Cancel)

                if answer == QMessageBox.Cancel:
                    return

            QApplication.setOverrideCursor(Qt.WaitCursor)
            provider = currentLayer.dataProvider()
            uri = provider.dataSourceUri()
            myDb = self.tools.layerDB('doRollback', currentLayer)
            if not self.tools.check_PGVS_revision(myDb):
                return
            mySchema = QgsDataSourceUri(uri).schema()

            if len(mySchema) == 0:
                mySchema = 'public'
            myTable = QgsDataSourceUri(uri).table()

            sql = "select * from versions.pgvsrollback('" + mySchema + "." + myTable.replace('_version', '') + "'," + revision + ")"

            success,  error = myDb.run(sql)
            self.LogViewDialog.close()
            currentLayer.triggerRepaint()
            QApplication.restoreOverrideCursor()
            self.tools.setModified(self.layer_list)
            self.LogViewDialog.close()
            self.iface.messageBar().pushMessage(
                'Info',
                self.tr('Rollback to revision {0} was successful!').format(
                    revision), level=Qgis.MessageLevel(0), duration=3)

    def doCommit(self):
        canvas = self.iface.mapCanvas()

        if canvas.currentLayer() is None:
            self.iface.messageBar().pushMessage(
                'Warning', self.tr(
                    'Please select a versioned layer for committing'),
                level=Qgis.MessageLevel(1), duration=3)
            return

        canvas = self.iface.mapCanvas()
        theLayer = canvas.currentLayer()
        mySchema = self.tools.layerSchema(theLayer)
        myTable = self.tools.layerTable(theLayer).replace('_version', '')

        if not self.tools.hasVersion(theLayer):
            QMessageBox.warning(None, self.tr('Warning'),
                                self.tr('Please select a versioned layer!'))
        else:
            if self.tools.isModified(theLayer):
                confRecords = self.tools.confRecords(theLayer)
                if confRecords is None:
                    self.dlgCommitMessage = CommitMessageDialog()
                    self.dlgCommitMessage.show()
                    result = self.dlgCommitMessage.exec_()

                    if result == QDialog.Accepted:
                        QApplication.setOverrideCursor(Qt.WaitCursor)
                        sql = "select * from versions.pgvscommit('%s.%s','%s')\
                        " % (
                            mySchema, myTable,
                            self.dlgCommitMessage.textEdit.toPlainText())
                        myDB = self.tools.layerDB('commit', theLayer)
                        success,  error = myDB.run(sql)
                        self.tools.layerRepaint()
                        self.iface.messageBar().pushMessage(
                            "Info",
                            self.tr('Commit of your changes was successful'),
                            level=Qgis.MessageLevel(0), duration=3)
                        self.tools.setModified(self.layer_list)
                        QApplication.restoreOverrideCursor()
                else:
                    if self.w is not None:
                        self.w = None
                    self.w = ConflictWindow(theLayer, 'conflict', self)
                    self.w.show()
                    self.tools.setModified(self.layer_list)
            else:
                self.iface.messageBar().pushMessage(
                    'Info',
                    self.tr('No layer changes for committing, everything is\
                            OK'), level=Qgis.MessageLevel(0), duration=3)

        self.tools.setModified(self.layer_list)

    def doCheckout(self, revision, tag=None):
        if revision is None:
            QMessageBox.information(
                None, self.tr('Error'),
                self.tr('Please select a valid revision'))
            return

        canvas = self.iface.mapCanvas()
        currentLayer = canvas.currentLayer()

        if currentLayer is None:
            QMessageBox.information(
                None, '', self.tr('Please select a versioned layer'))
            return
        else:
            answer = QMessageBox.question(
                None, '',
                self.tr('Are you sure to checkout the layer to '
                        'revision {0}?').format(revision),
                QMessageBox.Yes | QMessageBox.Cancel)

            if answer == QMessageBox.Yes:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                provider = currentLayer.dataProvider()
                uri = provider.dataSourceUri()
                uniqueCol = QgsDataSourceUri(uri).keyColumn()
                geomCol = QgsDataSourceUri(uri).geometryColumn()

                mySchema = QgsDataSourceUri(uri).schema()
                myTable = QgsDataSourceUri(uri).table()

                if len(mySchema) == 0:
                    mySchema = 'public'

                sql = """select * from versions.pgvscheckout(NULL::"{0}"."{1}", {2})""".format(
                            mySchema,
                            myTable.replace('_version', ''),
                            revision)

                myUri = QgsDataSourceUri(uri)
                myUri.setDataSource("", u"(%s\n)" % (sql), geomCol, "",
                                    uniqueCol)

                layer = None

                if tag:
                    table_ext = " (Tag: %s)" % tag
                else:
                    table_ext = " (Revision: %s)" % revision

                layer = QgsVectorLayer(
                    myUri.uri(), myTable + table_ext, "postgres")

                QgsProject().instance().addMapLayer(layer)
                QApplication.restoreOverrideCursor()
                if layer.isValid():
                    self.iface.messageBar().pushMessage(
                        'Info', self.tr('Checkout to revision {0} was \
                                        successful!').format(revision),
                        level=Qgis.MessageLevel(0), duration=3)
                    layer.triggerRepaint()
                else:
                    self.iface.messageBar().pushMessage(
                        'Info', self.tr('Something went wrong during checkout \
                                        to revision {0}!').format(
                            revision),
                        level=Qgis.MessageLevel(0), duration=3)
                self.LogViewDialog.close()
                return

    def doRevert(self):
        theLayer = self.iface.activeLayer()
        if theLayer is None:
            QMessageBox.warning(None,
                                self.tr("Warning"),
                                self.tr("No Layer was selected. "
                                        "Please select one Layer."))
            return

        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()
        myDb = self.tools.layerDB('revert', theLayer)
        mySchema = QgsDataSourceUri(uri).schema()
        myTable = QgsDataSourceUri(uri).table()

        if not self.tools.hasVersion(theLayer):
            QMessageBox.warning(
                None, self.tr(
                    'Warning'), self.tr('Please select a versioned layer!'))
        else:
            if not self.tools.isModified(theLayer):
                self.iface.messageBar().pushMessage(
                    "Warning",
                    self.tr(
                        'The selected Layer is already at the HEAD Revision.'),
                    level=Qgis.MessageLevel(1), duration=3)
                return

            if len(mySchema) == 1:
                mySchema = 'public'

            answer = QMessageBox.question(
                None, '', self.tr(
                    'Are you sure to revert to the HEAD revision?'),
                QMessageBox.Yes | QMessageBox.Cancel)

            if answer == QMessageBox.Yes:
                sql = "select * from versions.pgvsrevert('" + mySchema + "." + myTable.replace('_version', '') + "')"
                result,  error = myDb.read(sql)
                success,  error = myDb.run(sql)
                if not success:
                    QMessageBox.information(None, '', result)
                else:
                    self.iface.messageBar().pushMessage(
                        "Info",
                        self.tr('All changes are set back to the HEAD \
                                revision: {0}').format(
                            str(result["PGVSREVERT"][0])),
                        level=Qgis.MessageLevel(0), duration=3)

            self.tools.setModified(self.layer_list)
            theLayer.triggerRepaint()

    def doLogView(self):
        canvas = self.iface.mapCanvas()
        theLayer = self.iface.activeLayer()

        if not self.tools.hasVersion(theLayer):
            QMessageBox.warning(None, self.tr('Warning'), self.tr(
                'Please select a versioned layer!'))
            return

        if theLayer is not None:
            provider = theLayer.dataProvider()
            uri = provider.dataSourceUri()
            myDb = self.tools.layerDB('logview', theLayer)
            mySchema = QgsDataSourceUri(uri).schema()
            myTable = QgsDataSourceUri(uri).table()

            if len(mySchema) == 0:
                mySchema = 'public'

            sql = "select * from versions.pgvslogview('" + mySchema + "." + myTable.replace(
                '_version', '') + "') order by revision desc"
            result,  error = myDb.read(sql)

            self.LogViewDialog.setLayer(theLayer)
            self.LogViewDialog.createTagList()
            self.LogViewDialog.treeWidget.clear()

            itemList = []

            for i in range(len(result["PROJECT"])):
                myItem = QTreeWidgetItem()
                myItem.setText(0, str(result["REVISION"][i]))
                myItem.setText(1, str(result["DATUM"][i]))
                myItem.setText(2, str(result["PROJECT"][i]))
                myItem.setText(3, str(result["LOGMSG"][i]))
                itemList.append(myItem)

            self.LogViewDialog.treeWidget.addTopLevelItems(itemList)

            self.LogViewDialog.show()
            myDb.close()
            canvas.refresh()
        else:
            provider = theLayer.dataProvider()
            uri = provider.dataSourceUri()
            myDb = self.tools.layerDB('logview', theLayer)
            mySchema = QgsDataSourceUri(uri).schema()
            myTable = QgsDataSourceUri(uri).table()

            if len(mySchema) == 0:
                mySchema = 'public'

            sql = "select * from versions.pgvslogview('" + mySchema + "." + myTable.replace(
                '_version', '') + "') order by revision desc"
            result,  error = myDb.read(sql)

            self.LogViewDialog.setLayer(theLayer)
            self.LogViewDialog.createTagList()
            self.LogViewDialog.treeWidget.clear()

            itemList = []

            for i in range(len(result["PROJECT"])):
                myItem = QTreeWidgetItem()
                myItem.setText(0, str(result["REVISION"][i]))
                myItem.setText(1, str(result["DATUM"][i]))
                myItem.setText(2, str(result["PROJECT"][i]))
                myItem.setText(3, str(result["LOGMSG"][i]))
                itemList.append(myItem)

            self.LogViewDialog.treeWidget.addTopLevelItems(itemList)

            self.LogViewDialog.show()
            myDb.close()
            canvas.refresh()

    def doDiff(self):

        currentLayer = self.iface.activeLayer()

        if currentLayer is None or currentLayer.dataProvider().name() == "memory":
            self.iface.messageBar().pushMessage(
                'Warning',
                self.tr('Please select a versioned layer.'),
                level=Qgis.MessageLevel(1), duration=3)
            return

        if not self.tools.isModified(currentLayer):
            self.iface.messageBar().pushMessage(
                "Warning",
                self.tr(
                    'The selected Layer is at the HEAD Revision.'),
                level=Qgis.MessageLevel(1), duration=3)
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        geomCol = self.tools.layerGeomCol(currentLayer)
        geometryType = self.tools.layerGeometryType(currentLayer)
        mySchema = self.tools.layerSchema(currentLayer)
        myTable = self.tools.layerTable(currentLayer)

        if len(mySchema) == 0:
            mySchema = 'public'

        extent = self.iface.mapCanvas().extent().toString().replace(
            ':', ', ')
        authority, crs = currentLayer.crs().authid().split(':')
#        geo_idx = '%s && ST_MakeEnvelope(%s,%s)' % (geomCol, extent, crs)
        
        with open('{0}/sql/diff.sql'.format(os.path.dirname(os.path.abspath(__file__))),  'r') as sql_file:
            sql = sql_file.read().format(
            schema=mySchema,
            table=myTable,
            origin=myTable.replace(
                '_version', ''))
                
#                , geo_idx=geo_idx)

        myUri = QgsDataSourceUri(self.tools.layerUri(currentLayer))
        myUri.setDataSource("", u"(%s\n)" % sql, geomCol, "", "rownum")
        myUri.setSrid(crs)
        layer_name = myTable + " (Diff to HEAD Revision)"
        layer = QgsVectorLayer(myUri.uri(), layer_name, "postgres")

        mem_layer = self.tools.create_memory_layer(layer, layer_name)

        if mem_layer != None:
            if not mem_layer.isValid():
                self.iface.messageBar().pushMessage(
                        'Warning',
                        self.tr('No diffs to HEAD in current extend detected!'),
                        level=Qgis.MessageLevel(1), duration=3)
            else:
                legends_path = os.path.dirname(__file__)
                if geometryType == 0:
                    mem_layer.loadNamedStyle(
                        legends_path + "/legends/diff_point.qml")
                elif geometryType == 1:
                    mem_layer.loadNamedStyle(
                        legends_path + "/legends/diff_linestring.qml")
                elif geometryType == 2:
                    mem_layer.loadNamedStyle(
                        legends_path + "/legends/diff_polygon.qml")
                QgsProject().instance().addMapLayer(mem_layer)
                self.iface.messageBar().pushMessage(
                    'Info',
                    self.tr('Diff to HEAD revision was successful!'),
                    level=Qgis.MessageLevel(0), duration=3)

        QApplication.restoreOverrideCursor()
        self.LogViewDialog.close()
        return

    def doDrop(self):
        theLayer = self.iface.activeLayer()
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()
        mySchema = QgsDataSourceUri(uri).schema()
        if len(mySchema) == 0:
            mySchema = 'public'
        myTable = QgsDataSourceUri(uri).table()

        if theLayer is None:
            QMessageBox.information(None, '', self.tr(
                'Please select a layer for versioning'))
            return
        else:
            answer = QMessageBox.question(
                None, '',
                self.tr('Are you sure to to drop pgvs from the table '
                        '{0}?').format(mySchema + "." + myTable.replace(
                            '_version', '')),
                QMessageBox.Yes | QMessageBox.Cancel)

            if answer == QMessageBox.Yes:
                if self.tools.isModified(theLayer):
                    QMessageBox.warning(
                        None,
                        self.tr('Warning'),
                        self.tr('Layer %s has uncommited changes, please'
                                'commit them or revert to HEAD revision' % (
                                    theLayer.name())))
                else:
                    myDb = self.tools.layerDB('doDrop', theLayer)
                    sql = """select versions.pgvsdrop('{0}.{1}')""".format(
                        mySchema, myTable.replace('_version', ''))
                    myDb.read(sql)

                    layer_name = theLayer.name()
                    QgsProject().instance().removeMapLayer(
                        theLayer.id())
                    self.iface.messageBar().pushMessage(
                        'Info',
                        self.tr('Versioning for layer {0} dropped!').format(
                            layer_name), level=Qgis.MessageLevel(0),
                        duration=3)
                    self.iface.mapCanvas().refreshAllLayers()
                    

    def doHelp(self):
        helpUrl = QUrl()
        if self.locale != 'de':
            self.locale = 'en'
                
        absolut_path_string = '%s/docs/help/dokumentation_pgversion_QGIS3_%s.html' % (os.path.dirname(__file__),  self.locale)
        helpUrl.setUrl(QUrl.fromLocalFile(absolut_path_string).toString())

        self.helpDialog.webView.load(helpUrl)
        self.helpDialog.show()

    def doAbout(self):
        self.about = DlgAbout(self.plugin_path)
        self.about.show()
