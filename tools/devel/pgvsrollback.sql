/***************************************************************************
Function to rollback to a specific pgvs revision
table are still persisting of course.
----------------------------------------------------------------------------
begin		: 2011-07-22
copyright	: (C) 2011 by Dr. Horst Duester
email		: horst.duester@kappasys.ch
		  		
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

CREATE OR REPLACE FUNCTION versions.pgvsrollback(character varying, integer)
  RETURNS boolean AS
$BODY$
  DECLARE
    inTable ALIAS FOR $1;
    myRevision ALIAS FOR $2;
    pos INTEGER;
    mySchema TEXT;
    myTable TEXT;
    versionTable TEXT;
    versionView TEXT;
    versionLogTable TEXT;
    attributes record;
    fields TEXT;
    archiveWhere TEXT;
    myPKeyRec Record;
    myPkey Text;
    deleteQry Text;
    insertQry Text;
    myInsertFields Text;
    

  BEGIN	
    pos := strpos(inTable,'.');
    fields := '';
    myInsertFields := '';
    archiveWhere := '';


    if pos=0 then 
        mySchema := 'public';
  	    myTable := inTable; 
    else 
        mySchema = substr(inTable,0,pos);
        pos := pos + 1; 
        myTable = substr(inTable,pos);
    END IF;  
    
  -- Pruefen ob und welche Spalte der Primarykey der Tabelle ist 
    select into myPkeyRec col.column_name 
    from information_schema.table_constraints as key,
         information_schema.key_column_usage as col
    where key.table_schema = mySchema::name
      and key.table_name = myTable::name
      and key.constraint_type='PRIMARY KEY'
      and key.constraint_name = col.constraint_name
      and key.table_catalog = col.table_catalog
      and key.table_schema = col.table_schema
      and key.table_name = col.table_name;	
  
    myPkey := myPkeyRec.column_name;

    versionTable := mySchema||'.'||myTable||'_version_t';
    versionView := mySchema||'.'||myTable||'_version';
    versionLogTable := 'versions.'||mySchema||'_'||myTable||'_version_log';
    
    for attributes in select *
                               from  information_schema.columns
                               where table_schema=mySchema::name
                                    and table_name = myTable::name

        LOOP
          
          if attributes.column_name not in ('action','project','systime','revision','logmsg','commit') then
            fields := fields||',a."'||attributes.column_name||'"';
            myInsertFields := myInsertFields||',"'||attributes.column_name||'"';
          END IF;

          END LOOP;

-- Das erste Komma  aus dem String entfernen
        fields := substring(fields,2);
        myInsertFields := substring(myInsertFields,2);

        
     deleteQry := 'insert into versions.'||mySchema||'_'||myTable||'_version_log ('||myInsertFields||', action)
                    select '||fields||',''delete'' as action
                    from versions.'||mySchema||'_'||myTable||'_version_log as a inner join 
                      (select '||myPkey||', max(systime) as systime
                                              from versions.'||mySchema||'_'||myTable||'_version_log 
                                              where revision > '||myRevision||'  
                                                 and action = ''insert''
                                                 and commit
                                              group by '||myPkey||') as b 
                       on a.'||myPkey||'=b.'||myPkey||' and a.systime = b.systime
                      where action = ''insert''';        

--RAISE EXCEPTION '%', deleteQry;

      execute deleteQry;
      
     insertQry := 'insert into versions.'||mySchema||'_'||myTable||'_version_log ('||myInsertFields||', action)
                    select '||fields||',''insert'' as action
                    from versions.'||mySchema||'_'||myTable||'_version_log as a inner join 
                      (select '||myPkey||', max(systime) as systime
                                              from versions.'||mySchema||'_'||myTable||'_version_log 
                                              where revision > '||myRevision||'  
                                                 and action = ''delete''
                                                 and commit
                                              group by '||myPkey||') as b 
                       on a.'||myPkey||'=b.'||myPkey||' and a.systime = b.systime
                      where action = ''delete''';    

      execute insertQry;
                  
      execute 'select * from versions.pgvscommit('''||mySchema||'.'||myTable||''',''Rollback to Revision '||myRevision||''')';

  RETURN true ;                             

  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;


