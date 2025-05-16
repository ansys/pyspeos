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

"""PySpeos is a Python library based on Speos solver remote API.

It gathers functionaties and tools of these APIs.
"""

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:  # pragma: no cover
    import importlib_metadata  # type: ignore[no-redef]

# Version
__version__ = importlib_metadata.version("ansys-speos-core")


from ansys.speos.core.body import Body
import ansys.speos.core.bsdf as bsdf
from ansys.speos.core.face import Face
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.intensity import Intensity
from ansys.speos.core.logger import LOG, Logger
from ansys.speos.core.lxp import LightPathFinder, RayPath
from ansys.speos.core.opt_prop import OptProp
from ansys.speos.core.part import Part
from ansys.speos.core.project import Project
import ansys.speos.core.sensor as sensor
import ansys.speos.core.simulation as simulation
import ansys.speos.core.source as source
from ansys.speos.core.spectrum import Spectrum
from ansys.speos.core.speos import Speos
