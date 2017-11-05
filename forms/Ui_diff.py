# -*- coding: utf-8 -*-

"""
Module implementing DiffDlg.
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from qgis.core import *
from qgis.gui import *
from ..dbtools.dbTools import *
from ..pgversion_tools import PgVersionTools
from Ui_Ui_diff import Ui_DiffDlg

class DiffDlg(QDialog, Ui_DiffDlg):
    """
    Class documentation goes here.
    """
    def __init__(self, iface,  parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface

        self.tools = PgVersionTools(parent)
    

        self.dateEditRev1.setDate(QDate.currentDate())
        self.dateEditRev2.setDate(QDate.currentDate())
        
        canvas = self.iface.mapCanvas()
        theLayer = self.iface.activeLayer()
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()    
        myDb = self.tools.layerDB('logview', theLayer)
        mySchema = QgsDataSourceURI(uri).schema()
        myTable = QgsDataSourceURI(uri).table()
     
        if len(mySchema) == 0:
           mySchema = 'public'
               
        sql = "select revision from versions.pgvslogview('"+mySchema+"."+myTable.replace('_version', '')+"') order by revision desc"
        result = myDb.read(sql)
        
        for i in range(len(result['REVISION'])):
            self.cmbRevision1.addItem(result['REVISION'][i])
            self.cmbRevision2.addItem(result['REVISION'][i])
            
        
    def setDb(self,  theLayer):
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()    
        self.myDb = self.tools.layerDB('diffDlg', theLayer)
        self.mySchema = QgsDataSourceURI(uri).schema()
        self.myTable = QgsDataSourceURI(uri).table() 
        self.myKeyColumn = QgsDataSourceURI(uri).keyColumn()
    
        if len(self.mySchema) == 0:
            self.mySchema = 'public'      

        return
        
    


    @pyqtSignature("")
    def on_buttonBox_accepted(self):

        if self.radioRevisionRev1.isChecked():
            if self.cmbRevisionRev1.currentText() != '-----':
              myRevision1 = self.cmbRevisionRev1.currentText()           
               
        if self.radioRevisionRev2.isChecked():
            if self.cmbRevisionRev2.currentText() != '-----':
              myRevision2 = self.cmbRevisionRev2.currentText()
                
        if self.radioDateRev1.isChecked():
            myDate = self.dateEditRev1.date().toString(Qt.ISODate)
            
            sql = 'select revision from versions."'+self.mySchema+'_'+self.myTable+'_log" '
            sql += 'where systime <= (date_part(\'epoch\'::text, \''+myDate+'\'::timestamp without time zone) * (1000)::double precision)::bigint '
            sql += 'order by systime desc limit 1 '
            
            result = self.myDb.read(sql)
            myRevision1 = str(result['REVISION'][0])

                
        if self.radioDateRev2.isChecked():
            myDate = self.dateEditRev2.date().toString(Qt.ISODate)
            
            sql = 'select revision from versions."'+self.mySchema+'_'+self.myTable+'_log" '
            sql += 'where systime <= (date_part(\'epoch\'::text, \''+myDate+'\'::timestamp without time zone) * (1000)::double precision)::bigint '
            sql += 'order by systime desc limit 1 '
            
            result = self.myDb.read(sql)
            myRevision2 = str(result['REVISION'][0])
            
            pass
                
        if self.radioHeadRev1.isChecked():
            sql = 'select max(revision) as revision from versions."'+self.mySchema+'_'+self.myTable+'_log" '
            result = self.myDb.read(sql)
            myRevision1 = str(result['REVISION'][0])

        if self.radioHeadRev2.isChecked():
            sql = 'select max(revision) as revision from versions."'+self.mySchema+'_'+self.myTable+'_log" '
            result = self.myDb.read(sql)
            myRevision2 = str(result['REVISION'][0])
                
        if self.radioBaseRev1.isChecked():
            sql = 'select min(revision) as revision from versions."'+self.mySchema+'_'+self.myTable+'_log" '
            result = self.myDb.read(sql)
            myRevision1 = str(result['REVISION'][0])
            
        if self.radioBaseRev2.isChecked():
            sql = 'select min(revision) as revision from versions."'+self.mySchema+'_'+self.myTable+'_log" '
            result = self.myDb.read(sql)
            myRevision2 = str(result['REVISION'][0])
                
        try:        
            self.emit(SIGNAL("diffExecute(QString, QString)"),  myRevision1,  myRevision2)   
            self.close()
        except:
            QMessageBox.information(None, 'Message', 'This combination is not implemented yet')
    
    @pyqtSignature("")
    def on_buttonBox_rejected(self):
        self.close()
