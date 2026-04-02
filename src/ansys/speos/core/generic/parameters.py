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
import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from ansys.speos.core.generic.constants import ORIGIN

# =============================================================================
# Sensor parameters
# =============================================================================


@dataclass
class WavelengthsRangeParameters:
    """Wavelength Parameters."""

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


@dataclass
class IntensitySensorDimensionsConoscopicParameters:
    """Dataclass for Intensity Sensor dimension in case of conoscopic."""

    theta_max: float = 45
    """Maximum theta angle for the conoscopic type (in degrees)."""
    theta_sampling: int = 90
    """Theta sampling for the conoscopic type."""


@dataclass
class IntensitySensorDimensionsXAsMeridianParameters:
    """Dataclass for Intensity Sensor dimension in case of x_as_meridian."""

    y_start: float = -30
    """Lower bound y axis."""
    y_end: float = 30
    """Upper bound y axis."""
    y_sampling: int = 120
    """Sampling y axis."""
    x_start: float = -45
    """Lower bound x axis."""
    x_end: float = 45
    """Upper bound x axis."""
    x_sampling: int = 180
    """Sampling x axis."""


@dataclass
class IntensitySensorDimensionsXAsParallelParameters:
    """Dataclass for Intensity Sensor dimension in case of x_as_parallel."""

    x_start: float = -30
    """Lower bound x axis."""
    x_end: float = 30
    """Upper bound x axis."""
    x_sampling: int = 120
    """Sampling x axis."""
    y_start: float = -45
    """Lower bound x axis."""
    y_end: float = 45
    """Upper bound x axis."""
    y_sampling: int = 180
    """Sampling x axis."""


class LayerTypes(str, Enum):
    """Layer Separation Types."""

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
    """Maximum number of sequences stored in the Speos result file."""
    sequence_type: Union[SequenceTypes.by_face, SequenceTypes.by_geometry] = (
        SequenceTypes.by_geometry
    )
    """Defines how sequences are calculated"""


@dataclass
class GeometryLayerParameters:
    """Geometry Layer Parameters."""

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
    """Defines how result data is filtered."""


@dataclass
class LayerByIncidenceAngleParameters:
    """Layer separation type Parameters for Incidence angle separation."""

    incidence_sampling: int = 9
    """Number of incidence angle layers."""


class PngBits(str, Enum):
    """Bit resolution of create PNG image."""

    png_08 = "png_08"
    png_10 = "png_10"
    png_12 = "png_12"
    png_16 = "png_16"


class ColorBalanceModeTypes(str, Enum):
    """Color Balance Mode Types."""

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
    """Camera Color Mode Parameters."""

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
    """Path to the sensitivity spectrum."""


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
    """Camera sensor type; ``None`` means geometric sensor."""
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    """Location of the sensor origin."""
    distortion_file_uri: Union[str, Path] = ""
    """Distortion file location."""
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
    """Number of rays stored in LXP trajectory data."""


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
    """Integration Types."""

    planar = "planar"
    radial = "radial"
    hemispherical = "hemispherical"
    cylindrical = "cylindrical"
    semi_cylindrical = "semi_cylindrical"


class RayfileTypes(str, Enum):
    """Rayfile Types."""

    none = "none"
    classic = "classic"
    polarization = "polarization"
    tm25 = "tm25"
    tm25_no_polarization = "tm25_no_polarization"


class SensorTypes(str, Enum):
    """Sensor Types."""

    photometric = "photometric"
    radiometric = "radiometric"


class IntensitySensorOrientationTypes(str, Enum):
    """Intensity sensor orientation types."""

    conoscopic = "conoscopic"
    x_as_parallel = "x_as_parallel"
    x_as_meridian = "x_as_meridian"


class IntensitySensorViewingTypes(str, Enum):
    """Intensity sensor viewing types."""

    from_source = "from_source"
    from_sensor = "from_sensor"


@dataclass
class MeasuresParameters:
    """Measurements for 3d Irradiance Sensor."""

    reflection: bool = True
    """Reflection measure activation state."""
    transmission: bool = True
    """Transmission measure activation state."""
    absorption: bool = True
    """Absorption measure activation state."""


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


@dataclass
class NearfieldParameters:
    """Parameters data class for Nearfield."""

    cell_distance: float = 10
    """Distance of cell from origin of the sensor."""
    cell_diameter: float = 0.3491
    """Diameter of cell."""


@dataclass
class IntensityXMPSensorParameters:
    """Intensity Sensor Parameters Dataclass."""

    dimensions: Union[
        IntensitySensorDimensionsXAsMeridianParameters,
        IntensitySensorDimensionsXAsParallelParameters,
        IntensitySensorDimensionsConoscopicParameters,
    ] = field(default_factory=IntensitySensorDimensionsXAsMeridianParameters)
    """Dimensions of the sensor."""
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    """Position of the sensor."""
    sensor_type: Union[
        SensorTypes.photometric, ColorimetricParameters, SpectralParameters, SensorTypes.radiometric
    ] = SensorTypes.photometric
    """Type of the sensor."""
    orientation: IntensitySensorOrientationTypes = IntensitySensorOrientationTypes.x_as_meridian
    """Sensor orientation."""
    viewing_direction: IntensitySensorViewingTypes = IntensitySensorViewingTypes.from_source
    """Viewing direction used for the result."""
    layer_type: Union[
        LayerTypes.none,
        LayerTypes.by_source,
        LayerByFaceParameters,
        LayerBySequenceParameters,
    ] = LayerTypes.none
    """Layer separation type."""
    near_field_parameters: Optional[NearfieldParameters] = None
    """Parameters used when the sensor is near field."""


# =============================================================================
# Source parameters
# =============================================================================
@dataclass
class LuminousFluxParameters:
    """Luminous Flux Parameters."""

    value: float = 683
    """Luminous flux value."""


@dataclass
class RadiantFluxParameters:
    """Radiant Flux Parameters."""

    value: float = 1
    """Radiant flux value."""


@dataclass
class FluxFromFileParameters:
    """Flux from intensity file."""

    value: bool = True
    """Whether to read flux from the source intensity file."""


@dataclass
class SpectrumSampledParameters:
    """Spectrum Sampled Parameters."""

    wavelengths: list[float] = field(default_factory=lambda: [400.0, 700.0])
    """Sampled wavelength values."""
    values: list[float] = field(default_factory=lambda: [100.0, 100.0])
    """Spectrum values corresponding to ``wavelengths``."""


@dataclass
class SpectrumLibraryParameters:
    """Spectrum Library Parameters."""

    file_uri: Union[str, Path] = ""
    """Path to the spectrum file in the library."""


@dataclass
class SpectrumBlackBodyParameters:
    """Spectrum Black Body Parameters."""

    temperature: float = 2856
    """Blackbody temperature in Kelvin."""


class SpectrumType(str, Enum):
    """Spectrum Types."""

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
    """Path to the intensity file used by the luminaire."""
    flux_type: Union[LuminousFluxParameters, RadiantFluxParameters, FluxFromFileParameters] = field(
        default_factory=lambda: FluxFromFileParameters()
    )
    """Flux definition for the luminaire source."""
    spectrum_type: Union[SpectrumBlackBodyParameters, SpectrumLibraryParameters, SpectrumType] = (
        SpectrumType.incandescent
    )
    """Spectrum definition for the luminaire source."""
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    """Axis system used to position the source."""


@dataclass
class SpectrumMonochromaticParameters:
    """Spectrum Monochromatic Parameters."""

    wavelength: float = 555.0
    """Single wavelength value used for monochromatic spectrum."""


@dataclass
class RayFileSourceParameters:
    """Parameters class for Ray File Source."""

    ray_file_uri: Union[str, Path] = ""
    """Path to the ray file."""
    flux_type: Union[LuminousFluxParameters, RadiantFluxParameters, FluxFromFileParameters] = field(
        default_factory=lambda: FluxFromFileParameters()
    )
    """Flux definition for the ray file source."""
    spectrum_type: Optional[
        Union[
            SpectrumBlackBodyParameters, SpectrumLibraryParameters, SpectrumMonochromaticParameters
        ]
    ] = None
    """Optional spectrum definition for the ray file source."""
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    """Axis system used to position the source."""
    exit_geometry: Optional[list[str]] = None
    """Optional list of exit geometries associated with the source."""


@dataclass
class IntensityFluxParameters:
    """Luminous Flux Parameters."""

    value: float = 5
    """Intensity flux value."""


@dataclass
class IntensityLambertianParameters:
    """Intensity Lambertian Parameters."""

    total_angle: float = 180
    """Total angular extent of the Lambertian distribution."""


@dataclass
class IntensityCosParameters:
    """Intensity Cos Parameters."""

    n: float = 3
    """Exponent applied to the cosine intensity distribution."""
    total_angle: float = 180
    """Total angular extent of the cosine distribution."""


@dataclass
class IntensitySymmetricGaussianParameters:
    """Intensity Symmetric Gaussian Parameters."""

    total_angle: float = 180
    """Total angular extent of the Gaussian distribution."""
    fwhm: float = 30.0
    """Full width at half maximum of the symmetric Gaussian."""


@dataclass
class IntensitAsymmetricGaussianParameters:
    """Intensity Asymmetric Gaussian Parameters."""

    total_angle: float = 180
    """Total angular extent of the Gaussian distribution."""
    fwhm_x: float = 30.0
    """Full width at half maximum along the X direction."""
    fwhm_y: float = 30.0
    """Full width at half maximum along the Y direction."""
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    """Axis system defining the asymmetric Gaussian orientation."""


@dataclass
class IntensityOrientationAxisSystemParameters:
    """Intensity Orientation Axis System Parameters."""

    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    """Axis system used to orient the intensity distribution."""


class IntensityOrientationType(str, Enum):
    """Intensity Orientation Types."""

    normal_to_uv = "normal_to_uv"
    normal_to_surface = "normal_to_surface"


@dataclass
class IntensityLibraryParameters:
    """Intensity Library Parameters."""

    intensity_file_uri: Union[str, Path] = ""
    """Path to the intensity library file."""
    orientation_type: Union[IntensityOrientationType, IntensityOrientationAxisSystemParameters] = (
        field(default_factory=lambda: IntensityOrientationAxisSystemParameters())
    )
    """Orientation mode or explicit axis system for the library intensity."""
    exit_geometries: Optional[list[str]] = None
    """Optional list of source geometries where intensity exits."""


@dataclass
class VariableExitanceParameters:
    """Spectrum Exit Parameters."""

    xmp_file_uri: Union[str, Path] = ""
    """Path to the XMP file defining variable exitance."""
    axis_system: list[float] = field(default_factory=lambda: ORIGIN[0:9])
    """Axis system used to position variable exitance."""


@dataclass
class ConstantExitanceParameters:
    """Spectrum Exit Parameters."""

    emissive_faces: list[str] = field(default_factory=lambda: [])
    """Faces that emit with constant exitance."""


@dataclass
class SurfaceSourceParameters:
    """Parameters class for Surface Source."""

    flux_type: Union[
        LuminousFluxParameters,
        RadiantFluxParameters,
        IntensityFluxParameters,
        FluxFromFileParameters,
    ] = field(default_factory=lambda: LuminousFluxParameters())
    """Flux definition used by the surface source."""
    exitance_type: Union[VariableExitanceParameters, ConstantExitanceParameters] = field(
        default_factory=lambda: ConstantExitanceParameters()
    )
    """Exitance definition applied on emitting faces."""
    intensity_type: Union[
        IntensityLambertianParameters,
        IntensityCosParameters,
        IntensitySymmetricGaussianParameters,
        IntensitAsymmetricGaussianParameters,
        IntensityLibraryParameters,
    ] = field(default_factory=lambda: IntensityLambertianParameters())
    """Intensity distribution model used by the source."""
    spectrum_type: Optional[
        Union[
            SpectrumBlackBodyParameters, SpectrumLibraryParameters, SpectrumMonochromaticParameters
        ]
    ] = field(default_factory=lambda: SpectrumMonochromaticParameters())
    """Spectrum definition used by the source."""


@dataclass
class AutomaticSunParameters:
    """Spectrum Exit Parameters."""

    now = datetime.datetime.now()
    time_zone: str = "CET"
    """Time zone used for automatic sun positioning."""
    longitude: float = 0.0
    """Longitude used for automatic sun positioning."""
    latitude: float = 0.0
    """Latitude used for automatic sun positioning."""
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute


@dataclass
class ManualSunParameters:
    """Spectrum Exit Parameters."""

    direction: list[float] = field(default_factory=lambda: [0, 0, 1])
    """Manual sun direction vector."""


@dataclass
class AmbientNaturalLightParameters:
    """Ambient Natural Light Parameters."""

    with_sky: bool = field(default_factory=lambda: True)
    """Whether the sky contribution is enabled."""
    turbidity: float = 3.0
    """Atmospheric turbidity value."""
    zenith_direction: list[float] = field(default_factory=lambda: [0, 0, 1])
    """Zenith direction vector."""
    north_direction: list[float] = field(default_factory=lambda: [0, 1, 0])
    """North direction vector."""
    sun_type: Union[AutomaticSunParameters, ManualSunParameters] = field(
        default_factory=lambda: AutomaticSunParameters()
    )
    """Sun definition, automatic or manual."""


@dataclass
class UserDefinedWhitePointParameters:
    """User defined White Point Parameters."""

    x: float = 0.31271
    """Chromaticity x coordinate of the white point."""
    y: float = 0.32902
    """Chromaticity y coordinate of the white point."""


class WhitePointType(str, Enum):
    """White Point Types."""

    d65 = "d65"
    d50 = "d50"
    c = "c"
    e = "e"


@dataclass
class UserDefinedColorSpaceParameters:
    """User defined Color Space Parameters."""

    white_point_type: Union[WhitePointType, UserDefinedWhitePointParameters] = WhitePointType.d65
    """White point preset or custom white point definition."""
    red_spectrum_uri: Union[str, Path] = ""
    """Path to the red primary spectrum."""
    blue_spectrum_uri: Union[str, Path] = ""
    """Path to the blue primary spectrum."""
    green_spectrum_uri: Union[str, Path] = ""
    """Path to the green primary spectrum."""


class ColorSpaceType(str, Enum):
    """Color Space Types."""

    srgb = "srgb"
    adobe_rgb = "abode_rgb"


@dataclass
class AmbientEnvironmentParameters:
    """Ambient Environment Parameters."""

    zenith_direction: list[float] = field(default_factory=lambda: [0, 0, 1])
    """Zenith direction vector."""
    north_direction: list[float] = field(default_factory=lambda: [0, 1, 0])
    """North direction vector."""
    luminance: float = 1000.0
    """Environment luminance value."""
    image_file_uri: Union[str, Path] = ""
    """Path to the environment image."""
    color_space_type: Union[ColorSpaceType, UserDefinedColorSpaceParameters] = ColorSpaceType.srgb
    """Color space preset or custom color space definition."""


# =============================================================================
# Simulation parameters
# =============================================================================
class ColorimetricStandardTypes(str, Enum):
    """Colorimetric Standard Types."""

    cie_1931 = "cie_1931"
    cie_1964 = "cie_1964"


@dataclass
class DirectSimulationParameters:
    """Direct Simulation Parameters."""

    ambient_material_uri: Union[str, Path] = ""
    """Path to the ambient material file."""
    light_expoert: bool = False
    """Whether light export is enabled."""
    stop_condition_rays_number: int = 200000
    """Maximum number of rays before stopping the simulation."""
    stop_condition_duration: Optional[int] = None
    """Optional simulation stop duration in seconds."""
    automatic_save_frequency: int = 1800
    """Auto-save interval in seconds."""
    colorimetric_standard: ColorimetricStandardTypes = ColorimetricStandardTypes.cie_1931
    """Colorimetric standard used for result computation."""
    dispersion: bool = True
    """Whether wavelength dispersion is enabled."""
    geom_distance_tolerance: float = 0.01
    """Geometry distance tolerance value."""
    max_impact: int = 100
    """Maximum number of impacts considered per ray."""
    minimum_energy_percentage: float = 0.005
    """Minimum energy percentage threshold for ray continuation."""


@dataclass
class InverseSimulationParameters:
    """Inverse Simulation Parameters."""

    ambient_material_uri: Union[str, Path] = ""
    """Path to the ambient material file."""
    light_expoert: bool = False
    """Whether light export is enabled."""
    stop_condition_passes_number: int = 5
    """Maximum number of inverse passes before stopping."""
    stop_condition_duration: Optional[int] = None
    """Optional simulation stop duration in seconds."""
    automatic_save_frequency: int = 1800
    """Auto-save interval in seconds."""
    colorimetric_standard: ColorimetricStandardTypes = ColorimetricStandardTypes.cie_1931
    """Colorimetric standard used for result computation."""
    dispersion: bool = False
    """Whether wavelength dispersion is enabled."""
    geom_distance_tolerance: float = 0.01
    """Geometry distance tolerance value."""
    max_impact: int = 100
    """Maximum number of impacts considered per ray."""
    splitting: bool = False
    """Whether ray splitting is enabled."""
    minimum_energy_percentage: float = 0.005
    """Minimum energy percentage threshold for ray continuation."""
    number_of_gathering_rays_per_source: int = 1
    """Number of gathering rays shot per source."""
    maximum_gathering_error: int = 0
    """Maximum accepted gathering error."""


@dataclass
class InteractiveSimulationParameters:
    """Interactive Simulation Parameters."""

    ambient_material_uri: Union[str, Path] = ""
    """Path to the ambient material file."""
    light_expoert: bool = False
    """Whether light export is enabled."""
    impact_report: bool = False
    """Whether impact reporting is enabled."""
    geom_distance_tolerance = 0.01
    max_impact = 100
    minimum_energy_percentage: float = 0.005
    """Minimum energy percentage threshold for ray continuation."""
    colorimetric_standard: ColorimetricStandardTypes = ColorimetricStandardTypes.cie_1931
    """Colorimetric standard used for result computation."""


@dataclass
class SensorSamplingUnionParameters:
    """Sensor Sampling Union Parameters used in virtual BSDF Simulation Parameters."""

    theta_sampling: int = 45
    """Sampling count in the theta direction."""
    phi_sampling: int = 180
    """Sampling count in the phi direction."""


@dataclass
class VirtualBSDFSimulationParameters:
    """Virtual BSDF Simulation Parameters."""

    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    """Axis system used to position the simulation."""
    analysis_x_ratio: float = 100
    """Analysis ratio along the X axis."""
    analysis_y_ratio: float = 100
    """Analysis ratio along the Y axis."""
    integration_angle: float = 2
    """Integration angle used for BSDF analysis."""
    stop_condition_ray_number: int = 100000
    """Maximum number of rays before stopping the simulation."""
    geom_distance_tolerance: float = 0.01
    """Geometry distance tolerance value."""
    max_impact = 100
    minimum_energy_percentage: float = 0.005
    """Minimum energy percentage threshold for ray continuation."""
    colorimetric_standard: ColorimetricStandardTypes = ColorimetricStandardTypes.cie_1931
    """Colorimetric standard used for result computation."""
    wavelength_range: WavelengthsRangeParameters = field(default_factory=WavelengthsRangeParameters)
    """Wavelength range used by the simulation."""
    sensor_sampling_mode: Optional[SensorSamplingUnionParameters] = field(
        default_factory=SensorSamplingUnionParameters
    )
    """Sensor angular sampling parameters."""


# =============================================================================
# Optical property parameters
# =============================================================================


class SopTypes(str, Enum):
    """Allowed mapping types."""

    optical_polished = "optical_polished"


@dataclass
class SopMirrorParameters:
    """SOP Mirror Parameters Dataclass."""

    reflectance = 100
    """Rreflectance of a perfect mirror."""


@dataclass
class SopLibraryParameters:
    """SOP Library Parameters Dataclass."""

    file_uri: Union[str, Path] = ""
    """Path to the SOP library file."""


@dataclass
class MeshData:
    """Store named data on meshed Geometry."""

    name: str
    """Name of the data added to the mesh."""
    data: list[float]
    """Numerical data values associated with the named mesh item."""


class MappingTypes(str, Enum):
    """Allowed mapping types."""

    planar = "planar"
    cubic = "cubic"
    _spherical = "spherical"
    _cylindrical = "cylindrical"


@dataclass
class MappingCylindricalParameters:
    """Cylindrical mapping parameters."""

    perimeter: float = 1
    """Perimeter value used for cylindrical mapping."""


@dataclass
class MappingSphericalParameters:
    """Spherical mapping parameters."""

    perimeter: float = 1
    """Perimeter value used for spherical mapping."""


@dataclass
class MappingOperator:
    """Store all information needed to create a UV mapping."""

    mapping_type: Union[MappingTypes, MappingCylindricalParameters, MappingSphericalParameters] = (
        MappingTypes.planar
    )
    """Type of mapping applied on the geometry."""
    u_length: float = 10
    """Length of the mapping along the U axis."""
    v_length: Optional[float] = None
    """Length of the mapping along the V axis."""
    u_offset: float = 0
    """Offset of the mapping origin along the U axis."""
    v_offset: float = 0
    """Offset of the mapping origin along the V axis."""
    axis_system: list[float] = field(default_factory=lambda: ORIGIN)
    """Axis system used to position and orient the mapping."""
    u_scale: float = 1
    """Scaling factor applied along the U axis."""
    v_scale: float = 1
    """Scaling factor applied along the V axis."""
    rotation: float = 0
    """Rotation angle of the mapping."""


@dataclass
class MappingByData:
    """Store mapping data when using custom mapping.

    Final data is stored on Face object.
    """

    vertices_data_index: int
    """Index of the vertex data used for custom mapping."""
    repeat_v: Optional[bool] = None
    """Whether mapping repeats along the V direction."""
    repeat_u: Optional[bool] = None
    """Whether mapping repeats along the U direction."""


class NormalMapTypes(str, Enum):
    """Normal Map Types."""

    from_normal_map = "from_normal_map"
    from_image = "from_image"


class TextureTypes(str, Enum):
    """Different texture types."""

    image = "image"
    normal_map = "normal_map"
    anisotropy_map = "anisotropy_map"


class TextureNormalizationTypes(str, Enum):
    """Texture normalization types."""

    unspecified = "unspecified"
    none = "none"
    color_from_texture = "color_from_texture"
    color_from_bsdf = "color_from_bsdf"


@dataclass
class ImageTextureParameters:
    """Parameters of an image based texture."""

    file_path: Union[str, Path] = ""
    """Path to the texture image file."""
    repeat_u: bool = True
    """Whether the image texture repeats along the U direction."""
    repeat_v: bool = True
    """Whether the image texture repeats along the V direction."""
    mapping: [Union[MappingOperator, MappingByData]] = field(default_factory=MappingOperator)
    """Mapping settings applied to the image texture."""


@dataclass
class NormalMapParameters(ImageTextureParameters):
    """Parameters of a normal map based texture."""

    normal_map_type: NormalMapTypes = NormalMapTypes.from_image
    """Mapping parameters to apply on the normal map if normal_map_type is from_normal_map."""
    roughness: float = 1
    """Roughness value to apply on the normal map"""


@dataclass
class TextureLayerParameters:
    """Texture Layer Parameters Dataclass."""

    sop_parameters: Optional[Union[SopTypes, SopMirrorParameters, SopLibraryParameters]] = field(
        default_factory=SopMirrorParameters
    )
    """SOP parameters applied to the texture layer."""
    image_texture_parameters: Optional[ImageTextureParameters] = None
    """Image texture parameters when ``image_texture`` is enabled."""
    normal_map_parameters: Optional[NormalMapParameters] = None
    """Normal map image parameters when ``normal_map`` is enabled."""
    anisotropy_map_parameters: Optional[Union[MappingOperator, MappingByData]] = None
    """Mapping parameters applied to the anisotropy map."""


@dataclass
class VopLibraryParameters:
    """VOP Parameters Dataclass."""

    material_file_uri: Optional[Union[str, Path]] = None
    """Path to the VOP library file when ``vop_type`` is ``library``."""


@dataclass
class VopOpticParameters:
    """Optics Material Parameters."""

    index: float = 1.5
    """Real part of refractive index."""
    absorption: float = 0
    """Absorption coefficient."""
    constringence: Optional[float] = None
    """Abbe Number."""


class VopTypes(str, Enum):
    """Allowed mapping types."""

    none = None
    opaque = "opaque"


@dataclass
class OptPropParameters:
    """Store default values for optical properties."""

    sop_parameters: Optional[
        Union[SopTypes, SopMirrorParameters, SopLibraryParameters, List[TextureLayerParameters]]
    ] = field(default_factory=SopMirrorParameters)
    """SOP parameters used for optical properties."""
    vop_parameters: Optional[Union[VopTypes, VopLibraryParameters, VopOpticParameters]] = (
        VopTypes.none
    )
    """VOP parameters used for optical properties."""
