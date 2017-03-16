-- Database diff generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler  version: 0.9.0-alpha1
-- PostgreSQL version: 9.4

-- [ Diff summary ]
-- Dropped objects: 1
-- Created objects: 1
-- Changed objects: 2
-- Truncated tables: 0

SET check_function_bodies = false;
-- ddl-end --

SET search_path=public,pg_catalog,versions;
-- ddl-end --


-- [ Dropped objects ] --
DROP FUNCTION IF EXISTS versions._hasserial(character varying) CASCADE;
-- ddl-end --


-- [ Created objects ] --
-- object: versions._hasserial | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions._hasserial(IN character varying) CASCADE;
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



-- [ Changed objects ] --
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
    revision := '2.1.6';
  RETURN revision ;                             

  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsrevision() OWNER TO versions;
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


     sql := format('with checkout as 
                  (select foo2.%1$s::bigint as log_id, foo2.systime 
                  from (
                    select %1$s, max(systime) as systime
                    from %2$s
                    where commit = true and revision <= %3$s
                    group by %1$s) as foo,
                    (select * 
                     from %2$s
                    ) as foo2
                    where foo.%1$s = foo2.%1$s 
                      and foo.systime = foo2.systime 
                      and action <> ''delete'')

                select %4$s 
                from checkout as c,  %2$s as v 
                where c.log_id = v.%1$s  
                  and c.systime = v.systime', myPkey, versionLogTable, revision, fields);

     --RAISE EXCEPTION '%', sql;
     return QUERY EXECUTE sql;

  END;
$$;
-- ddl-end --



-- [ Created permissions ] --
-- object: grant_9377ca3578 | type: PERMISSION --
GRANT SELECT,UPDATE,USAGE
   ON SEQUENCE versions.version_tables_logmsg_id_seq
   TO versions;
-- ddl-end --

-- object: grant_efaee713ef | type: PERMISSION --
GRANT SELECT,UPDATE,USAGE
   ON SEQUENCE versions.version_tables_version_table_id_seq
   TO versions;
-- ddl-end --

-- object: grant_e974a2e416 | type: PERMISSION --
GRANT SELECT,UPDATE,USAGE
   ON SEQUENCE versions.version_tags_tags_id_seq
   TO versions;
-- ddl-end --

