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

from typing import List, Mapping, Optional

import ansys.speos.core as core


class Intensity:
    def __init__(self, speos: core.Speos, name: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None) -> None:
        self._client = speos.client
        self._intensity_template_link = None

        # Create IntensityTemplate
        self._intensity_template = core.IntensityTemplate(
            name=name, description=description if description else "", metadata=metadata if metadata else {}
        )
        # Create IntensityProperties
        self._intensity_properties = core.Scene.SourceInstance.IntensityProperties()

    def set_library(self, intensity_file_uri: str) -> Intensity:
        self._intensity_template.library.intensity_file_uri = intensity_file_uri
        return self

    def set_cos(self, N: float, total_angle: float) -> Intensity:
        self._intensity_template.cos.N = N
        self._intensity_template.cos.total_angle = total_angle
        self._intensity_properties = core.Scene.SourceInstance.IntensityProperties()
        return self

    def set_gaussian(self, FWHM_angle_x: float, FWHM_angle_y: float, total_angle: float) -> Intensity:
        self._intensity_template.gaussian.FWHM_angle_x = FWHM_angle_x
        self._intensity_template.gaussian.FWHM_angle_y = FWHM_angle_y
        self._intensity_template.gaussian.total_angle = total_angle
        return self

    def set_library_properties_axis_system(self, axis_system: List[float]) -> Intensity:
        self._intensity_properties.library_properties.axis_system.ClearField("values")
        self._intensity_properties.library_properties.axis_system.values.extend(axis_system)
        return self

    def set_library_properties_normal_to_surface(self) -> Intensity:
        self._intensity_properties.library_properties.normal_to_surface.SetInParent()
        return self

    def set_library_properties_normal_to_uv_map(self) -> Intensity:
        self._intensity_properties.library_properties.normal_to_uv_map.SetInParent()
        return self

    def set_gaussian_properties(self, axis_system: List[float] = None) -> Intensity:
        if axis_system is None:
            self._intensity_properties.gaussian_properties.SetInParent()
        else:
            self._intensity_properties.gaussian_properties.ClearField("axis_system")
            self._intensity_properties.gaussian_properties.axis_system.extend(axis_system)
        return self

    def __str__(self) -> str:
        template = ""
        if self._intensity_template_link is None:
            template = f"local: {self._intensity_template}"
        else:
            template = str(self._intensity_template_link)
        if self._intensity_properties is not None:
            template += f"\n{self._intensity_properties}"
        return template

    def commit(self) -> Intensity:
        """Save feature"""
        if self._intensity_template_link is None:
            self._intensity_template_link = self._client.intensity_templates().create(message=self._intensity_template)
        else:
            self._intensity_template_link.set(data=self._intensity_template)

        return self

    def delete(self) -> Intensity:
        self._intensity_template_link.delete()
        self._intensity_template_link = None
        return self
