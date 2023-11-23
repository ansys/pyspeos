"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from ansys.api.speos.spectrum.v1 import spectrum_pb2 as messages
from ansys.api.speos.spectrum.v1 import spectrum_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub

Spectrum = messages.Spectrum


class SpectrumLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def get(self) -> Spectrum:
        return self._stub.Read(self)

    def set(self, data: Spectrum) -> None:
        self._stub.Update(self, data)

    def delete(self) -> None:
        self._stub.Delete(self)


class SpectrumStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.SpectrumsManagerStub(channel=channel))

    def Create(self, message: Spectrum) -> SpectrumLink:
        """Create a new entry."""
        resp = CrudStub.Create(self, messages.Create_Request(spectrum=message))
        return SpectrumLink(self, resp.guid)

    def Read(self, ref: SpectrumLink) -> Spectrum:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("SpectrumLink is not on current database")
        resp = CrudStub.Read(self, messages.Read_Request(guid=ref.key))
        return resp.spectrum

    def Update(self, ref: SpectrumLink, data: Spectrum):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("SpectrumLink is not on current database")
        CrudStub.Update(self, messages.Update_Request(guid=ref.key, spectrum=data))

    def Delete(self, ref: SpectrumLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("SpectrumLink is not on current database")
        CrudStub.Delete(self, messages.Delete_Request(guid=ref.key))

    def List(self) -> list[SpectrumLink]:
        """List existing entries."""
        guids = CrudStub.List(self, messages.List_Request()).guids
        return list(map(lambda x: SpectrumLink(self, x), guids))
