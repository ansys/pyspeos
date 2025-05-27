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

"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""

import logging
import os
from pathlib import Path
import subprocess
import time
from typing import TYPE_CHECKING, List, Optional, Union

import grpc
from grpc._channel import _InactiveRpcError

from ansys.api.speos.part.v1 import body_pb2, face_pb2, part_pb2
from ansys.speos.core.generic.constants import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_VERSION,
    MAX_CLIENT_MESSAGE_SIZE,
)
from ansys.speos.core.generic.general_methods import retrieve_speos_install_dir
from ansys.speos.core.kernel.body import BodyLink, BodyStub
from ansys.speos.core.kernel.face import FaceLink, FaceStub
from ansys.speos.core.kernel.intensity_template import (
    IntensityTemplateLink,
    IntensityTemplateStub,
)
from ansys.speos.core.kernel.job import JobLink, JobStub
from ansys.speos.core.kernel.part import PartLink, PartStub
from ansys.speos.core.kernel.scene import SceneLink, SceneStub
from ansys.speos.core.kernel.sensor_template import (
    SensorTemplateLink,
    SensorTemplateStub,
)
from ansys.speos.core.kernel.simulation_template import (
    SimulationTemplateLink,
    SimulationTemplateStub,
)
from ansys.speos.core.kernel.sop_template import (
    SOPTemplateLink,
    SOPTemplateStub,
)
from ansys.speos.core.kernel.source_template import (
    SourceTemplateLink,
    SourceTemplateStub,
)
from ansys.speos.core.kernel.spectrum import SpectrumLink, SpectrumStub
from ansys.speos.core.kernel.vop_template import (
    VOPTemplateLink,
    VOPTemplateStub,
)
from ansys.speos.core.logger import LOG as LOGGER, PySpeosCustomAdapter

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
        except (_InactiveRpcError, grpc.FutureTimeoutError):
            continue
    else:
        target_str = channel._channel.target().decode()
        raise TimeoutError(
            f"Channel health check to target '{target_str}' timed out after {timeout} seconds."
        )


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
    speos_install_path : Optional[str, Path]
        location of Speos rpc executable
    """

    def __init__(
        self,
        host: Optional[str] = DEFAULT_HOST,
        port: Union[str, int] = DEFAULT_PORT,
        version: str = DEFAULT_VERSION,
        channel: Optional[grpc.Channel] = None,
        message_size: int = MAX_CLIENT_MESSAGE_SIZE,
        remote_instance: Optional["Instance"] = None,
        timeout: Optional[int] = 60,
        logging_level: Optional[int] = logging.INFO,
        logging_file: Optional[Union[Path, str]] = None,
        speos_install_path: Optional[Union[Path, str]] = None,
    ):
        """Initialize the ``SpeosClient`` object."""
        self._closed = False
        self._remote_instance = remote_instance
        if speos_install_path:
            speos_install_path = retrieve_speos_install_dir(speos_install_path, version)
            if os.name == "nt":
                self.__speos_exec = str(speos_install_path / "SpeosRPC_Server.exe")
            else:
                self.__speos_exec = str(speos_install_path / "SpeosRPC_Server.x")
        else:
            self.__speos_exec = None
        if not version:
            self._version = DEFAULT_VERSION
        else:
            self._version = version
        if channel:
            # Used for PyPIM when directly providing a channel
            self._channel = channel
            self._target = str(channel)
        else:
            self._host = host
            self._port = port
            self._target = f"{host}:{port}"
            self._channel = grpc.insecure_channel(
                self._target,
                options=[("grpc.max_receive_message_length", message_size)],
            )
        # do not finish initialization until channel is healthy
        wait_until_healthy(self._channel, timeout)

        # once connection with the client is established, create a logger
        self._log = LOGGER.add_instance_logger(
            name=self._target, client_instance=self, level=logging_level
        )
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
        self._sceneDB = None
        self._jobDB = None

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
        except BaseException:
            return False

    def target(self) -> str:
        """Get the target of the channel."""
        if self._closed:
            return ""
        return self._channel._channel.target().decode()

    def faces(self) -> FaceStub:
        """Get face database access."""
        self.__closed_error()
        # connect to database
        if self._faceDB is None:
            self._faceDB = FaceStub(self._channel)
        return self._faceDB

    def bodies(self) -> BodyStub:
        """Get body database access."""
        self.__closed_error()
        # connect to database
        if self._bodyDB is None:
            self._bodyDB = BodyStub(self._channel)
        return self._bodyDB

    def parts(self) -> PartStub:
        """Get part database access."""
        self.__closed_error()
        # connect to database
        if self._partDB is None:
            self._partDB = PartStub(self._channel)
        return self._partDB

    def sop_templates(self) -> SOPTemplateStub:
        """Get sop template database access."""
        self.__closed_error()
        # connect to database
        if self._sopTemplateDB is None:
            self._sopTemplateDB = SOPTemplateStub(self._channel)
        return self._sopTemplateDB

    def vop_templates(self) -> VOPTemplateStub:
        """Get vop template database access."""
        self.__closed_error()
        # connect to database
        if self._vopTemplateDB is None:
            self._vopTemplateDB = VOPTemplateStub(self._channel)
        return self._vopTemplateDB

    def spectrums(self) -> SpectrumStub:
        """Get spectrum database access."""
        self.__closed_error()
        # connect to database
        if self._spectrumDB is None:
            self._spectrumDB = SpectrumStub(self._channel)
        return self._spectrumDB

    def intensity_templates(self) -> IntensityTemplateStub:
        """Get intensity template database access."""
        self.__closed_error()
        # connect to database
        if self._intensityTemplateDB is None:
            self._intensityTemplateDB = IntensityTemplateStub(self._channel)
        return self._intensityTemplateDB

    def source_templates(self) -> SourceTemplateStub:
        """Get source template database access."""
        self.__closed_error()
        # connect to database
        if self._sourceTemplateDB is None:
            self._sourceTemplateDB = SourceTemplateStub(self._channel)
        return self._sourceTemplateDB

    def sensor_templates(self) -> SensorTemplateStub:
        """Get sensor template database access."""
        self.__closed_error()
        # connect to database
        if self._sensorTemplateDB is None:
            self._sensorTemplateDB = SensorTemplateStub(self._channel)
        return self._sensorTemplateDB

    def simulation_templates(self) -> SimulationTemplateStub:
        """Get simulation template database access."""
        self.__closed_error()
        # connect to database
        if self._simulationTemplateDB is None:
            self._simulationTemplateDB = SimulationTemplateStub(self._channel)
        return self._simulationTemplateDB

    def scenes(self) -> SceneStub:
        """Get scene database access."""
        self.__closed_error()
        # connect to database
        if self._sceneDB is None:
            self._sceneDB = SceneStub(self._channel)
        return self._sceneDB

    def jobs(self) -> JobStub:
        """Get job database access."""
        self.__closed_error()
        # connect to database
        if self._jobDB is None:
            self._jobDB = JobStub(self._channel)
        return self._jobDB

    def __closed_error(self):
        """Check if closed."""
        if self._closed:
            raise ConnectionAbortedError()

    def __getitem__(
        self, key: str
    ) -> Union[
        SOPTemplateLink,
        VOPTemplateLink,
        SpectrumLink,
        IntensityTemplateLink,
        SourceTemplateLink,
        SensorTemplateLink,
        SimulationTemplateLink,
        SceneLink,
        JobLink,
        PartLink,
        BodyLink,
        FaceLink,
        None,
    ]:
        """Get item from key.

        Parameters
        ----------
        key : str
            Key of the item (also named guid).

        Returns
        -------
        Union[ansys.speos.core.kernel.sop_template.SOPTemplateLink, \
ansys.speos.core.kernel.vop_template.VOPTemplateLink, \
ansys.speos.core.kernel.spectrum.SpectrumLink, \
ansys.speos.core.kernel.intensity_template.IntensityTemplateLink, \
ansys.speos.core.kernel.source_template.SourceTemplateLink, \
ansys.speos.core.kernel.sensor_template.SensorTemplateLink, \
ansys.speos.core.kernel.simulation_template.SimulationTemplateLink, \
ansys.speos.core.kernel.scene.SceneLink, \
ansys.speos.core.kernel.job.JobLink, \
ansys.speos.core.kernel.part.PartLink, \
ansys.speos.core.kernel.body.BodyLink, \
ansys.speos.core.kernel.face.FaceLink, \
None]
            Link object corresponding to the key - None if no objects corresponds to the key.
        """
        self.__closed_error()
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
        for sce in self.scenes().list():
            if sce.key == key:
                return sce
        for job in self.jobs().list():
            if job.key == key:
                return job
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

    def get_items(
        self, keys: List[str], item_type: type
    ) -> Union[
        List[SOPTemplateLink],
        List[VOPTemplateLink],
        List[SpectrumLink],
        List[IntensityTemplateLink],
        List[SourceTemplateLink],
        List[SensorTemplateLink],
        List[SimulationTemplateLink],
        List[SceneLink],
        List[JobLink],
        List[PartLink],
        List[BodyLink],
        List[FaceLink],
    ]:
        """Get items from keys.

        Parameters
        ----------
        keys : List[str]
            Keys of the items (also named guids).
        item_type : type
            Type of items expected

        Returns
        -------
        Union[List[ansys.speos.core.kernel.sop_template.SOPTemplateLink], \
List[ansys.speos.core.kernel.vop_template.VOPTemplateLink], \
List[ansys.speos.core.kernel.spectrum.SpectrumLink], \
List[ansys.speos.core.kernel.intensity_template.IntensityTemplateLink], \
List[ansys.speos.core.kernel.source_template.SourceTemplateLink], \
List[ansys.speos.core.kernel.sensor_template.SensorTemplateLink], \
List[ansys.speos.core.kernel.simulation_template.SimulationTemplateLink], \
List[ansys.speos.core.kernel.scene.SceneLink], \
List[ansys.speos.core.kernel.job.JobLink], \
List[ansys.speos.core.kernel.part.PartLink], \
List[ansys.speos.core.kernel.body.BodyLink], \
List[ansys.speos.core.kernel.face.FaceLink]]
            List of Link objects corresponding to the keys - Empty if no objects corresponds to the
            keys.
        """
        self.__closed_error()

        if item_type == SOPTemplateLink:
            return [x for x in self.sop_templates().list() if x.key in keys]
        elif item_type == VOPTemplateLink:
            return [x for x in self.vop_templates().list() if x.key in keys]
        elif item_type == SpectrumLink:
            return [x for x in self.spectrums().list() if x.key in keys]
        elif item_type == IntensityTemplateLink:
            return [x for x in self.intensity_templates().list() if x.key in keys]
        elif item_type == SourceTemplateLink:
            return [x for x in self.source_templates().list() if x.key in keys]
        elif item_type == SensorTemplateLink:
            return [x for x in self.sensor_templates().list() if x.key in keys]
        elif item_type == SimulationTemplateLink:
            return [x for x in self.simulation_templates().list() if x.key in keys]
        elif item_type == SceneLink:
            return [x for x in self.scenes().list() if x.key in keys]
        elif item_type == JobLink:
            return [x for x in self.jobs().list() if x.key in keys]
        elif item_type == PartLink:
            guids = set(self.parts()._stubMngr.List(part_pb2.List_Request()).guids)
            return [PartLink(self.parts(), key=k) for k in keys if k in guids]
        elif item_type == BodyLink:
            guids = set(self.bodies()._stubMngr.List(body_pb2.List_Request()).guids)
            return [BodyLink(self.bodies(), key=k) for k in keys if k in guids]
        elif item_type == FaceLink:
            guids = set(self.faces()._stubMngr.List(face_pb2.List_Request()).guids)
            return [FaceLink(self.faces(), key=k) for k in keys if k in guids]
        return []

    def __repr__(self) -> str:
        """Represent the client as a string."""
        lines = []
        lines.append(f"Ansys Speos client ({hex(id(self))})")
        lines.append(f"  Target:     {self._target}")
        if self._closed:
            lines.append("  Connection: Closed")
        elif self.healthy:
            lines.append("  Connection: Healthy")
        else:
            lines.append("  Connection: Unhealthy")  # pragma: no cover
        return "\n".join(lines)

    def close(self):
        """Close the channel.

        Returns
        -------
        bool
            Information if the server instance was terminated.

        Notes
        -----
        If an instance of the Speos Service was started using
        PyPIM, this instance will be deleted.
        """
        wait_time = 0
        if self._remote_instance:
            self._remote_instance.delete()
        elif self._host in ["localhost", "0.0.0.0", "127.0.0.1"] and self.__speos_exec:
            self.__close_local_speos_rpc_server()
            while self.healthy and wait_time < 15:
                time.sleep(1)
                wait_time += 1  # takes some seconds to close rpc server
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
        self._sceneDB = None
        self._jobDB = None
        if wait_time >= 15:
            self._closed = not self.healthy
            return self._closed
        else:
            self._closed = True
            return self._closed

    def __close_local_speos_rpc_server(self):
        command = [self.__speos_exec, "-s{}".format(self._port)]
        subprocess.run(command, check=True)
