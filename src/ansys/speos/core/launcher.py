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

from ansys.speos.core import LOG as logger
from ansys.speos.core.speos import Speos

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
