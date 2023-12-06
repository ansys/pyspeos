"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum
from typing import Mapping

from ansys.api.speos.source.v1 import source_pb2 as messages
from ansys.api.speos.source.v1 import source_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.intensity_template import IntensityTemplateLink
from ansys.speos.core.proto_message_utils import protobuf_message_to_str
from ansys.speos.core.spectrum import SpectrumLink

SourceTemplate = messages.SourceTemplate


class SourceTemplateLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> SourceTemplate:
        return self._stub.read(self)

    def set(self, data: SourceTemplate) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class SourceTemplateStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.SourceTemplatesManagerStub(channel=channel))

    def create(self, message: SourceTemplate) -> SourceTemplateLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(source_template=message))
        return SourceTemplateLink(self, resp.guid)

    def read(self, ref: SourceTemplateLink) -> SourceTemplate:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("SourceTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.source_template

    def update(self, ref: SourceTemplateLink, data: SourceTemplate):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("SourceTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, source_template=data))

    def delete(self, ref: SourceTemplateLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("SourceTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> list[SourceTemplateLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SourceTemplateLink(self, x), guids))


class SourceTemplateFactory:
    class Flux:
        Unit = Enum("Unit", ["Lumen", "Watt", "Candela"])

        def __init__(self, unit: Unit = Unit.Lumen, value: float = 683) -> None:
            self.unit = unit
            self.value = value

    def luminaire(
        name: str,
        intensity_file_uri: str,
        spectrum: SpectrumLink,
        flux: Flux = None,
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> SourceTemplate:
        src = SourceTemplate(name=name, description=description)
        if metadata is not None:
            src.metadata.update(metadata)

        if flux is None:
            src.luminaire.flux_from_intensity_file.SetInParent()
        elif flux.unit == SourceTemplateFactory.Flux.Unit.Lumen:
            src.luminaire.luminous_flux.luminous_value = flux.value
        elif flux.unit == SourceTemplateFactory.Flux.Unit.Watt:
            src.luminaire.radiant_flux.radiant_value = flux.value
        else:
            src.luminaire.flux_from_intensity_file.SetInParent()

        src.luminaire.intensity_file_uri = intensity_file_uri
        src.luminaire.spectrum_guid = spectrum.key
        return src

    def surface(
        name: str,
        intensity_template: IntensityTemplateLink,
        flux: Flux = None,
        exitance_xmp_file_uri: str = "",
        spectrum: SpectrumLink = None,
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> SourceTemplate:
        src = SourceTemplate(name=name, description=description)
        if metadata is not None:
            src.metadata.update(metadata)

        if flux is None:
            src.surface.flux_from_intensity_file.SetInParent()
        elif flux.unit == SourceTemplateFactory.Flux.Unit.Lumen:
            src.surface.luminous_flux.luminous_value = flux.value
        elif flux.unit == SourceTemplateFactory.Flux.Unit.Watt:
            src.surface.radiant_flux.radiant_value = flux.value
        elif flux.unit == SourceTemplateFactory.Flux.Unit.Candela:
            src.surface.luminous_intensity_flux.luminous_intensity_value = flux.value
        else:
            src.surface.flux_from_intensity_file.SetInParent()

        src.surface.intensity_guid = intensity_template.key

        if exitance_xmp_file_uri == "":
            src.surface.exitance_constant.SetInParent()
        else:
            src.surface.exitance_variable.exitance_xmp_file_uri = exitance_xmp_file_uri

        if spectrum is not None:
            src.surface.spectrum_guid = spectrum.key
        else:
            src.surface.spectrum_from_xmp_file.SetInParent()

        return src
