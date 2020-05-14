# This is an extractor for MetaWards that exposes the standard parameters + I for each ward
from only_i_per_ward import output_wards_i


def extract_get_i_per_ward(**kwargs):
    # Non-standard import location due to https://github.com/metawards/MetaWards/issues/59    
    from metawards.extractors._extract_default import extract_default
    print("Sending I per ward to the output stream")
    return extract_default(**kwargs) + [output_wards_i]
