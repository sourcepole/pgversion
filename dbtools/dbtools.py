# -*- coding: utf-8 -*-
"""
/***************************************************************************
QGIS DbTools
                             -------------------
begin                : 2013-02-02
copyright            : (C) 2013 by Dr. Horst Duester / Sourcepole AG
email                : horst.duester@sourcepole.ch
 ***************************************************************************/
"""
from PyQt5.QtWidgets import QMessageBox
import subprocess
try:
    import psycopg2
except:
    subprocess.call(['pip3', 'install', 'psycopg2'])
    import psycopg2

import sys


class DbObj:
  MSG_BOX_TITLE = "Class dbObj"
  ## Konstruktor
  # @param pluginname string PlugIn-Name des PlugIns in welchem die DB-Verbindung hergestellt wird (default default)
  # @param typ string Datenbank Typ (default pg)
  # @param service string Connection name defined in pg_service.conf
  # @param hostname string Hostname Name des db Hosts 
  # @param port string Port Name des db Ports (default 5432)
  # @param dbname string dbname Name der DB 
  # @param username string Username Name des users 
  # @param password string Passwort
  def __init__(self,pluginname="default",
                               typ="pg",
                               service=None,  
                               db_file=None,  
                               hostname=None,
                               port=5432,
                               dbname=None,
                               username=None, 
                               password=""):
                
        self.errorDB = ""
        self.errorDriver = ""
        self.service = service
        self.hostName = hostname
        self.databaseName = dbname
        self.userName = username
        self.port = port
        self.password = password
        self.db_file = db_file
        self.pluginName = pluginname
        self.typ = typ
        self.conn = self.connect()

  def connect(self):
# Mit PostgreSQL verbinden
        if self.typ == 'pg':
            try:
                if self.service != None:
                    conn = psycopg2.connect(service=self.service)
                elif self.hostName == None:
                    conn = psycopg2.connect(database=self.databaseName, 
                                                                    port=self.port,  
                                                                    user=self.userName,  
                                                                    password=self.password)
                else:
                    conn = psycopg2.connect(dbname=self.databaseName, 
                                                            host=self.hostName,  
                                                            port=self.port,  
                                                            user=self.userName,  
                                                            password=self.password)   
                
                    
#            except psycopg2.OperationalError as e:
#                self._error_message (e)
#                conn = None
            except:
                self._error_message(sys.exc_info())
                conn = None
            return conn


  ## Lesen des Ergebnisses in ein Dictionary ["FELDNAME"][RecNo]. Jedem Key des Dictionary wird eine list zugeordnet.
  # @param abfrage string gewnschte SQL-Query
  # @return datensatz dictionary  Dictionary ["FELDNAME"][RecNo]
  def read(self, sql,  Message=False):
        datensatz = None
        if self.conn != None:
            try:
                column_names = []
                cursor = self.conn.cursor()
                column_names = self.cols(sql)
                cursor.execute(sql)
                self.conn.commit()
                rows = cursor.fetchall()
                
                if len(rows) > 0:
                    datensatz = {}
                    i = 0
                    
                    for col in column_names:
                        result = []
                        for row in rows:
                            result.append(row[i])
                        i = i + 1
                        datensatz.update({col.upper(): result})
                    cursor.close()  
                return datensatz,  None

            except  psycopg2.ProgrammingError as e:
                self._error_message(e)
                return None,  e
            except psycopg2.InternalError as e:
                self._error_message(e)
                return None,  e
            except psycopg2.DatabaseError as  e:
                self._error_message(e)
                return None,  e                

   # do stuff                

  ## Schliesst die DB-Verbindung
  def close(self):
    self.conn.close()

  ## Ausfuehren einer Query ohne Rckgabeergebnis
  # @param abfrage string gewnschte SQL-Query
  def run(self, sql,  isolated=False):
    try:
        if isolated:
            self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cursor = self.conn.cursor()
        rows = cursor.execute(sql)
        self.conn.commit()
        return True,  None
    except  psycopg2.ProgrammingError as e:
        self._error_message(e)
        return None,  e
    except psycopg2.InternalError as e:
        self._error_message(e)
        return None,  e
    except psycopg2.DatabaseError as  e:
        self._error_message(e)
        return None,  e                       

  ## Gibt die Spalten eines Abfrageergebnisses zurck
  # @param abfrage string gewnschte SQL-Query
  # @return result array 1-Dim Array der Spaltennamen
  def cols(self, abfrage):
    column_names = []
    
    if len(abfrage) > 0:
        sql = abfrage.replace(';', '')+" LIMIT 0;"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        column_names = [desc[0].upper() for desc in cursor.description]
        cursor.close()
        
        return column_names
    else:
        return None

  ## Gibt die Spalten eines Abfrageergebnisses zurck
  # @return result array 2-Dim Array des Abfrageergebnisses
  def resultCols(self,  result):
      pass


  ## Gibt die Datentypen der Spalten eines Abfrageergebnisses zurck
  # @param abfrage string gewnschte SQL-Query
  # @return datensatz dictionary Dictionary ["FELDNAME"][DatenTyp]
#  def colType(self, abfrage):
#
#    sql = abfrage
#    query = QSqlQuery(sql,self.db)
#    query.next()
#    datensatz = {}
#    i = 0
#    while i < query.record().count():
#
#      fieldType = query.record().field(i).type()
#      datensatz.update({str(query.record().fieldName(i)).upper(): query.record().field(i).value().typeToName(fieldType)})
#      i = i + 1
#    return datensatz

  ## Ausfuehren einer Query ohne Rckgabeergebnis aber mit Ausgabe einer Fehlermeldung
  # @param abfrage string gewnschte SQL-Query
  # @return lastError string PostgreSQL Fehlermeldung
  # @todo Momentan liefert lediglich der Driver eine Angabe, ob die Abfrage ausgefhrt wurde oder nicht. Der Datenbanktext wird leider nicht angezeigt.
#  def runError(self, abfrage):
#    driver = self.db.driver()
#    sql = abfrage
#    self.db.exec_(sql)
#    lastError = self.db.lastError().text()
##    if len(lastError) > 1:
##      QMessageBox.information(None, self.tr('DB-Error'),  lastError)
#    return lastError

  ## Ausfuehren einer Query ohne Rckgabeergebnis aber mit Ausgabe einer Notice
  # @param abfrage string gewnschte SQL-Query
  # @return notice string PostgreSQL Notice
  # @todo zur Zeit ist diese Ausgabe nicht mï¿½lich
  def runNotice(self, abfrage):
    pass

  ## Ausfuehren einer Query ohne Rckgabeergebnis aber mit Ausgabe einer Notice
  # @param abfrage string gewnschte SQL-Query
  # @return notice string PostgreSQL Notice
  # @todo zur Zeit ist diese Ausgabe nicht mï¿½lich
  def readNotice(self, abfrage):
    pass

  ## Prueft, ob ein Objekt vom Typ objtyp (table||view) in der Datenbank existiert
  # @param objTyp String (table||view|schema)
  # @param name String  Name des Objektes
  # @return Boolean
  def exists(self, objTyp, name):

        tmp_arr = name.split(".");
        if (len(tmp_arr) == 1) and objTyp != 'schema':
            schema = "public"
        elif (len(tmp_arr) == 2):
            schema = tmp_arr[0]
            name = tmp_arr[1]
        else:
            sql = """
                SELECT exists( 
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = '%s')
              """ % (name)
            result,  error = self.read(sql)
        
        if (objTyp == "table"):
            sql = """
                SELECT exists( 
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = '%s' and table_name = '%s')
                """ % (schema,  name)
                
            result,  error =  self.read(sql)
        elif (objTyp == "view"):
            sql = """
                    SELECT exists( 
                    SELECT view_name 
                    FROM information_schema.views 
                    WHERE view_schema = '%s' and view_name = '%s')
                """ % (schema,  name)
                
            result,  error =  self.read(sql)
        else:
            return
        
        return result['EXISTS'][0]


  def dbConn(self):
      return self.db

  def dbHost(self):
      return self.hostName

  def dbName(self):
      return self.conn.info.dsn_parameters['dbname']

  def dbUser(self):
      return self.conn.info.dsn_parameters['user']

  def setDbUser(self,  userName):
      self.db.setUserName(userName)
      
  def setPassword(self,  password):
      pass

  def dbPort(self):
      return self.conn.info.dsn_parameters['port']

  def dbPasswd(self):
      return self.password

  def connection(self):
      return "dbname="+self.dbName+" host="+self.dbHost+" user="+self.dbUser+" port="+self.dbPort

  def primaryKey(self,  schema,  table):
        sql    = """
                        select col.column_name as pkey 
                        from information_schema.table_constraints as key, 
                                information_schema.key_column_usage as col 
                        where key.table_schema = '%s' 
                            and key.table_name = '%s' 
                            and key.constraint_type='PRIMARY KEY' 
                            and key.table_schema = col.table_schema 
                            and key.table_name = col.table_name
        """ % (schema, table)

        pkey = self.read(sql)

        return pkey['PKEY'][0]
        
#  def _error_message(self, e):
#      print (e)
#      return e
      
  def _error_message(self, e):
        QMessageBox.information(None,'PG: Error',  str(e[1]))
        return None      
