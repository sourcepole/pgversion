-- Diff code generated with pgModeler (PostgreSQL Database Modeler)
-- pgModeler version: 0.9.4
-- Diff date: 2022-11-16 17:05:29
-- Source model: pgvs_develop
-- Database: pgversion
-- PostgreSQL version: 13.0

-- [ Diff summary ]
-- Dropped objects: 0
-- Created objects: 1
-- Changed objects: 2

SET check_function_bodies = false;
-- ddl-end --

SET search_path=public,pg_catalog,versions;
-- ddl-end --


-- [ Created objects ] --
-- object: versions.pgvsincrementalupdate | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsincrementalupdate(varchar,varchar) CASCADE;

-- Prepended SQL commands --
DROP FUNCTION versions.pgvsincrementalupdate(varchar,varchar);
-- ddl-end --

CREATE FUNCTION versions.pgvsincrementalupdate (IN in_new_layer varchar, IN in_old_layer varchar)
	RETURNS text
	LANGUAGE plpgsql
	VOLATILE 
	CALLED ON NULL INPUT
	SECURITY INVOKER
	PARALLEL UNSAFE
	COST 100
	AS $$
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
       RAISE EXCEPTION 'Die Tabelle % entspricht nicht der Tabelle %', new_layer, old_layer;
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
  
    	old_fields := old_fields ||','|| attributes.att;
  					 
  -- Eine Spalte vom Typ Bool darf nicht in die Coalesce-Funktion gesetzt werden					 
    	IF old_pkey_rec.column_name <> attributes.att THEN
       		IF attributes.typ = 'bool' THEN
           		where_fields := where_fields ||' and n.'||attributes.att||'=o.'||attributes.att;					 
       		ELSE
  	   		where_fields := where_fields ||' and coalesce(n.'||attributes.att||'::text,'''')=coalesce(o.'||attributes.att||'::text,'''')';
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

$$;
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
                       to_timestamp(v1.systime/1000)::timestamp without time zone as start_time, 
                       to_timestamp(v2.systime/1000)::timestamp without time zone as end_time '||time_fields||'
                FROM '||versionLogTable||' v1
                LEFT JOIN '||versionLogTable||' v2 ON v2.id=v1.id AND v2.action=''delete''
                WHERE v1.action=''insert''';

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
    revision := '2.1.14';
  RETURN revision ;                             

  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsrevision() OWNER TO versions;
-- ddl-end --

