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
import time

from ansys.speos.core import LOG  # Global logger
from ansys.speos.core.job import JobLink
from ansys.speos.core.job import messages as job_messages
from ansys.speos.core.proto_message_utils import protobuf_message_to_str
from ansys.speos.core.speos import SpeosClient
from conftest import config


def clean_all_dbs(speos_client: SpeosClient):
    for item in (
        speos_client.jobs().list()
        + speos_client.scenes().list()
        + speos_client.simulation_templates().list()
        + speos_client.sensor_templates().list()
        + speos_client.source_templates().list()
        + speos_client.intensity_templates().list()
        + speos_client.spectrums().list()
        + speos_client.vop_templates().list()
        + speos_client.sop_templates().list()
        + speos_client.parts().list()
        + speos_client.bodies().list()
        + speos_client.faces().list()
    ):
        item.delete()


def run_job_and_check_state(job: JobLink):
    job.start()
    job_state_res = job.get_state()
    while (
        job_state_res.state != job_messages.Job.State.FINISHED
        and job_state_res.state != job_messages.Job.State.STOPPED
        and job_state_res.state != job_messages.Job.State.IN_ERROR
    ):
        time.sleep(2)
        job_state_res = job.get_state()
        LOG.info(protobuf_message_to_str(job_state_res))
        if job_state_res.state == job_messages.Job.State.IN_ERROR:
            LOG.error(protobuf_message_to_str(job.get_error()))
            assert False


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
        return subprocess.call("docker exec " + config.get("SpeosContainerName") + ' test -f "' + path + '"', shell=True) == 0
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
