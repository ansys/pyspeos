# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
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

from typing import List, Mapping, Optional
import warnings

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

        if key == "":
            # Create Spectrum
            self._spectrum = ProtoSpectrum(name=name, description=description, metadata=metadata)

            # Default value
            self.set_monochromatic()  # By default will be monochromatic
        else:
            # Retrieve Spectrum
            self.spectrum_link = speos_client[key]
            self._spectrum = self.spectrum_link.get()

    def set_monochromatic(self, wavelength: float = 555.0) -> Spectrum:
        """Set the spectrum as monochromatic.

        Parameters
        ----------
        wavelength : float
            Wavelength of the spectrum, in nm.
            By default, ``555.0``.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.monochromatic.wavelength = wavelength
        return self

    def set_blackbody(self, temperature: float = 2856) -> Spectrum:
        """Set the spectrum as blackbody.

        Parameters
        ----------
        temperature : float
            Temperature of the blackbody, in K.
            By default, ``2856``.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.blackbody.temperature = temperature
        return self

    def set_sampled(self, wavelengths: List[float], values: List[float]) -> Spectrum:
        """Set the spectrum as sampled.

        Parameters
        ----------
        wavelengths : List[float]
            List of wavelengths, in nm
        values : List[float]
            List of values, expected from 0. to 100. in %

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.sampled.wavelengths[:] = wavelengths
        self._spectrum.sampled.values[:] = values
        return self

    def set_library(self, file_uri: str) -> Spectrum:
        """Set the spectrum as library.

        Parameters
        ----------
        file_uri : str
            uri of the spectrum file.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum feature.
        """
        self._spectrum.library.file_uri = file_uri
        return self

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
