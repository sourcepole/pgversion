-- Database diff generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler  version: 0.9.0-alpha1
-- PostgreSQL version: 9.6

-- [ Diff summary ]
-- Dropped objects: 1
-- Created objects: 1
-- Changed objects: 0
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



-- [ Created permissions ] --
-- object: grant_f6873826fd | type: PERMISSION --
GRANT SELECT,UPDATE,USAGE
   ON SEQUENCE versions.version_tables_logmsg_id_seq
   TO versions;
-- ddl-end --

-- object: grant_369e0b492d | type: PERMISSION --
GRANT SELECT,UPDATE,USAGE
   ON SEQUENCE versions.version_tables_version_table_id_seq
   TO versions;
-- ddl-end --

-- object: grant_c4dab013df | type: PERMISSION --
GRANT SELECT,UPDATE,USAGE
   ON SEQUENCE versions.version_tags_tags_id_seq
   TO versions;
-- ddl-end --

