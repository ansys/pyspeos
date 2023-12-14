"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum
from typing import List, Mapping, Optional

from ansys.api.speos.simulation.v1 import simulation_template_pb2 as messages
from ansys.api.speos.simulation.v1 import simulation_template_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

SimulationTemplate = messages.SimulationTemplate


class SimulationTemplateLink(CrudItem):
    """
    Link object for simulation template in database.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.simulation_template import SimulationTemplateFactory
    >>> speos = Speos(host="localhost", port=50051)
    >>> sim_t_db = speos.client.simulation_templates()
    >>> sim_t_link = sim_t_db.create(message=SimulationTemplateFactory.direct_mc(name="Direct_Default"))

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> SimulationTemplate:
        """Get the datamodel from database."""
        return self._stub.read(self)

    def set(self, data: SimulationTemplate) -> None:
        """Change datamodel in database."""
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class SimulationTemplateStub(CrudStub):
    """
    Database interactions for simulation templates.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> sim_t_db = speos.client.simulation_templates()

    """

    def __init__(self, channel):
        super().__init__(stub=service.SimulationTemplatesManagerStub(channel=channel))

    def create(self, message: SimulationTemplate) -> SimulationTemplateLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(simulation_template=message))
        return SimulationTemplateLink(self, resp.guid)

    def read(self, ref: SimulationTemplateLink) -> SimulationTemplate:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("SimulationTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.simulation_template

    def update(self, ref: SimulationTemplateLink, data: SimulationTemplate):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("SimulationTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, simulation_template=data))

    def delete(self, ref: SimulationTemplateLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("SimulationTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SimulationTemplateLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SimulationTemplateLink(self, x), guids))


class SimulationTemplateFactory:
    """Class to help creating SimulationTemplate message"""

    class CommonPropagationParameters:
        ColorimetricStandard = Enum("ColorimetricStandard", ["CIE_1931", "CIE_1964"])

        class Weight:
            """
            The Weight represents the ray energy. In real life, a ray looses some energy (power) when it interacts with an object.
            Activating weight means that the Weight message is present.
            When weight is not activated, rays' energy stay constant and probability laws dictate if they continue or stop propagating.
            When weight is activated, the ray's energy evolves with interactions until they reach the sensors.
            It is highly recommended to use Weight excepted in interactive simulation.
            Not using Weight is useful to understand certain phenomena as absorption.

            Parameters
            ----------
            minimum_energy_percentage : float, optional
                The Minimum energy percentage parameter defines the minimum energy ratio to continue to propagate a ray with weight.
                By default, ``0.5``.
            """

            def __init__(self, minimum_energy_percentage: Optional[float] = 0.5) -> None:
                self.minimum_energy_percentage = minimum_energy_percentage

        def __init__(
            self,
            geom_distance_tolerance: Optional[float] = 0.05,
            max_impact: Optional[int] = 100,
            colorimetric_standard: Optional[ColorimetricStandard] = ColorimetricStandard.CIE_1931,
            ambient_material_uri: Optional[str] = "",
            weight: Optional[Weight] = Weight(),
        ) -> None:
            """
            Represents common propagation parameters for a simulation.

            Parameters
            ----------
            geom_distance_tolerance : float, optional
                Maximum distance in mm to consider two faces as tangent.
                By default, ``0.05``.
            max_impact : int, optional
                Define a value to determine the maximum number of ray impacts during propagation.
                When a ray has interacted N times with the geometry, the propagation of the ray stops.
                By default, ``100``.
            colorimetric_standard : SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard, optional
                Default Colorimetric Standard.
                By default, ``SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard.CIE_1931``.
            ambient_material_uri : str, optional
                Define the environment in which the light will propagate (water, fog, smoke etc.). It is expressed in a .material file.
                By default, ``""``, ie air material.
            weight : SimulationTemplateFactory.CommonPropagationParameters.Weight, optional
                Activates Weight. Highly recommended to fill. See Weight class description.
                By default, ``SimulationTemplateFactory.CommonPropagationParameters.Weight()``.
            """
            self.geom_distance_tolerance = geom_distance_tolerance
            self.max_impact = max_impact
            self.colorimetric_standard = colorimetric_standard
            self.ambient_material_uri = ambient_material_uri
            self.weight = weight

    def direct_mc(
        name: str,
        common_propagation_parameters: Optional[CommonPropagationParameters] = CommonPropagationParameters(),
        dispersion: Optional[bool] = True,
        fast_transmission_gathering: Optional[bool] = False,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> SimulationTemplate:
        """
        Create a SimulationTemplate message, with direct type.

        Parameters
        ----------
        name : str
            Name of the simulation template.
        common_propagation_parameters : SimulationTemplateFactory.CommonPropagationParameters, optional
            Common propagation parameters.
            By default, ``SimulationTemplateFactory.CommonPropagationParameters()``.
        dispersion : bool, optional
            To activate the dispersion calculation.
            By default, ``True``.
        fast_transmission_gathering : bool, optional
            To accelerate the simulation by neglecting the light refraction that occurs when the light is being
            transmitted though a transparent surface.
            By default, ``False``.
        description : str, optional
            Description of the simulation template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the simulation template.
            By default, ``None``.

        Returns
        -------
        SimulationTemplate
            SimulationTemplate message created.
        """
        simu = SimulationTemplate(name=name, description=description)
        if metadata is not None:
            simu.metadata.update(metadata)
        simu.direct_mc_simulation_template.geom_distance_tolerance = common_propagation_parameters.geom_distance_tolerance
        simu.direct_mc_simulation_template.max_impact = common_propagation_parameters.max_impact
        if common_propagation_parameters.weight is not None:
            simu.direct_mc_simulation_template.weight.minimum_energy_percentage = (
                common_propagation_parameters.weight.minimum_energy_percentage
            )

        if (
            common_propagation_parameters.colorimetric_standard
            == SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard.CIE_1931
        ):
            simu.direct_mc_simulation_template.colorimetric_standard = messages.EnumColorimetricStandard.CIE_1931
        elif (
            common_propagation_parameters.colorimetric_standard
            == SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard.CIE_1964
        ):
            simu.direct_mc_simulation_template.colorimetric_standard = messages.EnumColorimetricStandard.CIE_1964

        simu.direct_mc_simulation_template.dispersion = dispersion
        simu.direct_mc_simulation_template.fast_transmission_gathering = fast_transmission_gathering
        simu.direct_mc_simulation_template.ambient_material_uri = common_propagation_parameters.ambient_material_uri
        return simu

    def inverse_mc(
        name: str,
        common_propagation_parameters: Optional[CommonPropagationParameters] = CommonPropagationParameters(),
        dispersion: Optional[bool] = False,
        splitting: Optional[bool] = False,
        number_of_gathering_rays_per_source: Optional[int] = 1,
        maximum_gathering_error: Optional[int] = 0,
        fast_transmission_gathering: Optional[bool] = False,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> SimulationTemplate:
        """
        Create a SimulationTemplate message, with inverse type.

        Parameters
        ----------
        name : str
            Name of the simulation template.
        common_propagation_parameters : SimulationTemplateFactory.CommonPropagationParameters, optional
            Common propagation parameters.
            By default, ``SimulationTemplateFactory.CommonPropagationParameters()``.
        dispersion : bool, optional
            To activate the dispersion calculation.
            By default, ``False``.
        splitting : bool, optional
            To split each propagated ray into several paths at their first impact after leaving the observer point.
            By default, ``False``.
        number_of_gathering_rays_per_source : int, optional
            This number pilots the number of shadow rays to target at each source.
            By default, ``1``.
        maximum_gathering_error : int, optional
            This value defines the level below which a source can be neglected. 0,
            the default value means that no approximation will be done.
            By default, ``0``.
        fast_transmission_gathering : bool, optional
            To accelerate the simulation by neglecting the light refraction that occurs when the light is being
            transmitted though a transparent surface.
            By default, ``False``.
        description : str, optional
            Description of the simulation template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the simulation template.
            By default, ``None``.

        Returns
        -------
        SimulationTemplate
            SimulationTemplate message created.
        """
        simu = SimulationTemplate(name=name, description=description)
        if metadata is not None:
            simu.metadata.update(metadata)
        simu.inverse_mc_simulation_template.geom_distance_tolerance = common_propagation_parameters.geom_distance_tolerance
        simu.inverse_mc_simulation_template.max_impact = common_propagation_parameters.max_impact
        if common_propagation_parameters.weight is not None:
            simu.inverse_mc_simulation_template.weight.minimum_energy_percentage = (
                common_propagation_parameters.weight.minimum_energy_percentage
            )

        if (
            common_propagation_parameters.colorimetric_standard
            == SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard.CIE_1931
        ):
            simu.inverse_mc_simulation_template.colorimetric_standard = messages.EnumColorimetricStandard.CIE_1931
        elif (
            common_propagation_parameters.colorimetric_standard
            == SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard.CIE_1964
        ):
            simu.inverse_mc_simulation_template.colorimetric_standard = messages.EnumColorimetricStandard.CIE_1964

        simu.inverse_mc_simulation_template.dispersion = dispersion
        simu.inverse_mc_simulation_template.splitting = splitting
        simu.inverse_mc_simulation_template.number_of_gathering_rays_per_source = number_of_gathering_rays_per_source
        simu.inverse_mc_simulation_template.maximum_gathering_error = maximum_gathering_error
        simu.inverse_mc_simulation_template.fast_transmission_gathering = fast_transmission_gathering
        simu.inverse_mc_simulation_template.ambient_material_uri = common_propagation_parameters.ambient_material_uri
        return simu

    def interactive(
        name: str,
        common_propagation_parameters: Optional[CommonPropagationParameters] = CommonPropagationParameters(weight=None),
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> SimulationTemplate:
        """
        Create a SimulationTemplate message, with interactive type.

        Parameters
        ----------
        name : str
            Name of the simulation template.
        common_propagation_parameters : SimulationTemplateFactory.CommonPropagationParameters, optional
            Common propagation parameters.
            By default, ``SimulationTemplateFactory.CommonPropagationParameters(weight=None)``.
        description : str, optional
            Description of the simulation template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the simulation template.
            By default, ``None``.

        Returns
        -------
        SimulationTemplate
            SimulationTemplate message created.
        """
        simu = SimulationTemplate(name=name, description=description)
        if metadata is not None:
            simu.metadata.update(metadata)
        simu.interactive_simulation_template.geom_distance_tolerance = common_propagation_parameters.geom_distance_tolerance
        simu.interactive_simulation_template.max_impact = common_propagation_parameters.max_impact
        if common_propagation_parameters.weight is not None:
            simu.interactive_simulation_template.weight.minimum_energy_percentage = (
                common_propagation_parameters.weight.minimum_energy_percentage
            )

        if (
            common_propagation_parameters.colorimetric_standard
            == SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard.CIE_1931
        ):
            simu.interactive_simulation_template.colorimetric_standard = messages.EnumColorimetricStandard.CIE_1931
        elif (
            common_propagation_parameters.colorimetric_standard
            == SimulationTemplateFactory.CommonPropagationParameters.ColorimetricStandard.CIE_1964
        ):
            simu.interactive_simulation_template.colorimetric_standard = messages.EnumColorimetricStandard.CIE_1964

        simu.interactive_simulation_template.ambient_material_uri = common_propagation_parameters.ambient_material_uri
        return simu
