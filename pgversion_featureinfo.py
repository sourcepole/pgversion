from qgis.gui import QgsMapToolEmitPoint
from dbtools.dbTools import *

class FeatureHistory(QgsMapToolEmitPoint):
    def __init__(self, iface):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        QgsMapToolEmitPoint.__init__(self, self.canvas)

    def canvasPressEvent( self, e ):
        point = self.toMapCoordinates(self.canvas.mouseLastXY())
        self.feature_history(point)
        
        
    def feature_history(self,  point):
        theLayer = self.iface.activeLayer()
        provider = theLayer.dataProvider()
        uri = provider.dataSourceUri()    
        myDb = self.layerDB('feature_info', theLayer)
        my_schema = QgsDataSourceURI(uri).schema()
        my_table = QgsDataSourceURI(uri).table()           
        srid = str.split(str(theLayer.crs().authid()),  ':')[1]
        mapRenderer = self.iface.mapCanvas().mapRenderer()
        canvas_srs=str.split(str(mapRenderer.destinationCrs().authid()),  ':')[1]
        sql = "select * \
          from versions.%s_%s_log\
          where st_distance(%s, st_setsrid(st_geometryFromText('%s'), %s)) = 0"  % ( my_schema,  
                                                                                                                            my_table, 
                                                                                                                            QgsDataSourceURI(uri).geometryColumn(), 
                                                                                                                            point.wellKnownText(),  
                                                                                                                            canvas_srs, 
                                                                                                                            )
        QApplication.setOverrideCursor(Qt.WaitCursor)
        result = myDb.read(sql)
        QApplication.restoreOverrideCursor()
        return result
         
    def layerDB(self, connectionName,  layer):

        myUri = QgsDataSourceURI(layer.source())

        if layer.dataProvider().name() == 'postgres':
      # If username and password are not saved in the DB settings
            if myUri.username() == '':
                connectionInfo = myUri.connectionInfo()
                (success,  user,  password) =  QgsCredentials.instance().get(connectionInfo, None, None)
                QgsCredentials.instance().put( connectionInfo, user, password )
                myUri.setPassword(password)
                myUri.setUsername(user)
    
            try:
                myDb = DbObj(pluginname=connectionName,typ='pg',hostname=myUri.host(),port=myUri.port(),dbname=myUri.database(),username=myUri.username(), passwort=myUri.password())
                return myDb
            except:
                QMessageBox.information(None, self.tr('Error'), self.tr('No Database Connection Established.'))
                return None

        if not self.tools.check_PGVS_revision(myDb):
          return        
