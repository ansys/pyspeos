# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Provides a way to interact with Speos feature: Spectrum."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Mapping, Optional, Union
import warnings

from ansys.api.speos.spectrum.v1 import spectrum_pb2

from ansys.speos.core.generic.file_format import (
    LineReader,
    SpeosTextFileFormat,
    check_percentage,
    format_number,
)
from ansys.speos.core.generic.parameters import (
    SpectrumBlackBodyParameters,
    SpectrumLibraryParameters,
    SpectrumMonochromaticParameters,
    SpectrumSampledParameters,
)
from ansys.speos.core.kernel.client import SpeosClient
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_dict
from ansys.speos.core.kernel.spectrum import ProtoSpectrum
from ansys.speos.core.proto_message_utils import dict_to_str


class Spectrum:
    """Speos feature : Spectrum.

    By default, a monochromatic spectrum is created.

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        The Speos instance client.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    key : str
        Creation from an SpectrumLink key

    Attributes
    ----------
    spectrum_link : ansys.speos.core.kernel.spectrum.SpectrumLink
        Link object for the spectrum in database.
    """

    class Monochromatic:
        """Monochromatic type of spectrum.

        By default, monochromatic spectrum wavelength is set to be 550.

        Parameters
        ----------
        monochromatic : ansys.api.speos.spectrum.v1.spectrum_pb2.Monochromatic
            Monochromatic protobuf object to modify.
        default_parameters : Optional[\
        ansys.speos.core.generic.parameters.SpectrumMonochromaticParameters] = None
            If defined the values in the Monochromatic instance will be
            overwritten by the values of the data class
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_monochromatic method available in
        Spectrum classes.
        """

        def __init__(
            self,
            monochromatic: spectrum_pb2.Spectrum.Monochromatic,
            default_parameters: Optional[SpectrumMonochromaticParameters] = None,
            stable_ctr: bool = False,
        ):
            if not stable_ctr:
                msg = "Monochromatic class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._monochromatic = monochromatic

            if default_parameters is not None:
                self.wavelength = default_parameters.wavelength

        @property
        def wavelength(self) -> float:
            """Property the wavelength of the spectrum.

            Parameters
            ----------
            value : float
                Wavelength of the spectrum.

            Returns
            -------
            float
                Wavelength of the spectrum.
            """
            return self._monochromatic.wavelength

        @wavelength.setter
        def wavelength(self, value: float) -> None:
            self._monochromatic.wavelength = value

    class Blackbody:
        """Blackbody type of spectrum.

        By default, Blackbody temperature is set to be 2856.

        Parameters
        ----------
        blackbody : ansys.api.speos.spectrum.v1.spectrum_pb2.Blackbody
            Blackbody protobuf object to modify.
        default_parameters : Optional[\
        ansys.speos.core.generic.parameters.SpectrumBlackBodyParameters] = None
            If defined the values in the Blackbody instance will be
            overwritten by the values of the data class
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_blackbody method available in
        Spectrum classes.
        """

        def __init__(
            self,
            blackbody: spectrum_pb2.Spectrum.BlackBody,
            default_parameters: Optional[SpectrumBlackBodyParameters] = None,
            stable_ctr: bool = False,
        ):
            if not stable_ctr:
                msg = "Blackbody class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._blackbody = blackbody

            if default_parameters is not None:
                self.temperature = default_parameters.temperature

        @property
        def temperature(self) -> float:
            """Property the temperature of the spectrum.

            Parameters
            ----------
            value : float
                Temperature of the spectrum.

            Returns
            -------
            float
                Temperature of the spectrum.

            """
            return self._blackbody.temperature

        @temperature.setter
        def temperature(self, value: float) -> None:
            self._blackbody.temperature = value

    class Sampled:
        """Sampled type of spectrum.

        By default, Sampled temperature is set to be 2856.

        Parameters
        ----------
        sampled : ansys.api.speos.spectrum.v1.spectrum_pb2.Sampled
            Sampled protobuf object to modify.
        default_parameters : Optional[\
        ansys.speos.core.generic.parameters.SpectrumSampledParameters] = None
            If defined the values in the Sampled instance will be
            overwritten by the values of the data class
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_sampled method available in
        Spectrum classes.
        """

        def __init__(
            self,
            sampled: spectrum_pb2.Spectrum.Sampled,
            default_parameters: Optional[SpectrumSampledParameters] = None,
            stable_ctr: bool = False,
        ):
            if not stable_ctr:
                msg = "Sampled class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._sampled = sampled

            if default_parameters is not None:
                self.wavelength = default_parameters.wavelengths
                self.values = default_parameters.values

        @property
        def wavelengths(self) -> List[float]:
            """Wavelength property values of the spectrum.

            Parameters
            ----------
            wavelengths : List[float]
                Wavelength values of the spectrum.

            Returns
            -------
            List[float]
                Wavelength values of the spectrum.

            """
            return self._sampled.wavelengths[:]

        @wavelengths.setter
        def wavelengths(self, wavelengths: List[float]) -> None:
            self._sampled.wavelengths[:] = wavelengths

        @property
        def values(self) -> List[float]:
            """Property values of the spectrum sampled wavelengths.

            Parameters
            ----------
            values : List[float]
                List of values, expected from 0. to 100. in %.

            Returns
            -------
            List[float]
                List of values, expected from 0. to 100. in %.
            """
            return self._sampled.values

        @values.setter
        def values(self, values: List[float]) -> None:
            self._sampled.values[:] = values

    class Library:
        """Library type of spectrum.

        By default, file uri is empty.

        Parameters
        ----------
        library : ansys.api.speos.spectrum.v1.spectrum_pb2.Spectrum.Library
            Library protobuf object to modify.
        default_parameters : Optional[\
        ansys.speos.core.generic.parameters.SpectrumLibraryParameters] = None
            If defined the values in the Library instance will be
            overwritten by the values of the data class
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_blackbody method available in
        Spectrum classes.
        """

        def __init__(
            self,
            library: spectrum_pb2.Spectrum.Library,
            default_parameters: Optional[SpectrumLibraryParameters] = None,
            stable_ctr: bool = False,
        ):
            if not stable_ctr:
                msg = "Blackbody class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._library = library

            if default_parameters is not None:
                self.file_uri = default_parameters.file_uri

        @property
        def file_uri(self) -> str:
            """Property the file uri of the library type spectrum.

            Parameters
            ----------
            file_uri : Union[str, pathlib.Path]
                File uri of the library type spectrum.

            Returns
            -------
            str
                File uri of the library type spectrum.

            """
            return self._library.file_uri

        @file_uri.setter
        def file_uri(self, file_uri: Union[str, Path]) -> None:
            self._library.file_uri = str(file_uri)

    def __init__(
        self,
        speos_client: SpeosClient,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        key: str = "",
    ) -> None:
        self._client = speos_client
        self.spectrum_link = None
        """Link object for the spectrum in database."""

        if metadata is None:
            metadata = {}

        # Attribute gathering more complex spectrun type
        self._type = None

        if key == "":
            # Create Spectrum
            self._spectrum = ProtoSpectrum(name=name, description=description, metadata=metadata)

            # Default value
            self.set_monochromatic()  # By default will be monochromatic
        else:
            # Retrieve Spectrum
            self.spectrum_link = speos_client[key]
            self._spectrum = self.spectrum_link.get()

    def set_monochromatic(self) -> Spectrum.Monochromatic:
        """Set the spectrum as monochromatic.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum.Monochromatic
            Spectrum Monochromatic feature.
        """
        if self._type is None and self._spectrum.HasField("monochromatic"):
            self._type = Spectrum.Monochromatic(
                monochromatic=self._spectrum.monochromatic,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, Spectrum.Monochromatic):
            self._type = Spectrum.Monochromatic(
                monochromatic=self._spectrum.monochromatic,
                default_parameters=SpectrumMonochromaticParameters(),
                stable_ctr=True,
            )
        elif self._type._monochromatic is not self._spectrum.monochromatic:
            self._type._monochromatic = self._spectrum.monochromatic
        return self._type

    def set_blackbody(self) -> Spectrum.Blackbody:
        """Set the spectrum as blackbody.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum.Blackbody
            Spectrum Blackbody feature to complete.
        """
        if self._type is None and self._spectrum.HasField("blackbody"):
            self._type = Spectrum.Blackbody(
                blackbody=self._spectrum.blackbody,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, Spectrum.Blackbody):
            self._type = Spectrum.Blackbody(
                blackbody=self._spectrum.blackbody,
                default_parameters=SpectrumBlackBodyParameters(),
                stable_ctr=True,
            )
        elif self._type._blackbody is not self._spectrum.blackbody:
            self._type._blackbody = self._spectrum.blackbody
        return self._type
        # self._spectrum.blackbody.temperature = temperature
        # return self

    def set_sampled(self) -> Spectrum.Sampled:
        """Set the spectrum as sampled.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum.Sampled
            Spectrum Sampled feature to complete.
        """
        if self._type is None and self._spectrum.HasField("sampled"):
            self._type = Spectrum.Sampled(
                sampled=self._spectrum.sampled,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, Spectrum.Sampled):
            self._type = Spectrum.Sampled(
                sampled=self._spectrum.sampled,
                default_parameters=SpectrumSampledParameters(),
                stable_ctr=True,
            )
        elif self._type._sampled is not self._spectrum.sampled:
            self._type._sampled = self._spectrum.sampled
        return self._type

    def set_library(self) -> Spectrum.Library:
        """Set the spectrum as library.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum.Library
            Spectrum Library feature to complete.
        """
        if self._type is None and self._spectrum.HasField("library"):
            self._type = Spectrum.Library(
                library=self._spectrum.library,
                default_parameters=None,
                stable_ctr=True,
            )
        elif not isinstance(self._type, Spectrum.Library):
            self._type = Spectrum.Library(
                library=self._spectrum.library,
                default_parameters=SpectrumLibraryParameters(),
                stable_ctr=True,
            )
        elif self._type._library is not self._spectrum.library:
            self._type._library = self._spectrum.library
        return self._type

    def set_incandescent(self) -> Spectrum:
        """Set the spectrum as incandescent (predefined spectrum).

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.predefined.incandescent.SetInParent()
        return self

    def set_warmwhitefluorescent(self) -> Spectrum:
        """Set the spectrum as warmwhitefluorescent (predefined spectrum).

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.predefined.warmwhitefluorescent.SetInParent()
        return self

    def set_daylightfluorescent(self) -> Spectrum:
        """Set the spectrum as daylightfluorescent (predefined spectrum).

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.predefined.daylightfluorescent.SetInParent()
        return self

    def set_whiteLED(self) -> Spectrum:
        """Set the spectrum as white led (predefined spectrum).

        .. deprecated:: 0.2.2
            `set_whiteLed` will be removed with 0.3.0
            `set_white_led` shall be used to comply with PEP8 naming convention

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        warnings.warn(
            "`set_whiteLED` is deprecated. Use `set_white_led` method instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.set_white_led()

    def set_white_led(self) -> Spectrum:
        """Set the spectrum as white led (predefined spectrum).

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.predefined.whiteLED.SetInParent()
        return self

    def set_halogen(self) -> Spectrum:
        """Set the spectrum as halogen (predefined spectrum).

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.predefined.halogen.SetInParent()
        return self

    def set_metalhalide(self) -> Spectrum:
        """Set the spectrum as metalhalide (predefined spectrum).

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.predefined.metalhalide.SetInParent()
        return self

    def set_highpressuresodium(self) -> Spectrum:
        """Set the spectrum as highpressuresodium (predefined spectrum).

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.predefined.highpressuresodium.SetInParent()
        return self

    def _to_dict(self) -> dict:
        if self.spectrum_link is None:
            return protobuf_message_to_dict(self._spectrum)
        else:
            return protobuf_message_to_dict(message=self.spectrum_link.get())

    def __str__(self) -> str:
        """Return the string representation of the spectrum."""
        out_str = ""
        if self.spectrum_link is None:
            out_str += "local: "
        out_str += dict_to_str(self._to_dict())
        return out_str

    def commit(self) -> Spectrum:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        if self.spectrum_link is None:
            self.spectrum_link = self._client.spectrums().create(message=self._spectrum)
        elif self.spectrum_link.get() != self._spectrum:
            self.spectrum_link.set(data=self._spectrum)  # Only update if data has changed

        return self

    def reset(self) -> Spectrum:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        if self.spectrum_link is not None:
            self._spectrum = self.spectrum_link.get()
        return self

    def delete(self) -> Spectrum:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        if self.spectrum_link is not None:
            self.spectrum_link.delete()
            self.spectrum_link = None

        return self


MAX_SPECTRUM_SAMPLES = 32767
"""Maximum number of wavelength samples accepted by Speos in a ``*.spectrum`` file."""


@dataclass
class SpectrumFile(SpeosTextFileFormat):
    """Speos ``*.spectrum`` file, holding a sampled spectral distribution.

    The file is the text (``v1``) flavor of the format: a header line, a description, the
    number of samples, then one ``wavelength<TAB>value`` line per sample. Files are read
    and written locally, no Speos server is needed.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths of the samples, in nm. By default, ``[]``.
    values : List[float], optional
        Relative spectral values of the samples, in percent (0 to 100). By default, ``[]``.
    description : str, optional
        Free text written on the second line of the file. By default, ``""``.

    Examples
    --------
    >>> from ansys.speos.core import SpectrumFile
    >>> SpectrumFile(wavelengths=[400.0, 700.0], values=[100.0, 50.0]).save("led.spectrum")
    """

    wavelengths: List[float] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    description: str = ""

    EXTENSION = ".spectrum"
    HEADER = "OPTIS - Spectrum file v1"
    # Kept loose on purpose: some files shipped by Ansys misspell the header as
    # "OPTIS - Spectrum fie v1.0", and Speos reads them.
    HEADER_PREFIX = "OPTIS - Spectrum"

    def validate(self) -> None:
        """Check the spectrum against the constraints of the ``*.spectrum`` format.

        Raises
        ------
        ValueError
            If the sample lists are empty, do not have the same length, hold more than
            32767 samples, or if a value is outside the 0 to 100 percent range.
        """
        if len(self.wavelengths) != len(self.values):
            raise ValueError(
                f"wavelengths and values must have the same length, got "
                f"{len(self.wavelengths)} and {len(self.values)}."
            )
        if not self.wavelengths:
            raise ValueError("A spectrum must hold at least one sample.")
        if len(self.wavelengths) > MAX_SPECTRUM_SAMPLES:
            raise ValueError(
                f"A spectrum cannot hold more than {MAX_SPECTRUM_SAMPLES} samples, "
                f"got {len(self.wavelengths)}."
            )
        for wavelength, value in zip(self.wavelengths, self.values):
            check_percentage(f"The value at {wavelength} nm", value)

    def _to_lines(self) -> List[str]:
        lines = [self.description, str(len(self.wavelengths))]
        lines.extend(
            f"{format_number(wavelength)}\t{format_number(value)}"
            for wavelength, value in zip(self.wavelengths, self.values)
        )
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> SpectrumFile:
        description = reader.next_line()
        sample_count = reader.next_int()
        wavelengths, values = [], []
        for _ in range(sample_count):
            wavelength, value = reader.next_floats(count=2)
            wavelengths.append(wavelength)
            values.append(value)
        return cls(wavelengths=wavelengths, values=values, description=description)

    @classmethod
    def from_sampled(cls, spectrum: Spectrum, description: str = "") -> SpectrumFile:
        """Build a spectrum file from a sampled :class:`Spectrum` feature.

        Parameters
        ----------
        spectrum : ansys.speos.core.spectrum.Spectrum
            Spectrum feature configured with :meth:`Spectrum.set_sampled`.
        description : str, optional
            Free text written on the second line of the file. By default, ``""``, which
            uses the name of the spectrum feature.

        Returns
        -------
        ansys.speos.core.spectrum.SpectrumFile
            Spectrum file model.

        Raises
        ------
        ValueError
            If ``spectrum`` is not of sampled type.
        """
        sampled = spectrum._type
        if not isinstance(sampled, Spectrum.Sampled):
            raise ValueError("from_sampled expects a spectrum set with set_sampled().")
        return cls(
            wavelengths=list(sampled.wavelengths),
            values=list(sampled.values),
            description=description or spectrum._spectrum.name,
        )
