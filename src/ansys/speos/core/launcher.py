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

"""Module to start Speos RPC Server."""

import os
from pathlib import Path
import subprocess
import tempfile
from typing import Optional, Union

from ansys.speos.core import LOG as LOGGER
from ansys.speos.core.generic.constants import (
    DEFAULT_PORT,
    DEFAULT_VERSION,
    MAX_CLIENT_MESSAGE_SIZE,
    MAX_SERVER_MESSAGE_LENGTH,
)
from ansys.speos.core.generic.general_methods import retrieve_speos_install_dir
from ansys.speos.core.speos import Speos

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
        LOGGER.info("Starting Speos service remotely. The startup configuration will be ignored.")
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
    version: str = DEFAULT_VERSION,
    port: Union[str, int] = DEFAULT_PORT,
    server_message_size: int = MAX_SERVER_MESSAGE_LENGTH,
    client_message_size: int = MAX_CLIENT_MESSAGE_SIZE,
    logfile_loc: str = None,
    log_level: int = 20,
    speos_rpc_path: Optional[Union[Path, str]] = None,
) -> Speos:
    """Launch Speos RPC server locally.

    .. warning::
        Do not execute this function with untrusted input parameters.

    Parameters
    ----------
    version : str
        The Speos server version to run, in the 3 digits format, such as "242".
        If unspecified, the version will be chosen as
        ``ansys.speos.core.kernel.client.LATEST_VERSION``.
    port : Union[str, int], optional
        Port number where the server is running.
        By default, ``ansys.speos.core.kernel.client.DEFAULT_PORT``.
    server_message_size : int
        Maximum message length value accepted by the Speos RPC server,
        By default, value stored in environment variable SPEOS_MAX_MESSAGE_LENGTH or 268 435 456.
    client_message_size: int
        Maximum Message size of a newly generated channel
        By default, ``MAX_CLIENT_MESSAGE_SIZE``.
    logfile_loc : str
        location for the logfile to be created in.
    log_level : int
        The logging level to be applied to the server, integer values can be taken from logging
        module.
        By default, ``logging.WARNING`` = 20.
    speos_rpc_path : Optional[str, Path]
        location of Speos rpc executable

    Returns
    -------
    ansys.speos.core.speos.Speos
        An instance of the Speos Service.
    """
    speos_rpc_path = retrieve_speos_install_dir(speos_rpc_path, version)
    if os.name == "nt":
        speos_exec = speos_rpc_path / "SpeosRPC_Server.exe"
    else:
        speos_exec = speos_rpc_path / "SpeosRPC_Server.x"
    if not logfile_loc:
        logfile_loc = Path(tempfile.gettempdir()) / ".ansys"
        logfile = logfile_loc / "speos_rpc.log"
    else:
        logfile = Path(logfile_loc)
        if logfile.is_file():
            logfile_loc = logfile.parent
        else:
            logfile_loc = Path(logfile_loc)
            logfile = logfile_loc / "speos_rpc.log"
    if not logfile_loc.exists():
        logfile_loc.mkdir()
    command = [
        str(speos_exec),
        "-p{}".format(port),
        "-m{}".format(server_message_size),
        "-l{}".format(str(logfile)),
    ]
    out, stdout_file = tempfile.mkstemp(suffix="speos_out.txt", dir=logfile_loc)
    err, stderr_file = tempfile.mkstemp(suffix="speos_err.txt", dir=logfile_loc)

    subprocess.Popen(command, stdout=out, stderr=err)
    return Speos(
        host="localhost",
        port=port,
        message_size=client_message_size,
        logging_level=log_level,
        logging_file=logfile,
        speos_install_path=speos_rpc_path,
    )
