/***************************************************************************
Function to initialize the pgvs-ebvironment
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

CREATE OR REPLACE FUNCTION versions.pgvsbranch(character varying, character varying)
  RETURNS boolean AS
$BODY$
  DECLARE
    inTable ALIAS FOR $1;
    branch ALIAS FOR $2;
    pos INTEGER;
    mySchema TEXT;
    myTable TEXT;
    versionTable TEXT;
    versionView TEXT;
    versionLogTable TEXT;
    geomCol TEXT;
    geomType TEXT;
    geomDIM INTEGER;
    geomSRID INTEGER;
    attributes record;
    testRec record;
    testPKey record;
    fields TEXT;
    newFields TEXT;
    oldFields TEXT;
    updateFields TEXT;
    mySequence TEXT;
    myPkey TEXT;
    myPkeyRec record;
    testTab TEXT;
    archiveWhere TEXT;
    

  BEGIN	
    pos := strpos(inTable,'.');
    fields := '';
    newFields := '';
    oldFields := '';
    updateFields := '';
    geomCol := '';
    geomDIM := 2;
    geomSRID := -1;
    geomType := '';
    mySequence := '';
    archiveWhere := '';

    if pos=0 then 
        mySchema := 'public';
  	    myTable := inTable; 
    else 
        mySchema = substr(inTable,0,pos);
        pos := pos + 1; 
        myTable = substr(inTable,pos);
    END IF;  

    versionTable := mySchema||'.'||myTable||'_version_t';
    versionView := mySchema||'.'||myTable||'_'||branch;
    versionLogTable := 'versions.'||mySchema||'_'||myTable||'_'||branch||'_log';

-- Feststellen ob die Tabelle oder der View existiert
     select into testRec table_name
     from information_schema.tables
     where table_schema = mySchema::name
          and table_name = myTable::name;

     IF NOT FOUND THEN
       select into testRec table_name
       from information_schema.views
       where table_schema = mySchema::name
            and table_name = myTable::name;     
       IF NOT FOUND THEN
         RAISE EXCEPTION 'Table %.% does not exist', mySchema,myTable;
         RETURN False;
       END IF;
     END IF;    
 
 
-- Die grundlegenden Geometrieparameter des Ausgangslayers ermitteln
     select into testRec f_geometry_column, coord_dimension, srid, type
     from geometry_columns
     where f_table_schema = mySchema::name
       and f_table_name = myTable::name;

     IF NOT FOUND THEN
       RAISE EXCEPTION 'Table %.% is not registered in geometry_columns', mySchema, myTable;
       RETURN False;
     END IF;

     geomCol := testRec.f_geometry_column;
     geomDIM := testRec.coord_dimension;
     geomSRID := testRec.srid;
     geomType := testRec.type;

     
-- Pruefen ob und welche Spalte der Primarykey der Tabelle old_layer ist 
    select into testPKey col.column_name 
    from information_schema.table_constraints as key,
         information_schema.key_column_usage as col
    where key.table_schema = mySchema::name
      and key.table_name = myTable::name
      and key.constraint_type='PRIMARY KEY'
      and key.constraint_name = col.constraint_name
      and key.table_catalog = col.table_catalog
      and key.table_schema = col.table_schema
      and key.table_name = col.table_name;	
  
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Table %.% has no Primarykey', mySchema, myTable;
        RETURN False;
    END IF;			
       
-- Feststellen ob die Tabelle bereits besteht
     testTab := myTable||'_'||branch||'_log';
     select into testRec table_name
     from information_schema.tables
     where table_schema = mySchema::name
          and table_name = testTab::name;

     IF FOUND THEN
       RAISE NOTICE 'Table %.% has been deleted', mySchema,testTab;
       execute 'drop table '||mySchema||'.'||testTab||' cascade';
     END IF;    
  
-- Feststellen ob die Log-Tabelle bereits in geometry_columns registriert ist
     select into testRec f_table_name
     from geometry_columns
     where f_table_schema = mySchema::name
          and f_table_name = testTab::name;
          
     IF FOUND THEN
       execute 'delete from geometry_columns where f_table_schema='''||mySchema||''' and f_table_name='''||myTable||'_'||branch||'_log''';
     END IF;    

-- Feststellen ob der View bereits in geometry_columns registriert ist
     testTab := myTable||'_version';
     select into testRec f_table_name
     from geometry_columns
     where f_table_schema = mySchema::name
          and f_table_name = testTab::name;

     IF FOUND THEN
       execute 'delete from geometry_columns where f_table_schema='''||mySchema||''' and f_table_name='''||myTable||'_'||branch||'''';
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
  
    IF FOUND THEN
       myPkey := myPkeyRec.column_name;
    else
        RAISE EXCEPTION 'Table % has no Primarykey', mySchema||'.'||myTable;
        RETURN False;
    END IF;

    execute 'create table '||versionLogTable||' (LIKE '||inTable||');
             CREATE SEQUENCE '||versionLogTable||'_seq INCREMENT 1 START 1;
             GRANT ALL ON TABLE '||versionLogTable||' TO public;
             GRANT ALL ON TABLE '||versionLogTable||'_seq TO public;
             alter table '||versionLogTable||' add column action character varying;
             alter table '||versionLogTable||' add column project character varying default current_user;     
             alter table '||versionLogTable||' add column systime bigint default (EXTRACT(EPOCH FROM now()::TIMESTAMP)*1000);    
             alter table '||versionLogTable||' add column revision bigint;
             alter table '||versionLogTable||' add column logmsg text;        
             alter table '||versionLogTable||' add column commit boolean DEFAULT False;
             alter table '||versionLogTable||' add column branch character varying default '''||branch||''';
             create index '||myTable||'_'||branch||'_geo_idx on '||versionLogTable||' USING GIST ('||geomCol||');     
             insert into versions.version_tables (version_table_schema,version_table_name,version_view_schema,version_view_name,version_view_pkey,version_view_geometry_column,version_branch) 
                 values('''||mySchema||''','''||myTable||''','''||mySchema||''','''||myTable||'_'||branch||''','''||testPKey.column_name||''','''||geomCol||''', '''||branch||''');
             insert into public.geometry_columns (f_table_catalog, f_table_schema,f_table_name,f_geometry_column,coord_dimension,srid,type)
               values ('''','''||mySchema||''','''||myTable||'_'||branch||''','''||geomCol||''','||geomDIM||','||geomSRID||','''||geomTYPE||''');';
    
    for attributes in select *
                               from  information_schema.columns
                               where table_schema=mySchema::name
                                    and table_name = myTable::name

        LOOP
          
          if attributes.column_default LIKE 'nextval%' then
             execute 'alter table '||versionLogTable||' alter column '||attributes.column_name||' drop not null';
             mySequence := attributes.column_default;
          ELSE
            if myPkey <> attributes.column_name then
              fields := fields||',"'||attributes.column_name||'"';
              newFields := newFields||',new."'||attributes.column_name||'"';
              oldFields := oldFields||',old."'||attributes.column_name||'"';
              updateFields := updateFields||',"'||attributes.column_name||'"=new."'||attributes.column_name||'"';
            END IF;
          END IF;
          IF attributes.column_name = 'archive' THEN
            archiveWhere := 'and archive=0';           
          END IF;  
        END LOOP;

-- Das erste Komma  aus dem String entfernen
        fields := substring(fields,2);
        newFields := substring(newFields,2);
        oldFields := substring(oldFields,2);
        updateFields := substring(updateFields,2);
        
        IF length(mySequence)=0 THEN
          RAISE EXCEPTION 'No Sequence defined for Table %.%', mySchema,myTable;
          RETURN False;
        END IF;

     execute 'alter table '||versionLogTable||' add constraint '||myTable||'_'||branch||'_pkey primary key ('||myPkey||',project,systime,branch) ';  

     execute 'create or replace view '||versionView||' as 
             select * from (
               select '||myPkey||','||fields||' from '||inTable||' where '||myPkey||' not in (select '||myPkey||' from '||versionLogTable||' where project = current_user and not commit) '||archiveWhere||' 
               union 
               select '||myPkey||','||fields||' from '||versionLogTable||' where project = current_user and action <> ''delete'' and systime||''-''||'||myPkey||' in (
                  select max(systime||''-''||'||myPkey||') 
                  from '||versionLogTable||' 
                  where project=current_user 
                    and not commit
                    group by '||myPkey||')
             )as foo;
             GRANT ALL ON TABLE '||versionView||' TO public;';
            
             
    execute 'CREATE OR REPLACE RULE delete AS
                ON DELETE TO '||versionView||' DO INSTEAD  
                INSERT INTO '||versionLogTable||' ('||myPkey||','||fields||',action) VALUES (old.'||myPkey||','||oldFields||',''delete'')';                

       
    execute 'CREATE OR REPLACE RULE insert AS
                ON INSERT TO '||versionView||' DO INSTEAD  
                INSERT INTO '||versionLogTable||' ('||myPkey||','||fields||',action) VALUES ('||mySequence||','||newFields||',''insert'')';
          
     execute 'CREATE OR REPLACE RULE update AS
                ON UPDATE TO '||versionView||' DO INSTEAD  
                INSERT INTO '||versionLogTable||' ('||myPkey||','||fields||',action) VALUES (old.'||myPkey||','||newFields||',''update'')';               


  RETURN true ;                             

  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;

