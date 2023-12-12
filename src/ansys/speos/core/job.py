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


class JobLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)
        self._actions_stub = db._actions_stub

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> Job:
        return self._stub.read(self)

    def set(self, data: Job) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)

    # Actions
    def get_state(self) -> messages.GetState_Response:
        return self._actions_stub.GetState(messages.GetState_Request(guid=self.key))

    def start(self) -> None:
        return self._actions_stub.Start(messages.Start_Request(guid=self.key))

    def stop(self) -> None:
        return self._actions_stub.Stop(messages.Stop_Request(guid=self.key))

    def get_error(self) -> messages.GetError_Response:
        return self._actions_stub.GetError(messages.GetError_Request(guid=self.key))

    def get_results(self) -> messages.GetResults_Response:
        return self._actions_stub.GetResults(messages.GetResults_Request(guid=self.key))

    def get_progress_status(self) -> messages.GetInformation_Response:
        return self._actions_stub.GetInformation(messages.GetInformation_Request(guid=self.key))

    def get_ray_paths(self) -> Iterator[RayPath]:
        for rp in self._actions_stub.GetRayPaths(messages.GetRayPaths_Request(guid=self.key)):
            yield rp


class JobStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.JobsManagerStub(channel=channel))
        self._actions_stub = service.JobActionsStub(channel=channel)

    def create(self, message: Job) -> JobLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(job=message))
        return JobLink(self, resp.guid)

    def read(self, ref: JobLink) -> Job:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("JobLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.job

    def update(self, ref: JobLink, data: Job):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("JobLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, job=data))

    def delete(self, ref: JobLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("JobLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[JobLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: JobLink(self, x), guids))


class JobFactory:
    """Class to help creating Job message"""

    Type = Enum("Type", ["CPU", "GPU"])

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
        scene : SceneLink
            Scene used as base to create a job.
        simulation_path : str
            Simulation path to choose a SimulationInstance in the selected scene.
            Example: "simulation_instance_name", "subscene_name/simulation_instance_name"
        properties : Union[Job.DirectMCSimulationProperties, Job.InverseMCSimulationProperties, Job.InteractiveSimulationProperties]
            simulation properties, depends on the type of the simulation selected.
            Those properties can contains for example stop conditions for the job.
            Some methods can help to build needed messages:
            JobFactory.direct_mc_props(...), JobFactory.inverse_mc_props(...), JobFactory.interactive_props(...)
        type : Type, optional
            Job type.
            By default, ``JobFactory.Type.CPU``.
        description : str, optional
            Description of the job.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the job.
            By default, ``None``.

        Returns
        -------
        Job
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
        Job.DirectMCSimulationProperties
            DirectMCSimulationProperties message created.
        """
        props = Job.DirectMCSimulationProperties()
        if stop_condition_rays_nb is not None:
            props.stop_condition_rays_number = stop_condition_rays_nb
        if stop_condition_duration is not None:
            props.stop_condition_duration = stop_condition_duration
        props.automatic_save_frequency = automatic_save_frequency
        return props

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
        Job.InverseMCSimulationProperties
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

    def interactive_props(
        rays_nb_per_source: Optional[List[RaysNbPerSource]] = None,
        light_expert: Optional[bool] = False,
        impact_report: Optional[bool] = False,
    ) -> Job.InteractiveSimulationProperties:
        """
        Create a InteractiveSimulationProperties message.

        Parameters
        ----------
        rays_nb_per_source : List[RaysNbPerSource], optional
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
        Job.InteractiveSimulationProperties
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
