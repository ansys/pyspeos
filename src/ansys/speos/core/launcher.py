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

import os
from pathlib import Path
import subprocess

from ansys.speos.core import LOG as logger
from ansys.speos.core.kernel.client import DEFAULT_PORT, LATEST_VERSION
from ansys.speos.core.speos import Speos
from ansys.tools.path import get_available_ansys_installations

"""Maximum message length value accepted by the Speos RPC server"""
MAX_MESSAGE_LENGTH = int(os.environ.get("SPEOS_MAX_MESSAGE_LENGTH", 256 * 1024**2))

try:
    import ansys.platform.instancemanagement as pypim

    _HAS_PIM = True
except ModuleNotFoundError:  # pragma: no cover
    _HAS_PIM = False


def launch_speos(version: str = None) -> Speos:
    """Start the Speos Service remotely using the product instance management API.
    Prerequisite : product instance management configured.

    Parameters
    ----------
    version : str, optional
        The Speos Service version to run, in the 3 digits format, such as "242".
        If unspecified, the version will be chosen by the server.

    Returns
    -------
    ansys.speos.core.speos.Speos
        An instance of the Speos Service.
    """
    if not _HAS_PIM:  # pragma: no cover
        raise ModuleNotFoundError(
            "The package 'ansys-platform-instancemanagement' is required to use this function."
        )

    if pypim.is_configured():
        logger.info("Starting Speos service remotely. The startup configuration will be ignored.")
        return launch_remote_speos(version)


def launch_remote_speos(
    version: str = None,
) -> Speos:
    """Start the Speos Service remotely using the product instance management API.
    When calling this method, you need to ensure that you are in an
    environment where PyPIM is configured. This can be verified with
    :func:`pypim.is_configured <ansys.platform.instancemanagement.is_configured>`.

    Parameters
    ----------
    version : str, optional
        The Speos Service version to run, in the 3 digits format, such as "242".
        If unspecified, the version will be chosen by the server.

    Returns
    -------
    ansys.speos.core.speos.Speos
        An instance of the Speos Service.
    """
    if not _HAS_PIM:  # pragma: no cover
        raise ModuleNotFoundError(
            "The package 'ansys-platform-instancemanagement' is required to use this function."
        )

    pim = pypim.connect()
    instance = pim.create_instance(product_name="speos", product_version=version)
    instance.wait_for_ready()
    channel = instance.build_grpc_channel()
    return Speos(channel=channel, remote_instance=instance)


def launch_local_speos_rpc_server(
    version: str = LATEST_VERSION,
    port: str = DEFAULT_PORT,
    message_size: int = MAX_MESSAGE_LENGTH,
    logfile_loc: str = None,
    log_level: int = 20,
) -> Speos:
    """
    Launch Speos RPC server locally

    Parameters
    ----------
    version : str
        The Speos server version to run, in the 3 digits format, such as "242".
        If unspecified, the version will be chosen as ``ansys.speos.core.kernel.client.LATEST_VERSION``.
    port : Union[str, int], optional
        Port number where the server is running.
        By default, ``ansys.speos.core.kernel.client.DEFAULT_PORT``.
    message_size : int
        Maximum message length value accepted by the Speos RPC server,
        By default, value stored in environment variable SPEOS_MAX_MESSAGE_LENGTH or 268 435 456.
    logfile_loc : str
        location for the logfile to be created in.
    log_level : int
        The logging level to be applied to the server, integer values can be taken from logging module,
        By default, ``logging.WARNING`` = 20.


    Returns
    -------

    """
    versions = get_available_ansys_installations()
    ansys_loc = versions.get(int(version))
    if not ansys_loc:
        ansys_loc = os.environ.get("AWP_ROOT{}".format(version))
    if not ansys_loc:
        msg = (
            "Ansys installation directory is not found."
            " Please define AWP_ROOT{} environment variable"
        ).format(version)
        FileNotFoundError(msg)

    if os.name == "nt":
        speos_exec = os.path.join(ansys_loc, "Optical Products", "SPEOS_RPC", "SpeosRPC_Server.exe")
    else:
        speos_exec = os.path.join(ansys_loc, "OpticalProducts", "SPEOS_RPC", "SpeosRPC_Server.x")
    if not os.path.isfile(speos_exec):
        msg = "Ansys Speos RPC server version {} is not installed.".format(version)
        raise FileNotFoundError(msg)
    if not logfile_loc:
        if os.environ.get("temp"):
            logfile_loc = os.path.join(os.environ.get("temp"), ".ansys", "speos_rpc.log")
        else:
            logfile_loc = os.path.join(str(Path.cwd()), ".ansys", "speos_rpc.log")
        if not os.path.exists(os.path.dirname(logfile_loc)):
            Path.mkdir(Path(os.path.dirname(logfile_loc)))
    command = [
        speos_exec,
        "-p{}".format(port),
        "-m{}".format(message_size),
        "-l{}".format(logfile_loc),
    ]
    stdout_file = os.path.join(os.path.dirname(logfile_loc), "speos_out.txt")
    stderr_file = os.path.join(os.path.dirname(logfile_loc), "speos_err.txt")

    with open(stdout_file, "wb") as out, open(stderr_file, "wb") as err:
        subprocess.Popen(command, stdout=out, stderr=err)

    return Speos(host="localhost", port=port, logging_level=log_level, logging_file=logfile_loc)
