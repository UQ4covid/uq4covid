
__all__ = ["extract_large"]


def extract_large(**kwargs):
    """This extractor extracts the default files, plus the
       "large" files, e.g. S, E, I and R for each ward.
    """

    from metawards.extractors import output_wards_trajectory
    from metawards.extractors import extract_default

    return extract_default(**kwargs) + [output_wards_trajectory]
