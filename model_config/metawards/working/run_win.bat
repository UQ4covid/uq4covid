@echo off
if not exist "output1" md "output1"
if not exist "plots1" md "plots1"
if not exist "output5" md "output5"
if not exist "plots5" md "plots5"
python ..\..\tools\make_design\uq3a.py design1.csv .\defs\limits.csv uq3a_out1.csv -f
python ..\..\tools\make_design\uq3a.py design5.csv .\defs\limits.csv uq3a_out5.csv -f
python ..\..\tools\make_design\uq3b.py uq3a_out1.csv disease1.csv -f
python ..\..\tools\make_design\uq3b.py uq3a_out5.csv disease5.csv -f
metawards -d ncov -o output5 --force-overwrite-output --input disease5.csv -a ExtraSeedsLondon.dat --repeats 5 --extractor ..\..\tools\output_extractors\only_i_per_ward -u defs\lockdown_states.txt --iterator ..\..\tools\lockdown\iterate --start-date 2020/01/01
metawards -d ncov -o output1 --force-overwrite-output --input disease1.csv -a ExtraSeedsLondon.dat --repeats 1 --extractor ..\..\tools\output_extractors\only_i_per_ward -u defs\lockdown_states.txt --iterator ..\..\tools\lockdown\iterate
metawards-plot -i output5\results.csv.bz2 -o plots5
metawards-plot -i output1\results.csv.bz2 -o plots1