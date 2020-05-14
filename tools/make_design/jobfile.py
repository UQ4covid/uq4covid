import json as js
from typing import List
from utils import contains_required_keys, check_common_keys_in_dictionaries
from design_methods import __design_methods


# Job files are high-level descriptions that can remote run analyses
class JobFile:
    def __init__(self):
        self.file_name: str = ""
        self.description: dict = {}

    # Clear out the file name and description
    def clear(self) -> None:
        self.file_name = ""
        self.description = {}

    # Pull a job file from disk and load dictionary data
    def load_from_disk(self, location: str):
        # TODO: Should we re-raise or just return on the selected exceptions?
        try:
            with open(location) as j_file:
                self.description: dict = js.load(j_file)
                self.file_name = location
        except IOError as error:
            self.clear()
            print("File not found, or could not be opened " + error.msg)
            raise ValueError("Bad job file location")
        except js.JSONDecodeError as error:
            self.clear()
            print("JSON Decode problem: " + str(error.msg))
            raise ValueError("Bad job file format!")
        if not validate_job_description(self.description):
            self.clear()
            raise ValueError("Bad job file format!")
        return self

    # Return the disease name (this function is here in case the keys change)
    def get_disease_name(self) -> str:
        return self.description["disease"]

    # Find all the parameters that the current design modifies
    def list_transform_parameters(self) -> List[str]:
        transform_list: List[dict] = self.description["transform_stream"]
        p_list = [entry["disease_parameter"] for entry in transform_list]
        return list(set(p_list))

    # Return the number of outputs to metawards
    def get_num_stream_outputs(self) -> int:
        transform_stream: List[dict] = self.description["transform_stream"]
        return len(transform_stream)

    # Get a list of variables that this job outputs to metawards
    # NOTE: We currently correct for zero-base indexing here
    def get_transform_variables(self) -> List[str]:
        transform_stream: List[dict] = self.description["transform_stream"]
        return [output["disease_parameter"] + "[" + str(output["apply"] - 1) + "]" for output in transform_stream]


# Validate a job description file
def validate_job_description(data: dict) -> bool:
    # Check the dictionary for valid keys
    required_keys = ["parameter_list", "method", "disease", "transform_vars",
                     "transform_stream", "output_file"]
    if not contains_required_keys(data, required_keys):
        return False
    # Check the design algorithm is available and correct
    design = data["method"]
    if "algorithm" not in design:
        return False
    algorithm = next((item for item in __design_methods if item["name"] == design["algorithm"]), None)
    if algorithm is None:
        return False
    # Check for algorithm parameters if needed
    if not contains_required_keys(design["args"], algorithm["required_design_args"]):
        return False
    # Check parameter entries
    parameters: List[dict] = data["parameter_list"]
    parameter_keys = ["name", "min", "max"]
    parameter_keys += algorithm["required_parameter_keys"]
    if not check_common_keys_in_dictionaries(parameters, parameter_keys):
        return False
    # Check that there's a positive number of outputs
    num_transforms = data["transform_vars"]
    if not num_transforms > 0:
        return False
    # Check there are enough valid output assignments for the variables
    stream: List[dict] = data["transform_stream"]
    transform_keys = ["disease_parameter", "apply"]
    if not check_common_keys_in_dictionaries(stream, transform_keys):
        return False
    if len(stream) != data["transform_vars"]:
        return False
    # Check there is a valid file name to send to
    name: str = data["output_file"]
    if not name:
        return False
    return True
