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

"""Provides the ``Speos`` class."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from grpc import Channel

from ansys.speos.core.generic.constants import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_VERSION,
    MAX_CLIENT_MESSAGE_SIZE,
)
from ansys.speos.core.kernel.client import SpeosClient

if TYPE_CHECKING:  # pragma: no cover
    from ansys.platform.instancemanagement import Instance


class Speos:
    """Allows the Speos session (client) to interact with the SpeosRPC server.

    Parameters
    ----------
    host : str, optional
        Host where the server is running.
        By default, ``ansys.speos.core.kernel.client.DEFAULT_HOST``.
    port : Union[str, int], optional
        Port number where the server is running.
        By default, ``ansys.speos.core.kernel.client.DEFAULT_PORT``.
    version : str
        The Speos server version to run, in the 3 digits format, such as "242".
        If unspecified, the version will be chosen as
        ``ansys.speos.core.kernel.client.LATEST_VERSION``.
    channel : ~grpc.Channel, optional
        gRPC channel for server communication.
        By default, ``None``.
    message_size: int
        Maximum Message size of a newly generated channel
        By default, ``MAX_CLIENT_MESSAGE_SIZE``.
    remote_instance : ansys.platform.instancemanagement.Instance
        The corresponding remote instance when the Speos Service
        is launched through PyPIM. This instance will be deleted when calling
        :func:`SpeosClient.close <ansys.speos.core.kernel.client.SpeosClient.close >`.
    timeout : Real, optional
        Timeout in seconds to achieve the connection.
        By default, 60 seconds.
    logging_level : int, optional
        The logging level to be applied to the client.
        By default, ``INFO``.
    logging_file : Optional[str, Path]
        The file to output the log, if requested. By default, ``None``.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: Union[str, int] = DEFAULT_PORT,
        version: str = DEFAULT_VERSION,
        channel: Optional[Channel] = None,
        message_size: int = MAX_CLIENT_MESSAGE_SIZE,
        remote_instance: Optional["Instance"] = None,
        timeout: Optional[int] = 60,
        logging_level: Optional[int] = logging.INFO,
        logging_file: Optional[Union[Path, str]] = None,
        speos_install_path: Optional[Union[Path, str]] = None,
    ):
        self._client = SpeosClient(
            host=host,
            port=port,
            version=version,
            channel=channel,
            message_size=message_size,
            remote_instance=remote_instance,
            timeout=timeout,
            logging_level=logging_level,
            logging_file=logging_file,
            speos_install_path=speos_install_path,
        )

    @property
    def client(self) -> SpeosClient:
        """The ``Speos`` instance client."""
        return self._client

    def close(self) -> bool:
        """Close the channel and deletes all Speos objects from memory.

        Returns
        -------
        bool
            Information if the server instance was terminated.

        Notes
        -----
        If an instance of the Speos Service was started using
        PyPIM, this instance will be deleted.
        """
        return self.client.close()
