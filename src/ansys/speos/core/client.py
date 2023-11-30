"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
import logging
from pathlib import Path
import time
from typing import TYPE_CHECKING, Optional, Union

import grpc
from grpc._channel import _InactiveRpcError

from ansys.speos.core import LOG as logger
from ansys.speos.core.body import BodyLink, BodyStub
from ansys.speos.core.face import FaceLink, FaceStub
from ansys.speos.core.intensity_template import IntensityTemplateLink, IntensityTemplateStub
from ansys.speos.core.logger import PySpeosCustomAdapter
from ansys.speos.core.part import PartLink, PartStub
from ansys.speos.core.sensor_template import SensorTemplateLink, SensorTemplateStub
from ansys.speos.core.simulation_template import SimulationTemplateLink, SimulationTemplateStub
from ansys.speos.core.sop_template import SOPTemplateLink, SOPTemplateStub
from ansys.speos.core.source_template import SourceTemplateLink, SourceTemplateStub
from ansys.speos.core.spectrum import SpectrumLink, SpectrumStub
from ansys.speos.core.vop_template import VOPTemplateLink, VOPTemplateStub

DEFAULT_HOST = "localhost"
DEFAULT_PORT = "50051"


if TYPE_CHECKING:  # pragma: no cover
    from ansys.platform.instancemanagement import Instance


def wait_until_healthy(channel: grpc.Channel, timeout: float):
    """
    Wait until a channel is healthy before returning.

    Parameters
    ----------
    channel : ~grpc.Channel
        Channel to wait until established and healthy.
    timeout : float
        Timeout in seconds. One attempt will be made each 100 milliseconds
        until the timeout is exceeded.

    Raises
    ------
    TimeoutError
        Raised when the total elapsed time exceeds ``timeout``.
    """
    t_max = time.time() + timeout
    while time.time() < t_max:
        try:
            grpc.channel_ready_future(channel).result(timeout=timeout)
            return True
        except _InactiveRpcError:
            continue
    else:
        target_str = channel._channel.target().decode()
        raise TimeoutError(f"Channel health check to target '{target_str}' timed out after {timeout} seconds.")


class SpeosClient:
    """
    Wraps a speos gRPC connection.

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
        :func:`SpeosClient.close <ansys.speos.core.client.SpeosClient.close >`.
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
        host: Optional[str] = DEFAULT_HOST,
        port: Union[str, int] = DEFAULT_PORT,
        channel: Optional[grpc.Channel] = None,
        remote_instance: Optional["Instance"] = None,
        timeout: Optional[int] = 60,
        logging_level: Optional[int] = logging.INFO,
        logging_file: Optional[Union[Path, str]] = None,
    ):
        """Initialize the ``SpeosClient`` object."""
        self._closed = False
        self._remote_instance = remote_instance
        if channel:
            # Used for PyPIM when directly providing a channel
            self._channel = channel
            self._target = str(channel)
        else:
            self._target = f"{host}:{port}"
            self._channel = grpc.insecure_channel(self._target)
        # do not finish initialization until channel is healthy
        wait_until_healthy(self._channel, timeout)

        # once connection with the client is established, create a logger
        self._log = logger.add_instance_logger(name=self._target, client_instance=self, level=logging_level)
        if logging_file:
            if isinstance(logging_file, Path):
                logging_file = str(logging_file)
            self._log.log_to_file(filename=logging_file, level=logging_level)

        # Initialise databases
        self._faceDB = None
        self._bodyDB = None
        self._partDB = None
        self._sopTemplateDB = None
        self._vopTemplateDB = None
        self._spectrumDB = None
        self._intensityTemplateDB = None
        self._sourceTemplateDB = None
        self._sensorTemplateDB = None
        self._simulationTemplateDB = None

    @property
    def channel(self) -> grpc.Channel:
        """The gRPC channel of this client."""
        return self._channel

    @property
    def log(self) -> PySpeosCustomAdapter:
        """The specific instance logger."""
        return self._log

    @property
    def healthy(self) -> bool:
        """Return if the client channel if healthy."""
        if self._closed:
            return False
        try:
            grpc.channel_ready_future(self.channel).result(timeout=60)
            return True
        except:
            return False

    def target(self) -> str:
        """Get the target of the channel."""
        if self._closed:
            return ""
        return self._channel._channel.target().decode()

    def faces(self) -> FaceStub:
        """Get face database access."""
        if self._closed:
            raise ConnectionAbortedError()
        # connect to database
        if self._faceDB is None:
            self._faceDB = FaceStub(self._channel)
        return self._faceDB

    def bodies(self) -> BodyStub:
        """Get body database access."""
        if self._closed:
            raise ConnectionAbortedError()
        # connect to database
        if self._bodyDB is None:
            self._bodyDB = BodyStub(self._channel)
        return self._bodyDB

    def parts(self) -> PartStub:
        """Get part database access."""
        if self._closed:
            raise ConnectionAbortedError()
        # connect to database
        if self._partDB is None:
            self._partDB = PartStub(self._channel)
        return self._partDB

    def sop_templates(self) -> SOPTemplateStub:
        """Get sop template database access."""
        if self._closed:
            raise ConnectionAbortedError()
        # connect to database
        if self._sopTemplateDB is None:
            self._sopTemplateDB = SOPTemplateStub(self._channel)
        return self._sopTemplateDB

    def vop_templates(self) -> VOPTemplateStub:
        """Get vop template database access."""
        if self._closed:
            raise ConnectionAbortedError()
        # connect to database
        if self._vopTemplateDB is None:
            self._vopTemplateDB = VOPTemplateStub(self._channel)
        return self._vopTemplateDB

    def spectrums(self) -> SpectrumStub:
        """Get spectrum database access."""
        if self._closed:
            raise ConnectionAbortedError()
        # connect to database
        if self._spectrumDB is None:
            self._spectrumDB = SpectrumStub(self._channel)
        return self._spectrumDB

    def intensity_templates(self) -> IntensityTemplateStub:
        """Get intensity template database access."""
        if self._closed:
            raise ConnectionAbortedError()
        # connect to database
        if self._intensityTemplateDB is None:
            self._intensityTemplateDB = IntensityTemplateStub(self._channel)
        return self._intensityTemplateDB

    def source_templates(self) -> SourceTemplateStub:
        """Get source template database access."""
        if self._closed:
            raise ConnectionAbortedError()
        # connect to database
        if self._sourceTemplateDB is None:
            self._sourceTemplateDB = SourceTemplateStub(self._channel)
        return self._sourceTemplateDB

    def sensor_templates(self) -> SensorTemplateStub:
        """Get sensor template database access."""
        if self._closed:
            raise ConnectionAbortedError()
        # connect to database
        if self._sensorTemplateDB is None:
            self._sensorTemplateDB = SensorTemplateStub(self._channel)
        return self._sensorTemplateDB

    def simulation_templates(self) -> SimulationTemplateStub:
        """Get simulation template database access."""
        if self._closed:
            raise ConnectionAbortedError()
        # connect to database
        if self._simulationTemplateDB is None:
            self._simulationTemplateDB = SimulationTemplateStub(self._channel)
        return self._simulationTemplateDB

    def get_item(
        self, key: str
    ) -> Union[
        SOPTemplateLink,
        VOPTemplateLink,
        SpectrumLink,
        IntensityTemplateLink,
        SourceTemplateLink,
        SensorTemplateLink,
        SimulationTemplateLink,
        PartLink,
        BodyLink,
        FaceLink,
        None,
    ]:
        """Get item from key."""
        if self._closed:
            raise ConnectionAbortedError()
        for sop in self.sop_templates().list():
            if sop.key == key:
                return sop
        for vop in self.vop_templates().list():
            if vop.key == key:
                return vop
        for spec in self.spectrums().list():
            if spec.key == key:
                return spec
        for intens in self.intensity_templates().list():
            if intens.key == key:
                return intens
        for src in self.source_templates().list():
            if src.key == key:
                return src
        for ssr in self.sensor_templates().list():
            if ssr.key == key:
                return ssr
        for sim in self.simulation_templates().list():
            if sim.key == key:
                return sim
        for part in self.parts().list():
            if part.key == key:
                return part
        for body in self.bodies().list():
            if body.key == key:
                return body
        for face in self.faces().list():
            if face.key == key:
                return face
        return None

    def __repr__(self) -> str:
        """Represent the client as a string."""
        lines = []
        lines.append(f"Ansys Spoes client ({hex(id(self))})")
        lines.append(f"  Target:     {self._target}")
        if self._closed:
            lines.append(f"  Connection: Closed")
        elif self.healthy:
            lines.append(f"  Connection: Healthy")
        else:
            lines.append(f"  Connection: Unhealthy")  # pragma: no cover
        return "\n".join(lines)

    def close(self):
        """Close the channel.

        Notes
        -----
        If an instance of the Speos Service was started using
        PyPIM, this instance will be deleted.
        """
        if self._remote_instance:
            self._remote_instance.delete()
        self._closed = True
        self._channel.close()
        self._faceDB = None
        self._bodyDB = None
        self._partDB = None
        self._sopTemplateDB = None
        self._vopTemplateDB = None
        self._spectrumDB = None
        self._intensityTemplateDB = None
        self._sourceTemplateDB = None
        self._sensorTemplateDB = None
        self._simulationTemplateDB = None
