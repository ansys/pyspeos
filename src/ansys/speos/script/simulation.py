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
from ansys.speos.script.geo_ref import GeoRef
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
        """Type of weight : Minimum energy percentage."""

        def __init__(self, weight: simulation_template_pb2.Weight) -> None:
            self._weight = weight
            # Default values
            self.set_minimum_energy_percentage()

        def set_minimum_energy_percentage(self, value: float = 0.5) -> Simulation.Weight:
            """Set the minimum energy percentage.

            Parameters
            ----------
            value : float
                The minimum energy percentage.
                by default, ``0.5``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Weight
                Weight.
            """
            self._weight.minimum_energy_percentage = value
            return self

    class DirectSimulation:
        """
        Type of simulation : Direct
        By default,
        geometry distance tolerance is set to 0.05,
        maximum number of impacts is set to 100,
        colorimetric standard is set to CIE 1931,
        dispersion is set to True,
        fast transmission gathering is set to False,
        ambient material URI is empty,
        and weight is set to 0.5.

        Parameters
        ----------
        simulation_template : ansys.api.speos.simulation.v1.simulation_template_pb2.SimulationTemplate
            Simulation template.

        """

        def __init__(self, simulation_template: core.SimulationTemplate) -> None:
            self._simulation_template = simulation_template

            # Default values
            self.set_geom_distance_tolerance()
            self.set_max_impact()
            self.set_colorimetric_standard_CIE_1931()
            self.set_dispersion()
            self.set_fast_transmission_gathering()
            self.set_ambient_material_file_uri()
            self.set_weight()

        def set_geom_distance_tolerance(self, value: float = 0.05) -> Simulation.DirectSimulation:
            """Set the geometry distance tolerance.

            Parameters
            ----------
            value : float
                The geometry distance tolerance.
                by default, ``0.05``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.DirectSimulation
                Direct simulation
            """
            self._simulation_template.direct_mc_simulation_template.geom_distance_tolerance = value
            return self

        def set_max_impact(self, value: int = 100) -> Simulation.DirectSimulation:
            """Set the maximum number of impacts.

            Parameters
            ----------
            value : int
                The maximum number of impacts.
                by default, ``100``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.DirectSimulation
                Direct simulation
            """
            self._simulation_template.direct_mc_simulation_template.max_impact = value
            return self

        def set_weight(self) -> Simulation.Weight:
            """Set the weight.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Weight
                Weight.
            """
            return Simulation.Weight(self._simulation_template.direct_mc_simulation_template.weight)

        def set_weight_none(self) -> Simulation.DirectSimulation:
            """Deactivate the weight.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.DirectSimulation
                Direct simulation
            """
            self._simulation_template.ClearField("weight")
            return self

        def set_colorimetric_standard_CIE_1931(self) -> Simulation.DirectSimulation:
            """Set the colorimetric standard to CIE 1931.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.DirectSimulation
                Direct simulation
            """
            self._simulation_template.direct_mc_simulation_template.colorimetric_standard = simulation_template_pb2.CIE_1931
            return self

        def set_colorimetric_standard_CIE_1964(self) -> Simulation.DirectSimulation:
            """Set the colorimetric standard to CIE 1964.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.DirectSimulation
                Direct simulation
            """
            self._simulation_template.direct_mc_simulation_template.colorimetric_standard = simulation_template_pb2.CIE_1964
            return self

        def set_dispersion(self, value: bool = True) -> Simulation.DirectSimulation:
            """Set the dispersion.

            Parameters
            ----------
            value : bool
                The dispersion.
                by default, ``True``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.DirectSimulation
                Direct simulation
            """
            self._simulation_template.direct_mc_simulation_template.dispersion = value
            return self

        def set_fast_transmission_gathering(self, value: bool = False) -> Simulation.DirectSimulation:
            """Set the fast transmission gathering.

            Parameters
            ----------
            value : bool
                The fast transmission gathering.
                by default, ``False``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.DirectSimulation
                Direct simulation
            """
            self._simulation_template.direct_mc_simulation_template.fast_transmission_gathering = value
            return self

        def set_ambient_material_file_uri(self, url: str = "") -> Simulation.DirectSimulation:
            """Set the ambient material URI.

            Parameters
            ----------
            url : str
                The ambient material URI.
                by default, ``""``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.DirectSimulation
                Direct simulation
            """
            self._simulation_template.direct_mc_simulation_template.ambient_material_uri = url
            return self

        def __str__(self) -> str:
            out_str = ""
            if self._simulation_template is not None:
                out_str += str(self._simulation_template)
            return out_str

    class InverseSimulation:
        """Type of simulation : Inverse
        By default,
        geometry distance tolerance is set to 0.05,
        maximum number of impacts is set to 100,
        colorimetric standard is set to CIE 1931,
        dispersion is set to True,
        splitting is set to False,
        number of gathering rays per source is set to 1,
        maximum gathering error is set to 0,
        fast transmission gathering is set to False,
        ambient material URI is empty,
        and weight is set to 0.5.

        Parameters
        ----------
        simulation_template : ansys.api.speos.simulation.v1.simulation_template_pb2.SimulationTemplate
            Simulation template.
        """

        def __init__(self, simulation_template: core.SimulationTemplate) -> None:
            self._simulation_template = simulation_template

            # Default values
            self.set_geom_distance_tolerance()
            self.set_max_impact()
            self.set_weight()
            self.set_colorimetric_standard_CIE_1931()
            self.set_dispersion()
            self.set_splitting()
            self.set_number_of_gathering_rays_per_source()
            self.set_maximum_gathering_error()
            self.set_fast_transmission_gathering()
            self.set_ambient_material_file_uri()

        def set_geom_distance_tolerance(self, value: float = 0.05) -> Simulation.InverseSimulation:
            """Set the geometry distance tolerance.

            Parameters
            ----------
            value : float
                The geometry distance tolerance.
                by default, ``0.05``

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.inverse_mc_simulation_template.geom_distance_tolerance = value
            return self

        def set_max_impact(self, value: int = 100) -> Simulation.InverseSimulation:
            """Set the maximum number of impacts.

            Parameters
            ----------
            value : int
                The maximum number of impacts.
                by default, ``100``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.inverse_mc_simulation_template.max_impact = value
            return self

        def set_weight(self) -> Simulation.Weight:
            """Set the weight .

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Weight
                Simulation.Weight
            """
            return Simulation.Weight(self._simulation_template.inverse_mc_simulation_template.weight)

        def set_weight_none(self) -> Simulation.InverseSimulation:
            """Deactivate the weight.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.ClearField("weight")
            return self

        def set_colorimetric_standard_CIE_1931(self) -> Simulation.InverseSimulation:
            """Set the colorimetric standard to CIE 1931.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.inverse_mc_simulation_template.colorimetric_standard = simulation_template_pb2.CIE_1931
            return self

        def set_colorimetric_standard_CIE_1964(self) -> Simulation.InverseSimulation:
            """Set the colorimetric standard to CIE 1964.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.inverse_mc_simulation_template.colorimetric_standard = simulation_template_pb2.CIE_1964
            return self

        def set_dispersion(self, value: bool = True) -> Simulation.InverseSimulation:
            """Set the dispersion.

            Parameters
            ----------
            value : bool
                The dispersion.
                by default, ``True``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.inverse_mc_simulation_template.dispersion = value
            return self

        def set_splitting(self, value: bool = False) -> Simulation.InverseSimulation:
            """Set the splitting.

            Parameters
            ----------
            value : bool
                The splitting.
                by default, ``False``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.inverse_mc_simulation_template.splitting = value
            return self

        def set_number_of_gathering_rays_per_source(self, value: int = 1) -> Simulation.InverseSimulation:
            """Set the number of gathering rays per source.

            Parameters
            ----------
            value : int
                The number of gathering rays per source.
                by default, ``1``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.inverse_mc_simulation_template.number_of_gathering_rays_per_source = value
            return self

        def set_maximum_gathering_error(self, value: int = 0) -> Simulation.InverseSimulation:
            """Set the maximum gathering error.

            Parameters
            ----------
            value : int
                The maximum gathering error.
                by default, ``0``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.inverse_mc_simulation_template.maximum_gathering_error = value
            return self

        def set_fast_transmission_gathering(self, fast_transmission_gathering: bool = False) -> Simulation.InverseSimulation:
            """Set the fast transmission gathering.

            Parameters
            ----------
            fast_transmission_gathering : bool
                The fast transmission gathering.
                by default, ``False``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.inverse_mc_simulation_template.fast_transmission_gathering = fast_transmission_gathering
            return self

        def set_ambient_material_file_uri(self, url: str = "") -> Simulation.InverseSimulation:
            """Set the ambient material URI.

            Parameters
            ----------
            url : str
                The ambient material URI.
                by default, ``""``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.InverseSimulation
                Inverse simulation
            """
            self._simulation_template.inverse_mc_simulation_template.ambient_material_uri = url
            return self

        def __str__(self) -> str:
            out_str = ""
            if self._simulation_template is not None:
                out_str += str(self._simulation_template)
            return out_str

    class Interactive:
        """Type of simulation : Interactive
        By default,
        geometry distance tolerance is set to 0.05,
        maximum number of impacts is set to 100,
        colorimetric standard is set to CIE 1931,
        ambient material URI is empty,
        and weight is set to 0.5.

        Parameters
        ----------
        simulation_template : ansys.api.speos.simulation.v1.simulation_template_pb2.SimulationTemplate
            Simulation template.
        """

        def __init__(self, simulation_template: core.SimulationTemplate) -> None:
            self._simulation_template = simulation_template

            # Default values
            self.set_geom_distance_tolerance()
            self.set_max_impact()
            self.set_weight()
            self.set_colorimetric_standard_CIE_1931()
            self.set_ambient_material_file_uri()

        def set_geom_distance_tolerance(self, value: float = 0.05) -> Simulation.Interactive:
            """Set the geometry distance tolerance.

            Parameters
            ----------
            value : float
                The geometry distance tolerance.
                by default, ``0.05``

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._simulation_template.interactive_simulation_template.geom_distance_tolerance = value
            return self

        def set_max_impact(self, value: int = 100) -> Simulation.Interactive:
            """Set the maximum number of impacts.

            Parameters
            ----------
            value : int
                The maximum number of impacts.
                by default, ``100``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._simulation_template.interactive_simulation_template.max_impact = value
            return self

        def set_weight(self) -> Simulation.Weight:
            """Set the weight .

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Weight
                Simulation.Weight
            """
            return Simulation.Weight(self._simulation_template.interactive_simulation_template.weight)

        def set_weight_none(self) -> Simulation.Interactive:
            """Deactivate the weight.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._simulation_template.ClearField("weight")
            return self

        def set_colorimetric_standard_CIE_1931(self) -> Simulation.Interactive:
            """Set the colorimetric standard to CIE 1931.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._simulation_template.interactive_simulation_template.colorimetric_standard = simulation_template_pb2.CIE_1931
            return self

        def set_colorimetric_standard_CIE_1964(self) -> Simulation.Interactive:
            """Set the colorimetric standard to CIE 1964.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._simulation_template.interactive_simulation_template.colorimetric_standard = simulation_template_pb2.CIE_1964
            return self

        def set_ambient_material_file_uri(self, url: str = "") -> Simulation.Interactive:
            """Set the ambient material URI.

            Parameters
            ----------
            url : str
                The ambient material URI.
                by default, ``""``.

            Returns
            -------
            ansys.speos.script.simulation.Simulation.Interactive
                Interactive simulation
            """
            self._simulation_template.inverse_mc_simulation_template.ambient_material_uri = url
            return self

        def __str__(self) -> str:
            out_str = ""
            if self._simulation_template is not None:
                out_str += str(self._simulation_template)
            return out_str

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._unique_id = None
        self.simulation_template_link = None
        """Link object for the simulation template in database."""

        # Attribute representing the kind of simulation.
        self._type = None

        # Create local SimulationTemplate
        self._simulation_template = core.SimulationTemplate(name=name, description=description, metadata=metadata)

        # Create local SimulationInstance
        self._simulation_instance = core.Scene.SimulationInstance(name=name, description=description, metadata=metadata)

    def set_direct(self) -> DirectSimulation:
        """Set the Direct simulation template.

        Parameters
        ----------
        name : str
            Name of the Direct simulation template.

        Returns
        -------
        ansys.speos.script.simulation.Simulation.DirectSimulation
            Direct simulation.
        """

        if type(self._type) != Simulation.DirectSimulation:
            self._type = Simulation.DirectSimulation(direct_simulation_template=self._simulation_template)

        return self._type

    def set_inverse(self) -> InverseSimulation:
        """Set the Inverse simulation template.

        Parameters
        ----------
        name : str
            Name of the Inverse simulation template.

        Returns
        -------
        ansys.speos.script.simulation.Simulation.InverseSimulation
            Inverse simulation.
        """

        if type(self._type) != Simulation.InverseSimulation:
            self._type = Simulation.InverseSimulation(inverse_simulation_template=self._simulation_template)

        return self._type

    def set_interactive(self) -> Simulation.Interactive:
        """Set the Interactive simulation template.

        Parameters
        ----------
        name : str
            Name of the Interactive simulation template.

        Returns
        -------
        ansys.speos.script.simulation.Simulation.Interactive
            Interactive simulation.
        """

        if type(self._type) != Simulation.Interactive:
            self._type = Simulation.Interactive(interactive_simulation_template=self._simulation_template)

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

    def set_geometries(self, geometries: List[GeoRef]) -> Simulation:
        """Set geometries that the simulation will take into account.

        Parameters
        ----------
        geometries : List[ansys.speos.script.geo_ref.GeoRef]
            List of geometries.

        Returns
        -------
        ansys.speos.script.simulation.Simulation
            Simulation feature.
        """
        if geometries is []:
            self._simulation_instance.ClearField("geometries")
        else:
            self._simulation_instance.geometries.geo_paths[:] = [gr.to_native_link() for gr in geometries]

        return self

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
            out_str += f"\nlocal: {self._simulation_template}"
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

            print(scene_data)
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
