# R script to setup, run, load and transform data from the Bristol COVID model

library(stringr)

# Closest thing to 'header' / 'import' behaviour
if(!exists("test_str", mode="function")) source("common.R")
if(!exists("load_data", mode="function")) source("common.R")

# Load a ward trajectory file from beta[2] = 0.5 and too_ill_to_move[2] = 0.25
# Load run 2 of 5 ("x002")
wards <- load_data("output\\0i5v0i25x002\\wards_trajectory_I.csv.bz2")
ward_data <- load_data("Ward_Lookup.csv")

# Plot a ward with a given index
plot_ward <- function(index, prefix = "")
{
  # Column 1 is the simulation day
  slice_col = wards[,index + 1]
  
  # Find the ward data in the lookup table and create an identifier
  entry <- ward_data[ward_data$FID==index,]
  w_name <- str_c(entry$WD11NM, ", ", entry$LAD11NM)
  plot_title <- str_c(prefix, w_name)
  
  # Plot the disease progression across wards - note, this has 155 plots, it's not very good
  plot(slice_col, main = plot_title, xlab = "Day index", ylab = "Number of infected people")
}

# Plot all the wards in a given super/upper/mega/parent it is called council
plot_group <- function(parent_council)
{
  # Get data
  ex_ids <- ward_data[ward_data$LAD11NM==parent_council,]
  
  # Size the grid
  num_plots <- nrow(ex_ids)
  horizontal <- ceiling(sqrt(num_plots))
  vertical <- ceiling(num_plots / horizontal)
  
  # Occastionally errors can persist with errors between this and the second par call
  # TODO: Make this better / more robust
  old_gfx_settings <- par()
  par(mfrow = c(vertical, horizontal))
  
  # NOTE: the as.integer is needed to stop a bug in R where it literally sends "x[[FID]]" as a string
  apply(ex_ids, 1, function(x) plot_ward(as.integer(x[["FID"]])))
  par(old_gfx_settings)
}

# Select out a column at random
col <- sample(8588, 1)
plot_ward(col, "Infection count each day in ")    # Plot random ward
plot_group("Exeter")                              # Exeter
plot_group("Torbay")                              # Torbay
plot_group("Barnet")                              # This is where things get seeded (I think)

