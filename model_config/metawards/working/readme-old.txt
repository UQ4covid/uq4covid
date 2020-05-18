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

design.csv: The original [-1, 1] hypercube design to run the ensemble
uq3a_out.csv: An intermediate design matrix showing the configurations of the SEIR parameters
lockdown_states: parameters for a three-stage lockdown model
disease.csv: Design matrix for MetaWards created from the epidemiological parameters

Workflow steps
--------------

1) Generate a design of experiments over the epidemiological parameters defined in .\defs\limits.csv
2) Save the design (without headers) as design.csv
3) Run metawards as follows:
  > A: Run script uq3a to generate a mapping over the epidemiological variable limits:
	e.g.: "python ..\..\tools\make_design\uq3a.py design.csv .\defs\limits.csv uq3a_out.csv -f"
  > B: Run script uq3b to generate a mapping over the disease parameters for metawards
	e.g.: "python ..\..\tools\make_design\uq3b.py uq3a_out.csv disease.csv -f"
  > C: Run metawards using the disease mapping, lockdown process and ward data extractors
	e.g.: "Running the model: metawards -d ncov -o output --force-overwrite-output --input disease.csv -a ExtraSeedsLondon.dat --repeats 5 --extractor ..\..\tools\output_extractors\only_i_per_ward -u defs\lockdown_states.txt --iterator ..\..\tools\lockdown\iterate
4) [WIP] Run show_me_a_ward.R to see how to extract ward data
5) [WIP] UQ magic

Notes
-----

The working folder contains the older / in-progress stuff that is useful to know but not currently used

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