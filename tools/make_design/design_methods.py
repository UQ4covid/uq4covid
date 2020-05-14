from typing import List

# NOTE: This got put here to avoid circular dependencies
# TODO: Put these external somewhere?
__design_methods: List[dict] = \
    [
        {
            "name": "full_factorial",
            "required_parameter_keys": ["samples", "spacing"],
            "required_design_args": []
        },
        {
            "name": "latin_hypercube",
            "required_parameter_keys": [],
            "required_design_args": ["samples"]
        }
    ]
