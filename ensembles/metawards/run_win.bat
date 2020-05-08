@echo off
if not exist ".\output" md ".\output"
metawards -d ncov -o .\output --force-overwrite-output --input beta_table.csv -a ExtraSeedsLondon.dat --repeats 5
metawards-plot -i .\output\results.csv.bz2 -o .\