
/***************************************************************************
Temporary Function to check the update-conditions
and make all nesseccary updates to get the actual
system state. 
----------------------------------------------------------------------------
begin		: 2010-11-27
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
CREATE OR REPLACE FUNCTION versions._pgvscreateversiontable()
  RETURNS void AS
$BODY$    
  
  BEGIN
    execute 'CREATE TABLE if not exists versions.version_tables
           (
              version_table_id serial,
              version_table_schema character varying,
              version_table_name character varying,
              version_view_schema character varying,
              version_view_name character varying,
              version_view_pkey character varying,
              version_view_geometry_column character varying,
              CONSTRAINT version_table_pkey PRIMARY KEY (version_table_id)
            )';
    execute 'GRANT SELECT ON TABLE versions.version_tables TO public';

    execute 'CREATE TABLE if not exists versions.version_tables_logmsg
           (
              logmsg_id bigserial NOT NULL,
              version_table_id bigint NOT NULL,
              project character varying NOT NULL DEFAULT "current_user"(),
              systime bigint NOT NULL DEFAULT (date_part(''epoch''::text, (now())::timestamp without time zone) * (1000)::double precision),
              revision bigint NOT NULL,
              logmsg text,
              CONSTRAINT version_table_logmsg_pkey PRIMARY KEY (logmsg_id)
           )
           WITH (
              OIDS=FALSE
           )';
    execute 'GRANT SELECT ON TABLE versions.version_tables_logmsg TO public';

    EXCEPTION when others then
  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;  
  
  
CREATE OR REPLACE FUNCTION versions._pgvscreateconflicttype()
  RETURNS void AS
$BODY$    
  
  BEGIN
    execute 'create type versions.conflicts as (objectkey int, myproject text, mysystime bigint, project text, systime bigint)';
    EXCEPTION when others then
  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;  

CREATE OR REPLACE FUNCTION versions._pgvscreatelogviewtype()
  RETURNS void AS
$BODY$    
  
  BEGIN
    execute 'create type versions.logview as (revision integer, datum timestamp, project text, logmsg text)';
    EXCEPTION when others then
  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;    
  
CREATE OR REPLACE FUNCTION versions._pgvscheckouttype()
  RETURNS void AS
$BODY$    
  
  BEGIN
    execute 'create type versions.checkout as (mykey int, action varchar, revision int, systime bigint)';
    EXCEPTION when others then
  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;        
  
  select versions._pgvscreateversiontable();
  select versions._pgvscreateconflicttype();
  select versions._pgvscreatelogviewtype();
  select versions._pgvscheckouttype();

  
  
create or replace function versions._update07()
  Returns void as
$BODY$
Declare 
  myRec Record;
  attributes Record;
  tables Record;
  fields Text;
  newFields Text;
  oldFields Text;
  mySchema Text;
  myTable Text;
  myPkey Text;
  myPkeyRec Record;
  pos integer;
  branchExists boolean;

Begin

          
      -- in allen log-Tabellen den Primarykey anpassen
          for tables in select version_table_schema, version_table_name, version_view_pkey
                              from  versions.version_tables

          LOOP       
            
           mySchema := tables.version_table_schema;
           myTable := tables.version_table_name;
           
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
           RETURN;
       END IF;  

     RAISE NOTICE 'Das ist der PKEY: % der Tabelle %.%', myPkey,tables.version_table_schema,tables.version_table_name;  
  
           execute 'ALTER TABLE versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log DROP CONSTRAINT '||tables.version_table_name||'_pkey';
           execute 'alter table versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log add constraint '||tables.version_table_name||'_pkey primary key ('||tables.version_view_pkey||',project,systime,"action") ';  
           
          fields := '';
          newFields := '';
          oldFields := '';            
    -- die neuen Rules der Views erzeugen
           for attributes in select *
                                from  information_schema.columns
                                where table_schema=mySchema::name
                                    and table_name = myTable::name
                                    and column_name <> tables.version_view_pkey::name

            LOOP        
                if attributes.column_name = 'branch' then 
                  branchExists := true;
                end if;
                fields := fields||'"'||attributes.column_name||'",';
                newFields := newFields||'new."'||attributes.column_name||'",';
                oldFields := oldFields||'old."'||attributes.column_name||'",';
            END LOOP;

-- Das erste Komma  aus dem String entfernen
            fields := substr(fields,0,length(fields));
            newFields := substr(newFields,0,length(newFields));
            oldFields := substr(oldFields,0,length(oldFields));
            
            execute 'drop table if exists versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log_tmp cascade;';
            
            execute 'create table versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log_tmp (LIKE versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log);
             alter table versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log_tmp alter project set default current_user;     
             alter table versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log_tmp alter systime set default (EXTRACT(EPOCH FROM now()::TIMESTAMP)*1000);    
             alter table versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log_tmp alter commit set DEFAULT False;';
             
             if branchExists then
               execute 'alter table versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log_tmp drop branch;';
               execute 'alter table versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log drop branch;';
        end if;
            
             
            execute 'drop rule if exists update on '||tables.version_table_schema||'.'||tables.version_table_name||'_version';
            execute 'CREATE OR REPLACE RULE update_1 AS ON UPDATE TO '||tables.version_table_schema||'.'||tables.version_table_name||'_version DO INSTEAD INSERT INTO versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log ('||tables.version_view_pkey||','||fields||',action) VALUES (old.'||tables.version_view_pkey||','||newFields||',''insert''::character varying)';
            execute 'CREATE OR REPLACE RULE update_2 AS ON UPDATE TO '||tables.version_table_schema||'.'||tables.version_table_name||'_version DO INSTEAD INSERT INTO versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log ('||tables.version_view_pkey||','||fields||',action) VALUES (old.'||tables.version_view_pkey||','||oldFields||',''delete'')';      
            execute 'DROP RULE update_1 on '||tables.version_table_schema||'.'||tables.version_table_name||'_version';
            execute 'DROP RULE update_2 on '||tables.version_table_schema||'.'||tables.version_table_name||'_version';

            execute 'CREATE OR REPLACE RULE update AS
                ON UPDATE TO '||tables.version_table_schema||'.'||tables.version_table_name||'_version DO INSTEAD  
                (INSERT INTO versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log_tmp ('||myPkey||','||fields||',action) VALUES (old.'||myPkey||','||oldFields||',''delete'');               
                 INSERT INTO versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log_tmp ('||myPkey||','||fields||',action) VALUES (old.'||myPkey||','||newFields||',''insert'');
                 insert into versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log('||myPkey||','||fields||',action) select '||myPkey||','||fields||',action from versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log_tmp;
                 delete from versions.'||tables.version_table_schema||'_'||tables.version_table_name||'_version_log_tmp)';             
        END LOOP;  

End;  

$BODY$
LANGUAGE 'plpgsql' VOLATILE
COST 100;    
  
 
DROP FUNCTION IF EXISTS versions.pgvsupdatecheck(character varying);
CREATE OR REPLACE FUNCTION versions.pgvsupdatecheck(character varying)
  RETURNS boolean AS
$BODY$    
DECLARE
  inRevision ALIAS FOR $1;
  aktRevision TEXT;
  inMajor integer;
  inMinor integer;
  aktMajor integer;
  aktMinor integer;

  
  BEGIN	
      inMajor = to_number(substr(inRevision,1,1),'9');
      inMinor = to_number(substr(inRevision,3,1),'9');
      aktMajor = to_number(substr(versions.pgvsrevision(),1,1),'9');
      aktMinor = to_number(substr(versions.pgvsrevision(),3,1),'9');
      
      if aktMinor>=7 and inMinor<7 THEN
        execute 'select versions._update07()';
        return False;
      ELSE
        return True;
      END IF;
      
  RETURN revision ;                             

  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;  

  
