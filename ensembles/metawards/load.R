# R script to load and transform data from the Bristol COVID model

library(stringr)

#
# test_str: Check that an R object is a string
#
# IN:
#   - s: An object to test
#
# OUT:
#   - TRUE if valid, FALSE otherwise
#

test_str <- function(s)
{
  return (is.character(s) && length(s) == 1)
}

#
# load_data: Load a data frame (table) from the model output
# This is designed to be robust with respect to file names and different compression methods that
# might get added to MetaWards in the future. You can just one-line read.csv() directly.
#
# IN:
#   - file_name: A full or relative path which should be a string
#
# OUT:
#   - table: A data frame loaded from disk
#
# NOTES:
#
#   - If no file extension is supplied, '.csv', '.bz2' and '.csv.bz2' will be tried in that order
#   - If a file extension is supplied, but fails, '.bz2' is appended for a retry
#   - This will need to by synchronised with changes to compression options in the MetaWards codebase
#
# TODO: Should we be using scan() instead?
# TODO: What about zero-length tables / reads?
#

load_data <- function (file_name)
{
  fname <- file_name                                        # Copy file_name so it can be modified
  extensions <- c(".csv", ".bz2", ".csv.bz2")               # Possible file extensions
  
  if (!test_str(fname))
    stop("load_data: file_name must be a string")           # file_name is not a string
  
  extension <- str_extract(fname, regex("\\..*"))           # Check the file extension
  
  # If no extension was supplied, try loading a csv, compressed bare file, then compressed csv
  # TODO: the underlying call to file() in read.csv still spits out warnings on silent mode
  if (is.na(extension))
  {
    try_names <- str_c(fname, extensions)                   # Bind the extensions and file name
    for (str in try_names)
    {
      table <- try(read.csv(str), silent = TRUE)            # Try to load
      if (!inherits(table, 'try-error'))
        return (table)                                      # Success!
    }
  }
  
  # If there was an extension, try, then if it fails try a compressed extension
  table <- try(read.csv(fname), silent = TRUE)
  if (inherits(table, 'try-error'))
  {
    fname <- str_c(fname, ".bz2")                           # Add the .bz2 extension
    table <- read.csv(fname)                                # No try() to allow errors to raise
  }
  
  return (table)
}

# setup_job: Setup a job to run on MetaWards
# 
# TODO: This is a quick hack to allow people to run inside R without touching the scripts
#       It is not fully documented / tested yet.
#
setup_job <- function(r_params)
{
  # parmeters from R passed as r_params (emulators / seeds / sweeps / whatever)
  # Not used yet
  
  # Some quick defaults for testing, these will be replaced with parameters above
  #
  disease_file = "lurgy"                                    # JSON file to describe the disease
  num_repeats = as.integer(4)                               # Number of stochastic repeats
  out_folder = "output"                                     # Output folder
  
  # Create a folder
  if (!dir.exists(out_folder))
  {
    dir.create(out_folder)
  }

  # Build the command string
  command_str <- "metawards --force-overwrite-output -a ExtraSeedsLondon.dat"
    
  # Disease file
  if (test_str(disease_file))
  {
    # Clean up the file name as best as possible (good file names fall through)
    # TODO: This is probably redundant, better as a check further up for invalid names
    clean = str_extract(disease_file, regex("/^(.+)(\.[^ .]+)?$/"))
    command_str <- str_c(command_str, " -d ", disease_file)
  }
  else
    stop("No disease model selected")
  
  # Batch run mode
  if (num_repeats > 1)
    command_str <- str_c(command_str, " --repeats ", toString(num_repeats))
  
  command_str <- str_c(command_str, " -o ", out_folder)
  
  # Print to R
  print(str_c("Exec'ing: ", command_str))
  
  # Call MetaWards
  # TODO: system2() is a recommended replacement, but more complicated, do we need it?
  system(command_str)
}

# Uncomment this if you want to run MetaWards from here
#setup_job()

# Examples of calling load_data - it will work even if you forget / don't know the extension

table <- load_data("output\\results")           # 2 warnings
table <- load_data("output\\results.csv")       # 1 warning
table <- load_data("output\\results.csv.bz2")   # OK

# Plot the disease progression across wards - note, this has 155 plots, it's not very good
plot(table$date, table$IW)

# Load up trajectory file from beta = 0, 0, 0.87, 0.87, 0.87
beta_trajectory <- load_data("output\\0V0V0_87V0_87V0_87@005\\trajectory.csv.bz2")
plot(beta_trajectory$day, beta_trajectory$IW)

head(table)
head(beta_trajectory)
