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

from typing import Mapping

import ansys.speos.core as core
import ansys.speos.script.project as project
from ansys.speos.script.spectrum import Spectrum


class Source:
    class Luminaire:
        def __init__(self, project: project.Project, source_template: core.SourceTemplate, name: str) -> None:
            self._project = project
            self._source_template = source_template
            self._spectrum = Spectrum(speos_client=self._project.client, name=name + ".Spectrum", source_template=self._source_template)

            # Default values
            self.set_flux_from_intensity_file().set_spectrum().set_incandescent()

        def set_flux_from_intensity_file(self) -> Source.Luminaire:
            self._source_template.luminaire.flux_from_intensity_file.SetInParent()
            return self

        def set_flux_luminous(self, value: float = 683) -> Source.Luminaire:
            self._source_template.luminaire.luminous_flux.luminous_value = value
            return self

        def set_flux_radiant(self, value: float = 1) -> Source.Luminaire:
            self._source_template.luminaire.radiant_flux.radiant_value = value
            return self

        def set_intensity_file_uri(self, uri: str) -> Source.Luminaire:
            self._source_template.luminaire.intensity_file_uri = uri
            return self

        def set_spectrum(self) -> Spectrum:
            return self._spectrum

        def __str__(self) -> str:
            return str(self._spectrum)

        def _commit(self) -> Source.Luminaire:
            self._spectrum.commit()
            return self

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._source_template_link = None

        self._luminaire = None

        # Create SourceTemplate
        self._source_template = core.SourceTemplate(name=name, description=description, metadata=metadata)

        # Create SourceProperties
        self._source_properties = None

    def set_luminaire(self) -> Luminaire:
        if self._luminaire is None:
            self._luminaire = Source.Luminaire(
                project=self._project, source_template=self._source_template, name=self._source_template.name
            )
        return self._luminaire

    def __str__(self) -> str:
        out_str = ""
        if self._source_template_link is None:
            out_str += f"local: {self._source_template}"
        else:
            out_str += str(self._source_template_link)

        if self._luminaire is not None:
            out_str += "\n"
            out_str += str(self._luminaire)

        return out_str

    def commit(self) -> Source:
        if self._luminaire is not None:
            self._luminaire._commit()

        """Save feature"""
        if self._source_template_link is None:
            self._source_template_link = self._project.client.source_templates().create(message=self._source_template)
        else:
            self._source_template_link.set(data=self._source_template)

        return self

    def delete(self) -> Source:
        if self._source_template_link is not None:
            self._source_template_link.delete()
            self._source_template_link = None

        if self._luminaire is not None:
            self._luminaire._spectrum.delete()
        return self
