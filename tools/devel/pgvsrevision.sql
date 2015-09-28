/***************************************************************************
Function to get the pgvs Version Number
----------------------------------------------------------------------------
begin		: 2010-11.13
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

CREATE OR REPLACE FUNCTION versions.pgvsrevision()
  RETURNS TEXT AS
$BODY$    
DECLARE
  revision TEXT;
  BEGIN	
    revision := '1.8.4';
  RETURN revision ;                             

  END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;  
