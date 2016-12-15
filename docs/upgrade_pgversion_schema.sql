-- Database diff generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler  version: 0.9.0-alpha1
-- PostgreSQL version: 9.3

-- [ Diff summary ]
-- Dropped objects: 0
-- Created objects: 0
-- Changed objects: 3
-- Truncated tables: 0

SET check_function_bodies = false;
-- ddl-end --

SET search_path=public,pg_catalog,versions;
-- ddl-end --


-- [ Changed objects ] --
-- object: versions.pgvscommit | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvscommit(character varying,text) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvscommit ( _param1 character varying,  _param2 text)
	RETURNS SETOF versions.conflicts
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
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

-- object: versions.pgvslogview | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvslogview(character varying) CASCADE;
CREATE OR REPLACE FUNCTION versions.pgvslogview ( _param1 character varying)
	RETURNS SETOF versions.logview
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
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

    logViewQry := 'select logt.revision, to_timestamp(logt.systime/1000), logt.project,  logt.logmsg
                           from  versions.version_tables as vt left join versions.version_tables_logmsg as logt on (vt.version_table_id = logt.version_table_id)
                           where vt.version_table_schema = '''||mySchema||'''
                             and vt.version_table_name = '''||myTable||''' 
                           order by revision desc';

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
    revision := '2.1.1';
  RETURN revision ;                             

  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsrevision() OWNER TO versions;
-- ddl-end --



-- [ Created permissions ] --
-- object: grant_bc5b9e87fa | type: PERMISSION --
GRANT CREATE,USAGE
   ON SCHEMA versions
   TO versions;
-- ddl-end --

-- object: grant_040109aca4 | type: PERMISSION --
GRANT CREATE,USAGE
   ON SCHEMA versions
   TO postgres;
-- ddl-end --

-- object: grant_2b359c36b7 | type: PERMISSION --
GRANT CREATE,USAGE
   ON SCHEMA versions
   TO PUBLIC;
-- ddl-end --

-- object: grant_8a890802bb | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscheck(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: grant_71087a7341 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscheck(character varying)
   TO versions;
-- ddl-end --

-- object: grant_ab8f4ba2ef | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscheck(character varying)
   TO postgres;
-- ddl-end --

-- object: grant_0c3265b412 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscheckout(IN character varying,IN bigint)
   TO PUBLIC;
-- ddl-end --

-- object: grant_d7a15603fe | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscheckout(IN character varying,IN bigint)
   TO versions;
-- ddl-end --

-- object: grant_6b66465bec | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscommit(character varying,text)
   TO PUBLIC;
-- ddl-end --

-- object: grant_b860a287ed | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscommit(character varying,text)
   TO versions;
-- ddl-end --

-- object: grant_e6aee4488d | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscommit(character varying,text)
   TO postgres;
-- ddl-end --

-- object: grant_e92f60c1c1 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscommit(character varying,text)
   TO version;
-- ddl-end --

-- object: grant_ca919e0b10 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvscommit(character varying,text)
   TO pgversion_users;
-- ddl-end --

-- object: grant_a98e623900 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsdrop(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: grant_f34b070301 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsdrop(character varying)
   TO versions;
-- ddl-end --

-- object: grant_64b241f3f4 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsdrop(character varying)
   TO postgres;
-- ddl-end --

-- object: grant_113f6daf19 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsinit(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: grant_d67b489f0d | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsinit(character varying)
   TO versions;
-- ddl-end --

-- object: grant_59471459aa | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsinit(character varying)
   TO postgres;
-- ddl-end --

-- object: grant_058761c407 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsinit(character varying)
   TO version;
-- ddl-end --

-- object: grant_78d7fea6fa | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsinit(character varying)
   TO pgversion_users;
-- ddl-end --

-- object: grant_bc90ced3fa | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvslogview(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: grant_f51df11109 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvslogview(character varying)
   TO versions;
-- ddl-end --

-- object: grant_12644bfa4a | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvslogview(character varying)
   TO postgres;
-- ddl-end --

-- object: grant_7908bd53f2 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsmerge(character varying,integer,character varying)
   TO PUBLIC;
-- ddl-end --

-- object: grant_33ca632033 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsmerge(character varying,integer,character varying)
   TO versions;
-- ddl-end --

-- object: grant_3c8dd18f78 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsmerge(character varying,integer,character varying)
   TO postgres;
-- ddl-end --

-- object: grant_672adad542 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrevert(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: grant_599c4c10c7 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrevert(character varying)
   TO versions;
-- ddl-end --

-- object: grant_a97687cf68 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrevert(character varying)
   TO postgres;
-- ddl-end --

-- object: grant_fb6f7109fb | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrevision()
   TO PUBLIC;
-- ddl-end --

-- object: grant_23d9083d9f | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrevision()
   TO versions;
-- ddl-end --

-- object: grant_798af1727a | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrevision()
   TO postgres;
-- ddl-end --

-- object: grant_009da8982b | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrollback(character varying,integer)
   TO PUBLIC;
-- ddl-end --

-- object: grant_cb003484e2 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrollback(character varying,integer)
   TO versions;
-- ddl-end --

-- object: grant_018b6d3c5f | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsrollback(character varying,integer)
   TO postgres;
-- ddl-end --

-- object: grant_6eba990bcb | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsupdatecheck(character varying)
   TO PUBLIC;
-- ddl-end --

-- object: grant_97c9c3d020 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsupdatecheck(character varying)
   TO hdus;
-- ddl-end --

-- object: grant_6eee38f4f9 | type: PERMISSION --
GRANT EXECUTE
   ON FUNCTION versions.pgvsupdatecheck(character varying)
   TO postgres;
-- ddl-end --

-- object: grant_421f0513ae | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tables_logmsg
   TO versions;
-- ddl-end --

-- object: grant_4f53a0ca99 | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tables_logmsg
   TO postgres;
-- ddl-end --

-- object: grant_0d5313222a | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tables_logmsg
   TO PUBLIC;
-- ddl-end --

-- object: grant_789d6f3f7c | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tables
   TO versions;
-- ddl-end --

-- object: grant_efc90ff422 | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tables
   TO postgres;
-- ddl-end --

-- object: grant_b3d478305f | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tables
   TO PUBLIC;
-- ddl-end --

-- object: grant_91a6eeb8d3 | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tags
   TO versions;
-- ddl-end --

-- object: grant_ca710ef483 | type: PERMISSION --
GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER
   ON TABLE versions.version_tags
   TO hdus_cp;
-- ddl-end --

