Description
-----------

This is an ensemble (set of samples) created from runs from the MetaWards model.
It was created from the inputs listed in the inputs folder. There are
There are 6 configurtaions, repeated 5 times to make 30 test runs

Source		Branch	Version string
------------------------------------------
MetaWards	devel	0.10.0-157-g1a2d14f
MetaWards data	master	0.4.0-5-g8969083

Inputs
------

ensemble_job.json: A description of the current job which created these samples
ensemble_job_epidemiology.csv: An intermediate design matrix showing the configurations of the SEIR parameters
lockdown_states: parameters for a three-stage lockdown model
ncov_design_lh.csv: Design matrix for MetaWards created from the epidemiological parameters

Run commands
------------

Building the design matrix: python ..\..\tools\make_design\make_design.py inputs\ensemble_job.json inputs -e -f

Running the model: metawards -d ncov -o output --force-overwrite-output --input inputs\ncov_design_lh.csv -a ExtraSeedsLondon.dat --repeats 5 --extractor ..\..\tools\output_extractors\only_i_per_ward -u inputs\lockdown_states.txt --iterator ..\..\tools\lockdown\iterate
metawards-plot -i output\results.csv.bz2 -o plots

Notes
-----

If you are re-running things to test, then the overwrite flags (-f on my tools and --force-overwrite-output on MetaWards) are useful to prevent halting when running long scripts.

Output description
------------------

In the output folder there are a series of subfolders which correspond to each of the 30 runs.
Each folder name corresponds to a row in the design matrix, with "i" being a decimal point, "v" being a variable separator and "x" being a repeat number.

Plots were automatically generated from metawards-plot

There is a demo R file that loads data for further analysis: show_me_a_ward.R. This has been modified to remove the need to copy the ward lookup and disease data and will now use the local MetaWardsData repo instead. 

Job files
---------

These can be simplified - it is highly likely that they will need to made a lot more intelligently than manually fudging some JSON. File extensions are not important, the converter will work with other types by interpreting them as JSON data regardless.