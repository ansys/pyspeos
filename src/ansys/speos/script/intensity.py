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
from ansys.speos.script.geo_ref import GeoRef


class Intensity:
    def __init__(
        self,
        speos_client: core.SpeosClient,
        name: str,
        description: str = "",
        metadata: Mapping[str, str] = {},
        intensity_props_to_complete: Optional[core.Scene.SourceInstance.IntensityProperties] = None,
    ) -> None:
        self._client = speos_client
        self.intensity_template_link = None

        # Create IntensityTemplate
        self._intensity_template = core.IntensityTemplate(name=name, description=description, metadata=metadata)

        # Create IntensityProperties
        self._intensity_properties = core.Scene.SourceInstance.IntensityProperties()
        if intensity_props_to_complete is not None:
            self._intensity_properties = intensity_props_to_complete
            self._light_print = True

        # Default values
        self.set_lambertian()  # By default will be lambertian

    def set_library(self, intensity_file_uri: str) -> Intensity:
        self._intensity_template.library.intensity_file_uri = intensity_file_uri
        return self

    def set_lambertian(self, total_angle: float = 180) -> Intensity:
        self._intensity_template.cos.N = 1
        self._intensity_template.cos.total_angle = total_angle
        self._intensity_properties.Clear()
        return self

    def set_cos(self, N: float = 3, total_angle: float = 180) -> Intensity:
        self._intensity_template.cos.N = N
        self._intensity_template.cos.total_angle = total_angle
        self._intensity_properties.Clear()
        return self

    def set_gaussian(self, FWHM_angle_x: float = 30, FWHM_angle_y: float = 30, total_angle: float = 180) -> Intensity:
        self._intensity_template.gaussian.FWHM_angle_x = FWHM_angle_x
        self._intensity_template.gaussian.FWHM_angle_y = FWHM_angle_y
        self._intensity_template.gaussian.total_angle = total_angle
        return self

    def set_library_properties_axis_system(
        self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1], exit_geometries: Optional[List[GeoRef]] = None
    ) -> Intensity:
        self._intensity_properties.Clear()
        self._intensity_properties.library_properties.axis_system.values[:] = axis_system
        if exit_geometries is not None:
            self._intensity_properties.library_properties.exit_geometries.geo_paths[:] = [gr.to_native_link() for gr in exit_geometries]
        return self

    def set_library_properties_normal_to_surface(self, exit_geometries: Optional[List[GeoRef]] = None) -> Intensity:
        self._intensity_properties.Clear()
        self._intensity_properties.library_properties.normal_to_surface.SetInParent()
        if exit_geometries is not None:
            self._intensity_properties.library_properties.exit_geometries.geo_paths[:] = [gr.to_native_link() for gr in exit_geometries]
        return self

    def set_library_properties_normal_to_uv_map(self, exit_geometries: Optional[List[GeoRef]] = None) -> Intensity:
        self._intensity_properties.Clear()
        self._intensity_properties.library_properties.normal_to_uv_map.SetInParent()
        if exit_geometries is not None:
            self._intensity_properties.library_properties.exit_geometries.geo_paths[:] = [gr.to_native_link() for gr in exit_geometries]
        return self

    def set_gaussian_properties(self, axis_system: List[float] = None) -> Intensity:
        self._intensity_properties.Clear()
        if axis_system is None:
            self._intensity_properties.gaussian_properties.SetInParent()
        else:
            self._intensity_properties.gaussian_properties.axis_system[:] = axis_system
        return self

    def __str__(self) -> str:
        out_str = ""
        if self.intensity_template_link is None:
            out_str += f"local: {self._intensity_template}"
        else:
            out_str += str(self.intensity_template_link)

        if self._light_print is None:
            out_str += f"\nlocal: " + core.protobuf_message_to_str(self._intensity_properties)
        return out_str

    def commit(self) -> Intensity:
        """Save feature"""
        if self.intensity_template_link is None:
            self.intensity_template_link = self._client.intensity_templates().create(message=self._intensity_template)
        else:
            self.intensity_template_link.set(data=self._intensity_template)

        return self

    def delete(self) -> Intensity:
        if self.intensity_template_link is not None:
            self.intensity_template_link.delete()
            self.intensity_template_link = None
        return self
