# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
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
import subprocess  # nosec B404
import tempfile
from typing import Optional, Union
import warnings

from ansys.tools.common.path import get_available_ansys_installations

from ansys.speos.core import LOG as LOGGER
from ansys.speos.core.generic.constants import (
    DEFAULT_PORT,
    DEFAULT_VERSION,
    MAX_CLIENT_MESSAGE_SIZE,
    MAX_SERVER_MESSAGE_LENGTH,
)
from ansys.speos.core.generic.general_methods import retrieve_speos_install_dir
from ansys.speos.core.kernel.client import default_local_channel
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


def _resolve_speos_rpc_version_path(
    version: Optional[Union[str, int]],
    speos_rpc_path: Optional[Union[str, Path]],
) -> Path:
    """Resolve the Speos RPC path from a version hint or automatic discovery.

    When *version* is provided the function resolves that exact version.
    Otherwise it tries :data:`DEFAULT_VERSION` first, then walks all
    installed Ansys versions (newest first) until a valid Speos RPC
    executable is found.

    Parameters
    ----------
    version : Optional[Union[str, int]]
        Requested Ansys version (e.g. ``261`` or ``"261"``).
        Pass *None* to enable automatic fallback logic.
    speos_rpc_path : Optional[Union[str, Path]]
        Explicit path hint forwarded to :func:`retrieve_speos_install_dir`.

    Returns
    -------
    Path
        Resolved directory containing the ``SpeosRPC_Server`` executable.

    Raises
    ------
    FileNotFoundError
        When no suitable Speos RPC installation can be found.
    """
    # --- explicit version: fail fast, no fallback -------------------------
    if version is not None:
        return retrieve_speos_install_dir(speos_rpc_path, str(version))

    # --- try default version first ----------------------------------------
    # Will raise FileNotFoundError if DEFAULT_VERSION (271) is not installed.
    try:
        return retrieve_speos_install_dir(speos_rpc_path, str(DEFAULT_VERSION))
    except FileNotFoundError as exc:
        warnings.warn(
            f"Default installation missing: {exc}. Falling back to the latest installed version.",
            UserWarning,
            stacklevel=2,
        )

    # --- walk available versions, newest first ----------------------------
    installations = get_available_ansys_installations()  # {261: 'C:\\...', ...}
    for available_version in sorted(installations, reverse=True):  # [261, 252, 251]
        try:
            path = retrieve_speos_install_dir(speos_rpc_path, str(available_version))
            warnings.warn(
                f"Using Speos RPC version {available_version}.",
                UserWarning,
                stacklevel=2,
            )
            return path
        except FileNotFoundError:
            warnings.warn(
                f"Speos RPC version {available_version} not found at installation location.",
                UserWarning,
                stacklevel=2,
            )

    raise FileNotFoundError("No Speos RPC installation was found.")


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
    # build_grpc_channel() returns an grpc._interceptor._Channel
    # As we need a grpc.Channel in Speos object -> build_grpc_channel()._channel
    # Not doing that was leading to issue when trying to find the target() of the channel.
    channel = instance.build_grpc_channel()._channel
    return Speos(channel=channel, remote_instance=instance)


def launch_local_speos_rpc_server(
    version: Optional[Union[str, int]] = None,
    port: Union[str, int] = DEFAULT_PORT,
    server_message_size: int = MAX_SERVER_MESSAGE_LENGTH,
    client_message_size: int = MAX_CLIENT_MESSAGE_SIZE,
    logfile_loc: Optional[str] = None,
    log_level: int = 20,
    speos_rpc_path: Optional[Union[Path, str]] = None,
    use_insecure: bool = False,
) -> Speos:
    """Launch Speos RPC server locally.

    This method only works for SpeosRPC server supporting UDS or WNUA transport.
    For release 251, minimal requirement is 2025.1.4.
    For release 252, minimal requirement is 2025.2.4.
    From release 261, grpc transport is always supported.

    .. warning::

        Do not execute this function with untrusted function argument or environment
        variables.
        See the :ref:`security guide<ref_security_consideration>` for details.

    Parameters
    ----------
    version : Union[str, int], optional
        The Speos server version to run, in the 3 digits format, such as "242".
        If unspecified, the version will be chosen as
        ``ansys.speos.core.kernel.client.LATEST_VERSION``.
        If ``ansys.speos.core.kernel.client.LATEST_VERSION`` is not available,
        the latest version installed on the machine will be tried to be used.
    port : Union[str, int], optional
        Port number where the server is running.
        By default, ``ansys.speos.core.kernel.client.DEFAULT_PORT``.
    server_message_size : int
        Maximum message length value accepted by the Speos RPC server.
        By default, value stored in environment variable SPEOS_MAX_MESSAGE_LENGTH or 268 435 456.
    client_message_size : int
        Maximum message size of a newly generated channel.
        By default, ``MAX_CLIENT_MESSAGE_SIZE``.
    logfile_loc : str, optional
        Location for the logfile to be created in.
        When *None*, defaults to the system temp directory.
    log_level : int
        The logging level to be applied to the server, integer values can be taken from
        the logging module.
        By default, ``logging.WARNING`` = 20.
    speos_rpc_path : Optional[Union[str, Path]]
        Explicit path to the Speos RPC executable or its parent directory.
        When *None* or empty the function performs automatic discovery.
    use_insecure : bool
        Whether to use insecure transport mode for the Speos RPC server.
        By default, ``False``.

    Returns
    -------
    ansys.speos.core.speos.Speos
        An instance of the Speos Service.

    Raises
    ------
    ValueError
        When any numeric parameter cannot be cast to int.
    FileNotFoundError
        When no valid Speos RPC installation can be located.
    """
    # --- validate numeric parameters --------------------------------------
    for name, value in [
        ("version", version),
        ("port", port),
        ("server_message_size", server_message_size),
        ("client_message_size", client_message_size),
    ]:
        if value is not None:
            try:
                int(value)
            except (ValueError, TypeError):
                raise ValueError(f"The '{name}' value is not a valid integer.")

    # --- resolve installation path ----------------------------------------
    speos_rpc_path = _resolve_speos_rpc_version_path(version, speos_rpc_path)

    # --- resolve log file -------------------------------------------------
    if logfile_loc:
        logfile = Path(logfile_loc)
        logfile_loc = logfile.parent if logfile.is_file() else Path(logfile_loc)
        logfile = logfile_loc / "speos_rpc.log" if not logfile.is_file() else logfile
    else:
        logfile_loc = Path(tempfile.gettempdir()) / ".ansys"
        logfile = logfile_loc / "speos_rpc.log"

    logfile_loc.mkdir(exist_ok=True)

    # --- resolve transport option -----------------------------------------
    if use_insecure:
        transport_option = "--transport_insecure"
    elif os.name == "nt":
        transport_option = "--transport_wnua"
    else:
        transport_option = "--transport_uds"

    # --- launch server ----------------------------------------------------
    speos_exec = speos_rpc_path / (
        "SpeosRPC_Server.exe" if os.name == "nt" else "SpeosRPC_Server.x"
    )
    command = [
        str(speos_exec),
        f"-p{port}",
        f"-m{server_message_size}",
        f"-l{str(logfile)}",
        transport_option,
    ]
    out, _ = tempfile.mkstemp(suffix="speos_out.txt", dir=logfile_loc)
    err, _ = tempfile.mkstemp(suffix="speos_err.txt", dir=logfile_loc)

    subprocess.Popen(command, stdout=out, stderr=err)  # nosec B603
    return Speos(
        channel=default_local_channel(port=port, message_size=client_message_size),
        logging_level=log_level,
        logging_file=logfile,
        speos_install_path=speos_rpc_path,
    )
