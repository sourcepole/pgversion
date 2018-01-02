# -*- coding: utf-8 -*-
"""
/***************************************************************************
QGISLayer
                             -------------------
begin                : 2013-02-02
copyright            : (C) 2013 by Dr. Horst Duester / Sourcepole AG
email                : horst.duester@sourcepole.ch
 ***************************************************************************/
"""
from PyQt4.QtGui import QDialog, QMessageBox
from PyQt4.QtSql import QSqlDatabase, QSqlQuery

class DbObj(QDialog):
  MSG_BOX_TITLE = "Class dbObj"
  ## Konstruktor 
  # @param pluginname string PlugIn-Name des PlugIns in welchem die DB-Verbindung hergestellt wird (default default)
  # @param typ string Datenbank Typ (pg||oracle) (default pg)
  # @param hostname string Hostname Name des db Hosts (default srsofaioi4531)
  # @param port string Port Name des db Ports (default 5432)
  # @param dbname string dbname Name der DB (default None)
  # @param username string Username Name des users (default mspublic)
  # @param passwort string Passwort
  def __init__(self,pluginname="default",typ="pg", hostname=None,port=None,dbname=None,username=None, passwort=""):
      
    QDialog.__init__(self)
    self.errorDB = ""
    self.errorDriver = ""
    self.hostName = hostname
    self.databaseName = dbname
    self.userName = username
    self.port = port
    self.passwort = passwort
    self.pluginName = pluginname
    self.typ = typ

# Mit SQLite verbinden
    if typ == "sqlite":
      self.db =  QSqlDatabase.addDatabase("QSQLITE")
      self.db.setDatabaseName(self.hostName)
      self.db.open()        
      
    else:
        
    # Mit PostgreSQL verbinden
        if typ == "pg":
            self.db = QSqlDatabase.addDatabase("QPSQL",pluginname)
            self.db.setHostName(hostname)
            self.db.setDatabaseName(dbname)
            self.db.setUserName(username)
            self.db.setPassword(passwort)
            self.db.setPort(int(port))
                
    # Mit Oracle verbinden
        if typ == "oracle":
            self.db = QSqlDatabase.addDatabase("QOCI")
            self.db.setHostName(hostname)
            self.db.setDatabaseName(dbname)
            self.db.setUserName(username)
            self.db.setPassword(passwort)
            self.db.setPort(int(port))
    
    # Mit MySQL Datenbank verbinden
        if typ == "mysql":
            self.db = QSqlDatabase.addDatabase("QMYSQL")        
            self.db.setHostName(hostname)
            self.db.setDatabaseName(dbname)
            self.db.setUserName(username)
            self.db.setPassword(passwort)
            self.db.setPort(int(port))
    
    # Mit ODBC Datenbank verbinden      
        if typ == "odbc":
            self.db = QSqlDatabase.addDatabase("QODBC")
            self.db.setDatabaseName(hostname)

        self.db.open()


# Wenn Fehler bei der DB-Verbindung
    if self.db.open() == False:
      self.errorDriver = str(self.db.lastError().driverText())
      QMessageBox.warning(None, self.MSG_BOX_TITLE, (self.tr("Error:' {0}.' The connection to the database could not be established! Some functions of the PlugIn {1} may not work!").format(self.errorDriver,  pluginname)), QMessageBox.Ok, QMessageBox.Ok)
      
  ## Rckgabe des QSqlDatabase Objektes
  # @return self.db QSqlDatabase
  def dbObj(self):
    return self.db
  
  
  def __pystring(self,  qvar):
    return unicode(qvar.toString()) if hasattr(qvar, 'toString') else unicode(qvar)
    
    
  ## Lesen des Ergebnisses in ein Dictionary ["FELDNAME"][RecNo]. Jedem Key des Dictionary wird eine list zugeordnet.
  # @param abfrage string gewnschte SQL-Query
  # @return datensatz dictionary  Dictionary ["FELDNAME"][RecNo]
  def read(self, abfrage):
    sql = abfrage
    
    query = QSqlQuery(sql,self.db)
    datensatz = {}
    i = 0
    while i < query.record().count():
      result = []
      query.first()
      result.append(self.__pystring(query.value(i)))
      lastError = query.lastError().text()
      if len(lastError) > 1:
        QMessageBox.information(None, self.tr('DB-Error'),  lastError)      

      while query.next():
        result.append(self.__pystring(query.value(i)))
        lastError = query.lastError().text()
        if len(lastError) > 1:
          QMessageBox.information(None, self.tr('DB-Error'),  lastError)      

      datensatz.update({str(query.record().fieldName(i)).upper(): result})
      i = i + 1
    return datensatz

  ## Schliesst die DB-Verbindung
  def close(self):
    self.db.close()

  ## Ausfuehren einer Query ohne Rckgabeergebnis
  # @param abfrage string gewnschte SQL-Query
  def run(self, abfrage):
    sql = abfrage
    self.db.exec_(sql)
    lastError = self.db.lastError().text()
    if len(lastError) > 1:
      QMessageBox.information(None, self.tr('DB-Error'),  lastError)
    return lastError    

  ## Gibt die Spalten eines Abfrageergebnisses zurck
  # @param abfrage string gewnschte SQL-Query
  # @return result array 1-Dim Array der Spaltennamen
  def cols(self, abfrage):
    
    sql = abfrage
    query = QSqlQuery(sql,self.db)
    query.next()
    result = []
    i = 0
    while i < query.record().count():
      
      result.append(str(query.record().fieldName(i)))
      i = i + 1
    return result

  ## Gibt die Spalten eines Abfrageergebnisses zurck
  # @return result array 2-Dim Array des Abfrageergebnisses
  def resultCols(self,  result):
      pass
      
      
  ## Gibt die Datentypen der Spalten eines Abfrageergebnisses zurck
  # @param abfrage string gewnschte SQL-Query
  # @return datensatz dictionary Dictionary ["FELDNAME"][DatenTyp]
  def colType(self, abfrage):
    
    sql = abfrage
    query = QSqlQuery(sql,self.db)
    query.next()
    datensatz = {}
    i = 0
    while i < query.record().count():
      
      fieldType = query.record().field(i).type()
      datensatz.update({str(query.record().fieldName(i)).upper(): query.record().field(i).value().typeToName(fieldType)})
      i = i + 1
    return datensatz

  ## Ausfuehren einer Query ohne Rckgabeergebnis aber mit Ausgabe einer Fehlermeldung
  # @param abfrage string gewnschte SQL-Query
  # @return lastError string PostgreSQL Fehlermeldung
  # @todo Momentan liefert lediglich der Driver eine Angabe, ob die Abfrage ausgefhrt wurde oder nicht. Der Datenbanktext wird leider nicht angezeigt.
  def runError(self, abfrage):
    driver = self.db.driver()
    sql = abfrage
    self.db.exec_(sql)
    lastError = self.db.lastError().text()
    if len(lastError) > 1:
      QMessageBox.information(None, self.tr('DB-Error'),  lastError)
    return lastError

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
  # @param objTyp String (table||view)
  # @param name String  Name des Objektes
  # @return Boolean
  def exists(self, objTyp, name):

    tmp_arr = name.split(".");
    if (len(tmp_arr) == 1):
      schema = "public"
    elif (len(tmp_arr) == 2):
      schema = tmp_arr[0]
      name = tmp_arr[1]


    if self.typ == 'pg':    
      if (objTyp == "table"):
        objTyp = "BASE TABLE"
      elif (objTyp == "view"):
        objTyp = "VIEW"
      else:
        QMessageBox.warning(None, self.tr("Error"), self.tr("Only objects table or view can be checked"), QMessageBox.Ok, QMessageBox.Ok)
        return
      abfrage = "select count(table_name) as count from information_schema.tables where table_schema='"+schema+"' and table_name='"+name+"' and table_type='"+objTyp+"'"
      result = self.read(abfrage)
      
      try:
          if (result["COUNT"][0] == '0'):
            return False
          else:
            return True
      except:
          return False
          
    elif self.typ == 'sqlite':
      abfrage = "SELECT count(*) as count FROM sqlite_master WHERE type='"+objTyp+"' AND name='"+name+"'"
      result = self.read(abfrage)
      if (result["COUNT"][0] == '0'):
        return False
      else:
        return True

    else:
      QMessageBox.warning(None, self.tr("Error"), self.tr("This method is not supported by the connected DB-System"), QMessageBox.Ok, QMessageBox.Ok)
      return False
      
    
  def dbHost(self):
      return self.hostName
      
  def dbName(self):
      return self.databaseName
  
  def dbUser(self):
      return self.userName
      
  def setDbUser(self,  userName):
      self.db.setUserName(userName)
      
  def dbPort(self):
      return self.port
      
  def dbPasswd(self):
      return self.passwort
      
  def isOpen(self):
      if self.db.isOpen():
          return True
      else:
          return False

  def connection(self):
      return "dbname="+self.databaseName+" host="+self.hostName+" user="+self.userName+" port="+self.port

  def primaryKey(self,  schema,  table):
        sql    = "select col.column_name as pkey "
        sql += "from information_schema.table_constraints as key, "
        sql += "     information_schema.key_column_usage as col "
        sql += "where key.table_schema = \'"+schema+"\' "
        sql += "  and key.table_name = \'"+table+"\' "
        sql += "  and key.constraint_type=\'PRIMARY KEY\' "
        sql +="  and key.table_schema = col.table_schema "
        sql +="  and key.table_name = col.table_name"
        
        pkey = self.read(sql)

        return pkey['PKEY'][0]
            
