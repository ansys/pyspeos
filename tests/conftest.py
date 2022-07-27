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
local_test_path = os.path.join(local_path, "assets")

# Load the local config file
local_config_file = os.path.join(local_path, "local_config.json")
if os.path.exists(local_config_file):
    with open(local_config_file) as f:
        config = json.load(f)
else:
    raise ValueError("Missing local_config.json file")

# Retrieve the path of tmp dir on the server
test_path = file_transfer.get_server_tmp_directory(config.get("SpeosServerPort"))
