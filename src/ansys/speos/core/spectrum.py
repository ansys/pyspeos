"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum
from typing import List, Mapping

from ansys.api.speos.spectrum.v1 import spectrum_pb2 as messages
from ansys.api.speos.spectrum.v1 import spectrum_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

Spectrum = messages.Spectrum


class SpectrumLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> Spectrum:
        return self._stub.read(self)

    def set(self, data: Spectrum) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class SpectrumStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.SpectrumsManagerStub(channel=channel))

    def create(self, message: Spectrum) -> SpectrumLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(spectrum=message))
        return SpectrumLink(self, resp.guid)

    def read(self, ref: SpectrumLink) -> Spectrum:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("SpectrumLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.spectrum

    def update(self, ref: SpectrumLink, data: Spectrum):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("SpectrumLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, spectrum=data))

    def delete(self, ref: SpectrumLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("SpectrumLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SpectrumLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SpectrumLink(self, x), guids))


class SpectrumFactory:
    PredefinedType = Enum(
        "PredefinedType",
        [
            "Incandescent",
            "WarmWhiteFluorescent",
            "DaylightFluorescent",
            "WhiteLED",
            "Halogen",
            "MetalHalide",
            "HighPressureSodium",
        ],
    )

    def monochromatic(name: str, wavelength: float = 555, description: str = "", metadata: Mapping[str, str] = None) -> Spectrum:
        spec = Spectrum(name=name, description=description)
        if metadata is not None:
            spec.metadata.update(metadata)
        spec.monochromatic.wavelength = wavelength
        return spec

    def blackbody(name: str, temperature: float = 2856, description: str = "", metadata: Mapping[str, str] = None) -> Spectrum:
        spec = Spectrum(name=name, description=description)
        if metadata is not None:
            spec.metadata.update(metadata)
        spec.blackbody.temperature = temperature
        return spec

    def sampled(
        name: str, wavelengths: List[float], values: List[float], description: str = "", metadata: Mapping[str, str] = None
    ) -> Spectrum:
        spec = Spectrum(name=name, description=description)
        if metadata is not None:
            spec.metadata.update(metadata)
        spec.sampled.wavelengths.extend(wavelengths)
        spec.sampled.values.extend(values)
        return spec

    def library(name: str, file_uri: str, description: str = "", metadata: Mapping[str, str] = None) -> Spectrum:
        spec = Spectrum(name=name, description=description)
        if metadata is not None:
            spec.metadata.update(metadata)
        spec.library.file_uri = file_uri
        return spec

    def predefined(
        name: str, type: PredefinedType = PredefinedType.Incandescent, description: str = "", metadata: Mapping[str, str] = None
    ) -> Spectrum:
        spec = Spectrum(name=name, description=description)
        if metadata is not None:
            spec.metadata.update(metadata)
        if type == SpectrumFactory.PredefinedType.Incandescent:
            spec.predefined.incandescent.SetInParent()
        elif type == SpectrumFactory.PredefinedType.WarmWhiteFluorescent:
            spec.predefined.warmwhitefluorescent.SetInParent()
        elif type == SpectrumFactory.PredefinedType.DaylightFluorescent:
            spec.predefined.daylightfluorescent.SetInParent()
        elif type == SpectrumFactory.PredefinedType.WhiteLED:
            spec.predefined.whiteLED.SetInParent()
        elif type == SpectrumFactory.PredefinedType.Halogen:
            spec.predefined.halogen.SetInParent()
        elif type == SpectrumFactory.PredefinedType.MetalHalide:
            spec.predefined.metalhalide.SetInParent()
        elif type == SpectrumFactory.PredefinedType.HighPressureSodium:
            spec.predefined.highpressuresodium.SetInParent()

        return spec
