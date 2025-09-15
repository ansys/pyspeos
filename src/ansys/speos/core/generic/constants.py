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

"""Collection of all constants used in pySpeos."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Union

DEFAULT_HOST: str = "localhost"
"""Default host used by Speos RPC server and client """
DEFAULT_PORT: str = "50098"
"""Default port used by Speos RPC server and client """
DEFAULT_VERSION: str = "252"
"""Latest supported Speos version of the current PySpeos Package"""
MAX_SERVER_MESSAGE_LENGTH: int = int(os.environ.get("SPEOS_MAX_MESSAGE_LENGTH", 256 * 1024**2))
"""Maximum message length value accepted by the Speos RPC server,
By default, value stored in environment variable SPEOS_MAX_MESSAGE_LENGTH or 268 435 456.
"""
MAX_CLIENT_MESSAGE_SIZE: int = int(4194304)
"""Maximum message Size accepted by grpc channel,
By default, 4194304.
"""
ORIGIN = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
"""Global Origin"""


class SPECTRUM:
    """Constant class for Spectrum."""

    class MONOCHROMATIC:
        """Constant class for Monochromatic."""

        WAVELENGTH = 555

    class BLACKBODY:
        """Constant class for BlackBody."""

        TEMPERATURE = 2856


class SOURCE:
    """Constant class for Sources."""

    class LUMINOUS:
        """Constant class for Luminous."""

        VALUE = 683

    class RADIANT:
        """Constant class for Radiant."""

        VALUE = 1

    class INTENSITY:
        """Constant class for Intensity."""

        VALUE = 5


@dataclass
class FluxLuminous:
    """Constant class for Luminous type Flux."""

    value: float = 683
    flux_from_ray_file: bool = True


@dataclass
class FluxRadiant:
    """Constant class for Radiant type Flux."""

    value: float = 1
    flux_from_ray_file: bool = True


@dataclass
class SourceRayfileParamters:
    """Constant class for SourceRayfileParamters."""

    ray_file_uri: Union[str, Path] = Path()
    flux_type: Union[FluxLuminous, FluxRadiant] = FluxLuminous()
    axis_system: list[float] = field(default_factory=lambda: [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1])


class SENSOR:
    """Constant class for Sensors."""

    class WAVELENGTHSRANGE:
        """Wavelength constants."""

        START = 400
        """Wavelength start value."""
        END = 700
        """Wavelength end value."""
        SAMPLING = 13
        """Wavelength sampling."""

    class DIMENSIONS:
        """Dimension Constants."""

        X_START = -50
        """Lower bound x axis."""
        X_END = 50
        """Upper bound x axis."""
        X_SAMPLING = 100
        """Sampling x axis."""
        Y_START = -50
        """Lower bound y axis."""
        Y_END = 50
        """Upper bound y axis."""
        Y_SAMPLING = 100
        """Sampling y axis."""

    class LAYERTYPES:
        """Layer Separation constants."""

        MAXIMUM_NB_OF_SEQUENCE = 10
        """Number of sequences stored in sensor."""
        INCIDENCE_SAMPLING = 9
        """Number of incidence sampling stored in sensor"""
