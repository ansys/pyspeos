# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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
from __future__ import annotations

from typing import List, Mapping

import ansys.speos.core as core


class Spectrum:
    def __init__(
        self,
        speos_client: core.SpeosClient,
        name: str,
        description: str = "",
        metadata: Mapping[str, str] = {},
    ) -> None:
        self._client = speos_client
        self.spectrum_link = None

        # Create Spectrum
        self._spectrum = core.Spectrum(name=name, description=description, metadata=metadata)
        self.set_monochromatic()  # By default will be monochromatic

    def set_monochromatic(self, wavelength: float = 555.0) -> Spectrum:
        self._spectrum.monochromatic.wavelength = wavelength
        return self

    def set_blackbody(self, temperature: float = 2856) -> Spectrum:
        self._spectrum.blackbody.temperature = temperature
        return self

    def set_sampled(self, wavelengths: List[float], values: List[float]) -> Spectrum:
        self._spectrum.sampled.wavelengths[:] = wavelengths
        self._spectrum.sampled.values[:] = values
        return self

    def set_library(self, file_uri: str) -> Spectrum:
        self._spectrum.library.file_uri = file_uri
        return self

    def set_incandescent(self) -> Spectrum:
        self._spectrum.predefined.incandescent.SetInParent()
        return self

    def set_warmwhitefluorescent(self) -> Spectrum:
        self._spectrum.predefined.warmwhitefluorescent.SetInParent()
        return self

    def set_daylightfluorescent(self) -> Spectrum:
        self._spectrum.predefined.daylightfluorescent.SetInParent()
        return self

    def set_whiteLED(self) -> Spectrum:
        self._spectrum.predefined.whiteLED.SetInParent()
        return self

    def set_halogen(self) -> Spectrum:
        self._spectrum.predefined.halogen.SetInParent()
        return self

    def set_metalhalide(self) -> Spectrum:
        self._spectrum.predefined.metalhalide.SetInParent()
        return self

    def set_highpressuresodium(self) -> Spectrum:
        self._spectrum.predefined.highpressuresodium.SetInParent()
        return self

    def __str__(self) -> str:
        if self.spectrum_link is None:
            return f"local: {self._spectrum}"
        else:
            return str(self.spectrum_link)

    def commit(self) -> Spectrum:
        """Save feature"""
        if self.spectrum_link is None:
            self.spectrum_link = self._client.spectrums().create(message=self._spectrum)
        else:
            self.spectrum_link.set(data=self._spectrum)

        return self

    def delete(self) -> Spectrum:
        if self.spectrum_link is not None:
            self.spectrum_link.delete()
            self.spectrum_link = None

        return self
