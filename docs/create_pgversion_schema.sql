-- Prepended SQL commands --
DO $$
BEGIN
CREATE ROLE versions WITH 
	INHERIT
	ENCRYPTED PASSWORD '********';
EXCEPTION WHEN duplicate_object THEN RAISE NOTICE '%, skipping', SQLERRM USING ERRCODE = SQLSTATE;
END
$$;

DO $$
BEGIN
CREATE EXTENSION POSTGIS; 
EXCEPTION WHEN duplicate_object THEN RAISE NOTICE '%, skipping', SQLERRM USING ERRCODE = SQLSTATE;
END
$$;


-- 
-- -- Appended SQL commands --
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public, versions GRANT ALL ON TABLES TO versions;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA versions, public GRANT EXECUTE ON FUNCTIONS TO versions;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA versions, public GRANT USAGE, SELECT ON SEQUENCES TO versions;
-- GRANT ALL ON ALL TABLES IN SCHEMA public, versions TO versions;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA versions, public TO versions;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA versions, public TO versions;
-- -- ddl-end --
-- 

SET check_function_bodies = false;
-- ddl-end --

SET search_path TO pg_catalog,public,versions;
-- ddl-end --

-- object: versions | type: SCHEMA --
-- DROP SCHEMA IF EXISTS versions CASCADE;
CREATE SCHEMA IF NOT EXISTS versions;
-- ddl-end --

ALTER SCHEMA versions OWNER TO versions;
-- ddl-end --


-- object: versions.pgvsrevision | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsrevision() CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvsrevision ()
	RETURNS text
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS $$    
DECLARE
  revision TEXT;
  BEGIN	
    revision := '2.1.15';
    RETURN revision;                             
  END;
$$;


DROP TYPE IF EXISTS versions.checkout CASCADE;
CREATE TYPE versions.checkout AS
(
 systime bigint,
 revision integer,
 mykey integer,
 action character varying
);
-- ddl-end --
ALTER TYPE versions.checkout OWNER TO versions;
-- ddl-end --

-- object: versions.conflicts | type: TYPE --
DROP TYPE IF EXISTS versions.conflicts CASCADE;
CREATE TYPE versions.conflicts AS
(
 objectkey bigint,
 mysystime bigint,
 myuser text,
 myversion_log_id bigint,
 conflict_systime bigint,
 conflict_user text,
 conflict_version_log_id bigint
);
-- ddl-end --
ALTER TYPE versions.conflicts OWNER TO versions;
-- ddl-end --

-- object: versions.logview | type: TYPE --
DROP TYPE IF EXISTS versions.logview CASCADE;
CREATE TYPE versions.logview AS
(
 revision integer,
 datum timestamp,
 logmsg text,
 project text
);
-- ddl-end --
ALTER TYPE versions.logview OWNER TO versions;
-- ddl-end --

-- object: versions._hasserial | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions._hasserial(character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions._hasserial (in_table character varying)
	RETURNS boolean
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
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
ALTER FUNCTION versions._hasserial(character varying) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvscheck | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvscheck(character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvscheck(
	_param1 character varying)
    RETURNS SETOF versions.conflicts 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$

  DECLARE
    inTable ALIAS FOR $1;
    mySchema TEXT;
    myTable TEXT;
    myPkey TEXT;
    message TEXT;
    myDebug TEXT;
    confExists record;
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
    
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');   

  -- Pruefen ob und welche Spalte der Primarykey der Tabelle ist 
    select into myPkeyRec * from versions._primarykey(inTable);    
    myPkey := quote_ident(myPkeyRec.pkey_column);
    
/*
Check for conflicts before committing. When conflicts are existing stop the commit process 
with a listing of the conflicting objects.
*/    

    message := '';                                  
       
    myDebug := 'with 
                  foo as (select '||myPkey||', max(systime) as systime, max(version_log_id)
                          from '||versionLogTable||'
                          where commit
                            and project <> current_user
                          group by '||myPkey||'),
                                           
                  a as (select '||myPkey||', max(systime) as systime, max(version_log_id), project 
                        from '||versionLogTable||'
                        where project = current_user
                          and not commit
                        group by '||myPkey||', project),
                        
                  b as (select foo.*, v.project, v.action 
                        from '||versionLogTable||' as v, foo
                        where v.version_log_id = foo.max)
                                        
                select a.'||myPkey||' as objectkey, 
                   a.systime as mysystime, 
                   a.project as myuser,
                   a.max as myversion_log_id,
                   b.systime as conflict_systime, 
                   b.project as conflict_user,
                   b.max as conflict_version_log_id
                                  from a, b
                                  where a.systime < b.systime
                                    and a.'||myPkey||' = b.'||myPkey;

--RAISE EXCEPTION '%',myDebug;           
    EXECUTE myDebug into confExists;   
      
    IF COUNT(confExists) > 1 THEN
	for conflictCheck IN EXECUTE myDebug
	LOOP
	  return next conflictCheck;
	  conflict := True;
	  message := message||E'\n'||'WARNING! The object with '||myPkey||'='||conflictCheck.objectkey||' is also changed by user '||conflictCheck.conflict_user||'.';
	END LOOP;    

	message := message||E'\n\n';
	message := message||'Changes are not committed!'||E'\n\n';
	RAISE NOTICE '%', message;
    END IF;
  END;

$BODY$;
-- ddl-end --
ALTER FUNCTION versions.pgvscheck(character varying) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvscommit | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvscommit(character varying,text) CASCADE;
CREATE FUNCTION versions.pgvscommit (_param1 character varying, _param2 text)
	RETURNS SETOF versions.conflicts
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	ROWS 1000
	AS $$


  DECLARE
    inTable ALIAS FOR $1;
    logMessage ALIAS FOR $2;
    mySchema TEXT;
    myTable TEXT;
    myPkey TEXT;
    fields TEXT;
    insFields TEXT;
    message TEXT;
    myDebug TEXT;
    commitQuery TEXT;
    checkQuery TEXT;
    myPkeyRec record;
    attributes record;
    testRec record;
    conflict BOOLEAN;
    conflictCheck versions.conflicts%rowtype;
    pos integer;
    versionLogTable TEXT;
    revision integer;

  BEGIN	
    pos := strpos(inTable,'.');
    fields := '';
    insFields := '';
    conflict := False;
  
    if pos=0 then 
        mySchema := 'public';
  	    myTable := inTable; 
    else 
        mySchema := substr(inTable,0,pos);
        pos := pos + 1; 
        myTable := substr(inTable,pos);
    END IF;  

    
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');   

  -- Pruefen ob und welche Spalte der Primarykey der Tabelle ist 
    select into myPkeyRec * from versions._primarykey(inTable);    
    myPkey := quote_ident(myPkeyRec.pkey_column);   
    
/*
Check for conflicts before committing. When conflicts are existing stop the commit process 
with a listing of the conflicting objects.
*/    
  message := '';
                                
                                    
    for conflictCheck IN  EXECUTE 'select * from versions.pgvscheck('''||mySchema||'.'||myTable||''')'
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
    
         execute 'create temp table tmp_tab as 
       select project
       from '||versionLogTable||'
       where not commit ';

         select into testRec project from tmp_tab;

        IF NOT FOUND THEN
          execute 'drop table tmp_tab';
          RETURN;
        ELSE  
          execute 'drop table tmp_tab';
          for attributes in select *
                            from  information_schema.columns
                            where table_schema=mySchema::name
                              and table_name = myTable::name

              LOOP
                
                if attributes.column_name <> 'OID' 
                  and attributes.column_name <> 'versionarchive' then
                    fields := fields||',log.'||quote_ident(attributes.column_name);
                    insFields := insFields||','||quote_ident(attributes.column_name);
                END IF;
              END LOOP;    
            
              fields := substring(fields,2);
              insFields := substring(insFields,2);     
            
          revision := nextval('versions.'||quote_ident(mySchema||'_'||myTable||'_revision_seq'));
         
          commitQuery := 'delete from '||versionLogTable||'
                using (
                    select log.* from '||versionLogTable||' as log,
                       ( 
                    select '||myPkey||', systime
                    from '||versionLogTable||'
                    where not commit and project = current_user
                    except
                    select '||myPkey||', max(systime) as systime
                    from '||versionLogTable||'
                    where not commit and project = current_user
                    group by '||myPkey||') as foo
                    where log.project = current_user
                      and foo.'||myPkey||' = log.'||myPkey||'
                      and foo.systime = log.systime
                      and not commit) as foo
                where '||versionLogTable||'.'||myPkey||' = foo.'||myPkey||'
                  and '||versionLogTable||'.systime = foo.systime
                  and '||versionLogTable||'.project = foo.project;
                  
              delete from '||quote_ident(mySchema)||'.'||quote_ident(myTable)||' where '||myPkey||' in 
                   (select '||myPkey||'
                    from  '||versionLogTable||'
                             where not commit
                               and project = current_user
                             group by '||myPkey||', project);
   
              insert into '||quote_ident(mySchema)||'.'||quote_ident(myTable)||' ('||insFields||') 
                    select '||fields||' from '||versionLogTable||' as log,
                       (
                        select '||myPKey||', max(systime) as systime, max(revision) as revision
                        from '||versionLogTable||'
                        where project = current_user
                          and not commit
                          and action <> ''delete''
                        group by '||myPKey||'
                       ) as foo
                    where log.'||myPkey||'= foo.'||myPkey||'
                      and log.systime = foo.systime
                      and log.action <> ''delete'';
                      
                update '||versionLogTable||' set 
                         commit = True, 
                         revision = '||revision||', 
                         logmsg = '''||logMessage ||''',    
                         systime = ' || EXTRACT(EPOCH FROM now()::TIMESTAMP WITH TIME ZONE)*1000 || '
                    where not commit
                      and project = current_user;';

--RAISE EXCEPTION '%',commitQuery;

     execute 'INSERT INTO versions.version_tables_logmsg(
                version_table_id, revision, logmsg) 
              SELECT version_table_id, '||revision||', '''||logMessage||''' as logmsg 
              FROM versions.version_tables 
              where version_table_schema = '''||mySchema||'''
               and version_table_name = '''|| myTable||''''; 
                      

        execute commitQuery;              
     END IF;
  END IF;    

  RETURN;                             

  END;



$$;
-- ddl-end --
ALTER FUNCTION versions.pgvscommit(character varying,text) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvsdrop | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsdrop(character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvsdrop (_param1 character varying)
	RETURNS boolean
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS $$


  DECLARE
    inTable ALIAS FOR $1;
    pos INTEGER;
    mySchema TEXT;
    myTable TEXT;
    versionTableRec record;
    versionTable TEXT;
    versionView TEXT;
    versionLogTable TEXT;
    versionLogTableType TEXT;
    versionLogTableSeq TEXT;
    versionRevisionSeq TEXT;
    versionPkeySeq TEXT;
    geomCol TEXT;
    geomType TEXT;
    geomDIM INTEGER;
    geomSRID INTEGER;
    testRec record;
    uncommitRec record;
    testTab TEXT;
    myPkeyRec RECORD;
    myPkey TEXT;
    

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


    select into myPkeyRec * from versions._primarykey(inTable);    
    myPkey := quote_ident(myPkeyRec.pkey_column);

    versionView := quote_ident(mySchema)||'.'||quote_ident(myTable||'_version');
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');
    versionLogTableType := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log_type');
    versionLogTableSeq := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log_version_log_id_seq');
    versionRevisionSeq := 'versions.'||quote_ident(mySchema||'_'||myTable||'_revision_seq');
    versionPkeySeq :=     'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log'||'_'||myPkey||'_seq');


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

     execute 'create temp table tmp_tab on commit drop as 
       select project
       from '||versionLogTable||'
       where not commit ';

     select into testRec project from tmp_tab;

     IF FOUND THEN

       for uncommitRec in select distinct project from tmp_tab loop
         RAISE NOTICE 'Uncommitted Records are existing for user %. Please commit all changes before use pgvsdrop()', uncommitRec.project;
       end loop;
   --    execute 'drop table tmp_tab';
       RETURN False;
     END IF;  

     IF FOUND THEN
       RAISE EXCEPTION 'Uncommitted Records are existing. Please commit all changes before use pgvsdrop()';
       RETURN False;
     END IF;  

     select into versionTableRec version_table_id as vtid
     from versions.version_tables as vt
     where version_table_schema = mySchema::name
       and version_table_name = myTable::name;

     

    execute 'drop table if exists '||versionLogTable||' cascade;';
    execute 'drop type if exists '||versionLogTableType;
    execute 'DROP SEQUENCE if exists '||versionLogTableSeq;
    execute 'DROP SEQUENCE if exists '||versionRevisionSeq;
    execute 'DROP SEQUENCE if exists '||versionPkeySeq;


    
    execute 'delete from versions.version_tables 
               where version_table_id = '''||versionTableRec.vtid||''';';

    execute 'delete from versions.version_tables_logmsg 
               where version_table_id = '''||versionTableRec.vtid||''';';

    execute 'delete from versions.version_tags 
               where version_table_id = '''||versionTableRec.vtid||''';';               


  RETURN true ;                             

  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsdrop(character varying) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvsinit | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsinit(character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvsinit (_param1 character varying)
	RETURNS boolean
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
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
    time_fields TEXT;
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
    

  BEGIN	
    pos := strpos(inTable,'.');
    fields := '';
    time_fields := '';
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

-- Check if the table or view exists
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
 
 
-- Obtain the basic geometry parameters of the initial layer
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
		
       
-- Check if the table already exists
     testTab := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');
     select into testRec table_name
     from information_schema.tables
     where table_schema = mySchema::name
          and table_name = testTab::name;

     IF FOUND THEN
       RAISE NOTICE 'Table versions.% has been deleted', testTab;
       execute 'drop table '||quote_ident(mySchema)||'.'||quote_ident(testTab)||' cascade';
     END IF;    
  
     
-- Check if and which column is the primary key of the table 
    select into myPkeyRec * from versions._primarykey(inTable);    
    myPkey := quote_ident(myPkeyRec.pkey_column);

    sql := format('select max(%1$s) FROM %2$s.%3$s', myPkey, quote_ident(mySchema), quote_ident(myTable));
    execute sql into testRec;

    IF testRec.max is Null THEN
      RAISE EXCEPTION 'The table %.% is empty, but must contain at least one record for correct initialization.', mySchema, myTable;
    END IF;
    

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
             alter table '||versionLogTable||' add column systime bigint default extract(epoch from now()::TIMESTAMP WITH TIME ZONE)*1000;    
             alter table '||versionLogTable||' add column revision bigint;
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
              time_fields := time_fields||',v1.'||quote_ident(attributes.column_name);
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

     execute 'GRANT ALL PRIVILEGES ON TABLE '||versionView||' to versions';
     execute 'GRANT ALL PRIVILEGES ON TABLE '||quote_ident(mySchema)||'.'||quote_ident(myTable)||' to versions';

     execute 'create or replace view '||versionView||'_time as 
                SELECT row_number() OVER () AS rownum, 
                       to_timestamp(v1.systime/1000)::TIMESTAMP WITH TIME ZONE as start_time, 
                       CASE WHEN v2.systime IS NULL THEN 
                         CURRENT_TIMESTAMP
                       else
                         to_timestamp(v2.systime/1000)::TIMESTAMP WITH TIME ZONE 
                       END as end_time,
                       v1.*
                FROM '||versionLogTable||' v1
                LEFT JOIN '||versionLogTable||' v2 ON v2.id=v1.id AND v2.action=''delete'' and v1.revision <> v2.revision
                WHERE (v1.action=''insert'' or v1.action = ''update'') and v1.commit = True';

     execute 'ALTER VIEW '||versionView||'_time owner to versions';

     execute 'GRANT ALL PRIVILEGES ON TABLE '||versionView||'_time to versions';


     execute 'CREATE TRIGGER pgvs_version_record_trigger
              INSTEAD OF INSERT OR UPDATE OR DELETE
              ON '||versionView||'
              FOR EACH ROW
              EXECUTE PROCEDURE versions.pgvs_version_record();';                

     execute 'INSERT INTO '||versionLogTable||' ('||myPkey||','||fields||', action, revision, logmsg, commit ) 
                select '||myPkey||','||fields||', ''insert'' as action, 0 as revision, ''initial commit revision 0'' as logmsg, ''t'' as commit 
                from '||quote_ident(mySchema)||'.'||quote_ident(myTable);                          

     execute 'INSERT INTO versions.version_tables_logmsg(
                version_table_id, revision, logmsg) 
              SELECT version_table_id, 0 as revision, ''initial commit revision 0'' as logmsg FROM versions.version_tables where version_table_schema = '''||mySchema||''' and version_table_name = '''|| myTable||''''; 

     execute 'INSERT INTO versions.version_tags(
                version_table_id, revision, tag_text) 
              SELECT version_table_id, 0 as revision, ''initial commit revision 0'' as tag_text FROM versions.version_tables where version_table_schema = '''||mySchema||''' and version_table_name = '''|| myTable||''''; 

                
  RETURN true ;                             

  END;

$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsinit(character varying) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvslogview | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvslogview(character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvslogview (_param1 character varying)
	RETURNS SETOF versions.logview
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	ROWS 1000
	AS $$

    
  DECLARE
    inTable ALIAS FOR $1;
    mySchema TEXT;
    myTable TEXT;
    logViewQry TEXT;
    versionLogTable TEXT;
    pos integer;
    logs versions.logview%rowtype;


  BEGIN	
    pos := strpos(inTable,'.');
  
    if pos=0 then 
        mySchema := 'public';
  	    myTable := inTable; 
    else 
        mySchema := substr(inTable,0,pos);
        pos := pos + 1; 
        myTable := substr(inTable,pos);
    END IF;  
    
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');       

    logViewQry := format('select logt.revision, to_timestamp(logt.systime/1000),  logt.logmsg, logt.project
                           from  versions.version_tables as vt left join versions.version_tables_logmsg as logt on (vt.version_table_id = logt.version_table_id)
                           where vt.version_table_schema = ''%1$s''
                             and vt.version_table_name = ''%2$s'' 
                           order by revision desc', mySchema, myTable);

--RAISE EXCEPTION '%', logViewQry;

                           
    for logs IN  EXECUTE logViewQry
    LOOP

      return next logs;    
    end loop;                       
  
  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvslogview(character varying) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvsmerge | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsmerge(character varying,integer,character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvsmerge ("inTable" character varying, "targetGid" integer, "targetProject" character varying)
	RETURNS boolean
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS $$

  DECLARE
    inTable ALIAS FOR $1;
    targetGid ALIAS FOR $2;
    targetProject ALIAS FOR $3;
    sourceProject TEXT;
    mySchema TEXT;
    myTable TEXT;
    myPkey TEXT;
    myDebug TEXT;
    myMerge TEXT;
    myDelete TEXT;
    myPkeyRec record;
    myTimestamp bigint;
    conflict BOOLEAN;
    merged BOOLEAN;
    conflictCheck record;
    cols TEXT;
    pos integer;
    versionLogTable TEXT;

  BEGIN	
    sourceProject := current_user;
    pos := strpos(inTable,'.');
    conflict := False;
    merged := False;
  
    if pos=0 then 
        mySchema := 'public';
  	    myTable := inTable; 
    else 
        mySchema := substr(inTable,0,pos);
        pos := pos + 1; 
        myTable := substr(inTable,pos);
    END IF;  
    
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');   

  -- Pruefen ob und welche Spalte der Primarykey der Tabelle ist 
    select into myPkeyRec * from versions._primarykey(inTable);    
    myPkey := quote_ident(myPkeyRec.pkey_column); 
        

        
myDebug := 'select a.'||myPkey||' as objectkey, 
                   a.systime as mysystime, 
                   a.project as myuser,
                   b.systime as conflict_systime, 
                   b.project as conflict_user,
                   b.max as conflict_version_log_id
                                  from (select '||myPkey||', max(systime) as systime, max(version_log_id), project 
                                        from '||versionLogTable||'
                                        where project = '''||targetProject||'''
                                              and not commit
                                              and '||myPkey||' = '||targetGid||'
                                        group by '||myPkey||', project) as a,
                                       (
                                         select '||myPkey||', max(systime) as systime, max(version_log_id), project
                                         from '||versionLogTable||'
                                         where commit
                                           and project <> '''||targetProject||'''
                                         group by '||myPkey||', project
                                        ) as b
                                  where a.systime < b.systime
                                    and a.'||myPkey||' = b.'||myPkey||'
                                    and a.'||myPkey||' = '||targetGid; 
                                    
                                                                 
-- RAISE EXCEPTION '%',myDebug;    

    execute 'SELECT array_to_string(array_agg(quote_ident(column_name::name)), '','')
             FROM information_schema.columns 
             WHERE (table_schema, table_name) = ($1, $2)' into cols using mySchema, myTable;  

     myTimestamp := round(extract(epoch from now()::TIMESTAMP WITH TIME ZONE)*1000);
    
    for conflictCheck IN EXECUTE myDebug
    LOOP
       RAISE NOTICE '%  %  %  %  %  %',conflictCheck.objectkey,
                           conflictCheck.mysystime,
                           conflictCheck.myuser,
                           conflictCheck.conflict_systime, 
                           conflictCheck.conflict_user,
                           conflictCheck.conflict_version_log_id;         

       myMerge := 'insert into '||versionLogTable||' ('||cols||', action, project, systime)
                      select '||cols||', action, '''||targetProject||''' as project, 
                        '||myTimestamp||' as systime
                      from '||versionLogTable||' as v,
                        (
                         select max(systime) as systime
                         from '||versionLogTable||'
                         where project = '''||targetProject||'''
                           and '||myPkey||' = '||targetGid||'
                         group by '||myPkey||'
                        ) as foo
                      where '||myPkey||' = '||targetGid||' 
                         and v.systime = foo.systime '; 
                         
        execute myMerge;
      
      merged := True;
                     

     END LOOP;     

     if sourceProject <> targetProject then
       myDelete := 'delete from '||versionLogTable||' 
                       where '||myPkey||' = '||targetGid||' 
                          and project = '''||sourceProject||'''
                          and not commit 
                          and systime < '||myTimestamp;

--       RAISE EXCEPTION '%', myDelete;                             
       execute myDelete;
     end if;

                        


  
  RETURN True;
  
  END;

$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsmerge(character varying,integer,character varying) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvsrevert | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsrevert(character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvsrevert (_param1 character varying)
	RETURNS integer
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
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
    geomCol TEXT;
    geomType TEXT;
    geomDIM INTEGER;
    geomSRID INTEGER;
    revision INTEGER;
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

    versionView := quote_ident(mySchema)||'.'||quote_ident(myTable||'_version');
    versionLogTable := 'versions.'||quote_ident(mySchema||'_'||myTable||'_version_log');

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
 
     execute 'select max(revision) from '||versionLogTable into revision;
     
     execute 'delete from '||versionLogTable||' 
                    where project = current_user
                      and not commit';
                    
  RETURN revision ;                             

  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsrevert(character varying) OWNER TO versions;
-- ddl-end --

-- ddl-end --
ALTER FUNCTION versions.pgvsrevision() OWNER TO versions;
-- ddl-end --

-- object: versions.pgvsrollback | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsrollback(character varying,integer) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvsrollback (_param1 character varying, _param2 integer)
	RETURNS boolean
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
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

-- object: versions.pgvsupdatecheck | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsupdatecheck(character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvsupdatecheck (_param1 character varying)
	RETURNS boolean
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS $$

    
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

$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsupdatecheck(character varying) OWNER TO versions;
-- ddl-end --

-- object: versions.version_tables_version_table_id_seq | type: SEQUENCE --
--DROP SEQUENCE IF EXISTS versions.version_tables_version_table_id_seq CASCADE;
CREATE SEQUENCE IF NOT EXISTS versions.version_tables_version_table_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;

-- ddl-end --
ALTER SEQUENCE versions.version_tables_version_table_id_seq OWNER TO versions;
-- ddl-end --

-- object: versions.version_tables_logmsg_id_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS versions.version_tables_logmsg_id_seq CASCADE;
CREATE SEQUENCE IF NOT EXISTS versions.version_tables_logmsg_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;

-- ddl-end --
ALTER SEQUENCE versions.version_tables_logmsg_id_seq OWNER TO versions;
-- ddl-end --

-- object: versions.version_tables_logmsg | type: TABLE --
-- DROP TABLE IF EXISTS versions.version_tables_logmsg CASCADE;
CREATE TABLE IF NOT EXISTS versions.version_tables_logmsg (
	id bigint NOT NULL DEFAULT nextval('versions.version_tables_logmsg_id_seq'::regclass),
	version_table_id bigint,
	revision character varying,
	logmsg character varying,
	systime bigint DEFAULT (date_part('epoch'::text, now()) * (1000)::double precision),
	project character varying DEFAULT "current_user"(),
	CONSTRAINT version_tables_logmsg_pkey PRIMARY KEY (id)

);
-- ddl-end --
ALTER TABLE versions.version_tables_logmsg OWNER TO versions;
-- ddl-end --

-- object: versions.version_tables | type: TABLE --
-- DROP TABLE IF EXISTS versions.version_tables CASCADE;
CREATE TABLE IF NOT EXISTS versions.version_tables (
	version_table_id bigint NOT NULL DEFAULT nextval('versions.version_tables_version_table_id_seq'::regclass),
	version_table_schema character varying,
	version_table_name character varying,
	version_view_schema character varying,
	version_view_name character varying,
	version_view_pkey character varying,
	version_view_geometry_column character varying,
	CONSTRAINT version_table_pkey PRIMARY KEY (version_table_id)

);
-- ddl-end --
ALTER TABLE versions.version_tables OWNER TO versions;
-- ddl-end --

-- object: versions.version_tags_tags_id_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS versions.version_tags_tags_id_seq CASCADE;
CREATE SEQUENCE IF NOT EXISTS versions.version_tags_tags_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;

-- ddl-end --
ALTER SEQUENCE versions.version_tags_tags_id_seq OWNER TO versions;
-- ddl-end --

-- object: versions.version_tags | type: TABLE --
-- DROP TABLE IF EXISTS versions.version_tags CASCADE;
CREATE TABLE IF NOT EXISTS versions.version_tags (
	tags_id bigint NOT NULL DEFAULT nextval('versions.version_tags_tags_id_seq'::regclass),
	version_table_id bigint NOT NULL,
	revision bigint NOT NULL,
	tag_text character varying NOT NULL,
	CONSTRAINT version_tags_pkey PRIMARY KEY (version_table_id,revision,tag_text)

);
-- ddl-end --
ALTER TABLE versions.version_tags OWNER TO versions;
-- ddl-end --

-- object: fki_version_tables_fkey | type: INDEX --
-- DROP INDEX IF EXISTS versions.fki_version_tables_fkey CASCADE;
CREATE INDEX IF NOT EXISTS fki_version_tables_fkey ON versions.version_tables_logmsg
USING btree
(
	version_table_id
)
WITH (FILLFACTOR = 90);
-- ddl-end --

-- object: versions._primarykey | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions._primarykey(character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions._primarykey (IN intable character varying, OUT pkey_column character varying, OUT success boolean)
	RETURNS record
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS $$
DECLARE
    mySchema TEXT;
    myTable TEXT;
    myPkeyRec RECORD;
    message TEXT;
    pos INT;

  BEGIN	
    pos := strpos(inTable,'.');
  
    if pos=0 then 
        mySchema := 'public';
  	myTable := inTable; 
    else 
        mySchema := substr(inTable,0,pos);
        pos := pos + 1; 
        myTable := substr(inTable,pos);
    END IF;  

  -- Check if PKEY exists and which column represents it 
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
       pkey_column := myPkeyRec.column_name;     
       success := 'true';
    else
        RAISE EXCEPTION 'Table % does not have Primarykey defined', mySchema||'.'||myTable;
    END IF;    
  END;
$$;
-- ddl-end --
ALTER FUNCTION versions._primarykey(character varying) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvs_version_record | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvs_version_record() CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvs_version_record ()
	RETURNS trigger
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS $$


  DECLARE 
    pkey_rec record;
    pkey TEXT;
    qry TEXT;
    insert_qry TEXT;
    pgvslog TEXT;
    seq TEXT;
    fields TEXT;
    field_values TEXT;
    attributes RECORD;
    result TEXT;
    pkey_result RECORD;
    inTable TEXT;
    
  BEGIN	
    inTable := substring(TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME from 0 for position('_version' in TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME));


-- Get primarykey of relation 
    select into pkey_result * from versions._primarykey(inTable);    
    pkey := quote_ident(pkey_result.pkey_column);
    
     pgvslog := quote_ident(TG_TABLE_SCHEMA ||'_'|| TG_TABLE_NAME ||'_log');

     fields := '';
     field_values := '';

     IF TG_OP = 'INSERT' THEN 
        qry := format('select column_name from  information_schema.columns
                      where table_schema=''%s''::name
                        and table_name = ''%s''::name
                        and column_name not in (''%s'',''action'',''project'',''systime'',''revision'',''logmsg'',''commit'')
                        and (column_default not like ''nextval%%'' or column_default is null)', TG_TABLE_SCHEMA, TG_TABLE_NAME, pkey);

     ELSE
        qry := format('select column_name from  information_schema.columns
                      where table_schema=''%s''::name
                        and table_name = ''%s''::name
                        and column_name not in (''action'',''project'',''systime'',''revision'',''logmsg'',''commit'')
                        and (column_default not like ''nextval%%'' or column_default is null)', TG_TABLE_SCHEMA, TG_TABLE_NAME);
     END IF;

        for attributes in execute qry 

           LOOP
                fields := fields||', '||quote_ident(attributes.column_name);
                field_values := field_values||',$1.'||quote_ident(attributes.column_name);
              
           END LOOP;

          fields := substring(fields,2);
          field_values := substring(field_values, 2);
      
      qry := 'insert into versions.'|| pgvslog ||' 
                ('||fields||', action, project, systime, revision, logmsg, commit)
                select '||field_values||', '''||lower(TG_OP)||''', current_user, date_part(''epoch''::text, (now())::TIMESTAMP WITH TIME ZONE) * (1000)::double precision, NULL, NULL, false';    

      
     if TG_OP = 'INSERT' THEN     
        execute  qry USING NEW;
        RETURN NEW;
     ELSEIF TG_OP = 'UPDATE' THEN
        execute qry USING NEW;
        RETURN NEW;
     ELSEIF TG_OP = 'DELETE' THEN
        execute  qry USING OLD;
        RETURN OLD;
     END IF;                         
  END;



$$;
-- ddl-end --
ALTER FUNCTION versions.pgvs_version_record() OWNER TO versions;
-- ddl-end --

-- object: versions.pgvscheckout | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvscheckout(anyelement,bigint) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvscheckout (_in_table anyelement, revision bigint)
	RETURNS SETOF anyelement
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
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
ALTER FUNCTION versions.pgvscheckout(anyelement,bigint) OWNER TO versions;
-- ddl-end --

-- object: versions.pgvscheckout | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvscheckout(anyelement,bigint,text) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvscheckout (_in_table anyelement, revision bigint, extent text)
	RETURNS SETOF anyelement
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
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
ALTER FUNCTION versions.pgvscheckout(anyelement,bigint,text) OWNER TO versions;
-- ddl-end --

-- FUNCTION: versions.pgvsincrementalupdate(character varying, character varying)

-- DROP FUNCTION IF EXISTS versions.pgvsincrementalupdate(character varying, character varying);

CREATE OR REPLACE FUNCTION versions.pgvsincrementalupdate(
	in_new_layer character varying,
	in_old_layer character varying)
    RETURNS text
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
  new_layer TEXT;
  old_layer TEXT;
  old_schema TEXT;
  new_schema TEXT;
  old_pkey_rec RECORD;
  new_pkey_rec RECORD;
  old_geo_rec RECORD;
  new_geo_rec RECORD;
  old_pkey TEXT;
  new_pkey TEXT;		
  att_check RECORD;
  attributes RECORD;
  qry_delete TEXT;
  qry_insert TEXT;	
  fields TEXT;
  old_fields TEXT;
  n_arch_field TEXT;
  arch_fields TEXT;
  where_fields TEXT;
  pos INTEGER;
  integer_var INTEGER;		
  insub_query TEXT;
  missing_column TEXT;
  result text[];
  
  
  BEGIN
    pos := strpos(in_old_layer,'.');
    if pos=0 then 
        old_schema := 'public';
  	old_layer := in_old_layer; 
    else 
  	old_schema = substr(in_old_layer,0,pos);
  	pos := pos + 1; 
        old_layer = substr(in_old_layer,pos);
    END IF;

    pos := strpos(in_new_layer,'.');
    if pos=0 then 
        new_schema := 'public';
  	    new_layer := in_new_layer; 
    else 
        new_schema = substr(in_new_layer,0,pos);
  	    pos := pos+1; 
  	    new_layer = substr(in_new_layer,pos);
    END IF;
    
  -- Vorbelegen der Variablen
    fields := '';
    old_fields := '';		
    qry_insert := '';
    qry_delete := '';
    integer_var := 0;
  
  
  -- Feststellen wie die Geometriespalte der Layer heisst bzw. ob der Layer in der Tabelle geometry_columns definiert ist
     select into old_geo_rec f_geometry_column, type as geom_type 
     from public.geometry_columns 
     where f_table_schema = old_schema 
       and f_table_name = old_layer;
  
     IF NOT FOUND THEN
       RAISE EXCEPTION 'Die Tabelle % ist nicht als Geo-Layer in der Tabelle geometry_columns registriert', old_layer;
	   result := array_append(result, 'false');
       RETURN result;
     END IF;
  	  
     select into new_geo_rec f_geometry_column, type as geom_type 
     from public.geometry_columns 
     where f_table_schema = new_schema 
      and  f_table_name = new_layer;
  
     IF NOT FOUND THEN
        RAISE EXCEPTION 'Die Tabelle % ist nicht als Geo-Layer in der Tabelle geometry_columns registriert', new_layer;
  	    result := array_append(result, 'false');
        RETURN result;
     END IF;
  		
  
  -- Pruefen, ob der new_layer mindestens der Struktur des old_layer entspricht	
     missing_column := chr(10);
     select into att_check col.column_name
     from information_schema.columns as col
     where table_schema = old_schema::name
       and table_name = old_layer::name
       and (position('nextval' in lower(column_default)) is NULL or position('nextval' in lower(column_default)) = 0)		
     except
     select col.column_name
     from information_schema.columns as col
     where table_schema = new_schema::name
       and table_name = new_layer::name;
  	
    IF FOUND THEN
	   for att_check in 
	      select col.column_name
          from information_schema.columns as col
          where table_schema = old_schema::name
            and table_name = old_layer::name
             and (position('nextval' in lower(column_default)) is NULL or position('nextval' in lower(column_default)) = 0)		
          except
            select col.column_name
            from information_schema.columns as col
            where table_schema = new_schema::name
              and table_name = new_layer::name
  	   LOOP
	     missing_column := missing_column||chr(10)||att_check.column_name;
	   END LOOP;
	   missing_column := missing_column||chr(10);
       RAISE EXCEPTION 'Die Tabelle % entspricht nicht der Tabelle % % %diese Spalten fehlen: %', new_layer, old_layer, chr(10), chr(10), missing_column;
	   result := array_append(result, 'false');
       RETURN result;
    END IF;
   
    n_arch_field := ' ';
    arch_fields:=' ';
    where_fields:=' ';
  		
  		
  -- Pruefen ob und welche Spalte der Primarykey der Tabelle old_layer ist 
    select into old_pkey_rec col.column_name 
    from information_schema.table_constraints as key,
         information_schema.key_column_usage as col
    where key.table_schema = old_schema::name
      and key.table_name = old_layer::name
      and key.constraint_type='PRIMARY KEY'
      and key.table_catalog = col.table_catalog
      and key.table_schema = col.table_schema
      and key.table_name = col.table_name;	
  
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Die Tabelle % hat keinen Primarykey', old_layer;
  	    result := array_append(result, 'false');
        RETURN result;
    END IF;			
  
  
  -- Prfen ob und welche Spalte der Primarykey der Tabelle new_layer ist
    select into new_pkey_rec col.column_name 
    from information_schema.table_constraints as key,
         information_schema.key_column_usage as col
    where key.table_schema = new_schema::name
      and key.table_name = new_layer::name
      and key.constraint_type='PRIMARY KEY'
      and key.table_catalog = col.table_catalog
      and key.table_schema = col.table_schema
      and key.table_name = col.table_name;	
  
    IF NOT FOUND THEN
       RAISE EXCEPTION 'Die Tabelle % hat keinen Primarykey', new_layer;
  	    result := array_append(result, 'false');
        RETURN result;
    END IF;			
  				
    
    insub_query := FORMAT('select %1$s as id 
	                   from %2$s.%3$s 
  	                   except 
  			   select o.%1$s 
  			   from %4$s.%5$s as n,%2$s.%3$s as o 
  			   where md5(n.%6$s::TEXT)=md5(o.%7$s::TEXT) 
  			     and o.%7$s && n.%6$s ',
  			   old_pkey_rec.column_name,
  			   old_schema,
  			   old_layer,
  			   new_schema,
  			   new_layer,
  			   new_geo_rec.f_geometry_column,
  			   old_geo_rec.f_geometry_column
  	           );
  		
  -- Alle Sequenzen ermitteln und unbercksichtigt lassen		
    FOR attributes in select column_name as att, data_type as typ
                      from information_schema.columns as col
                      where table_schema = old_schema::name
                    	and table_name = old_layer::name
                    	and column_name not in (old_geo_rec.f_geometry_column::name)
                        and (position('nextval' in lower(column_default)) is NULL or position('nextval' in lower(column_default)) = 0)		
    LOOP
  
    	old_fields := old_fields ||','|| quote_ident(attributes.att);
  					 
  -- Eine Spalte vom Typ Bool darf nicht in die Coalesce-Funktion gesetzt werden					 
    	IF old_pkey_rec.column_name <> attributes.att THEN
       		IF attributes.typ = 'bool' THEN
           		where_fields := where_fields ||' and n.'||quote_ident(attributes.att)||'=o.'||quote_ident(attributes.att);					 
       		ELSE
  	   		where_fields := where_fields ||' and coalesce(n.'||quote_ident(attributes.att)||'::text,'''')=coalesce(o.'||quote_ident(attributes.att)||'::text,'''')';
       		END IF;
     	END IF;
  
    END LOOP;
  		
    where_fields := where_fields||' '||arch_fields;
    insub_query := insub_query||' '||where_fields;
  	  
  -- Vorbereiten der Update Funktion
    qry_delete := FORMAT('delete from %1$s.%2$s_version 
                          where %3$s in (%4$s)', 
				   old_schema, 
				   old_layer, 
				   old_pkey_rec.column_name, 
				   insub_query);	  
  
-- Ausfuehren der Update Funktion 
-- RAISE NOTICE '%',qry_delete;
-- RETURN false;											
  EXECUTE qry_delete;
  GET DIAGNOSTICS integer_var = ROW_COUNT;
  result := array_append(result, format(' %1$s Objekte archiviert',integer_var));
 --RETURN false;  
  -- Vorbereiten der Insert Funktion
  			
  insub_query := FORMAT('
		select %1$s as %2$s %7$s 
        from %3$s.%4$s as n
  		where %8$s in (
  		  select %8$s as id from %3$s.%4$s
  		  except
  		  select n.%8$s 
  		  from %3$s.%4$s as n,%5$s.%6$s_version as o 
  		  where md5(n.%1$s::TEXT)=md5(o.%2$s::TEXT) 
  		      and o.%2$s && n.%1$s %9$s )',
		  new_geo_rec.f_geometry_column,
		  old_geo_rec.f_geometry_column,
		  new_schema,
		  new_layer,
		  old_schema,
		  old_layer,
		  old_fields,
		  new_pkey_rec.column_name,
		  where_fields);			
		  

  qry_insert := FORMAT('insert into %1$s.%2$s_version (%3$s%4$s) %5$s', 
			    old_schema,
			    old_layer,
				old_geo_rec.f_geometry_column,
				old_fields,
				insub_query);  
  
--RAISE EXCEPTION '%',qry_insert;
--  RAISE NOTICE '%',insub_query;											
  EXECUTE qry_insert;
  GET DIAGNOSTICS integer_var = ROW_COUNT;
  result := array_append(result, format(' %1$s Objekte neu eingefuegt',integer_var));
  
  result := array_append(result, 'true');
  RETURN result;
END;

$BODY$;
-- ddl-end --

-- object: version_tables_fkey | type: CONSTRAINT --
ALTER TABLE versions.version_tables_logmsg DROP CONSTRAINT IF EXISTS version_tables_fkey CASCADE;
ALTER TABLE versions.version_tables_logmsg ADD CONSTRAINT version_tables_fkey FOREIGN KEY (version_table_id)
REFERENCES versions.version_tables (version_table_id) MATCH SIMPLE
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --

-- object: version_tables_fk | type: CONSTRAINT --
ALTER TABLE versions.version_tags DROP CONSTRAINT IF EXISTS version_tables_fk CASCADE;
ALTER TABLE versions.version_tags ADD CONSTRAINT version_tables_fk FOREIGN KEY (version_table_id)
REFERENCES versions.version_tables (version_table_id) MATCH FULL
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --

-- object: "grant_CU_eb94f049ac" | type: PERMISSION --
GRANT CREATE,USAGE
   ON SCHEMA public
   TO postgres;
-- ddl-end --

-- object: "grant_CU_cd8e46e7b6" | type: PERMISSION --
GRANT CREATE,USAGE
   ON SCHEMA public
   TO PUBLIC;
-- ddl-end --

-- object: "grant_CU_c9c921f140" | type: PERMISSION --
GRANT CREATE,USAGE
   ON SCHEMA versions
   TO versions;
-- ddl-end --

-- object: "grant_CU_97578721ad" | type: PERMISSION --
GRANT CREATE,USAGE
   ON SCHEMA versions
   TO postgres;
-- ddl-end --

-- object: "grant_CU_19cfb153df" | type: PERMISSION --
GRANT CREATE,USAGE
   ON SCHEMA versions
   TO PUBLIC;
-- ddl-end --

-- object: "grant_U_36abba67dd" | type: PERMISSION --
GRANT USAGE
   ON TYPE versions.checkout
   TO PUBLIC;
-- ddl-end --

-- object: "grant_U_6869c7bfde" | type: PERMISSION --
GRANT USAGE
   ON TYPE versions.checkout
   TO versions;
-- ddl-end --

-- object: "grant_U_25d5505568" | type: PERMISSION --
GRANT USAGE
   ON TYPE versions.conflicts
   TO PUBLIC;
-- ddl-end --

-- object: "grant_U_6ed296fb20" | type: PERMISSION --
GRANT USAGE
   ON TYPE versions.conflicts
   TO versions;
-- ddl-end --

-- object: "grant_U_d35d7e80f3" | type: PERMISSION --
GRANT USAGE
   ON TYPE versions.logview
   TO PUBLIC;
-- ddl-end --

-- object: "grant_U_32d5dd0409" | type: PERMISSION --
GRANT USAGE
   ON TYPE versions.logview
   TO versions;
-- ddl-end --

-- object: "grant_X_69a3597eb5" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscheck(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_15fde580b8" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscheck(character varying)
   TO versions;
-- ddl-end --

-- object: "grant_X_81bddac82f" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscommit(character varying,text)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_8a3a0c37cb" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscommit(character varying,text)
   TO versions;
-- ddl-end --

-- object: "grant_X_825f69f4cc" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsdrop(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_3d71ab0b83" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsdrop(character varying)
   TO versions;
-- ddl-end --

-- object: "grant_X_76287e64dd" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsinit(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_7c0c76e67f" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsinit(character varying)
   TO versions;
-- ddl-end --

-- object: "grant_X_f609b9e390" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvslogview(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_29ba5cd4bf" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvslogview(character varying)
   TO versions;
-- ddl-end --

-- object: "grant_X_1e420b9a0d" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsmerge(character varying,integer,character varying)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_0b0de7448b" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsmerge(character varying,integer,character varying)
   TO versions;
-- ddl-end --

-- object: "grant_X_2c2eba4edf" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrevert(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_fc34365d68" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrevert(character varying)
   TO versions;
-- ddl-end --

-- object: "grant_X_b45f4873d5" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrevision()
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_40631763b6" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrevision()
   TO versions;
-- ddl-end --

-- object: "grant_X_3c3b5449b4" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrollback(character varying,integer)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_2c43f1cc66" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrollback(character varying,integer)
   TO versions;
-- ddl-end --

-- object: "grant_X_275124c736" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsupdatecheck(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_37ba0f4e7e" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsupdatecheck(character varying)
   TO versions;
-- ddl-end --

-- object: "grant_rawdDxt_64147dc69c" | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tables_logmsg
   TO versions;
-- ddl-end --

-- object: "grant_rawdDxt_b3efd8927b" | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tables
   TO versions;
-- ddl-end --

-- object: "grant_rawdDxt_75f1f1e6e4" | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tags
   TO versions;
-- ddl-end --

-- object: "grant_X_3cb9e164cd" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions._primarykey(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_a603eb042a" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions._primarykey(character varying)
   TO versions;
-- ddl-end --

-- object: "grant_X_17846be44c" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvs_version_record()
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_24326a3c5f" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvs_version_record()
   TO versions;
-- ddl-end --

GRANT versions TO current_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public, versions GRANT ALL ON TABLES TO versions;
ALTER DEFAULT PRIVILEGES IN SCHEMA versions, public GRANT EXECUTE ON FUNCTIONS TO versions;
ALTER DEFAULT PRIVILEGES IN SCHEMA versions, public GRANT USAGE, SELECT ON SEQUENCES TO versions;
GRANT ALL ON ALL TABLES IN SCHEMA public, versions TO versions;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA versions, public TO versions;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA versions, public TO versions;








