"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from ansys.api.speos.spectrum.v1 import spectrum_pb2, spectrum_pb2_grpc
import grpc


class Spectrum:
    def __init__(self, db, key: str):
        self._database = db
        self._key = key

    Content = spectrum_pb2.Spectrum

    def get_database(self):
        """The database."""
        return self._database

    def get_key(self) -> str:
        """The guid in database."""
        return self._key

    def get_content(self) -> spectrum_pb2.Spectrum:
        return self._database.Read(self._key)

    def set_content(self, data: spectrum_pb2.Spectrum):
        self._database.Update(self._key, data)

    def delete(self):
        self._database.Delete(self._key)
        self._key = ""
        self._database = None


class SpectrumDB:
    """
    Wraps a speos gRPC connection.
    """

    def __init__(self, channel: grpc.Channel):
        """Initialize the ``SpeosClient`` object."""
        self._stubManager = spectrum_pb2_grpc.SpectrumsManagerStub(channel)

    def Create(self, message: spectrum_pb2.Spectrum) -> str:
        request = spectrum_pb2.Create_Request(spectrum=message)
        print(request)
        resp = self._stubManager.Create(request)
        print(resp)
        return resp.guid

    def Read(self, key: str) -> spectrum_pb2.Spectrum:
        request = spectrum_pb2.Read_Request(guid=key)
        resp = self._stubManager.Read(request)
        return resp.spectrum

    def Update(self, key: str, message: spectrum_pb2.Spectrum):
        request = spectrum_pb2.Update_Request(guid=key, spectrum=message)
        self._stubManager.Update(request)

    def Delete(self, key: str):
        request = spectrum_pb2.Delete_Request(guid=key)
        self._stubManager.Delete(request)

    def New(self, message: spectrum_pb2.Spectrum) -> Spectrum:
        k = self.Create(message)
        return Spectrum(db=self, key=k)

    def NewBlackbody(self, temperature: float) -> Spectrum:
        mess = spectrum_pb2.Spectrum()
        mess.name = "toto"
        mess.description = "my spectrum"
        mess.blackbody.temperature = temperature
        return self.New(message=mess)
