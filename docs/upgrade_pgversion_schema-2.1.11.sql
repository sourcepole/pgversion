-- Diff code generated with pgModeler (PostgreSQL Database Modeler)
-- pgModeler version: 1.0.0-alpha
-- Diff date: 2022-03-17 18:19:46
-- Source model: pgvs_develop
-- Database: pgversion
-- PostgreSQL version: 12.0

-- [ Diff summary ]
-- Dropped objects: 0
-- Created objects: 3
-- Changed objects: 2

SET check_function_bodies = false;
-- ddl-end --

SET search_path=public,pg_catalog,av,versions;
-- ddl-end --


-- [ Created objects ] --
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

-- object: versions.pgvscheck | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvscheck(character varying) CASCADE;
CREATE FUNCTION versions.pgvscheck (_param1 character varying)
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
    RAISE NOTICE '%', myPkey;
    
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
                                    
      for conflictCheck IN EXECUTE myDebug
      LOOP
        return next conflictCheck;
        conflict := True;
        message := message||E'\n'||'WARNING! The object with '||myPkey||'='||conflictCheck.objectkey||' is also changed by user '||conflictCheck.conflict_user||'.';
      END LOOP;    
              
      message := message||E'\n\n';
      message := message||'Changes are not committed!'||E'\n\n';
      RAISE NOTICE '%', message;
  END;




$$;
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
                         systime = ' || EXTRACT(EPOCH FROM now()::TIMESTAMP)*1000 || '
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



-- [ Changed objects ] --
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
             alter table '||versionLogTable||' add column systime bigint default extract(epoch from now()::timestamp)*1000;    
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
    revision := '2.1.12';
  RETURN revision ;                             

  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsrevision() OWNER TO versions;
-- ddl-end --



-- [ Created permissions ] --
-- object: "grant_U_d8901c038e" | type: PERMISSION --
GRANT USAGE
   ON TYPE versions.conflicts
   TO PUBLIC;
-- ddl-end --

-- object: "grant_U_d214edb885" | type: PERMISSION --
GRANT USAGE
   ON TYPE versions.conflicts
   TO versions;
-- ddl-end --

-- object: "grant_X_03f5193db0" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscheck(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_19ed3de1a9" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscheck(character varying)
   TO versions;
-- ddl-end --

-- object: "grant_X_2be9896bbf" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscommit(character varying,text)
   TO PUBLIC;
-- ddl-end --

-- object: "grant_X_139e258a8c" | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscommit(character varying,text)
   TO versions;
-- ddl-end --

