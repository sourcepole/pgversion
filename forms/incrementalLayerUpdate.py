# -*- coding: utf-8 -*-

"""
Module implementing IncrementalLayerUpdate.
"""
from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtCore import pyqtSlot,  Qt
from qgis.PyQt.QtWidgets import QDialog,  QDialogButtonBox,  QMessageBox,  QApplication
from qgis.PyQt import uic
from qgis.core import QgsProject
from ..dbtools.dbtools import DbObj
import re
import os
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'incrementalLayerUpdate.ui'))

class IncrementalLayerUpdateDialog(QDialog, FORM_CLASS):
    """
    Class documentation goes here.
    """

    def __init__(self, parent):
        """
        Constructor

        @param parent reference to the parent widget (defaults to None)
        @type QWidget (optional)
        """
        QDialog.__init__(self)
        super().__init__(self)
        self.setupUi(self)
        self.iface = parent.iface
        self.buttonBox.clicked.connect(self.handleButtonClick)
        self.tools = parent.tools
        excepted_layer_list = []
        self.layer_list = parent.layer_list
        self.loaded_layers = self.iface.layerTreeView().selectedLayers()
        self.update_layer = self.loaded_layers[0]
        excepted_layer_list.append(self.update_layer)
        
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() != QgsMapLayerType.VectorLayer:
                excepted_layer_list.append(layer)
            
        self.mMapLayerComboBox.setExceptedLayerList(excepted_layer_list)    
            
    def handleButtonClick(self, button):
        role = self.buttonBox.buttonRole(button)
        if role == QDialogButtonBox.ApplyRole:
            self.doApply()
        elif role == QDialogButtonBox.RejectRole:
            self.doReject()
            
#    @staticmethod
    def launder_pg_name(self,  name):
        # OGRPGDataSource::LaunderName
        # return re.sub(r"[#'-]", '_', unicode(name).lower())
        input_string = str(name).lower().encode('ascii', 'replace')
        input_string = input_string.replace(b" ", b"_")
        input_string = input_string.replace(b".", b"_")
        input_string = input_string.replace(b"-", b"_")
        input_string = input_string.replace(b"+", b"_")
        input_string = input_string.replace(b"'", b"_")

        # check if table_name starts with number

        if re.search(r"^\d", input_string.decode('utf-8')):
            input_string = '_'+input_string.decode('utf-8')

        try:
            return input_string.decode('utf-8')
        except:
            return input_string            

    @pyqtSlot()
    def doApply(self):
        db = self.layer_db_connection(self.update_layer)        
        self.selected_layer = self.mMapLayerComboBox.currentLayer()
        
        if self.selected_layer != None:
            success = True
    # check if the selected layer is a postgres layer
    # Import a non postgres layer to update_layer database      
    
            QApplication.setOverrideCursor(Qt.WaitCursor)
            if self.selected_layer.dataProvider().name() != 'postgres':                       
                success = self.import_to_postgis(db)
                
            if success:
                self.incremental_upgrade(db)
    
            QApplication.restoreOverrideCursor()
            
            self.close()
        else:
            res = QMessageBox.warning(
                self,
                self.tr("Warning"),
                self.tr("""Please select an import layer."""),
                (
                    QMessageBox.StandardButton.Ok),
            )
            

    def import_to_postgis(self,  db):
        self.selected_layer.setName(self.launder_pg_name(self.selected_layer.name()))

        if db.exists('table',  '{}.{}'.format(self.update_layer.dataProvider().uri().schema(), self.selected_layer.name())):
            answer = QMessageBox.information(
                None,
                self.tr("Table {schema}.{table} exists".format(
                                                schema = self.update_layer.dataProvider().uri().schema(), 
                                                table = self.selected_layer.name()
                                                )
                                    ),
                self.tr("""Do you like to overwrite the table? """),
                (
                    QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Yes),
            )
            
            if answer == QMessageBox.StandardButton.Yes:
                sql = "drop table {schema}.{table}".format(
                                                    schema = self.update_layer.dataProvider().uri().schema(), 
                                                    table = self.selected_layer.name()
                                                )
                db.run(sql)       
            else:
                self.close()
                
        con_string = "dbname='{dbname}' host='{dbhost}' port='{dbport}' user='{dbuser}' password='{dbpasswd}' key={key} type={geometrytype} schema={schema} table={table} {geometryColumn}".format(
                dbname = db.dbname(), 
                dbhost = db.dbHost(), 
                dbport = db.dbport(), 
                dbuser = db.dbUser(), 
                dbpasswd = db.dbpasswd(), 
                key = self.update_layer.dataProvider().uri().keyColumn(), 
                geometrytype = QgsWkbTypes.displayString(int(self.update_layer.wkbType())), 
                schema = self.update_layer.dataProvider().uri().schema(), 
                table = self.selected_layer.name(), 
                geometryColumn = self.selected_layer.dataProvider().uri().geometryColumn()
        )
        
        CRS = self.update_layer.crs().authid()
        err = QgsVectorLayerExporter.exportLayer(self.selected_layer, con_string, 'postgres', QgsCoordinateReferenceSystem(CRS), False)
        
        sql = "CREATE INDEX sidx_{table}_geom ON {schema}.{table}({geometry_column});".format(
                                                                                                schema=self.update_layer.dataProvider().uri().schema(), 
                                                                                                table=self.selected_layer.name(), 
                                                                                                geometry_column = self.update_layer.dataProvider().uri().geometryColumn()
                                                                                        )
        db.run(sql)
        
        if err[0] != 0:
            QMessageBox.information(None, self.tr('Import Error'),  err[1])
            return False
        else:
            return True

        self.close()

        
    def incremental_upgrade(self,  db):
        selected_schema = self.update_layer.dataProvider().uri().schema()
        selected_table = self.selected_layer.name()        
        update_schema = self.update_layer.dataProvider().uri().schema()
        update_table = self.update_layer.dataProvider().uri().table().replace('_version',  '')
        
        sql = """
        select pgvsincrementalupdate as update 
        from versions.pgvsincrementalupdate('%s.%s', '%s.%s')
        """ % (selected_schema,  selected_table,  update_schema,  update_table)
        result,  error = db.read(sql)

        if error == None:
            self.do_update_layer(db,  result)
        else: 
            message = str(error)
            QMessageBox.information(None, self.tr('Update Error'),  message)
        
        
    def do_update_layer(self,  db,  result):
        result_array = result['UPDATE'][0].split(',')
        message = ''
        message = '%s, %s' % (result_array[0],  result_array[1])
        message = message.replace('{',  '').replace('"',  '')
        
        self.iface.messageBar().pushMessage(
            "Info",
            message,
            level=Qgis.MessageLevel(0), duration=5)

        self.layer_list.append(self.update_layer.id())
        self.tools.setModified(self.layer_list)
        self.update_layer.triggerRepaint()        
        
        sql = """
                 DROP TABLE {schema}.{table} 
        """.format(schema = self.update_layer.dataProvider().uri().schema(), 
                         table = self.selected_layer.name()) 
        
        db.run(sql)
        
    def layer_db_connection(self,  layer):
        uri = layer.dataProvider().uri()
        db = DbObj(dbname=uri.database(),  
                            hostname=uri.host(),  
                            port=uri.port(),  
                            username=uri.username(),  
                            password=uri.password() )
                            
        return db        
#
# Prüfen, ob der Import-Layer dem Upgrade-Layer entspricht.
    def check_layer(self):
        pass
        

    @pyqtSlot()
    def doReject(self):
        """
        Slot documentation goes here.
        """
        self.close()
