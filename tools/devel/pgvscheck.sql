/***************************************************************************
Function to check conflicts
----------------------------------------------------------------------------
begin		: 2010-09-07
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
DROP FUNCTION IF EXISTS versions.pgvscheck(character varying);
CREATE OR REPLACE FUNCTION versions.pgvscheck(character varying) RETURNS setof versions.conflicts AS
$BODY$

  DECLARE
    inTable ALIAS FOR $1;
    mySchema TEXT;
    myTable TEXT;
    myPkey TEXT;
    message TEXT;
    myDebug TEXT;
    myPkeyRec record;
    conflict BOOLEAN;
    conflictCheck versions.conflicts%rowtype;
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
    END IF;    
    
/*
Check for conflicts before committing. When conflicts are existing stop the commit process 
with a listing of the conflicting objects.
*/    

    message := '';
            
  myDebug := ' select a.'||myPkey||', myproject, mysystime, project, systime 
                         from ( 
                              select '||myPkey||', project as myproject, max(systime) as mysystime
                              from '||versionLogTable||'
                              where not commit 
                                and project = current_user
                              group by '||myPkey||', project
                             ) as a,
                             (
                              select '||myPkey||', project, max(systime) as systime 
                              from '||versionLogTable||'
                              where commit and project <> current_user
                              group by '||myPkey||', project
                             ) as b
                         where b.systime > a.mysystime
                             and a.'||myPkey||' = b.'||myPkey;

--RAISE EXCEPTION '%',myDebug;                                    
                                    
    for conflictCheck IN  EXECUTE myDebug
    LOOP

      return next conflictCheck;
      conflict := True;
      message := message||E'\n'||'WARNING! The object with '||myPkey||'='||conflictCheck.objectkey||' is also changed by user '||conflictCheck.project||'.';
    END LOOP;    
              
    message := message||E'\n\n';
    message := message||'Changes are not committed!'||E'\n\n';
    IF conflict THEN
       RAISE NOTICE '%', message;
    ELSE    
       return;    
  END IF;    

  END;


$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;

