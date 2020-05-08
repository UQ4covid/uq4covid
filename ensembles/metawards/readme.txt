Description
-----------

This is an ensemble (set of samples) created from runs from the MetaWards model.
It was created by enumerating the different combinations of beta across the 5 stages.
There are 31 individual configurations (technically 32, but beta being all zero is trivial), repeated 5 times to make 155 runs

Source		Branch	Version string
------------------------------------------
MetaWards	devel	0.8.5+120.g9b32b5a
MetaWards data	master	0.4.0-5-g8969083

Run command
-----------

metawards -d ncov -o .\output --force-overwrite-output --input beta_table.csv -a ExtraSeedsLondon.dat --repeats 5

Notes
-----

In the original ncov there were explicit "1.0/1.15" values. These do not convert correctly in the main model code (the disease file goes through a JSON parser) so have been truncated with a decimal equivalent (0.87)
There is an outstanding issue on the MetaWards codebase for windows users that requires a modification to the code to run. This modification does not affect the results.

See: https://github.com/metawards/MetaWards/issues/56#

Output description
------------------

In the output folder there are a series of subfolders which correspond to each of the 155 runs.
The folder name corresponds to the beta array contents separated by "V" characters followed by @ then the run repeat ID.

Plots were automatically generated from metawards-plot

There is a demo R file that loads data for further analysis. It can also call metawards but is setup for the tutorial, not the run above.
