"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""

from ansys.api.speos.spectrum.v1 import spectrum_pb2, spectrum_pb2_grpc


class SpectrumDB:
    """
    Wraps a speos gRPC connection.
    """

    def __init__(self, channel: grpc.Channel):
        """Initialize the ``SpeosClient`` object."""
        self._stubManager = spectrum_pb2_grpc.SpectrumsManagerStub(channel)

    def __Create(self, message: spectrum_pb2.Spectrum) -> str:
        request = spectrum_pb2.Create_Request(spectrum=message)
        resp = self._stubManager.Create(request)
        return resp.guid

    def __Read(self, key: str) -> spectrum_pb2.Spectrum:
        request = spectrum_pb2.Read_Request(guid=key)
        resp = self._stubManager.Read(request)
        return resp.spectrum

    def __Update(self, key: str, message: spectrum_pb2.Spectrum):
        request = spectrum_pb2.Update_Request(guid=key, spectrum=message)
        self._stubManager.Update(request)

    def __Delete(self, key: str):
        request = spectrum_pb2.Delete_Request(guid=key)
        self._stubManager.Delete(request)

    def New(self, message: spectrum_pb2.Spectrum) -> Spectrum:
        return Spectrum(db=self, key=self.__Create(message))

    def NewBlackbody(self, temperature: float) -> Spectrum:
        mess = spectrum_pb2.Spectrum()
        mess.name = "toto"
        mess.description = "my spectrum"
        mess.blackbody.temperature = temperature
        return self.New(message=mess)


class Spectrum:
    def __init__(self, db: SpectrumDB, key: str):
        self._database = db
        self._key = key

    @property
    def database(self) -> SpectrumDB:
        """The database."""
        return self._database

    @property
    def key(self) -> str:
        """The guid in database."""
        return self._key

    def getContent(self) -> spectrum_pb2.Spectrum:
        return self._database.__Read(self._key)

    def setContent(self, data: spectrum_pb2.Spectrum):
        self._database.__Update(self._key, data)

    def delete(self):
        self._database.__Delete(self._key)
        self._key = ""
        self._database = None
