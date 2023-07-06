"""
Unit Test Helper Module
-------------------------------
Description
===========
This module offers some helpers that can be useful in PySpeos unit tests.
For example a method to check file existence depending on if the file is in the docker container or in local.
"""
import os
import subprocess

from conftest import config


def does_file_exist(path):
    """Check file existence

    Parameters
    ----------
    path (str) - path of the file.

    Returns
    -------
    True if the file exists.

    Return type
    -----------
    bool
    """
    if config.get("SpeosServerOnDocker"):
        return (
            subprocess.call("docker exec " + config.get("SpeosContainerName") + ' test -f "' + path + '"', shell=True)
            == 0
        )
    else:
        return os.path.isfile(path)


def remove_file(path):
    """Remove file

    Parameters
    ----------
    path (str) - path of the file.
    """
    if config.get("SpeosServerOnDocker"):
        subprocess.call("docker exec " + config.get("SpeosContainerName") + ' rm -rf "' + path + '"', shell=True)
    else:
        os.remove(path)
