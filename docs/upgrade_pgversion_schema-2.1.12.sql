-- Diff code generated with pgModeler (PostgreSQL Database Modeler)
-- pgModeler version: 0.9.4
-- Diff date: 2022-11-10 14:48:23
-- Source model: pgvs_develop
-- Database: pgversion
-- PostgreSQL version: 13.0

-- [ Diff summary ]
-- Dropped objects: 0
-- Created objects: 1
-- Changed objects: 1

SET check_function_bodies = false;
-- ddl-end --

SET search_path=public,pg_catalog,versions;
-- ddl-end --


-- [ Created objects ] --
-- object: versions.pgvsupdate | type: FUNCTION --
-- DROP FUNCTION IF EXISTS versions.pgvsupdate(varchar,varchar) CASCADE;
CREATE FUNCTION versions.pgvsupdate (IN in_new_layer varchar, IN in_out_layer varchar)
	RETURNS boolean
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
  old_geo_rec RECORD;
  new_geo_rec RECORD;
  pos INTEGER;
  integer_var INTEGER;		
  insub_query TEXT;
  
  
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
       RETURN False;
     END IF;
  	  
     select into new_geo_rec f_geometry_column, type as geom_type 
     from public.geometry_columns 
     where f_table_schema = new_schema 
      and  f_table_name = new_layer;
  
     IF NOT FOUND THEN
        RAISE EXCEPTION 'Die Tabelle % ist nicht als Geo-Layer in der Tabelle geometry_columns registriert', new_layer;
        RETURN False;
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
       RETURN False;
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
        RETURN False;
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
       RETURN False;
    END IF;			
  				
    
    insub_query := FORMAT('select %1$s as id 
	                   from %2$s.%3$s 
  	                   except 
  			   select o.%1$s 
  			   from %4$s.%5$s as n,%s$s.%2$S as o 
  			   where md5(n.%6$s::TEXT)=md5(o.%7$s::TEXT) 
  			     and o.%7$s && n.%6$s;',
  			   old_pkey_rec.column_name,
  			   old_schema,
  			   old_layer,
  			   new_schame,
  			   new_layer,
  			   new_geo_rec.f_geometry_column,
  			   old_geo_rec.f_geometry_column
  	           )	
  		
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
  RAISE NOTICE ' % Objekte wurden im Layer %.% archiviert',integer_var,old_schema,old_layer;
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
  RAISE NOTICE ' % Objekte wurden in den Layer %.% neu eingefuegt',integer_var,old_schema,old_layer;
  
  RETURN true;
END;

$$;
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
	PARALLEL UNSAFE
	COST 100
	AS $$

    
DECLARE
  revision TEXT;
  BEGIN	
    revision := '2.1.13';
  RETURN revision ;                             

  END;


$$;
-- ddl-end --
ALTER FUNCTION versions.pgvsrevision() OWNER TO versions;
-- ddl-end --

