# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
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

"""Collection of all parameter dataclasses used in PySpeos."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from ansys.speos.core.generic.constants import ORIGIN

## Sensor Parameters


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
    """Maximum number of sequencese stored in Speos Result file"""
    sequence_type: Union[SequenceTypes.by_face, SequenceTypes.by_geometry] = (
        SequenceTypes.by_geometry
    )
    """Defines how sequences are calculated"""


@dataclass
class GeometryLayerParameters:
    """Geometry layer parameters."""

    name: Optional[str] = None
    """Layer name stored in result file"""
    geometry: Optional[list] = None
    """List of Geometries of the Layer"""


@dataclass
class LayerByFaceParameters:
    """Layer separation type Parameters  for Face separation."""

    geometries: Optional[list[GeometryLayerParameters]] = None
    """List of Geometry Layers"""
    sca_filtering_types: Union[
        SCAFilteringTypes.intersected_one_time, SCAFilteringTypes.last_impact
    ] = SCAFilteringTypes.last_impact
    """Defines how data result data is filtered"""


@dataclass
class LayerByIncidenceAngleParameters:
    """Layer separation type Parameters for Incidence angle separation."""

    incidence_sampling: int = 9
    """Define Number of incidence angle layers"""


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
    red_spectrum_file_uri: Union[str, Path] = ""
    """Path to sensitivity spectrum of red Channel."""
    green_spectrum_file_uri: Union[str, Path] = ""
    """Path to sensitivity spectrum of green Channel."""
    blue_spectrum_file_uri: Union[str, Path] = ""
    """Path to sensitivity spectrum of blue Channel."""


@dataclass
class MonoChromaticParameters:
    """Monochromatic Camera Parameters."""

    sensitivity: Union[str, Path] = ""
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
    wavelength_range: WavelengthsRangeParameters = field(default_factory=WavelengthsRangeParameters)
    """Wavelength range of the Camera Sensor."""
    acquisition_integration_time: float = 0.01
    """Integration Time value for the Camera Sensor."""
    acquisition_lag_time: float = 0
    """Acquisition lag time for the Camera Sensor."""
    gamma_correction: float = 2.2
    """Gamma correction Value for the Camera Sensor."""
    transmittance_file_uri: Union[str, Path] = ""
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
    distortion_file_uri: Union[str, Path] = ""
    """distortion file location"""
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
    lxp_path_number: Optional[int] = None


@dataclass
class ColorimetricParameters:
    """Colorimetric settings of the Sensor."""

    wavelength_range: WavelengthsRangeParameters = field(default_factory=WavelengthsRangeParameters)
    """Wavelength range of the Sensor."""


@dataclass
class SpectralParameters:
    """Colorimetric settings of the Sensor."""

    wavelength_range: WavelengthsRangeParameters = field(default_factory=WavelengthsRangeParameters)
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
    integration_type: IntegrationTypes = IntegrationTypes.planar
    """Integration type of the sensor."""
    integration_direction: Optional[list[float]] = None
    """Integration direction of the sensor."""
    rayfile_type: Union[RayfileTypes] = RayfileTypes.none
    """Type of rayfile stored by the sensor."""
    layer_type: Union[
        LayerTypes.none,
        LayerTypes.by_source,
        LayerTypes.by_polarization,
        LayerByFaceParameters,
        LayerBySequenceParameters,
        LayerByIncidenceAngleParameters,
    ] = LayerTypes.none
    """Type of layer separation used by the sensor."""
    outpath_face_geometry: Optional[list] = None
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
    measures: MeasuresParameters = field(default_factory=MeasuresParameters)
    """Measurement activation state."""
    integration_type: Union[IntegrationTypes.planar, IntegrationTypes.radial] = (
        IntegrationTypes.planar
    )
    """Integration type."""
    rayfile_type: Union[RayfileTypes] = RayfileTypes.none
    """Rayfile type stored."""
    layer_type: Union[LayerTypes.none, LayerTypes.by_source] = LayerTypes.none
    """Layer separation type."""
    geometries: Optional[list] = None
    """Sensor geometry."""


## Source Parameters


@dataclass
class LuminousFluxParameters:
    """Luminous Flux Parameters."""

    value: float = 683


@dataclass
class RadiantFluxParameters:
    """Radiant Flux Parameters."""

    value: float = 1


@dataclass
class FluxFromFileParameters:
    """Flux frm inteisty file."""

    value: bool = True


@dataclass
class SpectrumLibraryParameters:
    """Spectrum library parameters."""

    file_uri: Union[str, Path] = ""


@dataclass
class SpectrumBlackBodyParameters:
    """Spectrum Black Body parameters."""

    temperature: float = 2856


class SpectrumType(str, Enum):
    """Spectrum type without parameters."""

    incandescent = "photometric"
    warm_white_fluorescent = "warm_white_fluorescent"
    daylight_fluorescent = "daylight_fluorescent"
    white_led = "white_led"
    halogen = "halogen"
    metal_halide = "metal_halide"
    high_pressure_sodium = "high_pressure_sodium"


@dataclass
class LuminaireSourceParameters:
    """Parameters class for Luminaire Source."""

    intensity_file_uri: Union[str, Path] = ""
    flux_type: Union[LuminousFluxParameters, RadiantFluxParameters, FluxFromFileParameters] = field(
        default_factory=lambda: FluxFromFileParameters()
    )
    spectrum_type: Union[SpectrumBlackBodyParameters, SpectrumLibraryParameters, SpectrumType] = (
        SpectrumType.incandescent
    )
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
