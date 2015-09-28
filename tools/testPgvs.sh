#!/bin/bash
psql kappasys -U hdus -h www.kappasys.ch -c "drop schema versions cascade"
psql kappasys -U hdus -h www.kappasys.ch -c "delete from geometry_columns where f_table_name = 'test_poly_version' or f_table_name = 'test_poly_version_log'" 
rm -rf python/plugins/pgversion
wget http://www.kappasys.ch/qgis/pgversion.zip ~/python/plugins
mv pgversion.zip python/plugins
unzip python/plugins/pgversion.zip -d python/plugins
psql kappasys -U hdus -h www.kappasys.ch -c "create schema versions"
cd pgversion/tools/devel
./createFunctions.sh
cd 
cd .qgis
psql kappasys -U hdus -h www.kappasys.ch -f python/plugins/pgversion/tools/createFunctions.sql
rm -rf python/plugins/pgversion
cd pgversion/tools/devel
./createFunctions.sh
cd ../../..
svn co https://www.kappasys.ch/svn/pgversion/trunk python/plugins/pgversion
/usr/local/qgis_devel/bin/qgis kappatest2.qgs
