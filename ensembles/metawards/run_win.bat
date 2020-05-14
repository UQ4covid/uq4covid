@echo off
if not exist "output" md "output"
if not exist "plots" md "plots"
python ..\..\tools\make_design\make_design.py inputs\ensemble_job.json inputs -e -f
metawards -d ncov -o output --force-overwrite-output --input inputs\ncov_design_lh.csv -a ExtraSeedsLondon.dat --repeats 5 --extractor ..\..\tools\output_extractors\only_i_per_ward -u inputs\lockdown_states.txt --iterator ..\..\tools\lockdown\iterate
metawards-plot -i output\results.csv.bz2 -o plots