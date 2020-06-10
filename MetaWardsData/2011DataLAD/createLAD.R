## load libraries
library(tidyverse)

## set path
pathToMetaWardsData <- "../../../MetaWardsData"
path <- paste0(pathToMetaWardsData, "/model_data/2011Data/")

## load different data sets
CBB2011 <- read_table2(paste0(path, "CBB2011.dat"), col_names = FALSE)
EW1 <- read_table2(paste0(path, "EW1.dat"), col_names = FALSE)
PlayMatrix <- read_table2(paste0(path, "PlayMatrix.dat"), col_names = FALSE)
PlaySize <- read_table2(paste0(path, "PlaySize.dat"), col_names = FALSE)
# seeds <- read_table2(paste0(path, "seeds.dat"), col_names = FALSE) ## not currently used
Ward_Lookup <- read_csv(paste0(path, "Ward_Lookup.csv"), guess_max = 3000)
WorkSize <- read_table2(paste0(path, "WorkSize.dat"), col_names = FALSE)

## CBB2011, Ward_Lookup, WorkSize and PlaySize correspond to a
## ward, indexed by the first column, and some movements of 
## positions in the other columns (I think)

## extract LAD lookup
LAD_Lookup <- select(Ward_Lookup, LAD11CD, LAD11NM) %>%
    distinct() %>%
    mutate(LADind = 1:n())

## set dummy indicator for Ward_Lookup
Ward_Lookup <- mutate(Ward_Lookup, ind = 1:n()) %>%
    left_join(LAD_Lookup)

## collapse to LAD level
CBB2011 <- left_join(CBB2011, select(Ward_Lookup, ind, LADind), by = c("X1" = "ind"))

## check for missing matches
stopifnot(all(!is.na(CBB2011$LADind)))

## for simplicity, set position to be average of (x, y)-coordinates
## (not sure how sensible this is? Ideally want LAD-level data)
CBB2011 <- group_by(CBB2011, LADind) %>%
    summarise(X2 = mean(X2), X3 = mean(X3)) %>%
    select(LADind, X2, X3)
    
## write file
write.table(CBB2011, "CBB2011.dat", row.names = FALSE, col.names = FALSE)
    
## collapse to LAD level
WorkSize <- left_join(WorkSize, select(Ward_Lookup, ind, LADind), by = c("X1" = "ind"))

## check for missing matches
stopifnot(all(!is.na(WorkSize$LADind)))

## sum in each LAD
WorkSize <- group_by(WorkSize, LADind) %>%
    summarise(X2 = sum(X2)) %>%
    select(LADind, X2)
    
## write file
write.table(WorkSize, "WorkSize.dat", row.names = FALSE, col.names = FALSE)
    
## collapse to LAD level
PlaySize <- left_join(PlaySize, select(Ward_Lookup, ind, LADind), by = c("X1" = "ind"))

## check for missing matches
stopifnot(all(!is.na(PlaySize$LADind)))

## sum in each LAD
PlaySize <- group_by(PlaySize, LADind) %>%
    summarise(X2 = sum(X2)) %>%
    select(LADind, X2)
    
## write file
write.table(PlaySize, "PlaySize.dat", row.names = FALSE, col.names = FALSE)

## I'm figuring EW1 contains movements from ward to ward, with 
## the first two columns denoting wards, and the last denoting
## number of moves

## collapse to LAD level
EW1 <- left_join(EW1, select(Ward_Lookup, ind, LADind), by = c("X1" = "ind")) %>%
    left_join(select(Ward_Lookup, ind, LADind), by = c("X2" = "ind"))

## check for missing matches
stopifnot(all(!is.na(EW1$LADind.x)))
stopifnot(all(!is.na(EW1$LADind.y)))

## sum in each LAD combination
EW1 <- group_by(EW1, LADind.x, LADind.y) %>%
    summarise(X3 = sum(X3)) %>%
    select(LADind.x, LADind.y, X3)
    
## write file
write.table(EW1, "EW1.dat", row.names = FALSE, col.names = FALSE)
  
## PlayMatrix (for some reason) contains proportions instead of counts
## but you can recover EW1 through PlayMatrix and WorkSize
## hence you can recover counts and calculate proportions correctly

PlayMatrix <- left_join(EW1, WorkSize, by = c("LADind.x" = "LADind")) %>%
    mutate(X3 = X3 / X2) %>%
    select(-X2)
    
## write file
write.table(PlayMatrix, "PlayMatrix.dat", row.names = FALSE, col.names = FALSE)


