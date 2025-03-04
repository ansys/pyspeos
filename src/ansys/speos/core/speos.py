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

from ansys.speos.core.kernel.client import SpeosClient

DEFAULT_HOST = "localhost"
DEFAULT_PORT = "50098"


if TYPE_CHECKING:  # pragma: no cover
    from ansys.platform.instancemanagement import Instance


class Speos:
    """Allows the Speos session (client) to interact with the SpeosRPC server.

    Parameters
    ----------
    host : str, optional
        Host where the server is running.
        By default, ``DEFAULT_HOST``.
    port : Union[str, int], optional
        Port number where the server is running.
        By default, ``DEFAULT_PORT``.
    channel : ~grpc.Channel, optional
        gRPC channel for server communication.
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
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: Union[str, int] = DEFAULT_PORT,
        channel: Optional[Channel] = None,
        remote_instance: Optional["Instance"] = None,
        timeout: Optional[int] = 60,
        logging_level: Optional[int] = logging.INFO,
        logging_file: Optional[Union[Path, str]] = None,
    ):
        self._client = SpeosClient(
            host=host,
            port=port,
            channel=channel,
            remote_instance=remote_instance,
            timeout=timeout,
            logging_level=logging_level,
            logging_file=logging_file,
        )

    @property
    def client(self) -> SpeosClient:
        """The ``Speos`` instance client."""
        return self._client
