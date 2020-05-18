This contains the configuration data to run MetaWards

limits.csv: Epidemiological variable limits for the model
lockdown_states: Definitions for the lock-down conditions
iterate.py: A custom MetaWards iterator that Controls how the model changes at each step, implements lock-down
only_i_per_ward.py: A custom MetaWards extractor that outputs the total number of infected people in each electoral ward
get_i_per_ward.py: A custom MetaWards extractor that outputs the standard data plus extra from only_i_per_ward.py