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

"""PySpeos is a Python library based on Speos solver remote API.

It gathers functionaties and tools of these APIs.
"""

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:  # pragma: no cover
    import importlib_metadata  # type: ignore[no-redef]

# Version
__version__ = importlib_metadata.version("ansys-speos-core")


import sys
import warnings

from ansys.speos.core.body import Body
import ansys.speos.core.bsdf as bsdf
from ansys.speos.core.face import Face
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.input_files import (
    CoatedSurfaceFile,
    CoatedSurfaceSample,
    FluorescentPigment,
    FluorescentPigmentFile,
    MaterialBirefringentCurve,
    MaterialBirefringentKettlerHelmholtz,
    MaterialBirefringentSellmeier,
    MaterialConstringence,
    MaterialDispersionCurve,
    MaterialFile,
    MaterialKettlerHelmholtz,
    MaterialMetallicCurve,
    MaterialOpticalClass,
    MaterialSellmeier,
    MaterialType,
    Ray,
    RayFile,
    ScatteringSurfaceFile,
    ScatteringSurfaceSample,
    SimpleScatteringMode,
    SimpleScatteringSurfaceFile,
    SpectrumFile,
    SpeosFileFormat,
    Texture3DMappingFile,
    TexturePattern,
    VolumeScatteringDoubleHenyeyGreenstein,
    VolumeScatteringGegenbauer,
    VolumeScatteringHenyeyGreenstein,
    VolumeScatteringUserDefined,
)
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

LATEST_EOL_PYTHON_VERSION = (3, 10)
_eol = ".".join(map(str, LATEST_EOL_PYTHON_VERSION))
PYTHON_EOL_WARNING = (
    f"Python {_eol} has reached its end of life. Support for Python {_eol} will be removed "
    "in an upcoming PySpeos release. Please upgrade to a supported Python version. For "
    "more information on Python versions, please refer to the official Python "
    "documentation (https://devguide.python.org/versions/#status-of-python-versions)."
)
"""Python end-of-life warning."""
LATEST_DEPRECATED_PYTHON_VERSION = (3, 11)
"""Latest deprecated python version."""
PYTHON_VERSION_WARNING = (
    "As part of our ongoing efforts to align with the Python Scientific Community's "
    "best practices, we are moving towards adopting SPEC 0000 "
    "(https://scientific-python.org/specs/spec-0000/). To ensure compatibility and "
    "take full advantage of the latest features and improvements, we strongly "
    "recommend updating the Python version being used."
)
"""Python version warning."""


def deprecation_warning() -> None:
    """Warning message informing users that some Python versions are deprecated in PySpeos."""
    # Store warnings showwarning
    existing_showwarning = warnings.showwarning

    # Define and use custom showwarning
    def custom_show_warning(message, category, filename, lineno, file=None, line=None) -> None:
        """Define and use custom warning to remove <stdin>:loc: pattern."""
        print(f"{category.__name__}: {message}")

    warnings.showwarning = custom_show_warning  # ty: ignore[invalid-assignment]

    current_python_version = sys.version_info[:2]
    if current_python_version <= LATEST_EOL_PYTHON_VERSION:
        warnings.warn(PYTHON_EOL_WARNING, FutureWarning)
    elif current_python_version <= LATEST_DEPRECATED_PYTHON_VERSION:
        warnings.warn(PYTHON_VERSION_WARNING, FutureWarning)

    # Restore warnings showwarning
    warnings.showwarning = existing_showwarning


deprecation_warning()
