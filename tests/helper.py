# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Unit Test Helper Module.

This module offers some helpers that can be useful in PySpeos unit tests.
For example a method to check file existence depending on if the file is in the docker container or
in local.
"""

from pathlib import Path
import subprocess
import time

from ansys.speos.core import log  # Global logger
from ansys.speos.core.kernel.job import JobLink, messages as job_messages
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str
from ansys.speos.core.speos import SpeosClient
from tests.conftest import config


def clean_all_dbs(speos_client: SpeosClient):
    """Clean all database entries of a current SpeosRPC client.

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        SpeosRPC server client

    Returns
    -------
    None
    """
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
    """Run a job and wait for state changes.

    Parameters
    ----------
    job:  ansys.speos.core.kernel.job.JobLink
        Job to be run and validated
    """
    job.start()
    job_state_res = job.get_state()
    while (
        job_state_res.state != job_messages.Job.State.FINISHED
        and job_state_res.state != job_messages.Job.State.STOPPED
        and job_state_res.state != job_messages.Job.State.IN_ERROR
    ):
        time.sleep(2)
        job_state_res = job.get_state()
        log.info(protobuf_message_to_str(job_state_res))
        if job_state_res.state == job_messages.Job.State.IN_ERROR:
            log.error(protobuf_message_to_str(job.get_error()))
            assert False


def does_file_exist(path):
    """Check file existence.

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
            subprocess.call(
                "docker exec "
                + config.get("SpeosContainerName")
                + ' test -f "'
                + Path(path).as_posix()
                + '"',
                shell=True,
            )
            == 0
        )
    else:
        return Path(path).exists()


def remove_file(path):
    """Remove file.

    Parameters
    ----------
    path (str) - path of the file.
    """
    if config.get("SpeosServerOnDocker"):
        subprocess.call(
            "docker exec " + config.get("SpeosContainerName") + ' rm -rf "' + path + '"',
            shell=True,
        )
    else:
        Path(path).unlink()
