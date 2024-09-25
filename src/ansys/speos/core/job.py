# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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
from enum import Enum
from typing import Iterator, List, Mapping, Optional, Union

from ansys.api.speos.job.v2 import job_pb2 as messages
from ansys.api.speos.job.v2 import job_pb2_grpc as service
from ansys.api.speos.results.v1.ray_path_pb2 import RayPath

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str
from ansys.speos.core.scene import SceneLink

Job = messages.Job
"""Job protobuf class : ansys.api.speos.Job.v2.job_pb2.Job"""
Job.__str__ = lambda self: protobuf_message_to_str(self)


class JobLink(CrudItem):
    """Link object for job in database."""

    def __init__(self, db, key: str):
        super().__init__(db, key)
        self._actions_stub = db._actions_stub

    def __str__(self) -> str:
        """Return the string representation of the Job."""
        return str(self.get())

    def get(self) -> Job:
        """Get the datamodel from database.

        Returns
        -------
        job.Job
            Job datamodel.
        """
        return self._stub.read(self)

    def set(self, data: Job) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : job.Job
            New Job datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)

    # Actions
    def get_state(self) -> messages.GetState_Response:
        """
        Retrieve job state.

        Returns
        -------
        ansys.api.speos.job.v2.job_pb2.GetState_Response
            State of the job.
        """
        return self._actions_stub.GetState(messages.GetState_Request(guid=self.key))

    def start(self) -> None:
        """Start the job."""
        self._actions_stub.Start(messages.Start_Request(guid=self.key))

    def stop(self) -> None:
        """Stop the job."""
        self._actions_stub.Stop(messages.Stop_Request(guid=self.key))

    def get_error(self) -> messages.GetError_Response:
        """
        Retrieve job error.

        Returns
        -------
        ansys.api.speos.job.v2.job_pb2.GetError_Response
            Error of the job.
        """
        return self._actions_stub.GetError(messages.GetError_Request(guid=self.key))

    def get_results(self) -> messages.GetResults_Response:
        """
        Retrieve job results.

        Returns
        -------
        ansys.api.speos.job.v2.job_pb2.GetResults_Response
            Results of the job.
        """
        return self._actions_stub.GetResults(messages.GetResults_Request(guid=self.key))

    def get_progress_status(self) -> messages.GetProgressStatus_Response:
        """
        Retrieve job progress.

        Returns
        -------
        ansys.api.speos.job.v2.job_pb2.GetProgressStatus_Response
            Progress status of the job.
        """
        return self._actions_stub.GetProgressStatus(messages.GetProgressStatus_Request(guid=self.key))

    def get_ray_paths(self) -> Iterator[RayPath]:
        """
        Retrieve ray paths.
        Available for interactive simulation.

        Returns
        -------
        Iterator[ansys.api.speos.results.v1.ray_path_pb2.RayPath]
            Ray paths generated by the interactive simulation.
        """
        for rp in self._actions_stub.GetRayPaths(messages.GetRayPaths_Request(guid=self.key)):
            yield rp


class JobStub(CrudStub):
    """
    Database interactions for job.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a JobStub is to retrieve it from SpeosClient via jobs() method.
    Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> job_db = speos.client.jobs()

    """

    def __init__(self, channel):
        super().__init__(stub=service.JobsManagerStub(channel=channel))
        self._actions_stub = service.JobActionsStub(channel=channel)

    def create(self, message: Job) -> JobLink:
        """Create a new entry.

        Parameters
        ----------
        message : job.Job
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.job.JobLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(job=message))
        return JobLink(self, resp.guid)

    def read(self, ref: JobLink) -> Job:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.job.JobLink
            Link object to read.

        Returns
        -------
        job.Job
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("JobLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.job

    def update(self, ref: JobLink, data: Job):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.job.JobLink
            Link object to update.

        data : job.Job
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("JobLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, job=data))

    def delete(self, ref: JobLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.job.JobLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("JobLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[JobLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.job.JobLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: JobLink(self, x), guids))


class JobFactory:
    """Class to help creating Job message"""

    class Type(Enum):
        """Enum representing the type of the device desired"""

        CPU = 1
        GPU = 2

    class RaysNbPerSource:
        """
        Define number of rays emitted by a specific source.

        Parameters
        ----------
        source_path : str
            Source path allowing to point to a specific source instance in the scene.
            Example: "source_instance_name", "subscene_name/source_instance_name"
        rays_nb : int, optional
            Number of rays to be emitted.
            By default, ``100``.
        """

        def __init__(self, source_path: str, rays_nb: Optional[int] = 100) -> None:
            self.source_path = source_path
            self.rays_nb = rays_nb

    @staticmethod
    def new(
        name: str,
        scene: SceneLink,
        simulation_path: str,
        properties: Union[
            Job.DirectMCSimulationProperties,
            Job.InverseMCSimulationProperties,
            Job.InteractiveSimulationProperties,
        ],
        type: Optional[Type] = Type.CPU,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Job:
        """
        Create a Job message.

        Parameters
        ----------
        name : str
            Name of the job.
        scene : ansys.speos.core.scene.SceneLink
            Scene used as base to create a job.
        simulation_path : str
            Simulation path to choose a SimulationInstance in the selected scene.
            Example: "simulation_instance_name", "subscene_name/simulation_instance_name"
        properties : Union[JobFactory.direct_mc_props, JobFactory.inverse_mc_props, JobFactory.interactive_props]
            simulation properties, depends on the type of the simulation selected.
            Those properties can contains for example stop conditions for the job.
            Some methods can help to build needed messages:
            JobFactory.direct_mc_props(...), JobFactory.inverse_mc_props(...), JobFactory.interactive_props(...)
        type : ansys.speos.core.job.JobFactory.Type, optional
            Job type.
            By default, ``Type.CPU``.
        description : str, optional
            Description of the job.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the job.
            By default, ``None``.

        Returns
        -------
        job.Job
            Job message created.
        """
        job = Job(name=name, description=description)
        if metadata is not None:
            job.metadata.update(metadata)
        job.scene_guid = scene.key

        if len(simulation_path) == 0 and len(scene.get().simulations) > 0:
            job.simulation_path = scene.get().simulations[0].name
        else:
            job.simulation_path = simulation_path

        if type == JobFactory.Type.CPU:
            job.job_type = Job.Type.CPU
        elif type == JobFactory.Type.GPU:
            job.job_type = Job.Type.GPU

        if isinstance(properties, Job.DirectMCSimulationProperties):
            job.direct_mc_simulation_properties.CopyFrom(properties)
        elif isinstance(properties, Job.InverseMCSimulationProperties):
            job.inverse_mc_simulation_properties.CopyFrom(properties)
        elif isinstance(properties, Job.InteractiveSimulationProperties):
            job.interactive_simulation_properties.CopyFrom(properties)

        return job

    @staticmethod
    def direct_mc_props(
        stop_condition_rays_nb: Optional[int] = 200000,
        stop_condition_duration: Optional[int] = None,
        automatic_save_frequency: Optional[int] = 1800,
    ) -> Job.DirectMCSimulationProperties:
        """
        Create a DirectMCSimulationProperties message.

        Parameters
        ----------
        stop_condition_rays_nb : int, optional
            To stop the simulation after a certain number of rays were sent.
            None = no stop condition regarding rays emitted.
            By default, ``200000``.
        stop_condition_duration : int, optional
            To stop the simulation after a certain duration.
            None = no stop condition regarding duration.
            By default, ``None``.
        automatic_save_frequency : int, optional
            Define a backup interval (s). This option is useful when computing long simulations.
            But a reduced number of save operations naturally increases the simulation performance.
            By default, ``1800``.

        Returns
        -------
        ansys.api.speos.Job.v2.job_pb2.Job.DirectMCSimulationProperties
            DirectMCSimulationProperties message created.
        """
        props = Job.DirectMCSimulationProperties()
        if stop_condition_rays_nb is not None:
            props.stop_condition_rays_number = stop_condition_rays_nb
        if stop_condition_duration is not None:
            props.stop_condition_duration = stop_condition_duration
        props.automatic_save_frequency = automatic_save_frequency
        return props

    @staticmethod
    def inverse_mc_props(
        stop_condition_passes_number: Optional[int] = 5,
        stop_condition_duration: Optional[int] = None,
        automatic_save_frequency: Optional[int] = 1800,
    ) -> Job.InverseMCSimulationProperties:
        """
        Create a InverseMCSimulationProperties message.

        Parameters
        ----------
        stop_condition_passes_number : int, optional
            To stop the simulation after a certain number of passes.
            None = no stop condition regarding number of passes.
            By default, ``5``.
        stop_condition_duration : int, optional
            To stop the simulation after a certain duration.
            None = no stop condition regarding duration.
            By default, ``None``.
        automatic_save_frequency : int, optional
            Define a backup interval (s). This option is useful when computing long simulations.
            But a reduced number of save operations naturally increases the simulation performance.
            By default, ``1800``.

        Returns
        -------
        ansys.api.speos.Job.v2.job_pb2.Job.InverseMCSimulationProperties
            InverseMCSimulationProperties message created.
        """
        props = Job.InverseMCSimulationProperties()
        if stop_condition_passes_number is not None:
            props.optimized_propagation_none.stop_condition_passes_number = stop_condition_passes_number
        else:
            props.optimized_propagation_none.SetInParent()
        if stop_condition_duration is not None:
            props.stop_condition_duration = stop_condition_duration
        props.automatic_save_frequency = automatic_save_frequency
        return props

    @staticmethod
    def interactive_props(
        rays_nb_per_source: Optional[List[RaysNbPerSource]] = None,
        light_expert: Optional[bool] = False,
        impact_report: Optional[bool] = False,
    ) -> Job.InteractiveSimulationProperties:
        """
        Create a InteractiveSimulationProperties message.

        Parameters
        ----------
        rays_nb_per_source : List[ansys.speos.core.job.JobFactory.RaysNbPerSource], optional
            Defines number of rays that will be emitted by each source instance.
            Source instances that are not mentioned will default to 100 rays.
            None = each source instance will generate default number of rays, ie 100.
            By default, ``None``.
        light_expert : bool, optional
            True to generate a light expert file.
            By default, ``False``.
        impact_report : bool, optional
            True to integrate details like number of impacts, position and surface state to the HTML simulation report.
            By default, ``False``.

        Returns
        -------
        ansys.api.speos.Job.v2.job_pb2.Job.InteractiveSimulationProperties
            InteractiveSimulationProperties message created.
        """
        props = Job.InteractiveSimulationProperties()
        if rays_nb_per_source is not None:
            props.rays_number_per_sources.extend(
                [
                    Job.InteractiveSimulationProperties.RaysNumberPerSource(source_path=rnps.source_path, rays_nb=rnps.rays_nb)
                    for rnps in rays_nb_per_source
                ]
            )
        props.light_expert = light_expert
        props.impact_report = impact_report
        return props
