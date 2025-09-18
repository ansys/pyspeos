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
from typing import Union

from ansys.speos.core import GeoRef, body, face, part

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


@dataclass
class WavelengthsRange:
    """Wavelength constants."""

    start: int = 400
    """Wavelength start value."""
    end: int = 700
    """Wavelength end value."""
    sampling: int = 13
    """Wavelength sampling."""


@dataclass
class Dimensions:
    """Dimension Constants."""

    x_start: float = -50
    """Lower bound x axis."""
    x_end: float = 50
    """Upper bound x axis."""
    x_sampling: int = 100
    """Sampling x axis."""
    y_start: float = -50
    """Lower bound y axis."""
    y_end: float = 50
    """Upper bound y axis."""
    y_sampling: int = 100
    """Sampling y axis."""


class LayerTypes(str, Enum):
    """Layer Separation types without parameters."""

    none = "none"
    by_source = "by_source"
    by_polarization = "by_polarization"


class SCAFilteringTypes(str, Enum):
    """Surface contribution analyser filtering types."""

    intersected_one_time = "intersected_one_time"
    last_impact = "last_impact"


class SequenceTypes(str, Enum):
    """Sequence types to separate the sequence data."""

    by_face = "by_face"
    by_geometry = "by_geometry"


@dataclass
class LayerBySequence:
    """Layer separation type Parameters  for Sequence separation."""

    maximum_nb_of_sequence: int = 10
    sequence_type: Union[SequenceTypes.by_face, SequenceTypes.by_geometry] = (
        SequenceTypes.by_geometry
    )


@dataclass
class LayerByFace:
    """Layer separation type Parameters  for Face separation."""

    geometries: list[list[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]] = None
    sca_filtering_types: Union[
        SCAFilteringTypes.intersected_one_time, SCAFilteringTypes.last_impact
    ] = SCAFilteringTypes.last_impact


@dataclass
class LayerbyIncidenceAngle:
    """Layer separation type Parameters for Incidence angle separation."""

    incidence_sampling: int = 9


class PngBits(str, Enum):
    """Bit resolution of create PNG image."""

    png_08 = "png_08"
    png_10 = "png_10"
    png_12 = "png_12"
    png_16 = "png_16"


class ColorBalanceMode(str, Enum):
    """Color Balance Mode types without parameters."""

    none = "none"
    grey_world = "grey_world"


@dataclass
class BalanceModeUserWhiteParameters:
    """Parameters for Balance mode: User White."""

    red_gain: float = 1.0
    """Gain value for Red."""
    green_gain: float = 1.0
    """Gain value for green."""
    blue_gain: float = 1.0
    """Gain value for blue."""


@dataclass
class BalanceModeDisplayPrimariesParameters:
    """Parameters for Balance mode: Display primaries."""

    red_display_file_uri: Union[str, Path] = ""
    """Spectrum path of the red display spectrum."""
    green_display_file_uri: Union[str, Path] = ""
    """Spectrum path of the green display spectrum."""
    blue_display_file_uri: Union[str, Path] = ""
    """Spectrum path of the red display spectrum."""


@dataclass
class ColorParameters:
    """Color mode Camera Parameter."""

    balance_mode: Union[
        ColorBalanceMode.none,
        ColorBalanceMode.grey_world,
        BalanceModeUserWhiteParameters,
        BalanceModeDisplayPrimariesParameters,
    ] = ColorBalanceMode.none
    """Camera Balance mode."""
    red_spectrum_file_uri: str = ""
    """Path to sensitivity spectrum of red Channel."""
    green_spectrum_file_uri: str = ""
    """Path to sensitivity spectrum of green Channel."""
    blue_spectrum_file_uri: str = ""
    """Path to sensitivity spectrum of blue Channel."""


@dataclass
class MonoChromaticParameters:
    """Monochromatic Camera Parameters."""

    sensitivity: str = ""
    """Path to Sensitivity Spectrum."""


@dataclass
class PhotometricCameraParameters:
    """Photometric Parameters for Camera."""

    color_mode: Union[MonoChromaticParameters, ColorParameters] = ColorParameters()
    """Color mode of the Camera Sensor."""
    layer_type: Union[LayerTypes.none, LayerTypes.by_source] = LayerTypes.none
    """Layer separation parameter."""
    png_bits: Union[PngBits.png_08, PngBits.png_10, PngBits.png_12, PngBits.png_16] = PngBits.png_16
    """PNG bit resolution of the Camera Sensor."""
    wavelength_range = WavelengthsRange()
    """Wavelength range of the Camera Sensor."""
    ACQUISITION_INTEGRATION: float = 0.01
    """Integration Time value for the Camera Sensor."""
    ACQUISITION_LAG_TIME: float = 0
    """Acquisition lag time for the Camera Sensor."""
    GAMMA_CORRECTION: float = 2.2
    """Gamma correction Value for the Camera Sensor."""


@dataclass
class CameraSensorParameters:
    """Camera Sensor Parameters."""

    sensor_type_parameters: Union[None, PhotometricCameraParameters] = PhotometricCameraParameters()
    """Camera sensor type None means geometric sensor"""
    axis_system: list[float] = field(default_factory=lambda: [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    """Location of the sensor Origin"""
    focal_length: float = 5
    """Default focal length of the Camera Sensor."""
    imager_distance: float = 10
    """Default imager distance of the camera sensor."""
    f_number: float = 20
    """Default f number of the camera sensor."""
    horz_pixel: int = 640
    """Default pixel number in horizontal direction."""
    vert_pixel: int = 480
    """Default pixel number in vertical direction."""
    width: float = 5.0
    """Default width of the camera chip."""
    height: float = 5.0
    """Default height of the camera chip."""
    trajectory_fil_uri: Union[str, Path] = ""


@dataclass(frozen=True)
class RadianceSensor:
    """Radiance Sensor Constants."""

    FOCAL_LENGTH = 250
    INTEGRATION_ANGLE = 5


@dataclass(frozen=True)
class SENSOR:
    """Constant class for Sensors."""

    WAVELENGTHSRANGE = WavelengthsRange()
    DIMENSIONS = Dimensions()
    LAYERTYPES = LayerTypes()
    CAMERASENSOR = ""
    RADIANCESENSOR = RadianceSensor()
