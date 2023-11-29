"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum

from ansys.api.speos.simulation.v1 import simulation_template_pb2 as messages
from ansys.api.speos.simulation.v1 import simulation_template_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message import protobuf_message_to_str

SimulationTemplate = messages.SimulationTemplate


class SimulationTemplateLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> SimulationTemplate:
        return self._stub.read(self)

    def set(self, data: SimulationTemplate) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class SimulationTemplateStub(CrudStub):
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

    def list(self) -> list[SimulationTemplateLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SimulationTemplateLink(self, x), guids))


class SimulationTemplateFactory:
    class CommonPropagationParameters:
        ColorimetricStandard = Enum("ColorimetricStandard", ["CIE_1931", "CIE_1964"])

        class Weight:
            def __init__(self, minimum_energy_percentage: float = 0.5) -> None:
                self.minimum_energy_percentage = minimum_energy_percentage

        def __init__(
            self,
            geom_distance_tolerance: float = 0.05,
            max_impact: int = 100,
            colorimetric_standard: ColorimetricStandard = ColorimetricStandard.CIE_1931,
            ambient_material_uri: str = "",
            weight: Weight | None = Weight(),
        ) -> None:
            self.geom_distance_tolerance = geom_distance_tolerance
            self.max_impact = max_impact
            self.colorimetric_standard = colorimetric_standard
            self.ambient_material_uri = ambient_material_uri
            self.weight = weight

    def direct_mc(
        name: str,
        description: str,
        common_propagation_parameters: CommonPropagationParameters = CommonPropagationParameters(),
        dispersion: bool = True,
        fast_transmission_gathering: bool = False,
    ) -> SimulationTemplate:
        simu = SimulationTemplate(name=name, description=description)
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
        description: str,
        common_propagation_parameters: CommonPropagationParameters = CommonPropagationParameters(),
        dispersion: bool = False,
        splitting: bool = False,
        number_of_gathering_rays_per_source: int = 1,
        maximum_gathering_error: int = 0,
        fast_transmission_gathering: bool = False,
    ) -> SimulationTemplate:
        simu = SimulationTemplate(name=name, description=description)
        simu.inverse_mc_simulation_template.geom_distance_tolerance = common_propagation_parameters.geom_distance_tolerance
        simu.inverse_mc_simulation_template.max_impact = common_propagation_parameters.max_impact
        if simu.inverse_mc_simulation_template.weight is not None:
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
        description: str,
        common_propagation_parameters: CommonPropagationParameters = CommonPropagationParameters(),
    ) -> SimulationTemplate:
        simu = SimulationTemplate(name=name, description=description)
        simu.interactive_simulation_template.geom_distance_tolerance = common_propagation_parameters.geom_distance_tolerance
        simu.interactive_simulation_template.max_impact = common_propagation_parameters.max_impact
        if simu.interactive_simulation_template.weight is not None:
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
