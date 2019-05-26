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
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtSql import *
from qgis.gui import *
from qgis.core import *
from .forms.dbVersionCheck import DbVersionCheckDialog
from datetime import datetime
from .dbtools.dbtools import *
import os


class PgVersionTools(QObject):

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self.pgvsRevision = '2.1.8'
        self.parent = parent
        self.iface = parent.iface
        self.layer_list = parent.layer_list

    def layerRepaint(self):
        for layer in self.iface.mapCanvas().layers():
            layer.triggerRepaint()

    def layerDB(self, connectionName, layer):
        myUri = QgsDataSourceUri(layer.source())
        if layer.dataProvider().name() == 'postgres':
            if myUri.username() == '':
                connectionInfo = myUri.connectionInfo()
                (success, user, password) = QgsCredentials.instance().get(
                    connectionInfo, None, None)
                QgsCredentials.instance().put(connectionInfo, user, password)
                myUri.setPassword(password)
                myUri.setUsername(user)
            try:
                myDb = DbObj(pluginname=connectionName,
                             typ='pg', hostname=myUri.host(),
                             port=myUri.port(), dbname=myUri.database(),
                             username=myUri.username(),
                             password=myUri.password())
                return myDb
            except:
                QMessageBox.information(
                    None, self.tr('Error'),
                    self.tr('No Database Connection Established.'))
                return None

    def setConfTable(self, theLayer):
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()
        myDb = layerDB('setConfTable', theLayer)
        mySchema = QgsDataSourceUri(uri).schema()
        myTable = QgsDataSourceUri(uri).table()
        if len(mySchema) == 0:
            mySchema = 'public'

        myTable = myTable.remove("_version")
        sql = "select versions.pgvscommit('" + mySchema + "." + myTable + "')"
        result,  error = myDb.read(sql)

    def hasVersion(self, theLayer):

            myLayerUri = QgsDataSourceUri(theLayer.source())
            myDb = self.layerDB('hasVersion', theLayer)

            if myDb is None:
                return None

            if len(myLayerUri.schema()) == 1:
                schema = 'public'
            else:
                schema = myLayerUri.schema()
            sql = """
                    select count(version_table_name) 
                    from versions.version_tables import 
                    where version_view_schema = '%s' and version_view_name = '%s'""" % (schema, myLayerUri.table())
                    
            result,  error = myDb.read(sql)
            if error == None:
                if result['COUNT'][0] == 1:
                    return True
                else:
                    return False
#            else:
#                QMessageBox.warning(None,  self.tr('Init error'),  str(error))

    def isModified(self, myLayer=None):
        if myLayer is None:
            return None
        myLayerUri = QgsDataSourceUri(myLayer.source())
        myDb = self.layerDB('isModified', myLayer)

        if myDb is None:
            return None

        if len(myLayerUri.schema()) == 0:
            schema = 'public'
        else:
            schema = myLayerUri.schema()

        sql = """
          select count(project)
          from versions."%s_%s_log"
          where project = '%s' and not commit""" % (
              schema, myLayerUri.table(), myDb.dbUser())
        result,  error = myDb.read(sql)

        try:
            if int(result["COUNT"][0]) == 0:
                return False
            else:
                return True
        except:
            return False

    def setModified(self, layer_list):

        layer_list = list(set(layer_list))

        for i in range(len(layer_list)):
            map_layer = QgsProject().instance().mapLayer(layer_list[i])
            if self.isModified(map_layer):
                if '(modified)' not in map_layer.name():
                    map_layer.setName(map_layer.name() + ' (modified)')
            else:
                map_layer.setName(map_layer.name().replace(' (modified)', ''))

    def vectorLayerExists(self, myName):
        layermap = QgsProject().instance().mapLayers()
        for layer in layermap:
            if layermap[layer].type() == QgsMapLayer.VectorLayer and layermap[
                    layer].name() == myName:
                if layermap[layer].isValid():
                    return True
                else:
                    return False

    def versionExists(self, layer):

        myDb = self.layerDB('versionExists', layer)
        provider = layer.dataProvider()
        uri = provider.dataSourceUri()

        try:
            myTable = QgsDataSourceUri(uri).table()
            mySchema = QgsDataSourceUri(uri).schema()

            if "versions.pgvscheckout" in myTable:
                QMessageBox.warning(
                    None,
                    self.tr("Layer error"),
                    self.tr("Please select a postgres layer for versioning."))
                return True

            if mySchema == '':
                mySchema = 'public'

            sql = ("select version_table_schema as schema, version_table_name as table from versions.version_tables where (version_view_schema = '{schema}' and version_view_name = '{table}') or (version_table_schema = '{schema}' and version_table_name = '{table}')").format(schema=mySchema, table=myTable)
            result,  error = myDb.read(sql)

            if result is not None and len(result) > 0:
                QMessageBox.information(
                    None, '',
                    self.tr('Table {schema}.{table} is already '
                            'versionized').format(
                        schema=mySchema, table=myTable))
                return True
            else:
                return False
        except Exception as e:
            # QMessageBox.information(
            #     None, '',
            #     self.tr('pgvs is not installed in your database. \n\n Please\
            #             install the pgvs functions from file \n\n \
            #             {createVersionPath}\n\n as mentioned in help').format(
            #         createVersionPath=self.createVersionPath))
            return True

    def createGridView(self, tabView, tabData, headerText, colWidth,
                       rowHeight):

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
            headerItem.setData(Qt.DisplayRole, text)
            tabView.setHorizontalHeaderItem(i, headerItem)
            i = i + 1

        for i in range(0, numRows):
            col = startVal
            
            for text in headerText:
                myItem = QTableWidgetItem()
                myItem.setData(Qt.DisplayRole, tabData[text.upper()][i])
                tabView.setItem(i, col, myItem)
                myItem.setSelected(False)
                col = col + 1
        return

    def confRecords(self, theLayer):
        confRecords = []
        myDb = self.layerDB('commit', theLayer)
        mySchema = self.layerSchema(theLayer)
        myTable = self.layerTable(theLayer).replace('_version', '')

        sql = """
                select version_table_schema as schema, version_table_name as table 
                from versions.version_tables 
                where version_view_schema = '{0}' 
                    and version_view_name = '{1}' """.format(mySchema, myTable)
        result,  error = myDb.read(sql)

        if result is not None and len(result) == 0:
            QMessageBox.information(
                None, '',
                self.tr('Table {0}.{1} is not versionized').format(
                    self.mySchema,  self.myTable))
            return None
        else:
            sql = "select count(myuser) from versions.pgvscheck('%s.%s')" % (
                mySchema, myTable)
            check,  error = myDb.read(sql)

        if check["COUNT"][0] is not 0:
            sql = "select * from versions.pgvscheck('%s.%s') order by objectkey" % (mySchema, myTable)
            result,  error = myDb.read(sql)
            myDb.close()

            for i in range(len(result["CONFLICT_USER"])):
                confRecords.append("Commit all changes of - %s" % (
                    result['MYUSER'][i]))
                confRecords.append("Commit all changes of - %s" % (
                    result['CONFLICT_USER'][i]))

            confRecords = list(set(confRecords))

            for i in range(len(result["CONFLICT_USER"])):
                resString = "{0} - {1} - {2}".format(result["OBJECTKEY"][i], 
                                                                    result["MYUSER"][i].strip(), 
                                                                    datetime.strftime(datetime.fromtimestamp(float(result["MYSYSTIME"][i]) / 1000.0), "%x %H:%M:%S")
                                                                )
                confRecords.append(resString)
                resString = "{0} - {1} - {2}".format(result["OBJECTKEY"][i], 
                                                                    result["CONFLICT_USER"][i].strip(), 
                                                                    datetime.strftime(datetime.fromtimestamp(float(result["CONFLICT_SYSTIME"][i]) / 1000.0), "%x %H:%M:%S")
                                                                )
                confRecords.append(resString)
            confRecords.insert(0, self.tr('select Candidate'))
            return confRecords
        else:
            return None

    def tableRecords(self, theLayer):
        myDb = self.layerDB('tableRecords', theLayer)
        mySchema = self.layerSchema(theLayer)
        myTable = self.layerTable(theLayer)
        geomCol = self.layerGeomCol(theLayer)

        sql = "select * from versions.version_tables \
          where version_view_schema = '%s' and version_view_name = '%s'" % (
              mySchema, myTable)
        layer,  error = myDb.read(sql)

        sql = "select objectkey, myversion_log_id, conflict_version_log_id \
          from versions.pgvscheck('%s.%s')" % (mySchema, myTable.replace(
              "_version", ""))

        result,  error = myDb.read(sql)
        timeListString = ''
        keyString = ''

        for i in range(len(result["OBJECTKEY"])):
            timeListString += "%s,%s," % (result["MYVERSION_LOG_ID"][i], result["CONFLICT_VERSION_LOG_ID"][i])
            keyString += "%s," % result["OBJECTKEY"][i]

        timeListString = timeListString[0:len(timeListString) - 1]
        keyString = keyString[0:len(keyString) - 1]

        sql = """
                select * from versions."%s_%s_log" 
                where version_log_id in (%s)
                order by %s""" % (mySchema, myTable, timeListString, layer["VERSION_VIEW_PKEY"][0])

        result,  error = myDb.read(sql)

        if error == None:
            cols = myDb.cols(sql)
            cols.remove('ACTION')
            cols.remove('SYSTIME')
            cols.remove('COMMIT')
            cols.remove(geomCol.upper())

            cols.insert(0, cols.pop(-1))
            cols.insert(0, cols.pop(-1))
            cols.insert(0, cols.pop(-1))

            resultArray = []
            resultArray.append(result)
            resultArray.append(cols)

            myDb.close()
            if len(resultArray) != 0:
                return resultArray
            else:
                return None
        else:
            return None

    def conflictLayer(self, theLayer):
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()
        myDb = self.layerDB('getConflictLayer', theLayer)
        mySchema = QgsDataSourceUri(uri).schema()
        myTable = QgsDataSourceUri(uri).table()
        if len(mySchema) == 0:
            mySchema = 'public'

        sql = """
                select * from versions.version_tables 
                where version_view_schema = '%s' and version_view_name = '%s'""" % (mySchema, myTable)
        layer,  error = myDb.read(sql)

        uri = QgsDataSourceUri()

        uri.setConnection(myDb.dbHost(), str(myDb.dbPort()), myDb.dbName(),
                          myDb.dbUser(), myDb.dbPasswd())

        sql = """
                select * from versions.pgvscheck('{0}.{1}')
                """.format(mySchema,  myTable.replace("_version", ''))
                
        result,  error = myDb.read(sql)
        myFilter = ''
        if result != None:
            for i in range(len(result["OBJECTKEY"])):
                key = result["OBJECTKEY"][i]
                mysystime = result["MYSYSTIME"][i]
                systime = result["CONFLICT_SYSTIME"][i]
                myFilter += "({0}={1} and systime = {2}) or ({0} = {1} and systime = {3}) or ".format(
                                                                                                    layer["VERSION_VIEW_PKEY"][0],  
                                                                                                    key, 
                                                                                                    systime, 
                                                                                                    mysystime)
    
            if len(myFilter) > 0:
                myFilter = myFilter[0:len(myFilter) - 4]
                uri.setDataSource(
                    "versions", 
                    "%s_%s_log" % (mySchema, myTable), 
                    layer["VERSION_VIEW_GEOMETRY_COLUMN"][0], 
                    myFilter, layer["VERSION_VIEW_PKEY"][0])
                    
                layerName = myTable + "_conflicts"
                vLayer = QgsVectorLayer(uri.uri(), layerName, "postgres")
                userPluginPath = QFileInfo(
                    QgsApplication.qgisAuthDatabaseFilePath()).path() + "/python/plugins/pgversion/"
                vLayer.setRenderer(None)
                vLayer.loadNamedStyle(userPluginPath + "/legends/conflict.qml")
                return vLayer

    def create_memory_layer(self, layer, name):
        feats = [feat for feat in layer.getFeatures()]
        if layer.geometryType() == 0:
            layer_type = 'MultiPoint?crs=' + layer.crs().authid()
        if layer.geometryType() == 1:
            layer_type = 'MultiLineString?crs=' + layer.crs().authid()
        if layer.geometryType() == 2:
            layer_type = 'MultiPolygon?crs=' + layer.crs().authid()
        
        try:
            mem_layer = QgsVectorLayer(layer_type, name, "memory")
    
            mem_layer_data = mem_layer.dataProvider()
            mem_layer.startEditing()
    
            attr = feats[0].fields()
            mem_layer_data.addAttributes(attr)
            mem_layer.updateFields()
    
            feat = QgsFeature()
            for feature in feats:
                feat.setGeometry(feature.geometry())
                feat.setAttributes(feature.attributes())
                mem_layer.addFeature(feature)
                mem_layer.updateExtents()
    
            mem_layer.commitChanges()
            return mem_layer
        except:
            self.iface.messageBar().pushMessage(
                'Warning',
                self.tr('No diffs to HEAD detected!'),
                level=Qgis.MessageLevel(1), duration=3)            
            return None

    def file_path(name, base_path=None):
        if not base_path:
            base_path = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(base_path, name)

# Check the revision of the DB-Functions
    def check_PGVS_revision(self, myDb):
        create_version_path = '%s/docs/create_pgversion_schema.sql' % (
            self.parent.plugin_path)
        upgrade_version_path = '%s/docs/upgrade_pgversion_schema.sql' % (
            self.parent.plugin_path)
        if not myDb.exists('table', 'versions.version_tables'):
            self.vsCheck = DbVersionCheckDialog(
                myDb, '', create_version_path, 'install')

            revisionMessage = self.tr("""
pgvs is not installed in the selected DB.
Please contact your DB-administrator to install the DB-functions from the file:

%s

If you have appropriate DB permissions you can install the DB 
functions directly with click on Install pgvs.""" % (create_version_path))

            self.vsCheck.messageTextEdit.setText(revisionMessage)
            self.vsCheck.btnUpdate.setText('Install pgvs')
            self.vsCheck.show()
            return False
        else:
            result, error = myDb.read(
                'select pgvsrevision from versions.pgvsrevision()')

            my_major_revision = self.pgvsRevision.split('.')[1]
            my_minor_revision = self.pgvsRevision.split('.')[2]
            db_major_revision = result["PGVSREVISION"][0].split('.')[1]
            db_minor_revision = result["PGVSREVISION"][0].split('.')[2]

            for i in range(int(db_minor_revision), int(my_minor_revision)):

                if my_major_revision + "." + my_minor_revision != db_major_revision + "." + db_minor_revision:
                    upgrade_version_path = '%s/docs/upgrade_pgversion_schema-2.%s.%s.sql' % (self.parent.plugin_path, db_major_revision,
                                   i)
                    self.vsCheck = DbVersionCheckDialog(
                        myDb, result["PGVSREVISION"][0], upgrade_version_path,
                        'upgrade')
                    revisionMessage = self.tr("""
The Plugin expects pgvs revision %s but DB-functions of revision %s are installed. 
Please contact your DB-administrator to upgrade the DB-functions from the file:

%s

If you have appropriate DB permissions you can update the DB directly with click on DB-Update.""") % (
                        self.pgvsRevision, result["PGVSREVISION"][0], 
                        upgrade_version_path)

                    self.vsCheck.messageTextEdit.setText(revisionMessage)
                    self.vsCheck.btnUpdate.setText(self.tr(
                        'Upgrade pgvs to Revision %s.%s.%s') % (
                            2, my_major_revision, i + 1))
                    self.vsCheck.show()
                    return False
        return True

    def getFieldNames(self, vLayer):
        myList = self.getFieldList(vLayer)

        fieldList = []
        for (k, attr) in myList.iteritems():
            fieldList.append(unicode(attr.name(), 'latin1'))

        return fieldList

    def getFieldList(self, vlayer):
        fProvider = vlayer.dataProvider()
        myFields = fProvider.fields().toList()
        return myFields

    def layerGeomCol(self, layer):
        return QgsDataSourceUri(self.layerUri(layer)).geometryColumn()

    def layerSchema(self, layer):
        mySchema = QgsDataSourceUri(self.layerUri(layer)).schema()
        if len(mySchema) == 0:
            mySchema = 'public'
        return mySchema

    def layerTable(self, layer):
        return QgsDataSourceUri(self.layerUri(layer)).table()

    def layerName(self, layer):
        return QgsDataSourceUri(layer.name())

    def layerKeyCol(self, layer):
        return QgsDataSourceUri(self.layerUri(layer)).keyColumn()

    def layerUri(self, layer):
        provider = layer.dataProvider()
        return provider.dataSourceUri()

    def layerGeometryType(self, layer):
        return layer.geometryType()

    def layerHost(self, layer):
        return QgsDataSourceUri(self.layerUri(layer)).host()

    def layerPassword(self, layer):
        return QgsDataSourceUri(self.layerUri(layer)).password()

    def layerPort(self, layer):
        return QgsDataSourceUri(self.layerUri(layer)).port()

    def layerUsername(self, layer):
        return QgsDataSourceUri(self.layerUri(layer)).username()
