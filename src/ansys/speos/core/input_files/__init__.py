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

"""Speos input file formats: local, server-free read/write of Speos file formats.

Every class in this package describes a file that Speos reads as an input, so they are
parsed and written locally and never require a connection to a Speos gRPC server. Each
module covers a single file extension.
"""

from ansys.speos.core.input_files._base import SpeosFileFormat, SpeosTextFileFormat
from ansys.speos.core.input_files.coated_surface import CoatedSurfaceFile, CoatedSurfaceSample
from ansys.speos.core.input_files.material import (
    MaterialConstringence,
    MaterialDispersionCurve,
    MaterialFile,
    MaterialKettlerHelmholtz,
    MaterialSellmeier,
    VolumeScatteringDoubleHenyeyGreenstein,
    VolumeScatteringGegenbauer,
    VolumeScatteringHenyeyGreenstein,
    VolumeScatteringUserDefined,
)
from ansys.speos.core.input_files.ray_file import Ray, RayFile
from ansys.speos.core.input_files.scattering_surface import (
    ScatteringSurfaceFile,
    ScatteringSurfaceSample,
)
from ansys.speos.core.input_files.simple_scattering_surface import SimpleScatteringSurfaceFile
from ansys.speos.core.input_files.spectrum_file import SpectrumFile
from ansys.speos.core.input_files.texture_3d import Texture3DMappingFile, TexturePattern

__all__ = [
    "CoatedSurfaceFile",
    "CoatedSurfaceSample",
    "MaterialConstringence",
    "MaterialDispersionCurve",
    "MaterialFile",
    "MaterialKettlerHelmholtz",
    "MaterialSellmeier",
    "Ray",
    "RayFile",
    "ScatteringSurfaceFile",
    "ScatteringSurfaceSample",
    "SimpleScatteringSurfaceFile",
    "SpectrumFile",
    "SpeosFileFormat",
    "SpeosTextFileFormat",
    "Texture3DMappingFile",
    "TexturePattern",
    "VolumeScatteringDoubleHenyeyGreenstein",
    "VolumeScatteringGegenbauer",
    "VolumeScatteringHenyeyGreenstein",
    "VolumeScatteringUserDefined",
]
