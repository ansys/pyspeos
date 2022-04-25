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


local_path = os.path.dirname(os.path.realpath(__file__))


# Load the local config file
local_config_file = os.path.join(local_path, 'local_config.json')
if os.path.exists(local_config_file):
    with open(local_config_file) as f:
        config = json.load(f)
else:
    raise ValueError('Missing local_config.json file')


# set test_path var depending on if we are using the servers in a docker container or not
if config.get('SpeosServerOnDocker'):
    test_path = '/app/assets/'
else:
    test_path = local_path