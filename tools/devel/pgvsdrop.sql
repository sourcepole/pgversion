/***************************************************************************
Function to drop an existing pgvs environment. The data from the main 
table are still persisting of course.
----------------------------------------------------------------------------
begin		: 2010-07-31
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

CREATE OR REPLACE FUNCTION versions.pgvsdrop(character varying)
  RETURNS boolean AS
$BODY$
  DECLARE
    inTable ALIAS FOR $1;
    pos INTEGER;
    mySchema TEXT;
    myTable TEXT;
    versionTableRec record;
    versionTable TEXT;
    versionView TEXT;
    versionLogTable TEXT;
    geomCol TEXT;
    geomType TEXT;
    geomDIM INTEGER;
    geomSRID INTEGER;
    testRec record;
    testTab TEXT;
    

  BEGIN	
    pos := strpos(inTable,'.');
    geomCol := '';
    geomDIM := 2;
    geomSRID := -1;
    geomType := '';

    if pos=0 then 
        mySchema := 'public';
  	    myTable := inTable; 
    else 
        mySchema = substr(inTable,0,pos);
        pos := pos + 1; 
        myTable = substr(inTable,pos);
    END IF;  

    versionView := mySchema||'.'||myTable||'_version';
    versionLogTable := 'versions.'||mySchema||'_'||myTable||'_version_log';

-- Feststellen ob die Tabelle existiert
     select into testRec table_name
     from information_schema.tables
     where table_schema = mySchema::name
          and table_name = myTable::name;

     IF NOT FOUND THEN
       RAISE EXCEPTION 'Table %.% does not exist', mySchema,myTable;
       RETURN False;
     END IF;    
     
-- Feststellen ob die Log-Tabelle existiert
     testTab := mySchema||'_'||myTable||'_version_log';
     
     select into testRec table_name
     from information_schema.tables
     where table_schema = 'versions'
          and table_name = testTab::name;

     IF NOT FOUND THEN
       RAISE EXCEPTION 'Log Table %.% does not exist', mySchema,myTable;
       RETURN False;
     END IF;        
 
     
-- Die grundlegenden Geometrieparameter des Ausgangslayers ermitteln
     select into testRec f_geometry_column, coord_dimension, srid, type
     from geometry_columns
     where f_table_schema = mySchema::name
       and f_table_name = myTable::name;

     geomCol := testRec.f_geometry_column;
     geomDIM := testRec.coord_dimension;
     geomSRID := testRec.srid;
     geomType := testRec.type;
     
     execute 'create temp table tmp_tab as 
       select project
       from '||versionLogTable||'
       where not commit ';

     select into testRec project
     from tmp_tab;

     IF FOUND THEN
       RAISE EXCEPTION 'Uncommitted Records are existing. Please commit all changes before use pgvsdrop()';
       RETURN False;
     END IF;  

     select into versionTableRec version_table_id as vtid
     from versions.version_tables as vt
     where version_table_schema = mySchema::name
       and version_table_name = myTable::name;

     

    execute 'DROP SEQUENCE if exists '||versionLogTable||'_seq';
    execute 'drop table if exists '||versionLogTable||' cascade;';
    execute 'drop table if exists '||versionLogTable||'_tmp cascade;';
    
    execute 'delete from versions.version_tables 
               where version_table_id = '''||versionTableRec.vtid||''';';

    execute 'delete from versions.version_tables_logmsg 
               where version_table_id = '''||versionTableRec.vtid||''';';


    execute 'delete from public.geometry_columns 
              where f_table_schema = ''versions''
                and f_table_name = '''||myTable||'_version_log''
                and f_geometry_column = '''||geomCol||'''
                and coord_dimension = '||geomDIM||'
                and srid = '||geomSRID||'
                and type = '''||geomTYPE||''';';
                
    execute 'delete from public.geometry_columns 
               where f_table_schema = '''||mySchema||'''
                 and f_table_name = '''||myTable||'_version''
                 and f_geometry_column = '''||geomCol||'''
                 and coord_dimension = '||geomDIM||'
                 and srid = '||geomSRID||'
                 and type = '''||geomTYPE||''';';

  RETURN true ;                             

  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;  
