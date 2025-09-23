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
from enum import Enum
import os
from pathlib import Path
from typing import Optional, Union

from ansys.speos.core.geo_ref import GeoRef

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


class FluxType(Enum):
    """Enum representing the type of flux."""

    LUMINOUS = "luminous"
    RADIANT = "radiant"
    FROM_FILE = "from_file"
    INTENSITY = "intensity"


@dataclass
class SourceRayfileParameters:
    """Constant class for SourceRayfileParameters."""

    ray_file_uri: Union[str, Path] = ""
    flux_type: FluxType = FluxType.FROM_FILE
    flux_value: Optional[float] = None
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    exit_geometry: Optional[GeoRef] = None

    def __post_init__(self):
        """Verify the dataclass initiation."""
        # Validation: restrict flux_type
        if self.flux_type not in {FluxType.FROM_FILE, FluxType.LUMINOUS, FluxType.RADIANT}:
            raise ValueError(
                f"Invalid flux_type '{self.flux_type}'. Must be FROM_FILE, LUMINOUS, or RADIANT."
            )

        # Set default flux_value based on flux_type (only if not manually provided)
        if self.flux_value is None:
            match self.flux_type:
                case FluxType.LUMINOUS:
                    self.flux_value = 683
                case FluxType.RADIANT:
                    self.flux_value = 1
                case FluxType.FROM_FILE:
                    self.flux_value = 0.0


@dataclass
class SourceLuminaireParameters:
    """Constant class for SourceLuminaireParamters."""

    intensity_file_uri: Union[str, Path] = ""
    flux_type: FluxType = FluxType.FROM_FILE
    flux_value: Optional[float] = None
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)

    def __post_init__(self) -> None:
        """Verify the dataclass initiation."""
        # Validation: restrict flux_type
        if self.flux_type not in {FluxType.FROM_FILE, FluxType.LUMINOUS, FluxType.RADIANT}:
            raise ValueError(
                f"Invalid flux_type '{self.flux_type}'. Must be FROM_FILE, LUMINOUS, or RADIANT."
            )

        # Set default flux_value based on flux_type (only if not manually provided)
        if self.flux_value is None:
            match self.flux_type:
                case FluxType.LUMINOUS:
                    self.flux_value = 683
                case FluxType.RADIANT:
                    self.flux_value = 1
                case FluxType.FROM_FILE:
                    self.flux_value = 0.0


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
