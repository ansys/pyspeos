"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum
from typing import Mapping, Union

from ansys.api.speos.job.v2 import job_pb2 as messages
from ansys.api.speos.job.v2 import job_pb2_grpc as service
from ansys.api.speos.results.v1.ray_path_pb2 import RayPath

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str
from ansys.speos.core.scene import SceneLink

Job = messages.Job


class JobLink(CrudItem):
    def __init__(self, db, key: str, actions_stub: service.JobActionsStub):
        super().__init__(db, key)
        self._actions_stub = actions_stub

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

    def get_ray_paths(self) -> RayPath:
        return self._actions_stub.GetRayPaths(messages.GetRayPaths_Request(guid=self.key))


class JobStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.JobsManagerStub(channel=channel))
        self._actions_stub = service.JobActionsStub(channel=channel)

    def create(self, message: Job) -> JobLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(job=message))
        return JobLink(self, resp.guid, self._actions_stub)

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

    def list(self) -> list[JobLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: JobLink(self, x, self._actions_stub), guids))


class JobFactory:
    Type = Enum("Type", ["CPU", "GPU"])

    class RaysNbPerSource:
        def __init__(self, source_path: str, rays_nb: int = 100) -> None:
            self.source_path = source_path
            self.rays_nb = rays_nb

    def new(
        name: str,
        scene: SceneLink,
        simulation_path: str,
        properties: Union[
            messages.Job.DirectMCSimulationProperties,
            messages.Job.InverseMCSimulationProperties,
            messages.Job.InteractiveSimulationProperties,
        ],
        type: Type = Type.CPU,
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> Job:
        job = Job(name=name, description=description)
        if metadata is not None:
            job.metadata.update(metadata)
        job.scene_guid = scene.key

        if len(simulation_path) == 0 and len(scene.get().simulations) > 0:
            job.simulation_path = scene.get().simulations[0].name
        else:
            job.simulation_path = simulation_path

        if type == JobFactory.Type.CPU:
            job.job_type = messages.Job.Type.CPU
        elif type == JobFactory.Type.GPU:
            job.job_type = messages.Job.Type.GPU

        if isinstance(properties, messages.Job.DirectMCSimulationProperties):
            job.direct_mc_simulation_properties.CopyFrom(properties)
        elif isinstance(properties, messages.Job.InverseMCSimulationProperties):
            job.inverse_mc_simulation_properties.CopyFrom(properties)
        elif isinstance(properties, messages.Job.InteractiveSimulationProperties):
            job.interactive_simulation_properties.CopyFrom(properties)

        return job

    def direct_mc_props(
        stop_condition_rays_nb: Union[int, None] = 200000,
        stop_condition_duration: Union[int, None] = None,
        automatic_save_frequency: int = 1800,
    ) -> messages.Job.DirectMCSimulationProperties:
        props = messages.Job.DirectMCSimulationProperties()
        if stop_condition_rays_nb is not None:
            props.stop_condition_rays_number = stop_condition_rays_nb
        if stop_condition_duration is not None:
            props.stop_condition_duration = stop_condition_duration
        props.automatic_save_frequency = automatic_save_frequency
        return props

    def inverse_mc_props(
        stop_condition_passes_number: Union[int, None] = 5,
        stop_condition_duration: Union[int, None] = None,
        automatic_save_frequency: int = 1800,
    ) -> messages.Job.InverseMCSimulationProperties:
        props = messages.Job.InverseMCSimulationProperties()
        if stop_condition_passes_number is not None:
            props.optimized_propagation_none.stop_condition_passes_number = stop_condition_passes_number
        else:
            props.optimized_propagation_none.SetInParent()
        if stop_condition_duration is not None:
            props.stop_condition_duration = stop_condition_duration
        props.automatic_save_frequency = automatic_save_frequency
        return props

    def interactive_props(
        rays_nb_per_source: list[RaysNbPerSource] = None, light_expert: bool = False, impact_report: bool = False
    ) -> messages.Job.InteractiveSimulationProperties:
        props = messages.Job.InteractiveSimulationProperties()
        if rays_nb_per_source is not None:
            props.rays_number_per_sources.extend(
                [
                    messages.Job.InteractiveSimulationProperties.RaysNumberPerSource(source_path=rnps.source_path, rays_nb=rnps.rays_nb)
                    for rnps in rays_nb_per_source
                ]
            )
        props.light_expert = light_expert
        props.impact_report = impact_report
        return props
