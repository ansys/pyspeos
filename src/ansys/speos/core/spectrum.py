"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from ansys.api.speos.spectrum.v1 import spectrum_pb2, spectrum_pb2_grpc
import grpc


class Spectrum:
    def __init__(self, db, key: str):
        self._database = db
        self._key = key

    Content = spectrum_pb2.Spectrum

    def database(self):
        """The database."""
        return self._database

    def key(self) -> str:
        """The guid in database."""
        return self._key

    def read_content(self) -> spectrum_pb2.Spectrum:
        return self._database.Read(self._key)

    def update_content(self, data: spectrum_pb2.Spectrum):
        self._database.Update(self._key, data)

    def delete(self):
        self._database.Delete(self._key)
        self._key = ""
        self._database = None


class SpectrumDB:
    """
    Wraps a speos gRPC connection.
    """

    Content = spectrum_pb2.Spectrum

    def __init__(self, channel: grpc.Channel):
        """Initialize the service stub."""
        self._stubManager = spectrum_pb2_grpc.SpectrumsManagerStub(channel)

    """Create a new entry."""

    def Create(self, message: spectrum_pb2.Spectrum) -> str:
        request = spectrum_pb2.Create_Request(spectrum=message)
        resp = self._stubManager.Create(request)
        return resp.guid

    """Get an existing entry."""

    def Read(self, key: str) -> spectrum_pb2.Spectrum:
        request = spectrum_pb2.Read_Request(guid=key)
        resp = self._stubManager.Read(request)
        return resp.spectrum

    """Change an existing entry."""

    def Update(self, key: str, message: spectrum_pb2.Spectrum):
        request = spectrum_pb2.Update_Request(guid=key, spectrum=message)
        self._stubManager.Update(request)

    """Remove an existing entry."""

    def Delete(self, key: str):
        request = spectrum_pb2.Delete_Request(guid=key)
        self._stubManager.Delete(request)

    """List existing entries."""

    def List(self):
        resp = self._stubManager.List(spectrum_pb2.List_Request())
        return resp.guids

    """ Factories"""

    def New(self, message: spectrum_pb2.Spectrum) -> Spectrum:
        k = self.Create(message)
        return Spectrum(db=self, key=k)

    def NewBlackbody(self, temperature: float) -> Spectrum:
        mess = spectrum_pb2.Spectrum()
        mess.name = "toto"
        mess.description = "my spectrum"
        mess.blackbody.temperature = temperature
        return self.New(message=mess)
