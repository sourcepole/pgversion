-- Database diff generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler  version: 0.9.1-alpha
-- PostgreSQL version: 9.4

-- [ Diff summary ]
-- Dropped objects: 2
-- Created objects: 6
-- Changed objects: 5
-- Truncated tables: 0

SET check_function_bodies = false;
-- ddl-end --

SET search_path=public,pg_catalog,versions;
-- ddl-end --


-- [ Dropped objects ] --
ALTER TABLE versions.version_tags DROP CONSTRAINT IF EXISTS version_tables_fk CASCADE;
-- ddl-end --
ALTER TABLE versions.version_tags DROP CONSTRAINT IF EXISTS version_tags_pkey CASCADE;
-- ddl-end --


-- [ Created objects ] --
-- object: versions._hasserial | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions._hasserial(IN character varying) CASCADE;

-- Prepended SQL commands --
drop function IF EXISTS versions._hasserial(IN character varying);
-- ddl-end --

CREATE FUNCTION versions._hasserial (IN in_table character varying)
	RETURNS boolean
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	COST 1
	AS $$
DECLARE
  qry TEXT;
  pos INTEGER;
  my_schema TEXT;
  my_table TEXT;
  my_serial_rec RECORD;


BEGIN
    pos := strpos(in_table,'.');
  
    if pos=0 then 
      my_schema := 'public';
  	  my_table := in_table; 
    else 
        my_schema := substr(in_table,0,pos);
        pos := pos + 1; 
        my_table := substr(in_table,pos);
    END IF;  

  -- Check if SERIAL exists and which column represents it 
    select into my_serial_rec column_name as att, 
               data_type as typ, column_default
    from information_schema.columns as col
    where table_schema = my_schema::name
      and table_name = my_table::name
      and (position('nextval' in lower(column_default)) is NOT NULL 
      or position('nextval' in lower(column_default)) <> 0);	
  
    IF FOUND THEN
       RETURN 'true';
    else
       RAISE EXCEPTION 'Table %.% does not has a serial defined', my_schema, my_table;
    END IF;
END;
$$;
-- ddl-end --
ALTER FUNCTION versions._hasserial(IN character varying) OWNER TO versions;
-- ddl-end --

-- object: versions.version_branch | type: TABLE --
-- DROP TABLE IF EXISTS versions.version_branch CASCADE;
CREATE TABLE versions.version_branch(
	branch_id bigserial NOT NULL,
	version_table_id bigint NOT NULL,
	branch_text character varying NOT NULL,
	CONSTRAINT version_tags_pkey_1 PRIMARY KEY (branch_id,version_table_id,branch_text)

);
-- ddl-end --
ALTER TABLE versions.version_branch OWNER TO versions;
-- ddl-end --

-- object: versions.pgvsmakebranch | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsmakebranch(IN character varying,IN varchar) CASCADE;

-- Prepended SQL commands --
drop function IF EXISTS versions.pgvsmakebranch(IN character varying,IN varchar)
-- ddl-end --

CREATE FUNCTION versions.pgvsmakebranch (IN in_table character varying, IN branch_name varchar)
	RETURNS bigint
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	COST 100
	AS $$

  DECLARE
    mySchema TEXT;
    myTable TEXT;
    myPkey TEXT;
    pos integer;
    versionLogTable TEXT;

  BEGIN	
    pos := strpos(in_table,'.');
  
    if pos=0 then 
        mySchema := 'public';
  	    myTable := in_table; 
    else 
        mySchema := substr(in_table,0,pos);
        pos := pos + 1; 
        myTable := substr(in_table,pos);
    END IF;  
    
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');   

    execute format('INSERT INTO versions.version_branch(version_table_id, revision, branch_text) 
                      SELECT version_table_id, 0 as revision, ''%3$s'' as branch_text 
                      FROM versions.version_tables 
                      where version_table_schema = ''%1$s'' 
                        and version_table_name = ''%2$s''', mySchema, myTable, branch_name); 

  
    RETURN (select last_value from versions.version_branch_branch_id_seq);
  
  END;

$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsmakebranch(IN character varying,IN varchar) OWNER TO versions;
-- ddl-end --



-- [ Changed objects ] --
-- object: versions.pgvsinit | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsinit(character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvsinit ( _param1 character varying)
	RETURNS boolean
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	COST 100
	AS $$
  DECLARE
    inTable ALIAS FOR $1;
    pos INTEGER;
    mySchema TEXT;
    myTable TEXT;
    versionTable TEXT;
    versionView TEXT;
    versionLogTable TEXT;
    versionLogTableType TEXT;
    versionLogTableSeq TEXT;
    versionLogTableTmp TEXT;
    geomCol TEXT;
    geomType TEXT;
    geomDIM INTEGER;
    geomSRID INTEGER;
    attributes record;
    testRec record;
    testPKey record;
    fields TEXT;
    type_fields TEXT;
    newFields TEXT;
    oldFields TEXT;
    updateFields TEXT;
    mySequence TEXT;
    myPkey TEXT;
    myPkeyRec record;
    testTab TEXT;
    archiveWhere TEXT;
    sql TEXT;   
    last_value BIGINT; 
    

  BEGIN	
    pos := strpos(inTable,'.');
    fields := '';
    type_fields := '';
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

    execute 'select * from versions._hasserial('''||mySchema||'.'||myTable||''')';

    versionTable := quote_ident(mySchema||'.'||myTable||'_version_t');
    versionView := quote_ident(mySchema)||'.'||quote_ident(myTable||'_version');
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');
    versionLogTableSeq := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log_version_log_id_seq');
    versionLogTableTmp := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log_tmp');

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
		
       
-- Feststellen ob die Tabelle bereits besteht
     testTab := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');
     select into testRec table_name
     from information_schema.tables
     where table_schema = mySchema::name
          and table_name = testTab::name;

     IF FOUND THEN
       RAISE NOTICE 'Table versions.% has been deleted', testTab;
       execute 'drop table '||quote_ident(mySchema)||'.'||quote_ident(testTab)||' cascade';
     END IF;    
  
     
  -- Pruefen ob und welche Spalte der Primarykey der Tabelle ist 
    select into myPkeyRec * from versions._primarykey(inTable);    
    myPkey := quote_ident(myPkeyRec.pkey_column);

    sql := format('select max(%1$s) FROM %2$s.%3$s', myPkey, quote_ident(mySchema), quote_ident(myTable));
    execute sql into testRec;
    

    sql := 'create table '||versionLogTable||' (LIKE '||quote_ident(mySchema)||'.'||quote_ident(myTable)||');
	    ALTER TABLE '||versionLogTable||' OWNER TO versions;
             create sequence versions.'||quote_ident(mySchema||'_'||myTable||'_revision_seq')||' INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;
             alter sequence versions.'||quote_ident(mySchema||'_'||myTable||'_revision_seq')||' owner to versions;
             create sequence versions.'||quote_ident(mySchema||'_'||myTable||'_version_log'||'_'||myPkey||'_seq')||' INCREMENT 1 MINVALUE '||testRec.max||' MAXVALUE 9223372036854775807 START '||testRec.max+1||' CACHE 1;
             alter sequence versions.'||quote_ident(mySchema||'_'||myTable||'_version_log'||'_'||myPkey||'_seq')||' owner to versions;
             alter table '||versionLogTable||' ALTER COLUMN '||myPkey||' SET DEFAULT nextval(''versions.'||quote_ident(mySchema||'_'||myTable||'_version_log_'||myPkey||'_seq')||''');
             alter table '||versionLogTable||' add column version_log_id bigserial;
             alter table '||versionLogTable||' add column action character varying;
             alter table '||versionLogTable||' add column project character varying default current_user;     
             alter table '||versionLogTable||' add column systime bigint default extract(epoch from now()::timestamp)*1000;    
             alter table '||versionLogTable||' add column revision bigint;
             alter table '||versionLogTable||' add column parent_branch bigint;
             alter table '||versionLogTable||' add column child_branch bigint;
             alter table '||versionLogTable||' add column logmsg text;        
             alter table '||versionLogTable||' add column commit boolean DEFAULT False;
             alter table '||versionLogTable||' add constraint '||myTable||'_pkey primary key ('||myPkey||',project,systime,action);

             CREATE INDEX '||quote_ident(mySchema||'_'||myTable||'_version_log_id_idx') ||' ON '||versionLogTable||' USING btree (version_log_id) where not commit;
             CREATE INDEX '||quote_ident(mySchema||'_'||myTable||'_systime_idx') ||' ON '||versionLogTable||' USING btree (systime) where not commit;
             CREATE INDEX '||quote_ident(mySchema||'_'||myTable||'_project_idx') ||' ON '||versionLogTable||' USING btree (project) where not commit;
             create index '||quote_ident(mySchema||'_'||myTable||'_version_geo_idx') ||' on '||versionLogTable||' USING GIST ('||geomCol||') where not commit;     
             
             insert into versions.version_tables (version_table_schema,version_table_name,version_view_schema,version_view_name,version_view_pkey,version_view_geometry_column) 
                 values('''||mySchema||''','''||myTable||''','''||mySchema||''','''||myTable||'_version'','''||myPkey||''','''||geomCol||''');';
    --RAISE EXCEPTION '%', sql;
    EXECUTE sql;
                 
    for attributes in select *
                      from  information_schema.columns
                      where table_schema=mySchema::name
                        and table_name = myTable::name

        LOOP
          
          if attributes.column_default LIKE 'nextval%' then
             mySequence := attributes.column_default;
          ELSE
            if myPkey <> attributes.column_name then
              fields := fields||','||quote_ident(attributes.column_name);
              type_fields := type_fields||','||quote_ident(attributes.column_name)||' '||attributes.udt_name||'';              
              newFields := newFields||',new.'||quote_ident(attributes.column_name);
              oldFields := oldFields||',old.'||quote_ident(attributes.column_name);
              updateFields := updateFields||','||quote_ident(attributes.column_name)||'=new.'||quote_ident(attributes.column_name);
            END IF;
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
     


            
     execute 'create or replace view '||versionView||' as 
                SELECT v.'||myPkey||', '||fields||'
                FROM '||quote_ident(mySchema)||'.'||quote_ident(myTable)||' v,
                  ( SELECT '||quote_ident(mySchema)||'.'||quote_ident(myTable)||'.'||myPkey||'
                    FROM '||quote_ident(mySchema)||'.'||quote_ident(myTable)||'
                    EXCEPT
                    SELECT v_1.'||myPkey||'
                    FROM '||versionLogTable||' v_1,
                     ( SELECT v_2.'||myPkey||',
                              max(v_2.version_log_id) AS version_log_id, min(action) as action
                       FROM '||versionLogTable||' v_2
                       WHERE NOT v_2.commit AND v_2.project::name = "current_user"()
                       GROUP BY v_2.'||myPkey||') foo_1
                    WHERE v_1.version_log_id = foo_1.version_log_id) foo
                WHERE v.'||myPkey||' = foo.'||myPkey||'
                UNION
                SELECT v.'||myPkey||', '||fields||'
                FROM '||versionLogTable||' v,
                 ( SELECT v_1.'||myPkey||',
                          max(v_1.version_log_id) AS version_log_id, min(action) as action
                   FROM '||versionLogTable||' v_1
                   WHERE NOT v_1.commit AND v_1.project::name = "current_user"()
                   GROUP BY v_1.'||myPkey||') foo
                WHERE v.version_log_id = foo.version_log_id and foo.action <> ''delete''';

     execute 'ALTER VIEW '||versionView||' owner to versions';


     execute 'CREATE TRIGGER pgvs_version_record_trigger
              INSTEAD OF INSERT OR UPDATE OR DELETE
              ON '||versionView||'
              FOR EACH ROW
              EXECUTE PROCEDURE versions.pgvs_version_record();';                

     execute 'INSERT INTO '||versionLogTable||' ('||myPkey||','||fields||', action, revision, logmsg, commit ) 
                select '||myPkey||','||fields||', ''insert'' as action, 0 as revision, ''initial commit revision 0'' as logmsg, ''t'' as commit 
                from '||quote_ident(mySchema)||'.'||quote_ident(myTable);                          

     execute format('INSERT INTO versions.version_tables_logmsg(
                version_table_id, revision, logmsg) 
              SELECT version_table_id, 0 as revision, ''initial commit revision 0'' as logmsg FROM versions.version_tables where version_table_schema = ''%1$s'' and version_table_name = ''%2$s''', mySchema, myTable); 

     execute format('INSERT INTO versions.version_tags(
                version_table_id, revision, tag_text) 
              SELECT version_table_id, 0 as revision, ''initial commit revision 0'' as tag_text FROM versions.version_tables where version_table_schema = ''%1$s'' and version_table_name = ''%2$s''', mySchema, myTable); 

     execute format('INSERT INTO versions.version_branch(
                version_table_id, branch_text) 
              SELECT version_table_id, ''master'' as branch_text FROM versions.version_tables where version_table_schema = ''%1$s'' and version_table_name = ''%2$s''', mySchema, myTable); 

     execute format('update %1$s set parent_branch = CURRVAL(''versions.version_branch_branch_id_seq'')',versionLogTable);
     execute format('update %1$s set child_branch = CURRVAL(''versions.version_branch_branch_id_seq'')',versionLogTable);

                
  RETURN true ;                             

  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsinit(character varying) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvsrevision | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsrevision() CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvsrevision ()
	RETURNS text
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	COST 100
	AS $$

    
DECLARE
  revision TEXT;
  BEGIN	
    revision := '218';
  RETURN revision ;                             

  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsrevision() OWNER TO versions;
-- ddl-end --

-- object: versions.pgvsrollback | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsrollback(character varying,integer) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvsrollback ( _param1 character varying,  _param2 integer)
	RETURNS boolean
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	COST 100
	AS $$


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
    rollbackQry Text;
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
    select into myPkeyRec * from versions._primarykey(inTable);    
    myPkey := quote_ident(myPkeyRec.pkey_column);

    versionTable := quote_ident(mySchema)||'.'||quote_ident(myTable||'_version_t');
    versionView := quote_ident(mySchema)||'.'||quote_ident(myTable||'_version');
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');
    
    for attributes in select *
                               from  information_schema.columns
                               where table_schema=mySchema::name
                                    and table_name = myTable::name

        LOOP
          
          if attributes.column_name not in ('action','project','systime','revision','logmsg','commit') then
            fields := fields||',v.'||quote_ident(attributes.column_name);
            myInsertFields := myInsertFields||','||quote_ident(attributes.column_name);
          END IF;

          END LOOP;

-- Das erste Komma  aus dem String entfernen
        fields := substring(fields,2);
        myInsertFields := substring(myInsertFields,2);


execute format('select versions.pgvsrevert(''%1$s.%2$s'')', mySchema, myTable);
/*
rollbackQry := format('insert into %1$s (%2$s, action)
with summary as
(  
select row_number() over(partition by %3$s order by systime desc)as rk, v.*
from versions.public_grenze_version_log as v
where revision <= %4$s
)

select %5$s, ''insert'' as action from summary as v where action != ''delete'' and rk = 1', versionLogTable, myInsertFields, myPkey, myRevision, fields);
*/

rollbackQry := 'insert into '||versionLogTable||' ('||myInsertFields||', action)
                select '||fields||', ''delete'' as action 
                from '||versionLogTable||' as v, 
                  (select v.'||myPkey||', max(v.version_log_id) as version_log_id
                   from '||versionLogTable||' as v,
                (select v.'||myPkey||'
                 from '||versionLogTable||' as v,
                  (select v.'||myPkey||'
                   from '||versionLogTable||' as v
                   where revision > '||myRevision||'
                   except
                   select v.'||myPkey||'
                   from '||versionLogTable||' as v
                   where revision <= '||myRevision||'
                  ) as foo
                 where v.'||myPkey||' = foo.'||myPkey||') as foo
               where v.'||myPkey||' = foo.'||myPkey||'    
               group by v.'||myPkey||') as foo
              where v.version_log_id = foo.version_log_id

              union

                select '||fields||', v.action 
                from '||versionLogTable||' as v, 
                  (select v.'||myPkey||', max(v.version_log_id) as version_log_id
                   from '||versionLogTable||' as v,
                     (select v.'||myPkey||' 
                      from '||versionLogTable||' as v
                      where revision > '||myRevision||'
                except
                 (select v.'||myPkey||'
                  from '||versionLogTable||' as v
                  where revision > '||myRevision||'
                  except
                  select v.'||myPkey||'
                  from '||versionLogTable||' as v
                  where revision <= '||myRevision||' 
                 )) as foo
                 where revision <= '||myRevision||' and v.'||myPkey||' = foo.'||myPkey||'    
                group by v.'||myPkey||') as foo
              where v.version_log_id = foo.version_log_id';

 --RAISE EXCEPTION '%', rollbackQry;
      execute rollbackQry;
              

  RETURN true ;                             

  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsrollback(character varying,integer) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvscheckout | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvscheckout(anyelement,bigint) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvscheckout ( _in_table anyelement,  revision bigint)
	RETURNS SETOF anyelement
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	COST 100
	ROWS 1000
	AS $$
  DECLARE
    mySchema TEXT;
    myTable TEXT;
    check_table TEXT;
    myPkey TEXT;
    message TEXT;
    diffQry TEXT;
    fields TEXT;
    myInsertFields TEXT;
    myPkeyRec record;
    attributes record;
    conflict BOOLEAN;
    pos integer;
    versionLogTable TEXT;
    sql TEXT;

  BEGIN	
    pos := strpos(pg_typeof(_in_table)::TEXT,'.');
    fields := '';
  
    if pos = 0 then 
        mySchema := 'public';
  	myTable := replace(pg_typeof(_in_table)::TEXT, '"',''); 
    else 
        mySchema := substr(pg_typeof(_in_table)::TEXT,0,pos);
        pos := pos + 1; 
        myTable := replace(substr(pg_typeof(_in_table)::TEXT,pos),'"','');
    END IF;  
    
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');   

    for attributes in select *
                      from  information_schema.columns
                      where table_schema=mySchema::name
                        and table_name = myTable::name

        LOOP
          
          if attributes.column_name not in ('action','project','systime','revision','logmsg','commit') then
            fields := fields||',v.'||quote_ident(attributes.column_name);
            myInsertFields := myInsertFields||','||quote_ident(attributes.column_name);
          END IF;

          END LOOP;

-- Das erste Komma  aus dem String entfernen
       fields := substring(fields,2);
       myInsertFields := substring(myInsertFields,2);

    check_table := replace(pg_typeof(_in_table)::TEXT, '"', '');

  -- Pruefen ob und welche Spalte der Primarykey der Tabelle ist 
    select into myPkeyRec * from versions._primarykey(check_table);    
    myPkey := quote_ident(myPkeyRec.pkey_column);


     sql := format('
with summary as 
(
  select row_number() over(partition by %1$s order by systime desc) as rk, * 
  from %2$s
  where commit = true and revision <= %3$s
)

select %4$s
from summary as v
where rk = 1 and action != ''delete''', myPkey, versionLogTable, revision, fields);


     -- RAISE EXCEPTION '%', sql;
     return QUERY EXECUTE sql;

  END;

$$;
-- ddl-end --

-- object: versions.pgvscheckout | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvscheckout(anyelement,bigint,text) CASCADE;

-- Prepended SQL commands --
DROP FUNCTION IF EXISTS versions.pgvscheckout(anyelement,bigint,text);
-- ddl-end --

CREATE OR REPLACE FUNCTION versions.pgvscheckout ( _in_table anyelement,  revision bigint,  extent text)
	RETURNS SETOF anyelement
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	COST 100
	ROWS 1000
	AS $$
  DECLARE
    mySchema TEXT;
    myTable TEXT;
    check_table TEXT;
    myPkey TEXT;
    message TEXT;
    diffQry TEXT;
    fields TEXT;
    myInsertFields TEXT;
    myPkeyRec record;
    attributes record;
    conflict BOOLEAN;
    pos integer;
    versionLogTable TEXT;
    sql TEXT;

  BEGIN	
    pos := strpos(pg_typeof(_in_table)::TEXT,'.');
    fields := '';
  
    if pos = 0 then 
        mySchema := 'public';
  	myTable := replace(pg_typeof(_in_table)::TEXT, '"',''); 
    else 
        mySchema := substr(pg_typeof(_in_table)::TEXT,0,pos);
        pos := pos + 1; 
        myTable := replace(substr(pg_typeof(_in_table)::TEXT,pos),'"','');
    END IF;  
    
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');   

    for attributes in select *
                      from  information_schema.columns
                      where table_schema=mySchema::name
                        and table_name = myTable::name

        LOOP
          
          if attributes.column_name not in ('action','project','systime','revision','logmsg','commit') then
            fields := fields||',v.'||quote_ident(attributes.column_name);
            myInsertFields := myInsertFields||','||quote_ident(attributes.column_name);
          END IF;

          END LOOP;

-- Das erste Komma  aus dem String entfernen
       fields := substring(fields,2);
       myInsertFields := substring(myInsertFields,2);

    check_table := replace(pg_typeof(_in_table)::TEXT, '"', '');

  -- Pruefen ob und welche Spalte der Primarykey der Tabelle ist 
    select into myPkeyRec * from versions._primarykey(check_table);    
    myPkey := quote_ident(myPkeyRec.pkey_column);


     sql := format('with summary as 
(
  select row_number() over(partition by %1$s order by systime desc) as rk, * 
  from %2$s
  where commit = true and revision <= %3$s
)

select %4$s
from summary as v
where %5$s and rk = 1 and action != ''delete''', myPkey, versionLogTable, revision, fields, extent);

     --RAISE EXCEPTION '%', sql;
     return QUERY EXECUTE sql;

  END;

$$;
-- ddl-end --



-- [ Created constraints ] --
-- object: version_tags_pkey | type: CONSTRAINT --
-- ALTER TABLE versions.version_tags DROP CONSTRAINT IF EXISTS version_tags_pkey CASCADE;
ALTER TABLE versions.version_tags ADD CONSTRAINT version_tags_pkey PRIMARY KEY (tags_id,version_table_id,revision,tag_text);
-- ddl-end --



-- [ Created foreign keys ] --
-- object: version_tables_fk_cp | type: CONSTRAINT --
-- ALTER TABLE versions.version_branch DROP CONSTRAINT IF EXISTS version_tables_fk_cp CASCADE;
ALTER TABLE versions.version_branch ADD CONSTRAINT version_tables_fk_cp FOREIGN KEY (version_table_id)
REFERENCES versions.version_tables (version_table_id) MATCH FULL
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --

-- object: version_tables_fk | type: CONSTRAINT --
-- ALTER TABLE versions.version_tags DROP CONSTRAINT IF EXISTS version_tables_fk CASCADE;
ALTER TABLE versions.version_tags ADD CONSTRAINT version_tables_fk FOREIGN KEY (version_table_id)
REFERENCES versions.version_tables (version_table_id) MATCH FULL
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --



-- [ Created permissions ] --
-- object: grant_7b6f035226 | type: PERMISSION --
GRANT SELECT,UPDATE,USAGE
   ON SEQUENCE versions.version_tables_logmsg_id_seq
   TO versions;
-- ddl-end --

-- object: grant_14e32fb692 | type: PERMISSION --
GRANT SELECT,UPDATE,USAGE
   ON SEQUENCE versions.version_tables_version_table_id_seq
   TO versions;
-- ddl-end --

-- object: grant_514df00181 | type: PERMISSION --
GRANT SELECT,UPDATE,USAGE
   ON SEQUENCE versions.version_tags_tags_id_seq
   TO versions;
-- ddl-end --

