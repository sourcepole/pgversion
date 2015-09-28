/***************************************************************************
Function to return diffs between the user editings and the HEAD revision
----------------------------------------------------------------------------
begin		: 2010-11-18
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
DROP FUNCTION IF EXISTS versions.pgvsdiff(character varying);
CREATE OR REPLACE FUNCTION versions.pgvsdiff(character varying, integer, integer) 
RETURNS setof versions.diffrecord AS
$BODY$
  DECLARE
    inTable ALIAS FOR $1;
    majorRevision ALIAS FOR $2;
    minorRevision ALIAS FOR $3;
    mySchema TEXT;
    myTable TEXT;
    myPkey TEXT;
    message TEXT;
    diffQry TEXT;
    myPkeyRec record;
    conflict BOOLEAN;
    pos integer;
    versionLogTable TEXT;
    diffRec versions.diffrecord%rowtype;

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
    
    versionLogTable := 'versions.'||mySchema||'_'||myTable||'_version_log';   

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

     diffQry := ' select '||myPkey||',
                         case 
                           when count(action) = 2 then ''update''
                           else max(action)
                         end as action,
                         revision, systime, logmsg
            from (
            select '||myPkey||', action, revision, systime, logmsg 
            from '||versionLogTable||' 
            where revision = '||majorRevision||'
            union
            select '||myPkey||', action, revision, systime, logmsg 
            from '||versionLogTable||'  
            where revision = '||minorRevision||'
              and '||myPkey||' in (select '||myPkey||' from '||versionLogTable||' where revision = '||majorRevision||')
            order by '||myPkey||', revision desc, action desc) as foo
            group by '||myPkey||', systime, revision, logmsg
            order by revision desc, '||myPkey;

            
select a.gid,
             case 
               when count(a.action) = 2 then 'update'
               else max(a.action)
             end as action, a.revision, a.systime
  
from versions.public_test_poly_version_log as a, (
  SELECT public_test_poly_version_log.gid, public_test_poly_version_log.name
  FROM versions.public_test_poly_version_log
  WHERE public_test_poly_version_log.revision=1
  Intersect
  SELECT public_test_poly_version_log.gid, public_test_poly_version_log.name
  FROM versions.public_test_poly_version_log
  WHERE public_test_poly_version_log.revision=3) as foo
where (a.gid = foo.gid and a.revision=1)    
   or (a.gid = foo.gid and a.revision=3)
group by a.gid, a.systime, a.revision, a.logmsg   
order by revision desc, a.gid            
            
            
            
RAISE EXCEPTION '%', diffQry;            
            
    for diffRec IN  EXECUTE diffQry
    LOOP
      return next diffRec;
    END LOOP;    

 
  END;


$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;

