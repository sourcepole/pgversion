--
-- PostgreSQL database dump
--

-- Dumped from database version 9.3.15
-- Dumped by pg_dump version 9.5.5

-- Started on 2016-12-02 09:44:38 CET

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- TOC entry 8 (class 2615 OID 360679)
-- Name: versions; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA versions;


SET search_path = versions, pg_catalog;

--
-- TOC entry 541 (class 1247 OID 360682)
-- Name: checkout; Type: TYPE; Schema: versions; Owner: -
--

CREATE TYPE checkout AS (
	mykey integer,
	action character varying,
	revision integer,
	systime bigint
);


--
-- TOC entry 544 (class 1247 OID 360685)
-- Name: conflicts; Type: TYPE; Schema: versions; Owner: -
--

CREATE TYPE conflicts AS (
	objectkey bigint,
	mysystime bigint,
	myuser text,
	myversion_log_id bigint,
	conflict_systime bigint,
	conflict_user text,
	conflict_version_log_id bigint
);


--
-- TOC entry 547 (class 1247 OID 360688)
-- Name: logview; Type: TYPE; Schema: versions; Owner: -
--

CREATE TYPE logview AS (
	revision integer,
	datum timestamp without time zone,
	project text,
	logmsg text
);


--
-- TOC entry 195 (class 1255 OID 360689)
-- Name: pgvs_version_record(); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvs_version_record() RETURNS trigger
    LANGUAGE plpgsql
    AS $_$
  DECLARE 
    pkey_rec record;
    pkey TEXT;
    qry TEXT;
    pgvslog TEXT;
    seq TEXT;
    
  BEGIN	
     select into pkey_rec col.column_name 
     from information_schema.table_constraints as key,
         information_schema.key_column_usage as col
     where key.table_schema = TG_TABLE_SCHEMA::name
       and key.table_name = TG_TABLE_NAME::name
       and key.constraint_type='PRIMARY KEY'
       and key.table_catalog = col.table_catalog
       and key.table_schema = col.table_schema
       and key.table_name = col.table_name;
     pkey := pkey_rec.column_name;
     pgvslog := quote_ident(TG_TABLE_SCHEMA ||'_'|| TG_TABLE_NAME ||'_log');
     seq := quote_ident(TG_TABLE_SCHEMA ||'_'|| TG_TABLE_NAME ||'_log_version_log_id_seq');
     qry := 'insert into versions.'|| pgvslog ||' select $1.*, 
                nextval(''versions.'|| seq ||'''), 
                '''||lower(TG_OP)||''', current_user, date_part(''epoch''::text, (now())::timestamp without time zone) * (1000)::double precision, NULL, NULL, false';     
      
     if TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN     
        execute  qry USING NEW;
        RETURN NEW;
     ELSEIF TG_OP = 'DELETE' THEN
        execute  qry USING OLD;
        RETURN OLD;
     END IF;                         
  END;
$_$;


--
-- TOC entry 200 (class 1255 OID 360690)
-- Name: pgvscheck(character varying); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvscheck(_param1 character varying) RETURNS SETOF conflicts
    LANGUAGE plpgsql
    AS $_$
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
    
    versionLogTable := 'versions."'||mySchema||'_'||myTable||'_version_log"';   
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
                                    and b.action <> ''delete''
                                    and a.'||myPkey||' = b.'||myPkey;
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
$_$;


--
-- TOC entry 203 (class 1255 OID 360691)
-- Name: pgvscheckout(character varying, bigint); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvscheckout(intable character varying, revision bigint) RETURNS TABLE(log_id bigint, systime bigint)
    LANGUAGE plpgsql
    AS $$
  DECLARE
    mySchema TEXT;
    myTable TEXT;
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
  BEGIN	
    pos := strpos(inTable,'.');
    fields := '';
  
    if pos=0 then 
        mySchema := 'public';
  	myTable := inTable; 
    else 
        mySchema := substr(inTable,0,pos);
        pos := pos + 1; 
        myTable := substr(inTable,pos);
    END IF;  
    
    versionLogTable := 'versions."'||mySchema||'_'||myTable||'_version_log"';   
    for attributes in select *
                      from  information_schema.columns
                      where table_schema=mySchema::name
                        and table_name = myTable::name
        LOOP
          
          if attributes.column_name not in ('action','project','systime','revision','logmsg','commit') then
            fields := fields||',v."'||attributes.column_name||'"';
            myInsertFields := myInsertFields||',"'||attributes.column_name||'"';
          END IF;
          END LOOP;
       fields := substring(fields,2);
       myInsertFields := substring(myInsertFields,2);
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
        RAISE EXCEPTION 'Table % does not have Primarykey defined', mySchema||'.'||pg_typeof(inTable);
    END IF;    
    diffQry := 'select foo2.'||myPkey||'::bigint, foo2.systime 
                from (
                  select '||myPkey||', max(systime) as systime
                  from '||versionLogTable||'
                  where commit = true and revision <= '||revision||'
                  group by '||myPkey||') as foo,
                  (select * 
                   from '||versionLogTable||'
                  ) as foo2
                  where foo.'||myPkey||' = foo2.'||myPkey||' 
                    and foo.systime = foo2.systime 
                    and action <> ''delete'' ';
     return QUERY EXECUTE diffQry;
  END;
$$;


--
-- TOC entry 198 (class 1255 OID 360692)
-- Name: pgvscommit(character varying, text); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvscommit(_param1 character varying, _param2 text) RETURNS SETOF conflicts
    LANGUAGE plpgsql
    AS $_$
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
    
    versionLogTable := 'versions."'||mySchema||'_'||myTable||'_version_log"';   
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
                    fields := fields||',log."'||attributes.column_name||'"';
                    insFields := insFields||',"'||attributes.column_name||'"';
                END IF;
              END LOOP;    
            
              fields := substring(fields,2);
              insFields := substring(insFields,2);     
            
          revision := nextval('versions."'||mySchema||'_'||myTable||'_revision_seq"');
         
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
                  
              delete from "'||mySchema||'"."'||myTable||'" where '||myPkey||' in 
                   (select '||myPkey||'
                    from  '||versionLogTable||'
                             where not commit
                               and project = current_user
                             group by '||myPkey||', project);
   
              insert into "'||mySchema||'"."'||myTable||'" ('||insFields||') 
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
     execute 'INSERT INTO versions.version_tables_logmsg(
                version_table_id, revision, logmsg) 
              SELECT version_table_id, '||revision||', '''||logMessage||''' as logmsg FROM versions.version_tables where version_table_schema = '''||mySchema||''' and version_table_name = '''|| myTable||''''; 
                      
        execute commitQuery;              
     END IF;
  END IF;    
  RETURN;                             
  END;
$_$;


--
-- TOC entry 196 (class 1255 OID 360694)
-- Name: pgvsdiff(anyelement, integer); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvsdiff(_rowtype anyelement, revision integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
  attributes RECORD;
  inTable TEXT;
  mySchema TEXT;
  myTable TEXT;
  fields TEXT;
  pos INTEGER;
  qry TEXT;
  
BEGIN
  inTable := pg_typeof(_rowtype)::TEXT;
  
  pos := strpos(inTable,'.');
  fields := '';
  
  if pos=0 then 
     mySchema := 'public';
     myTable := inTable; 
  else 
     mySchema := substr(inTable,0,pos);
     pos := pos + 1; 
     myTable := substr(inTable,pos);
  END IF;  
  for attributes in SELECT column_name
                  FROM information_schema.columns
                  WHERE table_schema = mySchema::NAME
                    AND table_name   = myTable::NAME
                  ORDER by ordinal_position
    LOOP
      fields := fields||','||attributes.column_name;
    END LOOP;
    fields := substring(fields,2);
    
EXECUTE format('create or replace view versions.%s_%s_diff as 
        select 
        row_number() OVER () AS rownum, ''insert'' as action, 
        %s from (
        select v.%s, st_asewkb(geom) 
        from %s_version as v 
        except
        select v.%s, st_asewkb(geom) 
        from versions.pgvscheckout(''%s'', 1) as c, 
             versions.%s_%s_version_log as v 
        where c.log_id = v.id_0 
          and c.systime = v.systime
      ) as foo
     union all
     select 
        row_number() OVER () AS rownum, ''delete'' as action, 
        %s from (
        select v.%s, st_asewkb(geom) 
        from versions.pgvscheckout(''%s'', 1) as c, 
             versions.%s_%s_version_log as v 
        where c.log_id = v.id_0 
          and c.systime = v.systime
        except
        select v.%s, st_asewkb(geom) 
        from %s_version as v) as foo ', mySchema, myTable, fields, fields, pg_typeof(_rowtype),fields, pg_typeof(_rowtype), mySchema, myTable, 
                                        fields, fields, pg_typeof(_rowtype), mySchema, myTable, fields, pg_typeof(_rowtype));
END
$$;


--
-- TOC entry 204 (class 1255 OID 360695)
-- Name: pgvsdrop(character varying); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvsdrop(_param1 character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $_$
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
    geomCol TEXT;
    geomType TEXT;
    geomDIM INTEGER;
    geomSRID INTEGER;
    testRec record;
    uncommitRec record;
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
    versionView := '"'||mySchema||'"."'||myTable||'_version"';
    versionLogTable := 'versions."'||mySchema||'_'||myTable||'_version_log"';
    versionLogTableType := 'versions."'||mySchema||'_'||myTable||'_version_log_type"';
    versionLogTableSeq := 'versions."'||mySchema||'_'||myTable||'_version_log_version_log_id_seq"';
    versionRevisionSeq := 'versions."'||mySchema||'_'||myTable||'_revision_seq"';
     select into testRec table_name
     from information_schema.tables
     where table_schema = mySchema::name
          and table_name = myTable::name;
     IF NOT FOUND THEN
       RAISE EXCEPTION 'Table %.% does not exist', mySchema,myTable;
       RETURN False;
     END IF;    
     
     testTab := mySchema||'_'||myTable||'_version_log';
     
     select into testRec table_name
     from information_schema.tables
     where table_schema = 'versions'
          and table_name = testTab::name;
     IF NOT FOUND THEN
       RAISE EXCEPTION 'Log Table %.% does not exist', mySchema,myTable;
       RETURN False;
     END IF;        
 
     
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
    
    execute 'delete from versions.version_tables 
               where version_table_id = '''||versionTableRec.vtid||''';';
    execute 'delete from versions.version_tables_logmsg 
               where version_table_id = '''||versionTableRec.vtid||''';';
    execute 'delete from versions.version_tags 
               where version_table_id = '''||versionTableRec.vtid||''';';               
  RETURN true ;                             
  END;
$_$;


--
-- TOC entry 199 (class 1255 OID 360696)
-- Name: pgvsinit(character varying); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvsinit(_param1 character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $_$
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
    versionTable := '"'||mySchema||'"."'||myTable||'_version_t"';
    versionView := '"'||mySchema||'"."'||myTable||'_version"';
    versionLogTable := 'versions."'||mySchema||'_'||myTable||'_version_log"';
    versionLogTableSeq := 'versions."'||mySchema||'_'||myTable||'_version_log_version_log_id_seq"';
    versionLogTableTmp := 'versions."'||mySchema||'_'||myTable||'_version_log_tmp"';
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
       
     testTab := '"versions"."'||myTable||'_version_log"';
     select into testRec table_name
     from information_schema.tables
     where table_schema = mySchema::name
          and table_name = testTab::name;
     IF FOUND THEN
       RAISE NOTICE 'Table %.% has been deleted', mySchema,testTab;
       execute 'drop table "'||mySchema||'"."'||testTab||'" cascade';
     END IF;    
  
     select into testRec f_table_name
     from geometry_columns
     where f_table_schema = mySchema::name
          and f_table_name = testTab::name;
          
     IF FOUND THEN
       execute 'delete from geometry_columns where f_table_schema='''||mySchema||''' and f_table_name='''||myTable||'_version_log''';
     END IF;    
     testTab := '"'||mySchema||'"."'||myTable||'_version"';
     select into testRec f_table_name
     from geometry_columns
     where f_table_schema = mySchema::name
          and f_table_name = testTab::name;
     IF FOUND THEN
       execute 'delete from geometry_columns where f_table_schema='''||mySchema||''' and f_table_name='''||myTable||'_version''';
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
       myPkey := '"'||myPkeyRec.column_name||'"';
    else
        RAISE EXCEPTION 'Table % has no Primarykey', mySchema||'.'||myTable;
        RETURN False;
    END IF;
    execute 'create table '||versionLogTable||' (LIKE "'||mySchema||'"."'||myTable||'");
             create sequence versions."'||mySchema||'_'||myTable||'_revision_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;
             alter table '||versionLogTable||' add column version_log_id bigserial;
             alter table '||versionLogTable||' add column action character varying;
             alter table '||versionLogTable||' add column project character varying default current_user;     
             alter table '||versionLogTable||' add column systime bigint default extract(epoch from now()::timestamp)*1000;    
             alter table '||versionLogTable||' add column revision bigint;
             alter table '||versionLogTable||' add column logmsg text;        
             alter table '||versionLogTable||' add column commit boolean DEFAULT False;
             alter table '||versionLogTable||' add constraint '||myTable||'_pkey primary key ('||myPkey||',project,systime,action);
             CREATE INDEX '||mySchema||'_'||myTable||'_version_log_id_idx ON '||versionLogTable||' USING btree (version_log_id);
             CREATE INDEX '||mySchema||'_'||myTable||'_systime_idx ON '||versionLogTable||' USING btree (systime);
             CREATE INDEX '||mySchema||'_'||myTable||'_project_idx ON '||versionLogTable||' USING btree (project);
             create index '||myTable||'_version_geo_idx on '||versionLogTable||' USING GIST ('||geomCol||');     
             
             insert into versions.version_tables (version_table_schema,version_table_name,version_view_schema,version_view_name,version_view_pkey,version_view_geometry_column) 
                 values('''||mySchema||''','''||myTable||''','''||mySchema||''','''||myTable||'_version'','''||testPKey.column_name||''','''||geomCol||''');';
    
                 
    for attributes in select *
                      from  information_schema.columns
                      where table_schema=mySchema::name
                        and table_name = myTable::name
        LOOP
          
          if attributes.column_default LIKE 'nextval%' then
             mySequence := attributes.column_default;
          ELSE
            if myPkey <> attributes.column_name then
              fields := fields||',"'||attributes.column_name||'"';
              type_fields := type_fields||',"'||attributes.column_name||'" '||attributes.udt_name||'';              
              newFields := newFields||',new."'||attributes.column_name||'"';
              oldFields := oldFields||',old."'||attributes.column_name||'"';
              updateFields := updateFields||',"'||attributes.column_name||'"=new."'||attributes.column_name||'"';
            END IF;
          END IF;
          IF attributes.column_name = 'archive' THEN
            archiveWhere := 'and archive=0';           
          END IF;  
        END LOOP;
        fields := substring(fields,2);
        newFields := substring(newFields,2);
        oldFields := substring(oldFields,2);
        updateFields := substring(updateFields,2);
        
        IF length(mySequence)=0 THEN
          RAISE EXCEPTION 'No Sequence defined for Table %.%', mySchema,myTable;
          RETURN False;
        END IF;
     
            
     execute 'create or replace view '||versionView||' as 
                SELECT v.'||myPkey||','||fields||'
                FROM "'||mySchema||'"."'||myTable||'" v,
                  ( SELECT "'||mySchema||'"."'||myTable||'".'||myPkey||'
                    FROM "'||mySchema||'"."'||myTable||'"
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
                SELECT v.'||myPkey||','||fields||'
                FROM '||versionLogTable||' v,
                 ( SELECT v_1.'||myPkey||',
                          max(v_1.version_log_id) AS version_log_id, min(action) as action
                   FROM '||versionLogTable||' v_1
                   WHERE NOT v_1.commit AND v_1.project::name = "current_user"()
                   GROUP BY v_1.'||myPkey||') foo
                WHERE v.version_log_id = foo.version_log_id and foo.action <> ''delete''';
     execute 'CREATE TRIGGER pgvs_version_record_trigger
              INSTEAD OF INSERT OR UPDATE OR DELETE
              ON '||versionView||'
              FOR EACH ROW
              EXECUTE PROCEDURE versions.pgvs_version_record();';                
     execute 'INSERT INTO '||versionLogTable||' ('||myPkey||','||fields||', action, revision, logmsg, commit ) 
                select '||myPkey||','||fields||', ''insert'' as action, 0 as revision, ''initial commit revision 0'' as logmsg, ''t'' as commit 
                from "'||mySchema||'"."'||myTable||'"';                          
     execute 'INSERT INTO versions.version_tables_logmsg(
                version_table_id, revision, logmsg) 
              SELECT version_table_id, 0 as revision, ''initial commit revision 0'' as logmsg FROM versions.version_tables where version_table_schema = '''||mySchema||''' and version_table_name = '''|| myTable||''''; 
     execute 'INSERT INTO versions.version_tags(
                version_table_id, revision, tag_text) 
              SELECT version_table_id, 0 as revision, ''initial commit revision 0'' as tag_text FROM versions.version_tables where version_table_schema = '''||mySchema||''' and version_table_name = '''|| myTable||''''; 
/*
    execute 'GRANT ALL ON TABLE '||versionLogTable||' TO version';
    execute 'GRANT ALL ON TABLE '||versionLogTableSeq||' TO version';
    execute 'GRANT ALL ON TABLE '||versionView||' TO version';
    execute 'GRANT ALL ON sequence versions."'||mySchema||'_'||myTable||'_revision_seq" to version'; 
*/    
                
  RETURN true ;                             
  END;
$_$;


--
-- TOC entry 205 (class 1255 OID 360698)
-- Name: pgvslogview(character varying); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvslogview(_param1 character varying) RETURNS SETOF logview
    LANGUAGE plpgsql
    AS $_$
    
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
    
    versionLogTable := 'versions."'||mySchema||'_'||myTable||'_version_log"';       
    logViewQry := 'select logt.revision, to_timestamp(logt.systime/1000), logt.project,  logt.logmsg
                           from  versions.version_tables as vt, versions.version_tables_logmsg as logt
                           where vt.version_table_id = logt.version_table_id
                             and vt.version_table_schema = '''||mySchema||'''
                             and vt.version_table_name = '''||myTable||''' 
                           order by revision desc';
                           
    for logs IN  EXECUTE logViewQry
    LOOP
      return next logs;    
    end loop;                       
  
  END;
$_$;


--
-- TOC entry 197 (class 1255 OID 360699)
-- Name: pgvsmerge(character varying, integer, character varying); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvsmerge("inTable" character varying, "targetGid" integer, "targetProject" character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $_$
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
    
    versionLogTable := 'versions."'||mySchema||'_'||myTable||'_version_log"';   
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
                                    
                                                                 
    execute 'SELECT array_to_string(array_agg(quote_ident(column_name::name)), '','')
             FROM information_schema.columns 
             WHERE (table_schema, table_name) = ($1, $2)' into cols using mySchema, myTable;  
     myTimestamp := round(extract(epoch from now()::timestamp)*1000);
    
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
       execute myDelete;
     end if;
                        
  
  RETURN True;
  
  END;
$_$;


--
-- TOC entry 206 (class 1255 OID 360700)
-- Name: pgvsrevert(character varying); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvsrevert(_param1 character varying) RETURNS integer
    LANGUAGE plpgsql
    AS $_$
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
    versionView := mySchema||'.'||myTable||'_version';
    versionLogTable := 'versions."'||mySchema||'_'||myTable||'_version_log"';
     select into testRec table_name
     from information_schema.tables
     where table_schema = mySchema::name
          and table_name = myTable::name;
     IF NOT FOUND THEN
       RAISE EXCEPTION 'Table %.% does not exist', mySchema,myTable;
       RETURN False;
     END IF;    
     
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
$_$;


--
-- TOC entry 201 (class 1255 OID 360701)
-- Name: pgvsrevision(); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvsrevision() RETURNS text
    LANGUAGE plpgsql
    AS $$
    
DECLARE
  revision TEXT;
  BEGIN	
    revision := '2.0.0';
  RETURN revision ;                             
  END;
$$;


--
-- TOC entry 207 (class 1255 OID 360702)
-- Name: pgvsrollback(character varying, integer); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvsrollback(_param1 character varying, _param2 integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $_$
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
    versionTable := '"'||mySchema||'"."'||myTable||'_version_t"';
    versionView := '"'||mySchema||'"."'||myTable||'_version"';
    versionLogTable := 'versions."'||mySchema||'_'||myTable||'_version_log"';
    
    for attributes in select *
                               from  information_schema.columns
                               where table_schema=mySchema::name
                                    and table_name = myTable::name
        LOOP
          
          if attributes.column_name not in ('action','project','systime','revision','logmsg','commit') then
            fields := fields||',v."'||attributes.column_name||'"';
            myInsertFields := myInsertFields||',"'||attributes.column_name||'"';
          END IF;
          END LOOP;
        fields := substring(fields,2);
        myInsertFields := substring(myInsertFields,2);
execute 'select versions.pgvsrevert('''||mySchema||'.'||myTable||''')';
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
 
      execute rollbackQry;
              
  RETURN true ;                             
  END;
$_$;


--
-- TOC entry 202 (class 1255 OID 360703)
-- Name: pgvsupdatecheck(character varying); Type: FUNCTION; Schema: versions; Owner: -
--

CREATE FUNCTION pgvsupdatecheck(_param1 character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $_$
    
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
$_$;


--
-- TOC entry 176 (class 1259 OID 360706)
-- Name: public_streets_revision_seq; Type: SEQUENCE; Schema: versions; Owner: -
--

CREATE SEQUENCE public_streets_revision_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 175 (class 1259 OID 360704)
-- Name: public_streets_version_log_version_log_id_seq; Type: SEQUENCE; Schema: versions; Owner: -
--

CREATE SEQUENCE public_streets_version_log_version_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 177 (class 1259 OID 360708)
-- Name: version_tables_version_table_id_seq; Type: SEQUENCE; Schema: versions; Owner: -
--

CREATE SEQUENCE version_tables_version_table_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 180 (class 1259 OID 360738)
-- Name: version_tables; Type: TABLE; Schema: versions; Owner: -
--

CREATE TABLE version_tables (
    version_table_id bigint DEFAULT nextval('version_tables_version_table_id_seq'::regclass) NOT NULL,
    version_table_schema character varying,
    version_table_name character varying,
    version_view_schema character varying,
    version_view_name character varying,
    version_view_pkey character varying,
    version_view_geometry_column character varying
);


--
-- TOC entry 178 (class 1259 OID 360710)
-- Name: version_tables_logmsg_id_seq; Type: SEQUENCE; Schema: versions; Owner: -
--

CREATE SEQUENCE version_tables_logmsg_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 179 (class 1259 OID 360712)
-- Name: version_tables_logmsg; Type: TABLE; Schema: versions; Owner: -
--

CREATE TABLE version_tables_logmsg (
    id bigint DEFAULT nextval('version_tables_logmsg_id_seq'::regclass) NOT NULL,
    version_table_id bigint,
    revision character varying,
    logmsg character varying,
    systime bigint DEFAULT (date_part('epoch'::text, now()) * (1000)::double precision),
    project character varying DEFAULT "current_user"()
);


--
-- TOC entry 181 (class 1259 OID 360750)
-- Name: version_tags_tags_id_seq; Type: SEQUENCE; Schema: versions; Owner: -
--

CREATE SEQUENCE version_tags_tags_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 182 (class 1259 OID 360752)
-- Name: version_tags; Type: TABLE; Schema: versions; Owner: -
--

CREATE TABLE version_tags (
    tags_id bigint DEFAULT nextval('version_tags_tags_id_seq'::regclass) NOT NULL,
    version_table_id bigint NOT NULL,
    revision bigint NOT NULL,
    tag_text character varying NOT NULL
);


--
-- TOC entry 1895 (class 2606 OID 360749)
-- Name: version_table_pkey; Type: CONSTRAINT; Schema: versions; Owner: -
--

ALTER TABLE ONLY version_tables
    ADD CONSTRAINT version_table_pkey PRIMARY KEY (version_table_id);


--
-- TOC entry 1893 (class 2606 OID 360737)
-- Name: version_tables_logmsg_pkey; Type: CONSTRAINT; Schema: versions; Owner: -
--

ALTER TABLE ONLY version_tables_logmsg
    ADD CONSTRAINT version_tables_logmsg_pkey PRIMARY KEY (id);


--
-- TOC entry 1897 (class 2606 OID 360763)
-- Name: version_tags_pkey; Type: CONSTRAINT; Schema: versions; Owner: -
--

ALTER TABLE ONLY version_tags
    ADD CONSTRAINT version_tags_pkey PRIMARY KEY (version_table_id, revision, tag_text);


--
-- TOC entry 1891 (class 1259 OID 360764)
-- Name: fki_version_tables_fkey; Type: INDEX; Schema: versions; Owner: -
--

CREATE INDEX fki_version_tables_fkey ON version_tables_logmsg USING btree (version_table_id) WITH (fillfactor='90');


--
-- TOC entry 1899 (class 2606 OID 360770)
-- Name: version_tables_fk; Type: FK CONSTRAINT; Schema: versions; Owner: -
--

ALTER TABLE ONLY version_tags
    ADD CONSTRAINT version_tables_fk FOREIGN KEY (version_table_id) REFERENCES version_tables(version_table_id) MATCH FULL ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 1898 (class 2606 OID 360765)
-- Name: version_tables_fkey; Type: FK CONSTRAINT; Schema: versions; Owner: -
--

ALTER TABLE ONLY version_tables_logmsg
    ADD CONSTRAINT version_tables_fkey FOREIGN KEY (version_table_id) REFERENCES version_tables(version_table_id) ON UPDATE CASCADE ON DELETE CASCADE;


-- Completed on 2016-12-02 09:44:44 CET

--
-- PostgreSQL database dump complete
--

