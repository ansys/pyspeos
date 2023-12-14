"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from enum import Enum
from typing import List, Mapping, Optional

from ansys.api.speos.spectrum.v1 import spectrum_pb2 as messages
from ansys.api.speos.spectrum.v1 import spectrum_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

Spectrum = messages.Spectrum


class SpectrumLink(CrudItem):
    """
    Link object for spectrum in database.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.spectrum import SpectrumFactory
    >>> speos = Speos(host="localhost", port=50051)
    >>> spe_db = speos.client.spectrums()
    >>> spe_link = spe_db.create(message=SpectrumFactory.monochromatic(name="Monochromatic_600", wavelength=600))

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> Spectrum:
        """Get the datamodel from database."""
        return self._stub.read(self)

    def set(self, data: Spectrum) -> None:
        """Change datamodel in database."""
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class SpectrumStub(CrudStub):
    """
    Database interactions for spectrums.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> spe_db = speos.client.spectrums()

    """

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
    """Class to help creating Spectrum message."""

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

    def monochromatic(
        name: str, wavelength: Optional[float] = 555, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None
    ) -> Spectrum:
        """
        Create a Spectrum message, with monochromatic type.

        Parameters
        ----------
        name : str
            Name of the spectrum.
        wavelength : float, optional
            Wavelength of the monochromatic spectrum, in nm.
            By default, ``555``.
        description : str, optional
            Description of the spectrum.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the spectrum.
            By default, ``None``.

        Returns
        -------
        Spectrum
            Spectrum message created.
        """
        spec = Spectrum(name=name, description=description)
        if metadata is not None:
            spec.metadata.update(metadata)
        spec.monochromatic.wavelength = wavelength
        return spec

    def blackbody(
        name: str, temperature: Optional[float] = 2856, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None
    ) -> Spectrum:
        """
        Create a Spectrum message, with blackbody type.

        Parameters
        ----------
        name : str
            Name of the spectrum.
        temperature : float, optional
            Temperature of the blackbody, in K
            By default, ``2856``.
        description : str, optional
            Description of the spectrum.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the spectrum.
            By default, ``None``.

        Returns
        -------
        Spectrum
            Spectrum message created.
        """
        spec = Spectrum(name=name, description=description)
        if metadata is not None:
            spec.metadata.update(metadata)
        spec.blackbody.temperature = temperature
        return spec

    def sampled(
        name: str,
        wavelengths: List[float],
        values: List[float],
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Spectrum:
        """
        Create a Spectrum message, with sampled type.

        Parameters
        ----------
        name : str
            Name of the spectrum.
        wavelengths : List[float]
            List of wavelengths, in nm.
        values : List[float]
            List of values, expected from 0. to 100. in %.
        description : str, optional
            Description of the spectrum.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the spectrum.
            By default, ``None``.

        Returns
        -------
        Spectrum
            Spectrum message created.
        """
        spec = Spectrum(name=name, description=description)
        if metadata is not None:
            spec.metadata.update(metadata)
        spec.sampled.wavelengths.extend(wavelengths)
        spec.sampled.values.extend(values)
        return spec

    def library(name: str, file_uri: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None) -> Spectrum:
        """
        Create a Spectrum message, with library type.

        Parameters
        ----------
        name : str
            Name of the spectrum.
        file_uri : str
            Spectrum file, expressed in \*.spectrum.
        description : str, optional
            Description of the spectrum.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the spectrum.
            By default, ``None``.

        Returns
        -------
        Spectrum
            Spectrum message created.
        """
        spec = Spectrum(name=name, description=description)
        if metadata is not None:
            spec.metadata.update(metadata)
        spec.library.file_uri = file_uri
        return spec

    def predefined(
        name: str,
        type: Optional[PredefinedType] = PredefinedType.Incandescent,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Spectrum:
        """
        Create a Spectrum message, with predefined type.

        Parameters
        ----------
        name : str
            Name of the spectrum.
        type : SpectrumFactory.PredefinedType, optional
            Predefined type.
            By default, ``SpectrumFactory.PredefinedType.Incandescent``.
        description : str, optional
            Description of the spectrum.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the spectrum.
            By default, ``None``.

        Returns
        -------
        Spectrum
            Spectrum message created.
        """
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
