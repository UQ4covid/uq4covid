@echo off
if not exist "output" md "output"
if not exist "plots" md "plots"
python ..\..\tools\make_design\uq3a.py design.csv .\defs\limits.csv uq3a_out.csv -f
python ..\..\tools\make_design\uq3b.py uq3a_out.csv disease.csv -f
metawards -d ncov -o output --force-overwrite-output --input disease.csv -a ExtraSeedsLondon.dat --repeats 5 --extractor ..\..\tools\output_extractors\only_i_per_ward -u defs\lockdown_states.txt --iterator ..\..\tools\lockdown\iterate
metawards-plot -i output\results.csv.bz2 -o plots