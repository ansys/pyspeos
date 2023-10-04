"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from ansys.api.speos.spectrum.v1 import spectrum_pb2 as messages
from ansys.api.speos.spectrum.v1 import spectrum_pb2_grpc as service

from ansys.speos.core.crud import Database, DatabaseItem


class Spectrum(DatabaseItem):
    Content = messages.Spectrum

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def send_read(self) -> Content:
        return DatabaseItem.send_read(self)


class SpectrumDatabase(Database):
    def __init__(self, channel):
        super().__init__(stub=service.SpectrumsManagerStub(channel=channel))

    """Create a new entry."""

    def Create(self, message: DatabaseItem) -> str:
        return Database.Create(self, messages.Create_Request(spectrum=message)).guid

    """Get an existing entry."""

    def Read(self, key: str) -> DatabaseItem:
        return Database.Read(self, messages.Read_Request(guid=key)).spectrum

    """Change an existing entry."""

    def Update(self, key: str, message: DatabaseItem):
        Database.Update(self, messages.Update_Request(guid=key, spectrum=message))

    """Remove an existing entry."""

    def Delete(self, key: str):
        Database.Delete(self, messages.Delete_Request(guid=key))

    """List existing entries."""

    def List(self) -> list:
        return Database.List(self, messages.List_Request()).guids

    def NewSpectrum(self, message: Spectrum.Content) -> Spectrum:
        k = self.Create(message)
        return Spectrum(db=self, key=k)

    def NewSpectrumBlackbody(self, temperature: float) -> Spectrum:
        mess = Spectrum.Content()
        mess.name = "toto"
        mess.description = "my spectrum"
        mess.blackbody.temperature = temperature
        return self.NewSpectrum(message=mess)
