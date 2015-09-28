select *
from (
  select v.version_log_id, 6 as major_revision, 'delete' as action 
                from versions."public_streets_version_log" as v, 
                  (select v.id_0, max(v.version_log_id) as version_log_id
                   from versions."public_streets_version_log" as v,
                (select v.id_0
                 from versions."public_streets_version_log" as v,
                  (select v.id_0
                   from versions."public_streets_version_log" as v
                   where revision > 6
                   except
                   select v.id_0
                   from versions."public_streets_version_log" as v
                   where revision <= 6
                  ) as foo
                 where v.id_0 = foo.id_0) as foo
               where v.id_0 = foo.id_0    
               group by v.id_0) as foo
              where v.version_log_id = foo.version_log_id

              union

                select v.version_log_id, 2 as major_revision, v.action 
                from versions."public_streets_version_log" as v, 
                  (select v.id_0, max(v.version_log_id) as version_log_id
                   from versions."public_streets_version_log" as v,
                     (select v.id_0 
                      from versions."public_streets_version_log" as v
                      where revision > 6
                except
                 (select v.id_0
                  from versions."public_streets_version_log" as v
                  where revision > 6
                  except
                  select v.id_0
                  from versions."public_streets_version_log" as v
                  where revision <= 6
                 )) as foo
                 where revision <= 6 and v.id_0 = foo.id_0    
                group by v.id_0) as foo
              where v.version_log_id = foo.version_log_id) as foo1 full outer join

              (
                select v.version_log_id, 1 as minor_revision, 'delete' as action 
                from versions."public_streets_version_log" as v, 
                  (select v.id_0, max(v.version_log_id) as version_log_id
                   from versions."public_streets_version_log" as v,
                (select v.id_0
                 from versions."public_streets_version_log" as v,
                  (select v.id_0
                   from versions."public_streets_version_log" as v
                   where revision > 1
                   except
                   select v.id_0
                   from versions."public_streets_version_log" as v
                   where revision <= 1
                  ) as foo
                 where v.id_0 = foo.id_0) as foo
               where v.id_0 = foo.id_0    
               group by v.id_0) as foo
              where v.version_log_id = foo.version_log_id

              union

                select v.version_log_id, 1 as minor_revision , v.action 
                from versions."public_streets_version_log" as v, 
                  (select v.id_0, max(v.version_log_id) as version_log_id
                   from versions."public_streets_version_log" as v,
                     (select v.id_0 
                      from versions."public_streets_version_log" as v
                      where revision > 1
                except
                 (select v.id_0
                  from versions."public_streets_version_log" as v
                  where revision > 1
                  except
                  select v.id_0
                  from versions."public_streets_version_log" as v
                  where revision <= 1
                 )) as foo
                 where revision <= 1 and v.id_0 = foo.id_0    
                group by v.id_0) as foo
              where v.version_log_id = foo.version_log_id) as foo2 using (version_log_id)
              where foo2.version_log_id is NULL or foo1.version_log_id is NULL