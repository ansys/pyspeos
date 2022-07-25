"""
Unit Test Configuration Module
-------------------------------
Description
===========
This module loads the configuration for pyoptics unit tests.
The configuration can be changed by modifying a file called local_config.json in the same
directory as this module.
"""
import json
import os

from ansys.pyoptics.speos import file_transfer

local_path = os.path.dirname(os.path.realpath(__file__))


# Load the local config file
local_config_file = os.path.join(local_path, "local_config.json")
if os.path.exists(local_config_file):
    with open(local_config_file) as f:
        config = json.load(f)
else:
    raise ValueError("Missing local_config.json file")


# Upload assets to the server
number_of_files_to_upload = len(list(file_transfer.list_files(os.path.join(local_path, "assets/"))))
file_upload_result = file_transfer.upload_files_to_server(
    config.get("SpeosServerPort"), os.path.join(local_path, "assets/")
)
if len(file_upload_result) != number_of_files_to_upload:
    raise ValueError("Issue during assets transfer to server")
# Retrieve the path where assets are uploaded
test_path = file_transfer.get_server_tmp_directory(config.get("SpeosServerPort"))
