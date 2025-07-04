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

"""Provides a way to interact with Speos feature: Simulation."""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
import time
from typing import List, Mapping, Optional, Union
import uuid
import warnings

from ansys.api.speos.job.v2 import job_pb2
from ansys.api.speos.job.v2.job_pb2 import Result
from ansys.api.speos.scene.v2 import scene_pb2 as messages
from ansys.api.speos.simulation.v1 import simulation_template_pb2
from ansys.speos.core.generic.general_methods import min_speos_version
from ansys.speos.core.kernel.job import ProtoJob
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.simulation_template import ProtoSimulationTemplate
from ansys.speos.core.logger import LOG
import ansys.speos.core.project as project
import ansys.speos.core.proto_message_utils as proto_message_utils
from ansys.speos.core.sensor import BaseSensor


class BaseSimulation:
    """
    Super Class for all simulations.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project in which simulation shall be created.
    name : str
        Name of the simulation.
    description : str
        Description of the Simulation.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    simulation_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SimulationInstance, optional
        Simulation instance to provide if the feature does not have to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.

    Notes
    -----
    This is a Super class, **Do not instantiate this class yourself**
    """

    class Weight:
        """The Weight represents the ray energy.

        In real life, a ray loses some energy (power) when it interacts with an object.
        Activating weight means that the Weight message is present.
        When weight is not activated, rays' energy stays constant and probability laws dictate if
        rays continue or stop propagating. When weight is activated, the rays' energy evolves with
        interactions until rays reach the sensors. It is highly recommended to fill this parameter
        excepted in interactive simulation. Not filling this parameter is useful to understand
        certain phenomena as absorption.

        Parameters
        ----------
        weight : ansys.api.speos.simulation.v1.simulation_template_pb2.Weight to complete.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_weight method available in simulation
        classes.

        """

        def __init__(
            self,
            weight: simulation_template_pb2.Weight,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "Weight class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._weight = weight
            # Default values
            self.set_minimum_energy_percentage()

        def set_minimum_energy_percentage(self, value: float = 0.005) -> BaseSimulation.Weight:
            """Set the minimum energy percentage.

            Parameters
            ----------
            value : float
                The Minimum energy percentage parameter defines the minimum energy ratio to continue
                to propagate a ray with weight. By default, ``0.005``.

            Returns
            -------
            ansys.speos.core.simulation.BaseSimulation.Weight
                Weight.
            """
            self._weight.minimum_energy_percentage = value
            return self

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        simulation_instance: Optional[ProtoScene.SimulationInstance] = None,
    ) -> None:
        self._project = project
        self._name = name
        self._unique_id = None
        self.simulation_template_link = None
        """Link object for the simulation template in database."""
        self.job_link = None
        """Link object for the job in database."""
        self.result_list = []
        """List of results created after a simulation compute."""

        if metadata is None:
            metadata = {}
        # Attribute representing the kind of simulation.
        self._type = None
        self._light_expert_changed = False

        if simulation_instance is None:
            # Create local SimulationTemplate
            self._simulation_template = ProtoSimulationTemplate(
                name=name, description=description, metadata=metadata
            )

            # Create local SimulationInstance
            self._simulation_instance = ProtoScene.SimulationInstance(
                name=name, description=description, metadata=metadata
            )
        else:
            self._unique_id = simulation_instance.metadata["UniqueId"]
            self.simulation_template_link = self._project.client[
                simulation_instance.simulation_guid
            ]
            self.reset()

        # Create local Job
        self._job = ProtoJob(
            name=self._name,
            description=description,
            metadata=metadata,
            simulation_path=self._simulation_instance.name,
        )
        if self._project.scene_link is not None:
            self._job.scene_guid = self._project.scene_link.key

    def set_sensor_paths(self, sensor_paths: List[str]) -> BaseSimulation:
        """Set the sensors that the simulation will take into account.

        Parameters
        ----------
        sensor_paths : List[str]
            The sensor paths.

        Returns
        -------
        ansys.speos.core.simulation.BaseSimulation
            Simulation feature.
        """
        self._simulation_instance.sensor_paths[:] = sensor_paths
        return self

    def set_source_paths(self, source_paths: List[str]) -> BaseSimulation:
        """Set the sources that the simulation will take into account.

        Parameters
        ----------
        source_paths : List[str]
            The source paths.

        Returns
        -------
        ansys.speos.core.simulation.BaseSimulation
            Simulation feature.
        """
        self._simulation_instance.source_paths[:] = source_paths
        return self

    # def set_geometries(self, geometries: List[GeoRef]) -> Simulation:
    #     """Set geometries that the simulation will take into account.
    #
    #     Parameters
    #     ----------
    #     geometries : List[ansys.speos.core.geo_ref.GeoRef]
    #        List of geometries.
    #
    #     Returns
    #     -------
    #     ansys.speos.core.simulation.BaseSimulation
    #        Simulation feature.
    #     """
    #     if geometries is []:
    #         self._simulation_instance.ClearField("geometries")
    #     else:
    #         geo_paths = [gr.to_native_link() for gr in geometries]
    #         self._simulation_instance.geometries.geo_paths[:] = geo_paths
    #     return self

    def export(self, export_path: Union[str, Path]) -> None:
        """Export simulation.

        Parameters
        ----------
        export_path: Union[str, Path]
            directory to export simulation to.

        Returns
        -------
        None

        """
        simulation_features = [
            _
            for _ in self._project._features
            if isinstance(_, (SimulationDirect, SimulationInverse))
        ]
        if len(simulation_features) > 1:
            warnings.warn(
                "Limitation : only the first inverse/direct simulation is "
                "exported and stop conditions are not exported.",
                stacklevel=2,
            )
        if self is simulation_features[0]:
            export_path = Path(export_path)
            self._project.scene_link.stub._actions_stub.SaveFile(
                messages.SaveFile_Request(
                    guid=self._project.scene_link.key,
                    file_uri=str(export_path / (self._name + ".speos")),
                )
            )
        else:
            raise ValueError(
                "Selected simulation is not the first simulation feature, it can't be exported."
            )

    def _export_vtp(self) -> List[Path]:
        """Export the simulation results into vtp files.

        Returns
        -------
        List[Path]
            list of vtp paths.

        """
        vtp_files = []
        from ansys.speos.core import Face
        from ansys.speos.core.sensor import Sensor3DIrradiance, SensorIrradiance
        from ansys.speos.core.workflow.open_result import export_xm3_vtp, export_xmp_vtp

        sensor_paths = self.get(key="sensor_paths")
        for feature in self._project._features:
            if feature._name not in sensor_paths:
                continue
            match feature:
                case SensorIrradiance():
                    xmp_data = feature.get(key="result_file_name")
                    exported_vtp = export_xmp_vtp(self, xmp_data)
                    vtp_files.append(exported_vtp)
                case Sensor3DIrradiance():
                    xm3_data = feature.get(key="result_file_name")
                    geo_paths = feature.get(key="geo_paths")
                    geos_faces = [
                        self._project.find(name=geo_path, feature_type=Face)[0]._face
                        for geo_path in geo_paths
                    ]
                    exported_vtp = export_xm3_vtp(self, geos_faces, xm3_data)
                    vtp_files.append(exported_vtp)
                case _:
                    warnings.warn(
                        "feature {} result currently not supported".format(feature._name),
                        stacklevel=2,
                    )
        return vtp_files

    def compute_CPU(
        self, threads_number: Optional[int] = None, export_vtp: Optional[bool] = False
    ) -> tuple[list[Result], list[Path]] | list[Result]:
        """Compute the simulation on CPU.

        Parameters
        ----------
        threads_number : int, optional
            The number of threads used.
            By default, ``None``, means the number of processor available.
        export_vtp: bool, optional
            True to generate vtp from the simulation results.

        Returns
        -------
        List[ansys.api.speos.job.v2.job_pb2.Result]
            List of simulation results.
        """
        self._job.job_type = ProtoJob.Type.CPU

        if threads_number is not None:
            self._simulation_template.metadata["SimulationSetting::OPTThreadNumber"] = (
                "int::" + str(threads_number)
            )

        self.result_list = self._run_job()
        if export_vtp:
            vtp_files = self._export_vtp()
            return self.result_list, vtp_files
        return self.result_list

    def compute_GPU(
        self, export_vtp: Optional[bool] = False
    ) -> tuple[list[Result], list[Path]] | list[Result]:
        """Compute the simulation on GPU.

        Parameters
        ----------
        export_vtp: bool, optional
            True to generate vtp from the simulation results.

        Returns
        -------
        List[ansys.api.speos.job.v2.job_pb2.Result]
            List of simulation results.
        """
        self._job.job_type = ProtoJob.Type.GPU
        self.result_list = self._run_job()
        if export_vtp:
            vtp_files = self._export_vtp()
            return self.result_list, vtp_files
        return self.result_list

    def _run_job(self) -> List[job_pb2.Result]:
        if self.job_link is not None:
            job_state_res = self.job_link.get_state()
            if job_state_res.state != ProtoJob.State.QUEUED:
                self.job_link.delete()
                self.job_link = None

        self.commit()

        # Save or Update the job
        if self.job_link is None:
            self.job_link = self._project.client.jobs().create(message=self._job)
        elif self.job_link.get() != self._job:
            self.job_link.set(data=self._job)  # Update only if job data has changed

        self.job_link.start()

        job_state_res = self.job_link.get_state()
        while (
            job_state_res.state != ProtoJob.State.FINISHED
            and job_state_res.state != ProtoJob.State.STOPPED
            and job_state_res.state != ProtoJob.State.IN_ERROR
        ):
            time.sleep(5)

            job_state_res = self.job_link.get_state()
            if job_state_res.state == ProtoJob.State.IN_ERROR:
                LOG.error(protobuf_message_to_str(self.job_link.get_error()))

        return self.job_link.get_results().results

    def _to_dict(self) -> dict:
        out_dict = {}

        # SimulationInstance (= simulation guid + simulation properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            sim_inst = next(
                (x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if sim_inst is not None:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=sim_inst
                )
            else:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._simulation_instance,
                )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._project.client,
                message=self._simulation_instance,
            )

        if "simulation" not in out_dict.keys():
            # SimulationTemplate
            if self.simulation_template_link is None:
                out_dict["simulation"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._simulation_template,
                )
            else:
                out_dict["simulation"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self.simulation_template_link.get(),
                )

        if self.job_link is None:
            out_dict["simulation_properties"] = proto_message_utils._replace_guids(
                speos_client=self._project.client,
                message=self._job,
                ignore_simple_key="scene_guid",
            )
        else:
            out_dict["simulation_properties"] = proto_message_utils._replace_guids(
                speos_client=self._project.client,
                message=self.job_link.get(),
                ignore_simple_key="scene_guid",
            )

        proto_message_utils._replace_properties(json_dict=out_dict)

        return out_dict

    def get(self, key: str = "") -> str | dict:
        """Get dictionary corresponding to the project - read only.

        Parameters
        ----------
        key: str

        Returns
        -------
        str | dict :
            Dictionary of Simulation Feature
        """
        if key == "":
            return self._to_dict()
        info = proto_message_utils._value_finder_key_startswith(dict_var=self._to_dict(), key=key)
        content = list(info)
        if len(content) != 0:
            content.sort(
                key=lambda x: SequenceMatcher(None, x[0], key).ratio(),
                reverse=True,
            )
            return content[0][1]
        info = proto_message_utils._flatten_dict(dict_var=self._to_dict())
        print("Used key: {} not found in key list: {}.".format(key, info.keys()))

    def __str__(self) -> str:
        """Return the string representation of the simulation."""
        out_str = ""

        # SimulationInstance (= simulation guid + simulation properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            sim_inst = next(
                (x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if sim_inst is None:
                out_str += "local: "
        else:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())

        return out_str

    def commit(self) -> BaseSimulation:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.simulation.BaseSimulation
            Simulation feature.
        """
        # The _unique_id will help to find correct item in the scene.simulations:
        # the list of SimulationInstance
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._simulation_instance.metadata["UniqueId"] = self._unique_id

        # Save or Update the simulation template (depending on if it was already saved before)
        if self.simulation_template_link is None:
            self.simulation_template_link = self._project.client.simulation_templates().create(
                message=self._simulation_template
            )
            self._simulation_instance.simulation_guid = self.simulation_template_link.key
        elif self.simulation_template_link.get() != self._simulation_template:
            self.simulation_template_link.set(
                data=self._simulation_template
            )  # Only update if template has changed

        # Update the scene with the simulation instance
        if self._project.scene_link:
            update_scene = True
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            simulation_inst = next(
                (x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if simulation_inst is not None:  # if yes, just replace
                if simulation_inst != self._simulation_instance:
                    simulation_inst.CopyFrom(self._simulation_instance)
                else:
                    update_scene = False
            else:
                scene_data.simulations.insert(
                    len(scene_data.simulations), self._simulation_instance
                )  # if no, just add it to the list of simulations

            if update_scene:  # Update scene only if instance has changed
                self._project.scene_link.set(data=scene_data)  # update scene data

        # Job will be committed when performing compute method
        return self

    def reset(self) -> BaseSimulation:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.simulation.BaseSimulation
            Simulation feature.
        """
        # Reset simulation template
        if self.simulation_template_link is not None:
            self._simulation_template = self.simulation_template_link.get()

        # Reset simulation instance
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            # Look if an element corresponds to the _unique_id
            sim_inst = next(
                (x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if sim_inst is not None:
                self._simulation_instance = sim_inst

        # Reset job
        if self.job_link is not None:
            self._job = self.job_link.get()
        return self

    def delete(self) -> BaseSimulation:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.simulation.BaseSimulation
            Simulation feature.
        """
        # Delete the simulation template
        if self.simulation_template_link is not None:
            self.simulation_template_link.delete()
            self.simulation_template_link = None

        # Reset then the simulation_guid (as the simulation template was deleted just above)
        self._simulation_instance.simulation_guid = ""

        # Remove the simulation from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data
        sim_inst = next(
            (x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id),
            None,
        )
        if sim_inst is not None:
            scene_data.simulations.remove(sim_inst)
            self._project.scene_link.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        self._simulation_instance.metadata.pop("UniqueId")

        # Delete job
        if self.job_link is not None:
            self.job_link.delete()
            self.job_link = None
        return self

    def _fill(self, sim_inst):
        self._unique_id = sim_inst.metadata["UniqueId"]
        self._simulation_instance = sim_inst
        self.simulation_template_link = self._project.client[sim_inst.simulation_guid]
        self.reset()


class SimulationDirect(BaseSimulation):
    """Type of Simulation: Direct.

    By default,
    geometry distance tolerance is set to 0.01,
    maximum number of impacts is set to 100,
    colorimetric standard is set to CIE 1931,
    dispersion is set to True,
    fast transmission gathering is set to False,
    ambient material URI is empty,
    and weight's minimum energy percentage is set to 0.005.
    By default, the simulation will stop after 200000 rays,
    with an automatic save frequency of 1800s.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project in which simulation shall be created.
    name : str
        Name of the simulation.
    description : str
        Description of the Simulation.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    simulation_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SimulationInstance, optional
        Simulation instance to provide if the feature does not have to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.
    default_values : bool
        Uses default values when True.
    """

    @min_speos_version(25, 2, 0)
    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        simulation_instance: Optional[ProtoScene.SimulationInstance] = None,
        default_values: bool = True,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            simulation_instance=simulation_instance,
        )

        if default_values:
            # Default values
            self.set_geom_distance_tolerance()
            self.set_max_impact()
            self.set_colorimetric_standard_CIE_1931()
            self.set_dispersion()
            # self.set_fast_transmission_gathering()
            self.set_ambient_material_file_uri()
            self.set_weight()
            self.set_light_expert()
            # Default job properties
            self.set_stop_condition_rays_number().set_stop_condition_duration().set_automatic_save_frequency()

    def set_geom_distance_tolerance(self, value: float = 0.01) -> SimulationDirect:
        """Set the geometry distance tolerance.

        Parameters
        ----------
        value : float
            Maximum distance in mm to consider two faces as tangent.
            By default, ``0.01``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Direct simulation
        """
        self._simulation_template.direct_mc_simulation_template.geom_distance_tolerance = value
        return self

    def set_max_impact(self, value: int = 100) -> SimulationDirect:
        """Define a value to determine the maximum number of ray impacts during propagation.

        When a ray has interacted N times with the geometry, the propagation of the ray stops.

        Parameters
        ----------
        value : int
            The maximum number of impacts.
            By default, ``100``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Direct simulation
        """
        self._simulation_template.direct_mc_simulation_template.max_impact = value
        return self

    def set_weight(self) -> BaseSimulation.Weight:
        """Activate weight. Highly recommended to fill.

        Returns
        -------
        ansys.speos.core.simulation.BaseSimulation.Weight
            Weight.
        """
        return BaseSimulation.Weight(
            self._simulation_template.direct_mc_simulation_template.weight,
            stable_ctr=True,
        )

    def set_weight_none(self) -> SimulationDirect:
        """Deactivate weight.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Direct simulation
        """
        self._simulation_template.direct_mc_simulation_template.ClearField("weight")
        return self

    def set_colorimetric_standard_CIE_1931(self) -> SimulationDirect:
        """Set the colorimetric standard to CIE 1931.

        2 degrees CIE Standard Colorimetric Observer Data.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Direct simulation
        """
        self._simulation_template.direct_mc_simulation_template.colorimetric_standard = (
            simulation_template_pb2.CIE_1931
        )
        return self

    def set_colorimetric_standard_CIE_1964(self) -> SimulationDirect:
        """Set the colorimetric standard to CIE 1964.

        10 degrees CIE Standard Colorimetric Observer Data.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Direct simulation
        """
        self._simulation_template.direct_mc_simulation_template.colorimetric_standard = (
            simulation_template_pb2.CIE_1964
        )
        return self

    def set_dispersion(self, value: bool = True) -> SimulationDirect:
        """Activate/Deactivate the dispersion calculation.

        Parameters
        ----------
        value : bool
            Activate/Deactivate.
            By default, ``True``, means activate.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Direct simulation
        """
        self._simulation_template.direct_mc_simulation_template.dispersion = value
        return self

    # def set_fast_transmission_gathering(self, value: bool = False) -> Simulation.Direct:
    #     """Activate/Deactivate the fast transmission gathering.
    #
    #     To accelerate the simulation by neglecting the light refraction that occurs when the
    #     light is being
    #     transmitted through a transparent surface.
    #
    #     Parameters
    #     ----------
    #     value : bool
    #        Activate/Deactivate.
    #        By default, ``False``, means deactivate
    #
    #     Returns
    #     -------
    #     ansys.speos.core.simulation.Direct
    #        Direct simulation
    #     """
    #     template = self._simulation_template.direct_mc_simulation_template
    #     template.fast_transmission_gathering = value
    #     return self

    def set_ambient_material_file_uri(self, uri: str = "") -> SimulationDirect:
        """To define the environment in which the light will propagate (water, fog, smoke etc.).

        Parameters
        ----------
        uri : str
            The ambient material, expressed in a .material file.
            By default, ``""``, means air as ambient material.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Direct simulation
        """
        self._simulation_template.direct_mc_simulation_template.ambient_material_uri = uri
        return self

    def set_stop_condition_rays_number(self, value: Optional[int] = 200000) -> SimulationDirect:
        """To stop the simulation after a certain number of rays were sent.

        Set None as value to have no condition about rays number.

        Parameters
        ----------
        value : int, optional
            The number of rays to send. Or None if no condition about the number of rays.
            By default, ``200000``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Direct simulation
        """
        if value is None:
            self._job.direct_mc_simulation_properties.ClearField("stop_condition_rays_number")
        else:
            self._job.direct_mc_simulation_properties.stop_condition_rays_number = value
        return self

    def set_stop_condition_duration(self, value: Optional[int] = None) -> SimulationDirect:
        """To stop the simulation after a certain duration.

        Set None as value to have no condition about duration.

        Parameters
        ----------
        value : int, optional
            Duration requested (s). Or None if no condition about duration.
            By default, ``None``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Direct simulation
        """
        if value is None:
            self._job.direct_mc_simulation_properties.ClearField("stop_condition_duration")
        else:
            self._job.direct_mc_simulation_properties.stop_condition_duration = value
        return self

    def set_automatic_save_frequency(self, value: int = 1800) -> SimulationDirect:
        """Define a backup interval (s).

        This option is useful when computing long simulations.
        But a reduced number of save operations naturally increases the simulation performance.

        Parameters
        ----------
        value : int, optional
            Backup interval (s).
            By default, ``1800``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Direct simulation
        """
        self._job.direct_mc_simulation_properties.automatic_save_frequency = value
        return self

    def set_light_expert(self, value: bool = False, ray_number: int = 10e6) -> SimulationDirect:
        """Activate/Deactivate the generation of light expert file.

        Parameters
        ----------
        value : bool
            Activate/Deactivate.
            By default, ``False``, means deactivate.
        ray_number : int
            number of rays stored in lpf file
            By default, ``10e6``

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Interactive simulation
        """
        self._light_expert_changed = True
        warnings.warn(
            "Please note that setting a value for light expert option forces a sensor"
            "commit when committing the Simulation class",
            stacklevel=2,
        )
        if value:
            for item in self._project._features:
                if isinstance(item, BaseSensor):
                    item.lxp_path_number = ray_number
        else:
            for item in self._project._features:
                if isinstance(item, BaseSensor):
                    item.lxp_path_number = None
        return self

    def commit(self) -> SimulationDirect:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.simulation.SimulationDirect
            Simulation feature.
        """
        if self._light_expert_changed:
            for item in self._project._features:
                if isinstance(item, BaseSensor):
                    item.commit()
            self._light_expert_changed = False
        super().commit()
        return self


class SimulationInverse(BaseSimulation):
    """Type of simulation : Inverse.

    By default,
    geometry distance tolerance is set to 0.01,
    maximum number of impacts is set to 100,
    colorimetric standard is set to CIE 1931,
    dispersion is set to False,
    splitting is set to False,
    number of gathering rays per source is set to 1,
    maximum gathering error is set to 0,
    fast transmission gathering is set to False,
    ambient material URI is empty,
    and weight's minimum energy percentage is set to 0.005.
    By default, the simulation will stop after 5 passes, with an automatic save frequency of 1800s.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project in which simulation shall be created.
    name : str
        Name of the simulation.
    description : str
        Description of the Simulation.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    simulation_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SimulationInstance, optional
        Simulation instance to provide if the feature does not have to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.
    default_values : bool
        Uses default values when True.
    """

    @min_speos_version(25, 2, 0)
    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        simulation_instance: Optional[ProtoScene.SimulationInstance] = None,
        default_values: bool = True,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            simulation_instance=simulation_instance,
        )

        if default_values:
            # Default values
            self.set_geom_distance_tolerance()
            self.set_max_impact()
            self.set_weight()
            self.set_colorimetric_standard_CIE_1931()
            self.set_dispersion()
            self.set_splitting()
            self.set_number_of_gathering_rays_per_source()
            self.set_maximum_gathering_error()
            # self.set_fast_transmission_gathering()
            self.set_ambient_material_file_uri()
            # Default job properties
            self.set_stop_condition_duration().set_stop_condition_passes_number().set_automatic_save_frequency()

    def set_geom_distance_tolerance(self, value: float = 0.01) -> SimulationInverse:
        """Set the geometry distance tolerance.

        Parameters
        ----------
        value : float
            Maximum distance in mm to consider two faces as tangent.
            By default, ``0.01``

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        self._simulation_template.inverse_mc_simulation_template.geom_distance_tolerance = value
        return self

    def set_max_impact(self, value: int = 100) -> SimulationInverse:
        """Define a value to determine the maximum number of ray impacts during propagation.

        When a ray has interacted N times with the geometry, the propagation of the ray stops.

        Parameters
        ----------
        value : int
            The maximum number of impacts.
            By default, ``100``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        self._simulation_template.inverse_mc_simulation_template.max_impact = value
        return self

    def set_weight(self) -> BaseSimulation.Weight:
        """Activate weight. Highly recommended to fill.

        Returns
        -------
        ansys.speos.core.simulation.BaseSimulation.Weight
            Simulation.Weight
        """
        return BaseSimulation.Weight(
            self._simulation_template.inverse_mc_simulation_template.weight,
            stable_ctr=True,
        )

    def set_weight_none(self) -> SimulationInverse:
        """Deactivate weight.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        self._simulation_template.inverse_mc_simulation_template.ClearField("weight")
        return self

    def set_colorimetric_standard_CIE_1931(self) -> SimulationInverse:
        """Set the colorimetric standard to CIE 1931.

        2 degrees CIE Standard Colorimetric Observer Data.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        self._simulation_template.inverse_mc_simulation_template.colorimetric_standard = (
            simulation_template_pb2.CIE_1931
        )
        return self

    def set_colorimetric_standard_CIE_1964(self) -> SimulationInverse:
        """Set the colorimetric standard to CIE 1964.

        10 degrees CIE Standard Colorimetric Observer Data.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        self._simulation_template.inverse_mc_simulation_template.colorimetric_standard = (
            simulation_template_pb2.CIE_1964
        )
        return self

    def set_dispersion(self, value: bool = False) -> SimulationInverse:
        """Activate/Deactivate the dispersion calculation.

        Parameters
        ----------
        value : bool
            Activate/Deactivate.
            By default, ``False``, means deactivate.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        self._simulation_template.inverse_mc_simulation_template.dispersion = value
        return self

    def set_splitting(self, value: bool = False) -> SimulationInverse:
        """Activate/Deactivate the splitting.

        To split each propagated ray into several paths at their first impact after leaving the
        observer point.

        Parameters
        ----------
        value : bool
            Activate/Deactivate.
            By default, ``False``, means deactivate.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        self._simulation_template.inverse_mc_simulation_template.splitting = value
        return self

    def set_number_of_gathering_rays_per_source(self, value: int = 1) -> SimulationInverse:
        """Set the number of gathering rays per source.

        Parameters
        ----------
        value : int
            This number pilots the number of shadow rays to target at each source.
            By default, ``1``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        template = self._simulation_template.inverse_mc_simulation_template
        template.number_of_gathering_rays_per_source = value
        return self

    def set_maximum_gathering_error(self, value: int = 0) -> SimulationInverse:
        """Set the maximum gathering error.

        Parameters
        ----------
        value : int
            This value defines the level below which a source can be neglected.
            By default, ``0``, means that no approximation will be done.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        self._simulation_template.inverse_mc_simulation_template.maximum_gathering_error = value
        return self

    # def set_fast_transmission_gathering(self, value: bool = False) -> Simulation.Inverse:
    #     """Activate/Deactivate the fast transmission gathering.
    #
    #     To accelerate the simulation by neglecting the light refraction that occurs when the light
    #     is being transmitted through a transparent surface.
    #
    #     Parameters
    #     ----------
    #     value : bool
    #         Activate/Deactivate.
    #         By default, ``False``, means deactivate
    #
    #     Returns
    #     -------
    #     ansys.speos.core.simulation.Inverse
    #         Inverse simulation
    #     """
    #     template = self._simulation_template.inverse_mc_simulation_template
    #     template.fast_transmission_gathering = value
    #     return self

    def set_ambient_material_file_uri(self, uri: str = "") -> SimulationInverse:
        """To define the environment in which the light will propagate (water, fog, smoke etc.).

        Parameters
        ----------
        uri : str
            The ambient material, expressed in a .material file.
            By default, ``""``, means air as ambient material.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        self._simulation_template.inverse_mc_simulation_template.ambient_material_uri = uri
        return self

    def set_stop_condition_passes_number(self, value: Optional[int] = 5) -> SimulationInverse:
        """To stop the simulation after a certain number of passes.

        Set None as value to have no condition about passes.

        Parameters
        ----------
        value : int, optional
            The number of passes requested. Or None if no condition about passes.
            By default, ``5``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        propagation_none = self._job.inverse_mc_simulation_properties.optimized_propagation_none
        if value is None:
            propagation_none.ClearField("stop_condition_passes_number")
        else:
            propagation_none.stop_condition_passes_number = value
        return self

    def set_stop_condition_duration(self, value: Optional[int] = None) -> SimulationInverse:
        """To stop the simulation after a certain duration.

        Set None as value to have no condition about duration.

        Parameters
        ----------
        value : int, optional
            Duration requested (s). Or None if no condition about duration.
            By default, ``None``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        if value is None:
            self._job.inverse_mc_simulation_properties.ClearField("stop_condition_duration")
        else:
            self._job.inverse_mc_simulation_properties.stop_condition_duration = value
        return self

    def set_automatic_save_frequency(self, value: int = 1800) -> SimulationInverse:
        """Define a backup interval (s).

        This option is useful when computing long simulations.
        But a reduced number of save operations naturally increases the simulation performance.

        Parameters
        ----------
        value : int, optional
            Backup interval (s).
            By default, ``1800``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Inverse simulation
        """
        self._job.inverse_mc_simulation_properties.automatic_save_frequency = value
        return self

    def set_light_expert(self, value: bool = False, ray_number: int = 10e6) -> SimulationInverse:
        """Activate/Deactivate the generation of light expert file.

        Parameters
        ----------
        value : bool
            Activate/Deactivate.
            By default, ``False``, means deactivate.
        ray_number : int
            number of rays stored in lpf file
            By default, ``10e6``

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Interactive simulation
        """
        self._light_expert_changed = True
        warnings.warn(
            "Please note that setting a value for light expert option forces a sensor"
            "commit when committing the Simulation class",
            stacklevel=2,
        )
        if value:
            for item in self._project._features:
                if isinstance(item, BaseSensor):
                    item.lxp_path_number = ray_number
        else:
            for item in self._project._features:
                if isinstance(item, BaseSensor):
                    item.lxp_path_number = None
        return self

    def commit(self) -> SimulationInverse:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInverse
            Simulation feature.
        """
        if self._light_expert_changed:
            for item in self._project._features:
                if isinstance(item, BaseSensor):
                    item.commit()
            self._light_expert_changed = False
        super().commit()
        return self


class SimulationInteractive(BaseSimulation):
    """Type of simulation : Interactive.

    By default,
    geometry distance tolerance is set to 0.01,
    maximum number of impacts is set to 100,
    a colorimetric standard is set to CIE 1931,
    ambient material URI is empty,
    and weight's minimum energy percentage is set to 0.005.
    By default, each source will send 100 rays.
    By default, the simulation deactivates both light expert and impact report.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project in which simulation shall be created.
    name : str
        Name of the simulation.
    description : str
        Description of the Simulation.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    simulation_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SimulationInstance, optional
        Simulation instance to provide if the feature does not have to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.
    default_values : bool
        Uses default values when True.
    """

    class RaysNumberPerSource:
        """Structure to describe the number of rays requested for a specific source.

        Parameters
        ----------
        source_path : str
            Source selected via its path ("SourceName").
        rays_nb : int, optional
            Number of rays to be emitted by the source.
            If None is given, 100 rays will be sent.
        """

        def __init__(self, source_path: str, rays_nb: Optional[int]) -> None:
            self.source_path = source_path
            """Source path."""
            self.rays_nb = rays_nb
            """Number of rays to be emitted by the source. If None, it means 100 rays."""

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        simulation_instance: Optional[ProtoScene.SimulationInstance] = None,
        default_values: bool = True,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            simulation_instance=simulation_instance,
        )

        if default_values:
            # Default values
            self.set_geom_distance_tolerance()
            self.set_max_impact()
            self.set_weight()
            self.set_colorimetric_standard_CIE_1931()
            self.set_ambient_material_file_uri()
            # Default job parameters
            self.set_light_expert().set_impact_report()

    def set_geom_distance_tolerance(self, value: float = 0.01) -> SimulationInteractive:
        """Set the geometry distance tolerance.

        Parameters
        ----------
        value : float
            Maximum distance in mm to consider two faces as tangent.
            By default, ``0.01``

        Returns
        -------
        ansys.speos.core.simulation.SimulationInteractive
            Interactive simulation
        """
        self._simulation_template.interactive_simulation_template.geom_distance_tolerance = value
        return self

    def set_max_impact(self, value: int = 100) -> SimulationInteractive:
        """Define a value to determine the maximum number of ray impacts during propagation.

        When a ray has interacted N times with the geometry, the propagation of the ray stops.

        Parameters
        ----------
        value : int
            The maximum number of impacts.
            By default, ``100``.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInteractive
            Interactive simulation
        """
        self._simulation_template.interactive_simulation_template.max_impact = value
        return self

    def set_weight(self) -> BaseSimulation.Weight:
        """Activate weight. Highly recommended to fill.

        Returns
        -------
        ansys.speos.core.simulation.BaseSimulation.Weight
            Simulation.Weight
        """
        return BaseSimulation.Weight(
            self._simulation_template.interactive_simulation_template.weight,
            stable_ctr=True,
        )

    def set_weight_none(self) -> SimulationInteractive:
        """Deactivate weight.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInteractive
            Interactive simulation
        """
        self._simulation_template.interactive_simulation_template.ClearField("weight")
        return self

    def set_colorimetric_standard_CIE_1931(self) -> SimulationInteractive:
        """Set the colorimetric standard to CIE 1931.

        2 degrees CIE Standard Colorimetric Observer Data.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInteractive
            Interactive simulation
        """
        self._simulation_template.interactive_simulation_template.colorimetric_standard = (
            simulation_template_pb2.CIE_1931
        )
        return self

    def set_colorimetric_standard_CIE_1964(self) -> SimulationInteractive:
        """Set the colorimetric standard to CIE 1964.

        10 degrees CIE Standard Colorimetric Observer Data.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInteractive
            Interactive simulation
        """
        self._simulation_template.interactive_simulation_template.colorimetric_standard = (
            simulation_template_pb2.CIE_1964
        )
        return self

    def set_ambient_material_file_uri(self, uri: str = "") -> SimulationInteractive:
        """To define the environment in which the light will propagate (water, fog, smoke etc.).

        Parameters
        ----------
        uri : str
            The ambient material, expressed in a .material file.
            By default, ``""``, means air as ambient material.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInteractive
            Interactive simulation
        """
        self._simulation_template.interactive_simulation_template.ambient_material_uri = uri
        return self

    def set_rays_number_per_sources(
        self, values: List[SimulationInteractive.RaysNumberPerSource]
    ) -> SimulationInteractive:
        """Select the number of rays emitted for each source.

        If a source is present in the simulation but not referenced here, it will send by default
        100 rays.

        Parameters
        ----------
        values : List[ansys.speos.core.simulation.SimulationInteractive.RaysNumberPerSource]
            List of rays number emitted by source.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInteractive
            Interactive simulation
        """
        my_list = [
            ProtoJob.InteractiveSimulationProperties.RaysNumberPerSource(
                source_path=rays_nb_per_source.source_path,
                rays_nb=rays_nb_per_source.rays_nb,
            )
            for rays_nb_per_source in values
        ]
        self._job.interactive_simulation_properties.ClearField("rays_number_per_sources")
        self._job.interactive_simulation_properties.rays_number_per_sources.extend(my_list)
        return self

    def set_light_expert(self, value: bool = False) -> SimulationInteractive:
        """Activate/Deactivate the generation of light expert file.

        Parameters
        ----------
        value : bool
            Activate/Deactivate.
            By default, ``False``, means deactivate.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInteractive
            Interactive simulation
        """
        self._job.interactive_simulation_properties.light_expert = value
        return self

    def set_impact_report(self, value: bool = False) -> SimulationInteractive:
        """Activate/Deactivate the details in the HTML simulation report.

        e.g: number of impacts, position and surface state

        Parameters
        ----------
        value : bool
            Activate/Deactivate.
            By default, ``False``, means deactivate.

        Returns
        -------
        ansys.speos.core.simulation.SimulationInteractive
            Interactive simulation
        """
        self._job.interactive_simulation_properties.impact_report = value
        return self
