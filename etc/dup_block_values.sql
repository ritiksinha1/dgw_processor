copy (
  select count(*) as count,
         institution,
         string_agg(requirement_id, ' ' order by requirement_id) as "RAs",
         block_type,
         block_value,
         string_agg('“'||title||'”', ' ') as titles
    from requirement_blocks
   where period_stop ~* '^9'
     and block_type in ('MAJOR', 'MINOR', 'CONC')
     and block_value !~* '^\d+$'
   group by institution, block_type, block_value
  having count(*) > 1
   order by block_type, institution, block_value)
  to '/Users/vickery/Projects/dgw_processor/etc/out/dup_block_values.csv' csv header
;
