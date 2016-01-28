#!/bin/bash
/usr/bin/pg_dump --host www.kappasys.ch --port 5432 --username "hdus" --no-password  --format plain --schema-only --no-owner --verbose --file "/home/hdus/dev/qgis/pgversion-plugin/pgversion/docs/create_versions_schema.sql" --schema "versions" "pgversion_development"
