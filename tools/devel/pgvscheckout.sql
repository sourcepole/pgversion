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
CREATE OR REPLACE FUNCTION versions.pgvscheckout(character varying, integer)
  RETURNS setof versions.checkout AS
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
    fieldsWhere TEXT;
    archiveWhere TEXT;
    myPKeyRec Record;
    myPkey Text;
    checkoutQry TEXT;
    checkoutRec versions.checkout%rowtype;
    geomCol TEXT;
    testRec Record;
    

  BEGIN	
    pos := strpos(inTable,'.');
    fields := '';
    archiveWhere := '';
    fieldsWhere := '';


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
    
    -- Die grundlegenden Geometrieparameter des Ausgangslayers ermitteln
     select into testRec f_geometry_column, coord_dimension, srid, type
     from geometry_columns
     where f_table_schema = mySchema::name
       and f_table_name = myTable::name;

     geomCol := testRec.f_geometry_column;


    versionTable := mySchema||'.'||myTable||'_version_t';
    versionView := mySchema||'.'||myTable||'_version';
    versionLogTable := 'versions.'||mySchema||'_'||myTable||'_version_log';
    
    for attributes in select *
                               from  information_schema.columns
                               where table_schema=mySchema::name
                                    and table_name = myTable::name

        LOOP
          
          fields := fields||',"'||attributes.column_name||'"';
          
          if attributes.column_name <> geomCol then
            fieldsWhere := fieldsWhere||' or log.'||attributes.column_name||' = main.'||attributes.column_name;
          END IF;

        END LOOP;

-- Das erste Komma  aus dem String entfernen
        fields := substring(fields,2);
    
    
        checkoutQry := 'select log.'||myPkey||', log.action, log.revision, log.systime
                                  from versions.'||mySchema||'_'||myTable||'_version_log as log, '||myTable||' as main
                                  where log.revision > '||myRevision||'
                                    and 
                                     (st_equals(log.'||geomCol||',main.'||geomCol||')
                                      '||fieldsWhere||')
                                  order by revision,action desc';
                                  
        for checkoutRec in EXECUTE checkoutQry loop
          RETURN Next checkoutRec;                             
        end loop;
   return;                      
    
/*    
     execute 'delete from '||mySchema||'.'||myTable||' where '||myPKey||' in (select '||myPKey||' from versions.'||mySchema||'_'||myTable||'_version_log where revision > '||myRevision||' and action = ''insert'')';
     execute 'insert into '||mySchema||'.'||myTable||' select '||fields||'  from versions.'||mySchema||'_'||myTable||'_version_log  where revision = '||myRevision||' and action = ''delete''';
     execute 'delete from versions.'||mySchema||'_'||myTable||'_version_log where revision > '||myRevision;                    
*/               
  

  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;


