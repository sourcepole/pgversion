/***************************************************************************
Functions and init for the Postgres Versioning System
----------------------------------------------------------------------------
begin		: 2010-07-31
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
create schema versions;  


CREATE OR REPLACE FUNCTION versions._pgvscreateversiontable()
  RETURNS void AS
$BODY$    
  
  BEGIN
    execute 'CREATE TABLE if exists versions.version_tables
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

-- DROP TABLE versions.version_tables_logmsg;

    execute 'CREATE TABLE if not exists versions.version_tables_logmsg
            (
               id bigserial NOT NULL,
               version_table_id bigint,
               revision character varying,
               logmsg character varying,
               CONSTRAINT version_tables_logmsg_pkey PRIMARY KEY (id)
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

CREATE OR REPLACE FUNCTION versions._pgvsdifftype()
  RETURNS void AS
$BODY$    
  
  BEGIN
    execute 'create type versions.diffrecord as (mykey int, action varchar, revision int, systime bigint, logmsg varchar)';
    EXCEPTION when others then
  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;      

  select versions._pgvscreateversiontable();
  select versions._pgvscreateconflicttype();
  select versions._pgvscreatelogviewtype();
  select versions._pgvscheckouttype();
  select versions._pgvsdifftype();


  
