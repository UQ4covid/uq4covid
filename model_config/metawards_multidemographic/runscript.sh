#!/bin/bash

mkdir -p raw_outputs

R CMD BATCH --no-restore --slave --no-save convertDesign.R 

export METAWARDSDATA=$HOME/Documents/covid/MetaWardsData

metawards --nproc 24 --nthreads 1 -d ncov.json -D demographics.json --mixer mix_pathways --mover move_pathways --input inputs/diseaseTest.dat -a ExtraSeedsLondon.dat -u lockdown_states.txt -o raw_outputs --force-overwrite-output --iterator iterate --start-date 2020/01/01 --theme simple --nsteps 100


