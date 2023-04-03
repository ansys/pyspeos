"""Provides the ``Modeler`` class."""
import logging
from pathlib import Path

from typing import TYPE_CHECKING, Optional, Union
from grpc import Channel

from ansys.pyoptics.speos.client import SpeosClient

DEFAULT_HOST = "localhost"
DEFAULT_PORT = "50051"


if TYPE_CHECKING:  # pragma: no cover
    from ansys.platform.instancemanagement import Instance


class Speos:
    """
    Provides interaction with the speos session.

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
        :func:`SpeosClient.close <ansys.pyoptics.speos.client.SpeosClient.close >`.
    timeout : Real, optional
        Timeout in seconds to achieve the connection.
        By default, 60 seconds.
    logging_level : int, optional
        The logging level to be applied to the client.
        By default, ``INFO``.
    logging_file : Optional[str, Path]
        The file to output the log, if requested. By default, ``None``.
    """

    """Constructor method for ``Modeler``."""

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
        """The ``Speos` instance client."""
        return self._client
