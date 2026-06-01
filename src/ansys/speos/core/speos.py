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

"""Provides the ``Speos`` class."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from grpc import Channel

from ansys.speos.core.generic.constants import (
    DEFAULT_VERSION,
)
from ansys.speos.core.kernel.client import SpeosClient

if TYPE_CHECKING:  # pragma: no cover
    from ansys.platform.instancemanagement import Instance


class Speos:
    """Allows the Speos session (client) to interact with the SpeosRPC server.

    Parameters
    ----------
    version : str
        The Speos server version to run, in the 3 digits format, such as "242".
        If unspecified, the version will be chosen as
        ``ansys.speos.core.kernel.client.LATEST_VERSION``.
    channel : grpc.Channel, optional
        gRPC channel for server communication.
        Can be created with ``ansys.speos.core.kernel.grpc.transport_options``
        and ``ansys.speos.core.kernel.grpc.cyberchannel``
        By default, ``None``.
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

    Examples
    --------
    >>> # Create default channel (to use when server was started with `SpeosRPC_Server.exe`)
    >>> speos = Speos()
    >>> # which is also equivalent to:
    >>> from ansys.speos.core.kernel.client import default_local_channel
    >>> channel = default_local_channel()
    >>> speos = Speos(channel=channel)
    >>> # Create channel with custom port and message size:
    >>> # use when server was started with `SpeosRPC_Server.exe --port 53123`
    >>> speos = Speos(channel=default_local_channel(port=53123, message_size=20000000))
    >>> # Create insecure channel, to use when server was started with:
    >>> # `SpeosRPC_Server.exe --transport-insecure`
    >>> from ansys.speos.core.kernel.grpc.transport_options import (
    ...     TransportOptions,
    ...     InsecureOptions,
    ...     TransportMode,
    ... )
    >>> transport = TransportOptions(
    ...     mode=TransportMode.INSECURE,
    ...     options=InsecureOptions(host=host, port=port, allow_remote_host=True),
    ... )
    >>> grpc_options = [("grpc.max_receive_message_length", message_size)]
    >>> speos = Speos(channel=transport.create_channel(grpc_options))
    """

    def __init__(
        self,
        version: str = DEFAULT_VERSION,
        channel: Optional[Channel] = None,
        remote_instance: Optional["Instance"] = None,
        timeout: Optional[int] = 60,
        logging_level: Optional[int] = logging.INFO,
        logging_file: Optional[Union[Path, str]] = None,
        speos_install_path: Optional[Union[Path, str]] = None,
    ):
        self._client = SpeosClient(
            version=version,
            channel=channel,
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
