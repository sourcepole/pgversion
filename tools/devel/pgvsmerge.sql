/**************************************************************************
Function to resolve conflicts between objects
----------------------------------------------------------------------------
begin		: 2010-08-17
copyright	: (C) 2010 by Dr. Horst Duester
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
CREATE OR REPLACE FUNCTION versions.pgvsmerge("inTable" character varying, "targetGid" integer, "targetProject" character varying)
  RETURNS boolean AS
$BODY$  DECLARE
    inTable ALIAS FOR $1;
    targetGid ALIAS FOR $2;
    targetProject ALIAS FOR $3;
    mySchema TEXT;
    myTable TEXT;
    myPkey TEXT;
    myDebug TEXT;
    myPkeyRec record;
    conflict BOOLEAN;
    conflictCheck record;
    pos integer;
    versionLogTable TEXT;

  BEGIN	
    pos := strpos(inTable,'.');
    conflict := False;
  
    if pos=0 then 
        mySchema := 'public';
  	    myTable := inTable; 
    else 
        mySchema := substr(inTable,0,pos);
        pos := pos + 1; 
        myTable := substr(inTable,pos);
    END IF;  
    
    versionLogTable := 'versions.'||mySchema||'_'||myTable||'_version_log';   

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
  
    IF FOUND THEN
       myPkey := myPkeyRec.column_name;
    else
        RAISE EXCEPTION 'Table % does not have Primarykey defined', mySchema||'.'||myTable;
        RETURN False;
    END IF;    
        

        
myDebug := 'select a.'||myPkey||' as objectkey, b.systime, b.project as myuser
                                  from '||versionLogTable||' as a,
                                       (
                                         select '||myPkey||', systime, project
                                         from '||versionLogTable||'
                                         where commit
                                           and project <> '''||targetProject||''') as b
                                  where not commit
                                    and a.systime < b.systime
                                    and a.'||myPkey||' = b.'||myPkey||'
                                    and a.'||myPkey||' = '||targetGid||'
                                  union
                                  select '||myPkey||',systime, project
                                  from '||versionLogTable||' as a
                                  where not commit 
                                    and project <> '''||targetProject||'''
                                    and '||myPkey||' = '||targetGid||''; 
                                                                 
-- RAISE EXCEPTION '%',myDebug;    
    
    for conflictCheck IN EXECUTE myDebug
    LOOP
       RAISE NOTICE '%  %',conflictCheck.objectkey,conflictCheck.systime;

      myDebug := 'delete from '||versionLogTable||' 
                     where '||myPkey||' = '||conflictCheck.objectkey||' 
                        and project = '''||conflictCheck.myuser||'''
                        and systime = '||conflictCheck.systime||' ';
-- RAISE EXCEPTION '%', myDebug;                        
      execute myDebug;
                      
    END LOOP; 
  
  RETURN True;
  
  END;$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;
