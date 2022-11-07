with head as (select max(revision) as head 
                      from versions."{schema}_{origin}_version_log"),
        delete as (select 'delete'::varchar as action, *
                        from (
                            select * from versions.pgvscheckout(NULL::"{schema}"."{origin}",
                            (select * from head)) 
                        except
                            select * from "{schema}"."{origin}_version"
                        ) as foo
        ),
        insert as (select 'insert'::varchar as action, *
                        from (
                            select * from "{schema}"."{origin}_version"
                        except
                            select * from versions.pgvscheckout(NULL::"{schema}"."{origin}",
                            (select * from head)) 
                        ) as foo
        )

select row_number() OVER () AS rownum, *
from (
    select * from delete
union
    select * from insert) as foo
