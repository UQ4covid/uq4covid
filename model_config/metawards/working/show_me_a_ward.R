# R script to setup, run, load and transform data from the Bristol COVID model

library(stringr)

# Closest thing to 'header' / 'import' behaviour
if(!exists("test_str", mode="function")) source("common.R")
if(!exists("load_data", mode="function")) source("common.R")

# Plot a ward with a given index
# NOTE: Apparently R can pass data by reference (it's read only) - Check this
plot_ward <- function(index, prefix = "", data, lookup)
{
  start_marker = grep("start_symptom", colnames(data))
  slice_col = data[,index + start_marker]
  
  # Find the ward data in the lookup table and create an identifier
  entry <- lookup[lookup$FID==index,]
  w_name <- str_c(entry$WD11NM, ", ", entry$LAD11NM)
  plot_title <- str_c(prefix, w_name)
  
  # Plot
  plot(slice_col, main = plot_title, xlab = "Day index", ylab = "Number of infected people")
}

# Plot all the wards in a given super/upper/mega/parent it is called council
plot_group <- function(parent_council, data, lookup)
{
  # Get data
  ex_ids <- lookup[lookup$LAD11NM==parent_council,]
  
  # Size the grid
  num_plots <- nrow(ex_ids)
  horizontal <- ceiling(sqrt(num_plots))
  vertical <- ceiling(num_plots / horizontal)
  
  # Occastionally errors can persist with errors between this and the second par call
  # TODO: Make this better / more robust
  old_gfx_settings <- par()
  par(mfrow = c(vertical, horizontal))
  
  # NOTE: the as.integer is needed to stop a bug in R where it literally sends "x[[FID]]" as a string
  apply(ex_ids, 1, function(x) plot_ward(as.integer(x[["FID"]]), data = data, lookup = lookup))
  par(old_gfx_settings)
}

# Load a ward trajectory file
ward_data <- load_data("output5\\0i747963v0i747963v0i222911v1i0v0i395117v0i128829v0i690946x003\\wards_trajectory_I.csv.bz2")
ward_info <- load_data(str_c(Sys.getenv("METAWARDSDATA"), "\\model_data\\2011Data\\", "Ward_Lookup.csv"))

# Select out a column at random
col <- sample(8588, 1)
plot_ward(col, "Infection count each day in ", ward_data, ward_info)    # Plot random ward
plot_group("Exeter", ward_data, ward_info)                              # Exeter
plot_group("Torbay", ward_data, ward_info)                              # Torbay
plot_group("Barnet", ward_data, ward_info)                              # This is where things get seeded (I think)

