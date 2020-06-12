## load libraries
library(lhs)
library(dplyr)
library(tidyr)

## source dataTools
source("dataTools.R")

## set up parameter ranges
parRanges <- data.frame(
    parameter = c("r_zero", "scale_asymp", "incubation_time", "infectious_time", "hospital_time",
                  "ptC", "lock_1_restrict", "lock_2_release",
                  "pEA", "pIH", "pIRprime", "pHC", "pHRprime", "pCR"),
    lower = c(2.5, 0, 4, 2, 4, rep(0, 9)),
    upper = c(4, 1, 6, 4, 12, rep(1, 9)),
    stringsAsFactors = FALSE
)

## generate LHS design
design <- randomLHS(5, nrow(parRanges))
colnames(design) <- parRanges$parameter
design <- as_tibble(design)

## convert to input space
input <- convertDesignToInput(design, parRanges, "zero_one")

## convert input to disease
disease <- convertInputToDisease(input, 2)

## write to external files
dir.create("inputs")
write.table(disease, "inputs/disease.dat", row.names = FALSE, sep = " ", quote = FALSE)

