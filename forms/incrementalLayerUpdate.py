# -*- coding: utf-8 -*-

"""
Module implementing IncrementalLayerUpdate.
"""
from qgis.core import *
from qgis.gui import *
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.QtWidgets import QDialog,  QDialogButtonBox,  QMessageBox
from qgis.PyQt import uic
from qgis.core import QgsProject
from ..dbtools.dbtools import DbObj
from ..pgVersionTools import PgVersionTools

import os
import sys
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
        try:        
            QDialog.__init__(self)
            super().__init__(self)
            self.setupUi(self)
            self.iface = parent.iface
            self.buttonBox.clicked.connect(self.handleButtonClick)
            self.tools = parent.tools
            excepted_layer_list = []
            self.layer_list = parent.layer_list
        

            self.update_layer = self.iface.layerTreeView().selectedLayers()[0]
            excepted_layer_list.append(self.update_layer)
            map_layers = QgsProject.instance().mapLayers().values()
            
            for layer in map_layers:
                if layer.dataProvider().name() != 'postgres':
                    excepted_layer_list.append(layer)
            self.mMapLayerComboBox.setExceptedLayerList(excepted_layer_list)    
        except:
            QMessageBox.information(None,  self.tr('Error'),  self.tr('Please select a versioned layer to upgrade'))
            

    def handleButtonClick(self, button):
        role = self.buttonBox.buttonRole(button)
        if role == QDialogButtonBox.ApplyRole:
            self.doApply()
        elif role == QDialogButtonBox.RejectRole:
            self.doReject()

    @pyqtSlot()
    def doApply(self):
        """
        Slot documentation goes here.
        """
        selected_layer = self.mMapLayerComboBox.currentLayer()
        
        db = self.layer_db_connection(self.update_layer)
        selected_schema = selected_layer.dataProvider().uri().schema()
        selected_table = selected_layer.dataProvider().uri().table()
        update_schema = self.update_layer.dataProvider().uri().schema()
        update_table = self.update_layer.dataProvider().uri().table().replace('_version',  '')
        if db.exists('table',  '%s.%s' % (selected_schema,  selected_table)):
            sql = """
            select pgvsincrementalupdate as update 
            from versions.pgvsincrementalupdate('%s.%s', '%s.%s')
            """ % (selected_schema,  selected_table,  update_schema,  update_table)
            
            result,  error = db.read(sql)
            
            result_array = result['UPDATE'][0].split(',')
            message = ''
            for text in result_array:
                message += '%s \n\n' % text
            
            self.iface.messageBar().pushMessage(
                "Info",
                message,
                level=Qgis.MessageLevel(0), duration=3)

            self.layer_list.append(self.update_layer)
            self.tools.setModified([self.update_layer])
            
            self.close()
        
                
        
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
