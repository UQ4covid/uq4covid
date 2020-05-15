# R script to setup, run, load and transform data from the Bristol COVID model

stop("This is very old now and will not work: archive somewhere")

library(stringr)

# Closest thing to 'header' / 'import' behaviour
if(!exists("test_str", mode="function")) source("common.R")
if(!exists("load_data", mode="function")) source("common.R")

stop("This will stamp on the output folder, it is from an earlier example, comment this line to run")

#
# This explores the beta parameter as defined in the example runs
# FIXME: This is totally unfinished
experiment_example <- function()
{
  # This is a list of parameters to add to the design
  parameter_names <- c("beta")
  parameter_minimums <- c(0.00)
  parameter_maximums <- c(0.87)
  
  # TODO: Make this a matrix with names
  design_names <- c("beta")
  design_samples <- c(2.0)
  design_state_algorithms <- c("linear")
  
  parameters <- matrix(nrow=1, ncol=3)
  colnames(parameters) <- c("name", "min", "max")
  
  design_method <- "full_factorial"
  
  ### Build the JSON
  jstr <- "{"
  jstr <- str_c(jstr, " \"disease\": \"ncov\", \"stages\": 5, \"parameter_list\":[")
  
  for (row in parameters)
  {
    
  }
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
  disease_file = "ncov"                                     # JSON file to describe the disease
  num_repeats = as.integer(4)                               # Number of stochastic repeats
  out_folder = "output"                                     # Output folder
  num_stages <- 5                                           # Number of stages in the current disease  
  
  # TODO Design controls?
  
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
    command_str <- str_c(command_str, " -d ", clean)
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
beta_trajectory <- load_data("output\\0i0i0_87i0_87i0_87x005\\trajectory.csv.bz2")
plot(beta_trajectory$day, beta_trajectory$IW)

head(table)
head(beta_trajectory)
