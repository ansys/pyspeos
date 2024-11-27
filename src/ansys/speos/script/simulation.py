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

"""Provides a way to interact with Speos feature: Simulation."""
from __future__ import annotations

import time
from typing import List, Mapping, Optional
import uuid

from ansys.api.speos.job.v2 import job_pb2
from ansys.api.speos.simulation.v1 import simulation_template_pb2

import ansys.speos.core as core

# from ansys.speos.script.geo_ref import GeoRef
import ansys.speos.script.project as project
import ansys.speos.script.proto_message_utils as proto_message_utils


class Simulation:
    """Speos feature : Simulation.

    Parameters
    ----------
    project : ansys.speos.script.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Mapping[str, str]
        Metadata of the feature.
        By default, ``{}``.

    Attributes
    ----------
    simulation_template_link : ansys.speos.core.simulation_template.SimulationTemplateLink
        Link object for the simulation template in database.
    """

    class Weight:
        """The Weight represents the ray energy. In real life, a ray looses some energy (power) when it interacts with an object.
        Activating weight means that the Weight message is present.
        When weight is not activated, rays' energy stays constant and probability laws dictate if rays continue or stop propagating.
        When weight is activated, the rays' energy evolves with interactions until rays reach the sensors.
        It is highly recommended to fill this parameter excepted in interactive simulation.
        Not fill this parameter is useful to understand certain phenomena as absorption.

        Parameters
        ----------
        weight : ansys.api.speos.simulation.v1.simulation_template_pb2.Weight
            Weight to complete.
        """

        def __init__(self, weight: simulation_template_pb2.Weight) -> None:
            self._weight = weight
            # Default values
            self.set_minimum_energy_percentage()

        def set_minimum_energy_percentage(self, value: float = 0.005) -> Simulation.Weight:
            """Set the minimum energy percentage.

            Parameters
            ----------
            value : float
                The Minimum energy percentage parameter defines the minimum energy ratio to continue to propagate a ray with weight.
                By default, ``0.005``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Weight
                Weight.
            """
            self._weight.minimum_energy_percentage = value
            return self

    class Direct:
        """
        Type of Simulation : Direct.
        By default,
        geometry distance tolerance is set to 0.01,
        maximum number of impacts is set to 100,
        colorimetric standard is set to CIE 1931,
        dispersion is set to True,
        fast transmission gathering is set to False,
        ambient material URI is empty,
        and weight's minimum energy percentage is set to 0.005.
        By default, the simulation will stop after 200000 rays, with an automatic save frequency of 1800s.

        Parameters
        ----------
        direct_template : ansys.api.speos.simulation.v1.simulation_template_pb2.DirectMCSimulationTemplate
            Direct simulation to complete.
        direct_props_from_job : ansys.api.speos.job.v2.job_pb2.Job.DirectMCSimulationProperties
            Direct simulation properties to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            direct_template: simulation_template_pb2.DirectMCSimulationTemplate,
            direct_props_from_job: core.Job.DirectMCSimulationProperties,
            default_values: bool = True,
        ) -> None:
            self._direct_template = direct_template
            self._direct_props_from_job = direct_props_from_job

            if default_values:
                # Default values
                self.set_geom_distance_tolerance()
                self.set_max_impact()
                self.set_colorimetric_standard_CIE_1931()
                self.set_dispersion()
                # self.set_fast_transmission_gathering()
                self.set_ambient_material_file_uri()
                self.set_weight()

            # Default job properties
            self.set_stop_condition_rays_number().set_stop_condition_duration().set_automatic_save_frequency()

        def set_geom_distance_tolerance(self, value: float = 0.01) -> Simulation.Direct:
            """Set the geometry distance tolerance.

            Parameters
            ----------
            value : float
                Maximum distance in mm to consider two faces as tangent.
                By default, ``0.01``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Direct
                Direct simulation
            """
            self._direct_template.geom_distance_tolerance = value
            return self

        def set_max_impact(self, value: int = 100) -> Simulation.Direct:
            """Defines a value to determine the maximum number of ray impacts during propagation.
            When a ray has interacted N times with the geometry, the propagation of the ray stops.

            Parameters
            ----------
            value : int
                The maximum number of impacts.
                By default, ``100``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Direct
                Direct simulation
            """
            self._direct_template.max_impact = value
            return self

        def set_weight(self) -> Simulation.Weight:
            """Activate weight. Highly recommended to fill.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Weight
                Weight.
            """
            return Simulation.Weight(self._direct_template.weight)

        def set_weight_none(self) -> Simulation.Direct:
            """Deactivate weight.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Direct
                Direct simulation
            """
            self._direct_template.ClearField("weight")
            return self

        def set_colorimetric_standard_CIE_1931(self) -> Simulation.Direct:
            """Set the colorimetric standard to CIE 1931.
            2 degrees CIE Standard Colorimetric Observer Data.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Direct
                Direct simulation
            """
            self._direct_template.colorimetric_standard = simulation_template_pb2.CIE_1931
            return self

        def set_colorimetric_standard_CIE_1964(self) -> Simulation.Direct:
            """Set the colorimetric standard to CIE 1964.
            10 degrees CIE Standard Colorimetric Observer Data.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Direct
                Direct simulation
            """
            self._direct_template.colorimetric_standard = simulation_template_pb2.CIE_1964
            return self

        def set_dispersion(self, value: bool = True) -> Simulation.Direct:
            """Activate/Deactivate the dispersion calculation.

            Parameters
            ----------
            value : bool
                Activate/Deactivate.
                By default, ``True``, means activate.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Direct
                Direct simulation
            """
            self._direct_template.dispersion = value
            return self

        # def set_fast_transmission_gathering(self, value: bool = False) -> Simulation.Direct:
        #    """Activate/Deactivate the fast transmission gathering.
        #    To accelerate the simulation by neglecting the light refraction that occurs when the light is being
        #    transmitted through a transparent surface.
        #
        #    Parameters
        #    ----------
        #    value : bool
        #        Activate/Deactivate.
        #        By default, ``False``, means deactivate
        #
        #    Returns
        #    -------
        #    ansys.speos.script.simulation.Simulation.Direct
        #        Direct simulation
        #    """
        #    self._direct_template.fast_transmission_gathering = value
        #    return self

        def set_ambient_material_file_uri(self, uri: str = "") -> Simulation.Direct:
            """To define the environment in which the light will propagate (water, fog, smoke etc.).

            Parameters
            ----------
            uri : str
                The ambient material, expressed in a .material file.
                By default, ``""``, means air as ambient material.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Direct
                Direct simulation
            """
            self._direct_template.ambient_material_uri = uri
            return self

        def set_stop_condition_rays_number(self, value: Optional[int] = 200000) -> Simulation.Direct:
            """To stop the simulation after a certain number of rays were sent. Set None as value to have no condition about rays number.

            Parameters
            ----------
            value : int, optional
                The number of rays to send. Or None if no condition about rays number.
                By default, ``200000``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Direct
                Direct simulation
            """
            if value is None:
                self._direct_props_from_job.ClearField("stop_condition_rays_number")
            else:
                self._direct_props_from_job.stop_condition_rays_number = value
            return self

        def set_stop_condition_duration(self, value: Optional[int] = None) -> Simulation.Direct:
            """To stop the simulation after a certain duration. Set None as value to have no condition about duration.

            Parameters
            ----------
            value : int, optional
                Duration requested (s). Or None if no condition about duration.
                By default, ``None``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Direct
                Direct simulation
            """
            if value is None:
                self._direct_props_from_job.ClearField("stop_condition_duration")
            else:
                self._direct_props_from_job.stop_condition_duration = value
            return self

        def set_automatic_save_frequency(self, value: int = 1800) -> Simulation.Direct:
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
            ansys.speos.script.simulation.Simulation.Direct
                Direct simulation
            """
            self._direct_props_from_job.automatic_save_frequency = value
            return self

    class Inverse:
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
        inverse_template : ansys.api.speos.simulation.v1.simulation_template_pb2.InverseMCSimulationTemplate
            Inverse simulation to complete.
        inverse_props_from_job : ansys.api.speos.job.v2.job_pb2.Job.InverseMCSimulationProperties
            Inverse simulation properties to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            inverse_template: simulation_template_pb2.InverseMCSimulationTemplate,
            inverse_props_from_job: core.Job.InverseMCSimulationProperties,
            default_values: bool = True,
        ) -> None:
            self._inverse_template = inverse_template
            self._inverse_props_from_job = inverse_props_from_job

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

        def set_geom_distance_tolerance(self, value: float = 0.01) -> Simulation.Inverse:
            """Set the geometry distance tolerance.

            Parameters
            ----------
            value : float
                Maximum distance in mm to consider two faces as tangent.
                By default, ``0.01``

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_template.geom_distance_tolerance = value
            return self

        def set_max_impact(self, value: int = 100) -> Simulation.Inverse:
            """Defines a value to determine the maximum number of ray impacts during propagation.
            When a ray has interacted N times with the geometry, the propagation of the ray stops.

            Parameters
            ----------
            value : int
                The maximum number of impacts.
                By default, ``100``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_template.max_impact = value
            return self

        def set_weight(self) -> Simulation.Weight:
            """Activate weight. Highly recommended to fill.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Weight
                Simulation.Weight
            """
            return Simulation.Weight(self._inverse_template.weight)

        def set_weight_none(self) -> Simulation.Inverse:
            """Deactivate weight.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_template.ClearField("weight")
            return self

        def set_colorimetric_standard_CIE_1931(self) -> Simulation.Inverse:
            """Set the colorimetric standard to CIE 1931.
            2 degrees CIE Standard Colorimetric Observer Data.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_template.colorimetric_standard = simulation_template_pb2.CIE_1931
            return self

        def set_colorimetric_standard_CIE_1964(self) -> Simulation.Inverse:
            """Set the colorimetric standard to CIE 1964.
            10 degrees CIE Standard Colorimetric Observer Data.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_template.colorimetric_standard = simulation_template_pb2.CIE_1964
            return self

        def set_dispersion(self, value: bool = False) -> Simulation.Inverse:
            """Activate/Deactivate the dispersion calculation.

            Parameters
            ----------
            value : bool
                Activate/Deactivate.
                By default, ``False``, means deactivate.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_template.dispersion = value
            return self

        def set_splitting(self, value: bool = False) -> Simulation.Inverse:
            """Activate/Deactivate the splitting.
            To split each propagated ray into several paths at their first impact after leaving the observer point.

            Parameters
            ----------
            value : bool
                Activate/Deactivate.
                By default, ``False``, means deactivate.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_template.splitting = value
            return self

        def set_number_of_gathering_rays_per_source(self, value: int = 1) -> Simulation.Inverse:
            """Set the number of gathering rays per source.

            Parameters
            ----------
            value : int
                This number pilots the number of shadow rays to target at each source.
                By default, ``1``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_template.number_of_gathering_rays_per_source = value
            return self

        def set_maximum_gathering_error(self, value: int = 0) -> Simulation.Inverse:
            """Set the maximum gathering error.

            Parameters
            ----------
            value : int
                This value defines the level below which a source can be neglected.
                By default, ``0``, means that no approximation will be done.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_template.maximum_gathering_error = value
            return self

        # def set_fast_transmission_gathering(self, value: bool = False) -> Simulation.Inverse:
        #    """Activate/Deactivate the fast transmission gathering.
        #    To accelerate the simulation by neglecting the light refraction that occurs when the light is being
        #    transmitted through a transparent surface.
        #
        #    Parameters
        #    ----------
        #    value : bool
        #        Activate/Deactivate.
        #        By default, ``False``, means deactivate
        #
        #    Returns
        #    -------
        #    ansys.speos.script.simulation.Simulation.Inverse
        #        Inverse simulation
        #    """
        #    self._inverse_template.fast_transmission_gathering = value
        #    return self

        def set_ambient_material_file_uri(self, uri: str = "") -> Simulation.Inverse:
            """To define the environment in which the light will propagate (water, fog, smoke etc.).

            Parameters
            ----------
            uri : str
                The ambient material, expressed in a .material file.
                By default, ``""``, means air as ambient material.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_template.ambient_material_uri = uri
            return self

        def set_stop_condition_passes_number(self, value: Optional[int] = 5) -> Simulation.Inverse:
            """To stop the simulation after a certain number of passes. Set None as value to have no condition about passes.

            Parameters
            ----------
            value : int, optional
                The number of passes requested. Or None if no condition about passes.
                By default, ``5``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            if value is None:
                self._inverse_props_from_job.optimized_propagation_none.ClearField("stop_condition_passes_number")
            else:
                self._inverse_props_from_job.optimized_propagation_none.stop_condition_passes_number = value
            return self

        def set_stop_condition_duration(self, value: Optional[int] = None) -> Simulation.Inverse:
            """To stop the simulation after a certain duration. Set None as value to have no condition about duration.

            Parameters
            ----------
            value : int, optional
                Duration requested (s). Or None if no condition about duration.
                By default, ``None``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            if value is None:
                self._inverse_props_from_job.ClearField("stop_condition_duration")
            else:
                self._inverse_props_from_job.stop_condition_duration = value
            return self

        def set_automatic_save_frequency(self, value: int = 1800) -> Simulation.Inverse:
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
            ansys.speos.script.simulation.Simulation.Inverse
                Inverse simulation
            """
            self._inverse_props_from_job.automatic_save_frequency = value
            return self

    class Interactive:
        """Type of simulation : Interactive.
        By default,
        geometry distance tolerance is set to 0.01,
        maximum number of impacts is set to 100,
        colorimetric standard is set to CIE 1931,
        ambient material URI is empty,
        and weight's minimum energy percentage is set to 0.005.
        By default, each source will send 100 rays.
        By default, the simulation deactivates both light expert and impact report.

        Parameters
        ----------
        interactive_template : ansys.api.speos.simulation.v1.simulation_template_pb2.SimulationTemplate.Interactive
            Interactive simulation to complete.
        inverse_props_from_job : ansys.api.speos.job.v2.job_pb2.Job.InteractiveSimulationProperties
            Interactive simulation properties to complete.
        default_values : bool
            Uses default values when True.
        """

        class RaysNumberPerSource:
            """Structure to describe rays number requested for a specific source.

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
            interactive_template: core.SimulationTemplate.Interactive,
            interactive_props_from_job: core.Job.InteractiveSimulationProperties,
            default_values: bool = True,
        ) -> None:
            self._interactive_template = interactive_template
            self._interactive_props_from_job = interactive_props_from_job

            if default_values:
                # Default values
                self.set_geom_distance_tolerance()
                self.set_max_impact()
                self.set_weight()
                self.set_colorimetric_standard_CIE_1931()
                self.set_ambient_material_file_uri()

            self.set_light_expert().set_impact_report()

        def set_geom_distance_tolerance(self, value: float = 0.01) -> Simulation.Interactive:
            """Set the geometry distance tolerance.

            Parameters
            ----------
            value : float
                Maximum distance in mm to consider two faces as tangent.
                By default, ``0.01``

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._interactive_template.geom_distance_tolerance = value
            return self

        def set_max_impact(self, value: int = 100) -> Simulation.Interactive:
            """Defines a value to determine the maximum number of ray impacts during propagation.
            When a ray has interacted N times with the geometry, the propagation of the ray stops.

            Parameters
            ----------
            value : int
                The maximum number of impacts.
                By default, ``100``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._interactive_template.max_impact = value
            return self

        def set_weight(self) -> Simulation.Weight:
            """Activate weight. Highly recommended to fill.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Weight
                Simulation.Weight
            """
            return Simulation.Weight(self._interactive_template.weight)

        def set_weight_none(self) -> Simulation.Interactive:
            """Deactivate weight.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._interactive_template.ClearField("weight")
            return self

        def set_colorimetric_standard_CIE_1931(self) -> Simulation.Interactive:
            """Set the colorimetric standard to CIE 1931.
            2 degrees CIE Standard Colorimetric Observer Data.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._interactive_template.colorimetric_standard = simulation_template_pb2.CIE_1931
            return self

        def set_colorimetric_standard_CIE_1964(self) -> Simulation.Interactive:
            """Set the colorimetric standard to CIE 1964.
            10 degrees CIE Standard Colorimetric Observer Data.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._interactive_template.colorimetric_standard = simulation_template_pb2.CIE_1964
            return self

        def set_ambient_material_file_uri(self, uri: str = "") -> Simulation.Interactive:
            """To define the environment in which the light will propagate (water, fog, smoke etc.).

            Parameters
            ----------
            uri : str
                The ambient material, expressed in a .material file.
                By default, ``""``, means air as ambient material.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._interactive_template.ambient_material_uri = uri
            return self

        def set_rays_number_per_sources(self, values: List[Simulation.Interactive.RaysNumberPerSource]) -> Simulation.Interactive:
            """Select the number of rays emitted for each source. If a source is present in the simulation but not referenced here,
            it will send by default 100 rays.

            Parameters
            ----------
            values : List[ansys.speos.script.simulation.Simulation.Interactive.RaysNumberPerSource]
                List of rays number emitted by source.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            my_list = [
                core.Job.InteractiveSimulationProperties.RaysNumberPerSource(
                    source_path=rays_nb_per_source.source_path, rays_nb=rays_nb_per_source.rays_nb
                )
                for rays_nb_per_source in values
            ]
            self._interactive_props_from_job.ClearField("rays_number_per_sources")
            self._interactive_props_from_job.rays_number_per_sources.extend(my_list)
            return self

        def set_light_expert(self, value: bool = False) -> Simulation.Interactive:
            """Activate/Deactivate the generation of light expert file.

            Parameters
            ----------
            value : bool
                Activate/Deactivate.
                By default, ``False``, means deactivate.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._interactive_props_from_job.light_expert = value
            return self

        def set_impact_report(self, value: bool = False) -> Simulation.Interactive:
            """Activate/Deactivate the details like number of impacts, position and surface state to the HTML simulation report.

            Parameters
            ----------
            value : bool
                Activate/Deactivate.
                By default, ``False``, means deactivate.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._interactive_props_from_job.impact_report = value
            return self

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._name = name
        self._unique_id = None
        self.simulation_template_link = None
        """Link object for the simulation template in database."""
        self.job_link = None
        """Link object for the job in database."""
        self.result_list = []
        """List of results created after a simulation compute."""

        # Attribute representing the kind of simulation.
        self._type = None

        # Create local SimulationTemplate
        self._simulation_template = core.SimulationTemplate(name=name, description=description, metadata=metadata)

        # Create local SimulationInstance
        self._simulation_instance = core.Scene.SimulationInstance(name=name, description=description, metadata=metadata)

        # Create local Job
        self._job = core.Job(
            name=self._name + ".Job", description=description, metadata=metadata, simulation_path=self._simulation_instance.name
        )
        if self._project.scene_link is not None:
            self._job.scene_guid = self._project.scene_link.key

    def set_direct(self) -> Direct:
        """Set the simulation as direct.

        Returns
        -------
        ansys.speos.script.simulation.Simulation.Direct
            Direct simulation.
        """
        if self._type is None and self._simulation_template.HasField("direct_mc_simulation_template"):
            self._type = Simulation.Direct(
                direct_template=self._simulation_template.direct_mc_simulation_template,
                direct_props_from_job=self._job.direct_mc_simulation_properties,
                default_values=False,
            )
        elif type(self._type) != Simulation.Direct:
            self._type = Simulation.Direct(
                direct_template=self._simulation_template.direct_mc_simulation_template,
                direct_props_from_job=self._job.direct_mc_simulation_properties,
            )

        return self._type

    def set_inverse(self) -> Inverse:
        """Set the simulation as inverse.

        Returns
        -------
        ansys.speos.script.simulation.Simulation.Inverse
            Inverse simulation.
        """
        if self._type is None and self._simulation_template.HasField("inverse_mc_simulation_template"):
            self._type = Simulation.Inverse(
                inverse_template=self._simulation_template.inverse_mc_simulation_template,
                inverse_props_from_job=self._job.inverse_mc_simulation_properties,
                default_values=False,
            )
        elif type(self._type) != Simulation.Inverse:
            self._type = Simulation.Inverse(
                inverse_template=self._simulation_template.inverse_mc_simulation_template,
                inverse_props_from_job=self._job.inverse_mc_simulation_properties,
            )

        return self._type

    def set_interactive(self) -> Simulation.Interactive:
        """Set the simulation as interactive.

        Returns
        -------
        ansys.speos.script.simulation.Simulation.Interactive
            Interactive simulation.
        """
        if self._type is None and self._simulation_template.HasField("interactive_simulation_template"):
            self._type = Simulation.Interactive(
                interactive_template=self._simulation_template.interactive_simulation_template,
                interactive_props_from_job=self._job.interactive_simulation_properties,
                default_values=False,
            )
        elif type(self._type) != Simulation.Interactive:
            self._type = Simulation.Interactive(
                interactive_template=self._simulation_template.interactive_simulation_template,
                interactive_props_from_job=self._job.interactive_simulation_properties,
            )

        return self._type

    @property
    def type(self) -> type:
        """Return type of simulation.

        Returns
        -------
        Example: ansys.speos.script.simulation.Simulation.Direct
        """
        return type(self._type)

    def set_sensor_paths(self, sensor_paths: List[str]) -> Simulation:
        """Set the sensors that the simulation will take into account.

        Parameters
        ----------
        sensor_paths : List[str]
            The sensor paths.

        Returns
        -------
        ansys.speos.script.simulation.Simulation
            Simulation feature.
        """
        self._simulation_instance.sensor_paths[:] = sensor_paths
        return self

    def set_source_paths(self, source_paths: List[str]) -> Simulation:
        """Set the sources that the simulation will take into account.

        Parameters
        ----------
        source_paths : List[str]
            The source paths.

        Returns
        -------
        ansys.speos.script.simulation.Simulation
            Simulation feature.
        """
        self._simulation_instance.source_paths[:] = source_paths
        return self

    # def set_geometries(self, geometries: List[GeoRef]) -> Simulation:
    #    """Set geometries that the simulation will take into account.
    #
    #    Parameters
    #    ----------
    #    geometries : List[ansys.speos.script.geo_ref.GeoRef]
    #        List of geometries.
    #
    #    Returns
    #    -------
    #    ansys.speos.script.simulation.Simulation
    #        Simulation feature.
    #    """
    #    if geometries is []:
    #        self._simulation_instance.ClearField("geometries")
    #    else:
    #        self._simulation_instance.geometries.geo_paths[:] = [gr.to_native_link() for gr in geometries]
    #
    #    return self

    def compute_CPU(self) -> List[job_pb2.Result]:
        """Compute the simulation on CPU.

        Returns
        -------
        List[ansys.api.speos.job.v2.job_pb2.Result]
            List of simulation results.
        """
        self._job.job_type = core.Job.Type.CPU
        self.result_list = self._run_job()
        return self.result_list

    def compute_GPU(self) -> List[job_pb2.Result]:
        """Compute the simulation on GPU.

        Returns
        -------
        List[ansys.api.speos.job.v2.job_pb2.Result]
            List of simulation results.
        """
        self._job.job_type = core.Job.Type.GPU
        self.result_list = self._run_job()
        return self.result_list

    def _run_job(self) -> List[job_pb2.Result]:
        if self.job_link is not None:
            job_state_res = self.job_link.get_state()
            if job_state_res.state != core.Job.State.QUEUED:
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
            job_state_res.state != core.Job.State.FINISHED
            and job_state_res.state != core.Job.State.STOPPED
            and job_state_res.state != core.Job.State.IN_ERROR
        ):
            time.sleep(5)

            job_state_res = self.job_link.get_state()
            if job_state_res.state == core.Job.State.IN_ERROR:
                core.LOG.error(core.protobuf_message_to_str(self.job_link.get_error()))

        return self.job_link.get_results().results

    def _to_dict(self) -> dict:
        out_dict = {}

        # SimulationInstance (= simulation guid + simulation properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            sim_inst = next((x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id), None)
            if sim_inst is not None:
                out_dict = proto_message_utils._replace_guids(speos_client=self._project.client, message=sim_inst)
            else:
                out_dict = proto_message_utils._replace_guids(speos_client=self._project.client, message=self._simulation_instance)
        else:
            out_dict = proto_message_utils._replace_guids(speos_client=self._project.client, message=self._simulation_instance)

        if "simulation" not in out_dict.keys():
            # SimulationTemplate
            if self.simulation_template_link is None:
                out_dict["simulation"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=self._simulation_template
                )
            else:
                out_dict["simulation"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=self.simulation_template_link.get()
                )

        if self.job_link is None:
            out_dict["simulation_properties"] = proto_message_utils._replace_guids(
                speos_client=self._project.client, message=self._job, ignore_simple_key="scene_guid"
            )
        else:
            out_dict["simulation_properties"] = proto_message_utils._replace_guids(
                speos_client=self._project.client, message=self.job_link.get(), ignore_simple_key="scene_guid"
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

        """

        if key == "":
            return self._to_dict()
        info = proto_message_utils._value_finder_key_startswith(dict_var=self._to_dict(), key=key)
        if list(info) != []:
            return next(info)[1]
        else:
            info = proto_message_utils._flatten_dict(dict_var=self._to_dict())
            print("Used key: {} not found in key list: {}.".format(key, info.keys()))

    def __str__(self) -> str:
        """Return the string representation of the simulation"""
        out_str = ""

        # SimulationInstance (= simulation guid + simulation properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            sim_inst = next((x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id), None)
            if sim_inst is None:
                out_str += "local: "
        else:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())

        return out_str

    def commit(self) -> Simulation:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.script.simulation.Simulation
            Simulation feature.
        """
        # The _unique_id will help to find correct item in the scene.simulations (the list of SimulationInstance)
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._simulation_instance.metadata["UniqueId"] = self._unique_id

        # Save or Update the simulation template (depending on if it was already saved before)
        if self.simulation_template_link is None:
            self.simulation_template_link = self._project.client.simulation_templates().create(message=self._simulation_template)
            self._simulation_instance.simulation_guid = self.simulation_template_link.key
        elif self.simulation_template_link.get() != self._simulation_template:
            self.simulation_template_link.set(data=self._simulation_template)  # Only update if template has changed

        # Update the scene with the simulation instance
        if self._project.scene_link:
            update_scene = True
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            simulation_inst = next((x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id), None)
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

    def reset(self) -> Simulation:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.script.simulation.Simulation
            Simulation feature.
        """
        # Reset simulation template
        if self.simulation_template_link is not None:
            self._simulation_template = self.simulation_template_link.get()

        # Reset simulation instance
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            # Look if an element corresponds to the _unique_id
            sim_inst = next((x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id), None)
            if sim_inst is not None:
                self._simulation_instance = sim_inst

        # Reset job
        if self.job_link is not None:
            self._job = self.job_link.get()
        return self

    def delete(self) -> Simulation:
        """Delete feature: delete data from the speos server database.
        The local data are still available

        Returns
        -------
        ansys.speos.script.simulation.Simulation
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
        sim_inst = next((x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id), None)
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
        self.simulation_template_link = self._project.client.get_item(key=sim_inst.simulation_guid)
        self.reset()

        # To get default values related to job -> simu properties
        if self._simulation_template.HasField("direct_mc_simulation_template"):
            self.set_direct()
        elif self._simulation_template.HasField("inverse_mc_simulation_template"):
            self.set_inverse()
        elif self._simulation_template.HasField("interactive_simulation_template"):
            self.set_interactive()
