#! /bin/bash
cat pgvshead.sql > ../createFunctions.sql
cat pgvsrevision.sql >> ../createFunctions.sql
cat pgvscommit.sql >> ../createFunctions.sql
cat pgvsinit.sql >> ../createFunctions.sql
cat pgvscheck.sql >> ../createFunctions.sql
cat pgvsmerge.sql >> ../createFunctions.sql
cat pgvsdrop.sql >> ../createFunctions.sql
cat pgvsrevert.sql >> ../createFunctions.sql
cat pgvslogview.sql >> ../createFunctions.sql
cat pgvsrollback.sql >> ../createFunctions.sql

cat pgvsrevision.sql > ../updateFunctions.sql
cat updatehead.sql >> ../updateFunctions.sql
cat pgvscommit.sql >> ../updateFunctions.sql
cat pgvsinit.sql >> ../updateFunctions.sql
cat pgvscheck.sql >> ../updateFunctions.sql
cat pgvsmerge.sql >> ../updateFunctions.sql
cat pgvsdrop.sql >> ../updateFunctions.sql
cat pgvsrevert.sql >> ../updateFunctions.sql
cat pgvslogview.sql >> ../updateFunctions.sql
cat pgvsrollback.sql >> ../updateFunctions.sql
