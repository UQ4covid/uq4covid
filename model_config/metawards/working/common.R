# Common R code for doing things with MetaWards
# TODO: This needs putting in to a proper library / 'header' type thing

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
