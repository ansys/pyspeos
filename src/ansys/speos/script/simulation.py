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

from typing import List, Mapping
import uuid

from ansys.api.speos.simulation.v1 import simulation_template_pb2

import ansys.speos.core as core

# from ansys.speos.script.geo_ref import GeoRef
import ansys.speos.script.project as project


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

        Parameters
        ----------
        direct_template : ansys.api.speos.simulation.v1.simulation_template_pb2.DirectMCSimulationTemplate
            Direct simulation to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(self, direct_template: simulation_template_pb2.DirectMCSimulationTemplate, default_values: bool = True) -> None:
            self._direct_template = direct_template

            if default_values:
                # Default values
                self.set_geom_distance_tolerance()
                self.set_max_impact()
                self.set_colorimetric_standard_CIE_1931()
                self.set_dispersion()
                # self.set_fast_transmission_gathering()
                self.set_ambient_material_file_uri()
                self.set_weight()

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

        Parameters
        ----------
        inverse_template : ansys.api.speos.simulation.v1.simulation_template_pb2.InverseMCSimulationTemplate
            Inverse simulation to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(self, inverse_template: simulation_template_pb2.InverseMCSimulationTemplate, default_values: bool = True) -> None:
            self._inverse_template = inverse_template

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

    class Interactive:
        """Type of simulation : Interactive.
        By default,
        geometry distance tolerance is set to 0.01,
        maximum number of impacts is set to 100,
        colorimetric standard is set to CIE 1931,
        ambient material URI is empty,
        and weight's minimum energy percentage is set to 0.005.

        Parameters
        ----------
        interactive_template : ansys.api.speos.simulation.v1.simulation_template_pb2.SimulationTemplate.Interactive
            Interactive simulation to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(self, interactive_template: core.SimulationTemplate.Interactive, default_values: bool = True) -> None:
            self._interactive_template = interactive_template

            if default_values:
                # Default values
                self.set_geom_distance_tolerance()
                self.set_max_impact()
                self.set_weight()
                self.set_colorimetric_standard_CIE_1931()
                self.set_ambient_material_file_uri()

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

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._name = name
        self._unique_id = None
        self.simulation_template_link = None
        """Link object for the simulation template in database."""

        # Attribute representing the kind of simulation.
        self._type = None

        # Create local SimulationTemplate
        self._simulation_template = core.SimulationTemplate(name=name, description=description, metadata=metadata)

        # Create local SimulationInstance
        self._simulation_instance = core.Scene.SimulationInstance(name=name, description=description, metadata=metadata)

    def set_direct(self) -> Direct:
        """Set the simulation as direct.

        Returns
        -------
        ansys.speos.script.simulation.Simulation.Direct
            Direct simulation.
        """
        if self._type is None and self._simulation_template.HasField("direct_mc_simulation_template"):
            self._type = Simulation.Direct(direct_template=self._simulation_template.direct_mc_simulation_template, default_values=False)
        elif type(self._type) != Simulation.Direct:
            self._type = Simulation.Direct(direct_template=self._simulation_template.direct_mc_simulation_template)

        return self._type

    def set_inverse(self) -> Inverse:
        """Set the simulation as inverse.

        Returns
        -------
        ansys.speos.script.simulation.Simulation.Inverse
            Inverse simulation.
        """
        if self._type is None and self._simulation_template.HasField("inverse_mc_simulation_template"):
            self._type = Simulation.Inverse(inverse_template=self._simulation_template.inverse_mc_simulation_template, default_values=False)
        elif type(self._type) != Simulation.Inverse:
            self._type = Simulation.Inverse(inverse_template=self._simulation_template.inverse_mc_simulation_template)

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
                interactive_template=self._simulation_template.interactive_simulation_template, default_values=False
            )
        elif type(self._type) != Simulation.Interactive:
            self._type = Simulation.Interactive(interactive_template=self._simulation_template.interactive_simulation_template)

        return self._type

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

    def __str__(self) -> str:
        """Return the string representation of the simulation"""
        out_str = ""
        # SimulationInstance (= simulation guid + simulation properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            sim_inst = next((x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id), None)
            if sim_inst is not None:
                out_str += core.protobuf_message_to_str(sim_inst)
            else:
                out_str += f"local: " + core.protobuf_message_to_str(self._simulation_instance)
        else:
            out_str += f"local: " + core.protobuf_message_to_str(self._simulation_instance)

        # SimulationTemplate
        if self.simulation_template_link is None:
            out_str += "\nlocal: " + core.protobuf_message_to_str(self._simulation_template)
        else:
            out_str += "\n" + str(self.simulation_template_link)

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
        else:
            self.simulation_template_link.set(data=self._simulation_template)

        # Update the scene with the simulation instance
        if self._project.scene_link:
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            simulation_inst = next((x for x in scene_data.simulations if x.metadata["UniqueId"] == self._unique_id), None)
            if simulation_inst is not None:
                simulation_inst.CopyFrom(self._simulation_instance)  # if yes, just replace
            else:
                scene_data.simulations.insert(
                    len(scene_data.simulations), self._simulation_instance
                )  # if no, just add it to the list of simulations

            self._project.scene_link.set(data=scene_data)  # update scene data

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
        return self
