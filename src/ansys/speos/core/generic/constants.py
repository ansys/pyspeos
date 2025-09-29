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
class WavelengthsRangeParameters:
    """Wavelength parameters."""

    start: int = 400
    """Wavelength start value."""
    end: int = 700
    """Wavelength end value."""
    sampling: int = 13
    """Wavelength sampling."""


@dataclass
class DimensionsParameters:
    """Dimension Parameters."""

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
class LayerBySequenceParameters:
    """Layer separation type Parameters  for Sequence separation."""

    maximum_nb_of_sequence: int = 10
    sequence_type: Union[SequenceTypes.by_face, SequenceTypes.by_geometry] = (
        SequenceTypes.by_geometry
    )


@dataclass
class GeometryLayerParameters:
    """Geometry layer parameters."""

    name: str
    geometry: list


@dataclass
class LayerByFaceParameters:
    """Layer separation type Parameters  for Face separation."""

    geometries: list[GeometryLayerParameters] = None
    sca_filtering_types: Union[
        SCAFilteringTypes.intersected_one_time, SCAFilteringTypes.last_impact
    ] = SCAFilteringTypes.last_impact


@dataclass
class LayerByIncidenceAngleParameters:
    """Layer separation type Parameters for Incidence angle separation."""

    incidence_sampling: int = 9


class PngBits(str, Enum):
    """Bit resolution of create PNG image."""

    png_08 = "png_08"
    png_10 = "png_10"
    png_12 = "png_12"
    png_16 = "png_16"


class ColorBalanceModeTypes(str, Enum):
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
        ColorBalanceModeTypes.none,
        ColorBalanceModeTypes.grey_world,
        BalanceModeUserWhiteParameters,
        BalanceModeDisplayPrimariesParameters,
    ] = ColorBalanceModeTypes.none
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

    color_mode: Union[MonoChromaticParameters, ColorParameters] = field(
        default_factory=ColorParameters
    )
    """Color mode of the Camera Sensor."""
    layer_type: Union[LayerTypes.none, LayerTypes.by_source] = LayerTypes.none
    """Layer separation parameter."""
    png_bits: PngBits = PngBits.png_16
    """PNG bit resolution of the Camera Sensor."""
    wavelength_range = field(default_factory=WavelengthsRangeParameters)
    """Wavelength range of the Camera Sensor."""
    acquisition_integration_time: float = 0.01
    """Integration Time value for the Camera Sensor."""
    acquisition_lag_time: float = 0
    """Acquisition lag time for the Camera Sensor."""
    gamma_correction: float = 2.2
    """Gamma correction Value for the Camera Sensor."""
    transmittance_file_uri: str = ""
    """Transmittance spectrum location"""


@dataclass
class CameraSensorParameters:
    """Camera Sensor Parameters."""

    sensor_type_parameters: Union[None, PhotometricCameraParameters] = field(
        default_factory=PhotometricCameraParameters
    )
    """Camera sensor type None means geometric sensor"""
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
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
    """Trajectory file information."""
    lxp_path_number: Union[None, int] = None


@dataclass
class ColorimetricParameters:
    """Colorimetric settings of the Sensor."""

    wavelength_range = field(default_factory=WavelengthsRangeParameters)
    """Wavelength range of the Sensor."""


@dataclass
class SpectralParameters:
    """Colorimetric settings of the Sensor."""

    wavelength_range = field(default_factory=WavelengthsRangeParameters)
    """Wavelength range of the Sensor."""


class IntegrationTypes(str, Enum):
    """Integration types without parameters."""

    planar = "planar"
    radial = "radial"
    hemispherical = "hemispherical"
    cylindrical = "cylindrical"
    semi_cylindrical = "semi_cylindrical"


class RayfileTypes(str, Enum):
    """Rayfile types without parameters."""

    none = "none"
    classic = "classic"
    polarization = "polarization"
    tm25 = "tm25"
    tm25_no_polarization = "tm25_no_polarization"


class SensorTypes(str, Enum):
    """Sensor types without parameters."""

    photometric = "photometric"
    radiometric = "radiometric"


@dataclass
class MeasuresParameters:
    """Measurements for 3d Irradiance Sensor."""

    reflection: bool = True
    """Reflection measure activation state."""
    transmission: bool = True
    """Transmission measure activation state."""
    absorption: bool = True
    """Ansorption measure activation state."""


@dataclass
class IrradianceSensorParameters:
    """Irradiance Sensor Parameters."""

    dimensions: DimensionsParameters = field(default_factory=DimensionsParameters)
    """Dimensions of the sensor."""
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    """Position of the sensor."""
    sensor_type: Union[
        SensorTypes.photometric, ColorimetricParameters, SpectralParameters, SensorTypes.radiometric
    ] = SensorTypes.photometric
    """Type of the sensor."""
    integration_type: Union[IntegrationTypes] = IntegrationTypes.planar
    """Integration type of the sensor."""
    integration_direction: Union[None, list[float]] = None
    """Integration direction of the sensor."""
    rayfile_type: Union[RayfileTypes] = RayfileTypes.none
    """Type of rayfile stored by the sensor."""
    layer_type: Union[
        LayerTypes,
        LayerByFaceParameters,
        LayerBySequenceParameters,
        LayerByIncidenceAngleParameters,
    ] = LayerTypes.none
    """Type of layer separation used by the sensor."""
    outpath_face_geometry: list = None
    """Outpath face used by the sensor"""


@dataclass
class RadianceSensorParameters:
    """Radiance Sensor Constants."""

    dimensions: DimensionsParameters = field(default_factory=DimensionsParameters)
    """Dimensions of the sensor."""
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    """Position of the sensor."""
    sensor_type: Union[
        SensorTypes.photometric, ColorimetricParameters, SpectralParameters, SensorTypes.radiometric
    ] = SensorTypes.photometric
    """Type of the sensor."""
    focal_length: float = 250.0
    """Distance between observer point and sensor and axis-system,
    will be ignored if observer is used."""
    integration_angle: float = 5
    """Integration angle."""
    observer: Union[None, list[float]] = None
    """The position of the observer point."""
    layer_type: Union[
        LayerTypes.none,
        LayerTypes.by_source,
        LayerByFaceParameters,
        LayerBySequenceParameters,
    ] = LayerTypes.none
    """Type of layer separation used by the sensor."""


@dataclass
class Irradiance3DSensorParameters:
    """Parameters class for 3D Irradiance Sensor."""

    sensor_type: Union[SensorTypes.photometric, ColorimetricParameters, SensorTypes.radiometric] = (
        SensorTypes.photometric
    )
    """Type of the sensor."""
    measures = field(default_factory=MeasuresParameters)
    """Measurement activation state."""
    integration_type: Union[IntegrationTypes.planar, IntegrationTypes.radial] = (
        IntegrationTypes.planar
    )
    """Integration type."""
    rayfile_type: Union[RayfileTypes] = RayfileTypes.none
    """Rayfile type stored."""
    layer_type: Union[LayerTypes.none, LayerTypes.by_source] = LayerTypes.none
    """Layer separation type."""
    geometries: list = None
    """Sensor geometry."""
