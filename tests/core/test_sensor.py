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

"""Test basic using sensor."""

import math
from pathlib import Path

from ansys.api.speos.sensor.v1 import camera_sensor_pb2
import numpy as np
import pytest

from ansys.speos.core import Body, GeoRef, Project, Speos, sensor
from ansys.speos.core.generic.constants import (
    ORIGIN,
)
from ansys.speos.core.generic.parameters import (
    BalanceModeUserWhiteParameters,
    CameraSensorParameters,
    ColorimetricParameters,
    DimensionsParameters,
    IntegrationTypes,
    IntensitySensorDimensionsConoscopic,
    IntensitySensorDimensionsXAsMeridian,
    IntensitySensorDimensionsXAsParallel,
    IntensitySensorOrientationTypes,
    IntensitySensorViewingTypes,
    IntensityXMPSensorParameters,
    Irradiance3DSensorParameters,
    IrradianceSensorParameters,
    LayerByFaceParameters,
    LayerByIncidenceAngleParameters,
    LayerBySequenceParameters,
    LayerTypes,
    MeasuresParameters,
    NearfieldParameters,
    RadianceSensorParameters,
    RayfileTypes,
    SensorTypes,
    SequenceTypes,
    SpectralParameters,
    WavelengthsRangeParameters,
)
from ansys.speos.core.sensor import (
    BaseSensor,
    Sensor3DIrradiance,
    SensorCamera,
    SensorIrradiance,
    SensorRadiance,
    SensorXMPIntensity,
)
from ansys.speos.core.simulation import SimulationDirect
from tests.conftest import test_path


@pytest.mark.supported_speos_versions(min=252)
def test_create_camera_sensor(speos: Speos):
    """Test creation of camera sensor."""
    p = Project(speos=speos)

    sensor_parameters = CameraSensorParameters()
    # Default value
    sensor1 = p.create_sensor(name="Camera.1", feature_type=SensorCamera)
    assert isinstance(sensor1, SensorCamera)
    sensor1.set_mode_photometric().set_mode_color().red_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityRed.spectrum"
    )
    sensor1.set_mode_photometric().set_mode_color().green_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityGreen.spectrum"
    )
    sensor1.set_mode_photometric().set_mode_color().blue_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityBlue.spectrum"
    )

    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("camera_sensor_template")
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.focal_length == sensor_parameters.focal_length
    assert camera_sensor_template.imager_distance == sensor_parameters.imager_distance
    assert camera_sensor_template.distortion_file_uri == ""
    assert camera_sensor_template.f_number == sensor_parameters.f_number
    assert camera_sensor_template.horz_pixel == sensor_parameters.horz_pixel
    assert camera_sensor_template.vert_pixel == sensor_parameters.vert_pixel
    assert camera_sensor_template.width == sensor_parameters.width
    assert camera_sensor_template.height == sensor_parameters.height
    assert camera_sensor_template.HasField("sensor_mode_photometric")
    mode_photometric = camera_sensor_template.sensor_mode_photometric
    assert (
        mode_photometric.acquisition_integration
        == sensor_parameters.sensor_type_parameters.acquisition_integration_time
    )
    assert (
        mode_photometric.acquisition_lag_time
        == sensor_parameters.sensor_type_parameters.acquisition_lag_time
    )
    assert (
        mode_photometric.transmittance_file_uri
        == sensor_parameters.sensor_type_parameters.transmittance_file_uri
    )
    assert math.isclose(
        a=mode_photometric.gamma_correction,
        b=sensor_parameters.sensor_type_parameters.gamma_correction,
        rel_tol=1.192092896e-07,
    )
    assert mode_photometric.png_bits == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
    assert mode_photometric.HasField("wavelengths_range")
    assert (
        mode_photometric.wavelengths_range.w_start
        == sensor_parameters.sensor_type_parameters.wavelength_range.start
    )
    assert (
        mode_photometric.wavelengths_range.w_end
        == sensor_parameters.sensor_type_parameters.wavelength_range.end
    )
    assert (
        mode_photometric.wavelengths_range.w_sampling
        == sensor_parameters.sensor_type_parameters.wavelength_range.sampling
    )
    assert mode_photometric.HasField("color_mode_color")
    assert mode_photometric.color_mode_color.red_spectrum_file_uri.endswith(
        "CameraSensitivityRed.spectrum"
    )
    assert mode_photometric.color_mode_color.green_spectrum_file_uri.endswith(
        "CameraSensitivityGreen.spectrum"
    )
    assert mode_photometric.color_mode_color.blue_spectrum_file_uri.endswith(
        "CameraSensitivityBlue.spectrum"
    )
    assert mode_photometric.color_mode_color.HasField("balance_mode_none")
    assert sensor1._sensor_instance.camera_properties.axis_system == sensor_parameters.axis_system
    assert (
        sensor1._sensor_instance.camera_properties.trajectory_file_uri
        == sensor_parameters.trajectory_fil_uri
    )
    assert (
        sensor1.set_mode_photometric().trajectory_file_uri == sensor_parameters.trajectory_fil_uri
    )
    assert sensor1._sensor_instance.camera_properties.HasField("layer_type_none")

    # focal_length
    sensor1.focal_length = 5.5
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.focal_length == 5.5
    assert sensor1.focal_length == 5.5

    # imager_distance
    sensor1.imager_distance = 10.5
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.imager_distance == 10.5
    assert sensor1.imager_distance == 10.5

    # f_number
    sensor1.f_number = 20.5
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.f_number == 20.5
    assert sensor1.f_number == 20.5

    # distortion_file_uri
    sensor1.distortion_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraDistortion_130deg.OPTDistortion"
    )
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.distortion_file_uri != ""
    assert sensor1.distortion_file_uri != ""

    # horz_pixel
    sensor1.horz_pixel = 680
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.horz_pixel == 680
    assert sensor1.horz_pixel == 680

    # vert_pixel
    sensor1.vert_pixel = 500
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.vert_pixel == 500
    assert sensor1.vert_pixel == 500

    # width
    sensor1.width = 5.5
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.width == 5.5
    assert sensor1.width == 5.5

    # height
    sensor1.height = 5.3
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.height == 5.3
    assert sensor1.height == 5.3

    # sensor_mode_geometric
    sensor1.set_mode_geometric()
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.HasField("sensor_mode_geometric")

    # sensor_mode_photometric
    sensor1.set_mode_photometric()
    color = sensor1.photometric.set_mode_color()
    color.red_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityRed.spectrum"
    )
    color.green_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityGreen.spectrum"
    )
    color.blue_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityBlue.spectrum"
    )
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.HasField("sensor_mode_photometric")

    # acquisition_integration
    sensor1.photometric.acquisition_integration = 0.03
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.sensor_mode_photometric.acquisition_integration == 0.03
    assert sensor1.photometric.acquisition_integration == 0.03

    # acquisition_lag_time
    sensor1.photometric.acquisition_lag_time = 0.1
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.sensor_mode_photometric.acquisition_lag_time == 0.1
    assert sensor1.photometric.acquisition_lag_time == 0.1

    # transmittance_file_uri
    sensor1.photometric.transmittance_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraTransmittance.spectrum"
    )
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.sensor_mode_photometric.transmittance_file_uri != ""
    assert sensor1.photometric.transmittance_file_uri != ""

    # gamma_correction
    sensor1.photometric.gamma_correction = 2.5
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.sensor_mode_photometric.gamma_correction == 2.5
    assert sensor1.photometric.gamma_correction == 2.5

    # png_bits
    sensor1.photometric.set_png_bits_08()
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert (
        camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_08
    )
    sensor1.set_mode_photometric().set_png_bits_10()
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert (
        camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_10
    )
    sensor1.set_mode_photometric().set_png_bits_12()
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert (
        camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_12
    )
    sensor1.set_mode_photometric().set_png_bits_16()
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert (
        camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
    )

    # color_mode_monochromatic
    sensor1.set_mode_photometric().set_mode_monochromatic(
        spectrum_file_uri=str(
            Path(test_path) / "CameraInputFiles" / "CameraSensitivityBlue.spectrum"
        )
    )
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    mode_photometric = camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.HasField("color_mode_monochromatic")
    assert mode_photometric.color_mode_monochromatic.spectrum_file_uri != ""

    # color_mode_color
    sensor1.set_mode_photometric()
    color = sensor1.photometric.set_mode_color()
    color.red_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityRed.spectrum"
    )
    color.green_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityGreen.spectrum"
    )
    color.blue_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityBlue.spectrum"
    )
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.sensor_mode_photometric.HasField("color_mode_color")

    mode_photometric = camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.red_spectrum_file_uri.endswith(
        "CameraSensitivityRed.spectrum"
    )
    assert mode_photometric.color_mode_color.green_spectrum_file_uri.endswith(
        "CameraSensitivityGreen.spectrum"
    )
    assert mode_photometric.color_mode_color.blue_spectrum_file_uri.endswith(
        "CameraSensitivityBlue.spectrum"
    )
    assert color.red_spectrum_file_uri.endswith("CameraSensitivityRed.spectrum")
    assert color.green_spectrum_file_uri.endswith("CameraSensitivityGreen.spectrum")
    assert color.blue_spectrum_file_uri.endswith("CameraSensitivityBlue.spectrum")

    # balance_mode_greyworld
    sensor1.set_mode_photometric().set_mode_color().set_balance_mode_grey_world()
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    mode_photometric = camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_greyworld")

    # balance_mode_userwhite
    sensor1.set_mode_photometric().set_mode_color().set_balance_mode_user_white()
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    mode_photometric = camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_userwhite")
    default_userwhites = BalanceModeUserWhiteParameters()
    assert (
        mode_photometric.color_mode_color.balance_mode_userwhite.red_gain
        == default_userwhites.red_gain
    )
    assert (
        mode_photometric.color_mode_color.balance_mode_userwhite.green_gain
        == default_userwhites.green_gain
    )
    assert (
        mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain
        == default_userwhites.blue_gain
    )

    balance_mode_user_white = (
        sensor1.set_mode_photometric().set_mode_color().set_balance_mode_user_white()
    )
    balance_mode_user_white.red_gain = 2
    balance_mode_user_white.green_gain = 3
    balance_mode_user_white.blue_gain = 4
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    mode_photometric = camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.balance_mode_userwhite.red_gain == 2
    assert mode_photometric.color_mode_color.balance_mode_userwhite.green_gain == 3
    assert mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain == 4
    assert balance_mode_user_white.red_gain == 2
    assert balance_mode_user_white.green_gain == 3
    assert balance_mode_user_white.blue_gain == 4

    # balance_mode_display
    display_primaries = (
        sensor1.set_mode_photometric().set_mode_color().set_balance_mode_display_primaries()
    )
    display_primaries.red_display_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityRed.spectrum"
    )
    display_primaries.green_display_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityGreen.spectrum"
    )
    display_primaries.blue_display_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityBlue.spectrum"
    )
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    mode_photometric = camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_display")
    assert mode_photometric.color_mode_color.balance_mode_display.red_display_file_uri.endswith(
        "CameraSensitivityRed.spectrum"
    )
    assert mode_photometric.color_mode_color.balance_mode_display.green_display_file_uri.endswith(
        "CameraSensitivityGreen.spectrum"
    )
    assert mode_photometric.color_mode_color.balance_mode_display.blue_display_file_uri.endswith(
        "CameraSensitivityBlue.spectrum"
    )
    assert display_primaries.red_display_file_uri == str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityRed.spectrum"
    )
    assert display_primaries.green_display_file_uri == str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityGreen.spectrum"
    )
    assert display_primaries.blue_display_file_uri == str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityBlue.spectrum"
    )

    # balance_mode_none
    sensor1.set_mode_photometric().set_mode_color().set_balance_mode_none()
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    mode_photometric = camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_none")

    # wavelengths_range
    wavelengths_range = sensor1.photometric.set_wavelengths_range()
    wavelengths_range.start = 430
    wavelengths_range.end = 750
    wavelengths_range.sampling = 15
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    mode_photometric = camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.wavelengths_range.w_start == 430
    assert mode_photometric.wavelengths_range.w_end == 750
    assert mode_photometric.wavelengths_range.w_sampling == 15
    assert wavelengths_range.start == 430
    assert wavelengths_range.end == 750
    assert wavelengths_range.sampling == 15

    # Properties

    # axis_system
    sensor1.axis_system = [10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.axis_system == [
        10,
        50,
        20,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    assert sensor1.axis_system == [
        10,
        50,
        20,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    # Properties for camera photometric

    # layer_type_source
    sensor1.set_mode_photometric().set_layer_type_source()
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.HasField("layer_type_source")

    # layer_type_none
    sensor1.set_mode_photometric().set_layer_type_none()
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.HasField("layer_type_none")

    # test distrotion v1,v2,v3
    sensor1.focal_length = 5.0
    sensor1.imager_distance = 10.0
    sensor1.f_number = 20.0
    sensor1.commit()
    sensor1.distortion_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "distortionV{}.OPTDistortion".format(2)
    )
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.f_number == 20.0
    assert camera_sensor_template.imager_distance == 10.0
    assert camera_sensor_template.focal_length == 5.0
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.f_number == 0
    assert camera_sensor_template.imager_distance == 0
    assert camera_sensor_template.focal_length == 0
    sensor1.distortion_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "distortionV{}.OPTDistortion".format(1)
    )
    sensor1.focal_length = 5.0
    sensor1.imager_distance = 10.0
    sensor1.f_number = 20.0
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.f_number == 0
    assert camera_sensor_template.imager_distance == 0
    assert camera_sensor_template.focal_length == 0
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.f_number == 20.0
    assert camera_sensor_template.imager_distance == 10.0
    assert camera_sensor_template.focal_length == 5.0
    sensor1.distortion_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "distortionV{}.OPTDistortion".format(4)
    )
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.f_number == 20.0
    assert camera_sensor_template.imager_distance == 10.0
    assert camera_sensor_template.focal_length == 5.0
    assert camera_sensor_template.sensor_mode_photometric.transmittance_file_uri != ""
    sensor1.commit()
    camera_sensor_template = sensor1.sensor_template_link.get().camera_sensor_template
    assert camera_sensor_template.f_number == 0
    assert camera_sensor_template.imager_distance == 0
    assert camera_sensor_template.focal_length == 0
    assert camera_sensor_template.sensor_mode_photometric.transmittance_file_uri == ""

    sensor1.delete()


@pytest.mark.supported_speos_versions(min=251)
def test_create_irradiance_sensor(speos: Speos):
    """Test creation of irradiance sensor."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="TheBodyB")
    body_b.create_face(name="TheFaceF").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_c = root_part.create_body(name="TheBodyC")
    body_c.create_face(name="TheFaceC1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_c.create_face(name="TheFaceC2").set_vertices([1, 0, 0, 2, 0, 0, 1, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()
    sensor_parameter = IrradianceSensorParameters()
    # Default value
    sensor1 = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("irradiance_sensor_template")
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("sensor_type_photometric")
    assert sensor_template.HasField("illuminance_type_planar")
    assert sensor_template.HasField("dimensions")
    assert sensor_template.dimensions.x_start == sensor_parameter.dimensions.x_start
    assert sensor_template.dimensions.x_end == sensor_parameter.dimensions.x_end
    assert sensor_template.dimensions.x_sampling == sensor_parameter.dimensions.x_sampling
    assert sensor_template.dimensions.y_start == sensor_parameter.dimensions.y_start
    assert sensor_template.dimensions.y_end == sensor_parameter.dimensions.y_end
    assert sensor_template.dimensions.y_sampling == sensor_parameter.dimensions.y_sampling
    assert sensor1._sensor_instance.HasField("irradiance_properties")
    irra_properties = sensor1._sensor_instance.irradiance_properties
    assert irra_properties.axis_system == sensor_parameter.axis_system
    assert irra_properties.HasField("layer_type_none")
    assert irra_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFileNone
    assert irra_properties.integration_direction == []
    color_parameters = ColorimetricParameters()
    # sensor_type_colorimetric
    # default wavelengths range
    sensor1.set_type_colorimetric()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("sensor_type_colorimetric")
    assert sensor_template.sensor_type_colorimetric.HasField("wavelengths_range")
    assert (
        sensor_template.sensor_type_colorimetric.wavelengths_range.w_start
        == color_parameters.wavelength_range.start
    )
    assert (
        sensor_template.sensor_type_colorimetric.wavelengths_range.w_end
        == color_parameters.wavelength_range.end
    )
    assert (
        sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling
        == color_parameters.wavelength_range.sampling
    )
    # chosen wavelengths range
    wavelengths_range = sensor1.set_type_colorimetric().set_wavelengths_range()
    wavelengths_range.start = 450
    wavelengths_range.end = 800
    wavelengths_range.sampling = 15
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.sensor_type_colorimetric.wavelengths_range.w_start == 450
    assert sensor_template.sensor_type_colorimetric.wavelengths_range.w_end == 800
    assert sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling == 15
    assert wavelengths_range.start == 450
    assert wavelengths_range.end == 800
    assert wavelengths_range.sampling == 15
    # sensor_type_radiometric
    sensor1.set_type_radiometric()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("sensor_type_radiometric")

    spectral_parameters = SpectralParameters()
    # sensor_type_spectral
    # default wavelengths range
    sensor1.set_type_spectral()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("sensor_type_spectral")
    assert sensor_template.sensor_type_spectral.HasField("wavelengths_range")
    assert (
        sensor_template.sensor_type_spectral.wavelengths_range.w_start
        == spectral_parameters.wavelength_range.start
    )
    assert (
        sensor_template.sensor_type_spectral.wavelengths_range.w_end
        == spectral_parameters.wavelength_range.end
    )
    assert (
        sensor_template.sensor_type_spectral.wavelengths_range.w_sampling
        == spectral_parameters.wavelength_range.sampling
    )
    # chosen wavelengths range
    wavelengths_range = sensor1.set_type_spectral().set_wavelengths_range()
    wavelengths_range.start = 450
    wavelengths_range.end = 800
    wavelengths_range.sampling = 15
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.sensor_type_spectral.wavelengths_range.w_start == 450
    assert sensor_template.sensor_type_spectral.wavelengths_range.w_end == 800
    assert sensor_template.sensor_type_spectral.wavelengths_range.w_sampling == 15
    assert wavelengths_range.start == 450
    assert wavelengths_range.end == 800
    assert wavelengths_range.sampling == 15

    # sensor_type_photometric
    sensor1.set_type_photometric()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("sensor_type_photometric")

    # illuminance_type_radial
    sensor1.set_illuminance_type_radial()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("illuminance_type_radial")

    # illuminance_type_hemispherical - bug to be fixed
    # sensor1.set_illuminance_type_hemispherical()
    # sensor1.commit()
    # sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    # assert sensor_template.HasField("illuminance_type_hemispherical")

    # illuminance_type_cylindrical
    sensor1.set_illuminance_type_cylindrical()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("illuminance_type_cylindrical")

    # illuminance_type_semi_cylindrical - bug to be fixed
    # sensor1.set_illuminance_type_semi_cylindrical(integration_direction=[1,0,0])
    # sensor1.commit()
    # sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    # assert sensor_template.HasField("illuminance_type_semi_cylindrical")

    # illuminance_type_planar
    sensor1.set_illuminance_type_planar()
    sensor1.integration_direction = [0, 0, -1]
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("illuminance_type_planar")
    assert sensor1.integration_direction == [0, 0, -1]

    sensor1.integration_direction = None  # cancel integration direction
    assert irra_properties.integration_direction == []
    assert sensor1.integration_direction == []

    # dimensions
    sensor1.dimensions.x_start = -10
    sensor1.dimensions.x_end = 10
    sensor1.dimensions.x_sampling = 60
    sensor1.dimensions.y_start = -20
    sensor1.dimensions.y_end = 20
    sensor1.dimensions.y_sampling = 120
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("dimensions")
    assert sensor_template.dimensions.x_start == -10.0
    assert sensor_template.dimensions.x_end == 10.0
    assert sensor_template.dimensions.x_sampling == 60
    assert sensor_template.dimensions.y_start == -20.0
    assert sensor_template.dimensions.y_end == 20.0
    assert sensor_template.dimensions.y_sampling == 120

    # properties
    # axis_system
    sensor1.axis_system = [10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sensor1.commit()
    assert irra_properties.axis_system == [
        10,
        50,
        20,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    assert sensor1.axis_system == [10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    # ray_file_type
    sensor1.set_ray_file_type_classic()
    sensor1.commit()
    assert irra_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFileClassic

    sensor1.set_ray_file_type_polarization()
    sensor1.commit()
    assert (
        irra_properties.ray_file_type
        == sensor1._sensor_instance.EnumRayFileType.RayFilePolarization
    )

    sensor1.set_ray_file_type_tm25()
    sensor1.commit()
    assert irra_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFileTM25

    sensor1.set_ray_file_type_tm25_no_polarization()
    sensor1.commit()
    assert (
        irra_properties.ray_file_type
        == sensor1._sensor_instance.EnumRayFileType.RayFileTM25NoPolarization
    )

    sensor1.set_ray_file_type_none()
    sensor1.commit()
    assert irra_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFileNone

    # layer_type_source
    sensor1.set_layer_type_source()
    sensor1.commit()
    assert irra_properties.HasField("layer_type_source")

    # layer_type_face
    layer1 = sensor.BaseSensor.FaceLayer(
        name="Layer.1", geometries=[GeoRef.from_native_link("TheBodyB")]
    )
    layer1.geometry = [body_b]
    layer2 = sensor.BaseSensor.FaceLayer(
        name="Layer.2",
        geometries=[
            GeoRef.from_native_link("TheBodyC/TheFaceC1"),
            GeoRef.from_native_link("TheBodyC/TheFaceC2"),
        ],
    )
    layer_face = sensor1.set_layer_type_face()
    layer_face.set_sca_filtering_mode_intersected_one_time()
    layer_face.layers = [layer1, layer2]
    sensor1.commit()
    assert irra_properties.HasField("layer_type_face")
    assert (
        irra_properties.layer_type_face.sca_filtering_mode
        == irra_properties.layer_type_face.EnumSCAFilteringType.IntersectedOneTime
    )
    assert len(irra_properties.layer_type_face.layers) == 2
    assert irra_properties.layer_type_face.layers[0].name == "Layer.1"
    assert irra_properties.layer_type_face.layers[0].geometries.geo_paths == ["TheBodyB"]
    assert irra_properties.layer_type_face.layers[1].name == "Layer.2"
    assert irra_properties.layer_type_face.layers[1].geometries.geo_paths == [
        "TheBodyC/TheFaceC1",
        "TheBodyC/TheFaceC2",
    ]
    assert layer1.name == "Layer.1"
    assert layer2.name == "Layer.2"
    for geo_path in layer1.geometry:
        assert isinstance(geo_path, GeoRef)
    layer_face.set_sca_filtering_mode_last_impact()
    sensor1.commit()
    assert (
        irra_properties.layer_type_face.sca_filtering_mode
        == irra_properties.layer_type_face.EnumSCAFilteringType.LastImpact
    )

    # layer_type_sequence
    layer_by_sequence = sensor1.set_layer_type_sequence()
    layer_by_sequence.maximum_nb_of_sequence = 5
    layer_by_sequence.set_define_sequence_per_faces()
    sensor1.commit()
    assert irra_properties.HasField("layer_type_sequence")
    assert layer_by_sequence.maximum_nb_of_sequence == 5
    assert irra_properties.layer_type_sequence.maximum_nb_of_sequence == 5
    assert (
        irra_properties.layer_type_sequence.define_sequence_per
        == irra_properties.layer_type_sequence.EnumSequenceType.Faces
    )

    sensor1.set_layer_type_sequence().set_define_sequence_per_geometries()
    sensor1.commit()
    assert (
        irra_properties.layer_type_sequence.define_sequence_per
        == irra_properties.layer_type_sequence.EnumSequenceType.Geometries
    )

    # layer_type_polarization
    sensor1.set_type_radiometric()
    sensor1.set_layer_type_polarization()
    sensor1.commit()
    assert irra_properties.HasField("layer_type_polarization")

    # layer_type_incidence_angle
    sensor1.set_layer_type_incidence_angle().sampling = 8
    sensor1.commit()
    assert irra_properties.HasField("layer_type_incidence_angle")
    assert sensor1.set_layer_type_incidence_angle().sampling == 8
    assert irra_properties.layer_type_incidence_angle.sampling == 8

    # layer_type_none
    sensor1.set_layer_type_none()
    sensor1.commit()
    assert irra_properties.HasField("layer_type_none")

    # output_face_geometries
    sensor1.output_face_geometries = [
        GeoRef.from_native_link(geopath="TheBodyB/TheFaceB1"),
        body_b,
    ]
    assert irra_properties.output_face_geometries.geo_paths == [
        "TheBodyB/TheFaceB1",
        "TheBodyB",
    ]

    # output_face_geometries
    sensor1.delete()


@pytest.mark.supported_speos_versions(min=251)
def test_create_radiance_sensor(speos: Speos):
    """Test creation of radiance sensor."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="TheBodyB")
    body_b.create_face(name="TheFaceF").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_c = root_part.create_body(name="TheBodyC")
    body_c.create_face(name="TheFaceC1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_c.create_face(name="TheFaceC2").set_vertices([1, 0, 0, 2, 0, 0, 1, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()
    sensor_parameter = RadianceSensorParameters()
    # Default value
    sensor1 = p.create_sensor(name="Radiance.1", feature_type=SensorRadiance)
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("radiance_sensor_template")
    assert sensor1.sensor_template_link.get().name == "Radiance.1"
    template = sensor1.sensor_template_link.get().radiance_sensor_template
    assert template.HasField("sensor_type_photometric")
    assert template.focal == sensor_parameter.focal_length
    assert sensor1.focal == sensor_parameter.focal_length
    assert template.integration_angle == sensor_parameter.integration_angle
    assert sensor1.integration_angle == sensor_parameter.integration_angle
    assert template.HasField("dimensions")
    assert template.dimensions.x_start == sensor_parameter.dimensions.x_start
    assert template.dimensions.x_end == sensor_parameter.dimensions.x_end
    assert template.dimensions.x_sampling == sensor_parameter.dimensions.x_sampling
    assert sensor1.set_dimensions().x_sampling == sensor_parameter.dimensions.x_sampling
    assert template.dimensions.y_start == sensor_parameter.dimensions.y_start
    assert template.dimensions.y_end == sensor_parameter.dimensions.y_end
    assert template.dimensions.y_sampling == sensor_parameter.dimensions.y_sampling
    assert sensor1.set_dimensions().y_sampling == sensor_parameter.dimensions.y_sampling
    assert sensor1._sensor_instance.HasField("radiance_properties")
    radiance_properties = sensor1._sensor_instance.radiance_properties
    assert radiance_properties.axis_system == sensor_parameter.axis_system
    assert radiance_properties.HasField("layer_type_none")
    assert radiance_properties.observer_point == []

    # sensor_type_radiometric
    sensor1.set_type_radiometric()
    sensor1.commit()
    template = sensor1.sensor_template_link.get().radiance_sensor_template
    assert template.HasField("sensor_type_radiometric")

    # sensor_type_colorimetric
    color_parameters = SpectralParameters()
    # default wavelengths range
    sensor1.set_type_colorimetric()
    sensor1.commit()
    template = sensor1.sensor_template_link.get().radiance_sensor_template
    assert template.HasField("sensor_type_colorimetric")
    assert template.sensor_type_colorimetric.HasField("wavelengths_range")
    assert (
        template.sensor_type_colorimetric.wavelengths_range.w_start
        == color_parameters.wavelength_range.start
    )
    assert (
        template.sensor_type_colorimetric.wavelengths_range.w_end
        == color_parameters.wavelength_range.end
    )
    assert (
        template.sensor_type_colorimetric.wavelengths_range.w_sampling
        == color_parameters.wavelength_range.sampling
    )

    # sensor_type_spectral
    spectral_parameters = SpectralParameters()
    # default wavelengths range
    sensor1.set_type_spectral()
    sensor1.commit()
    template = sensor1.sensor_template_link.get().radiance_sensor_template
    assert template.HasField("sensor_type_spectral")
    assert template.sensor_type_spectral.HasField("wavelengths_range")
    assert (
        template.sensor_type_spectral.wavelengths_range.w_start
        == spectral_parameters.wavelength_range.start
    )
    assert (
        template.sensor_type_spectral.wavelengths_range.w_end
        == spectral_parameters.wavelength_range.end
    )
    assert (
        template.sensor_type_spectral.wavelengths_range.w_sampling
        == spectral_parameters.wavelength_range.sampling
    )

    # chosen wavelengths range
    wavelengths_range = sensor1.set_type_spectral().set_wavelengths_range()
    wavelengths_range.start = 450
    wavelengths_range.end = 800
    wavelengths_range.sampling = 15
    sensor1.commit()
    template = sensor1.sensor_template_link.get().radiance_sensor_template
    assert template.sensor_type_spectral.wavelengths_range.w_start == 450
    assert template.sensor_type_spectral.wavelengths_range.w_end == 800
    assert template.sensor_type_spectral.wavelengths_range.w_sampling == 15

    # sensor_type_photometric
    sensor1.set_type_photometric()
    sensor1.commit()
    template = sensor1.sensor_template_link.get().radiance_sensor_template
    assert template.HasField("sensor_type_photometric")

    # focal
    sensor1.focal = 150.5
    sensor1.commit()
    template = sensor1.sensor_template_link.get().radiance_sensor_template
    assert template.focal == 150.5

    # integration_angle
    sensor1.integration_angle = 4.5
    sensor1.commit()
    template = sensor1.sensor_template_link.get().radiance_sensor_template
    assert template.integration_angle == 4.5

    # dimensions
    sensor1.dimensions.x_start = -10
    sensor1.dimensions.x_end = 10
    sensor1.dimensions.x_sampling = 60
    sensor1.dimensions.y_start = -20
    sensor1.dimensions.y_end = 20
    sensor1.dimensions.y_sampling = 120
    sensor1.commit()
    template = sensor1.sensor_template_link.get().radiance_sensor_template
    assert template.HasField("dimensions")
    assert template.dimensions.x_start == -10.0
    assert template.dimensions.x_end == 10.0
    assert template.dimensions.x_sampling == 60
    assert template.dimensions.y_start == -20.0
    assert template.dimensions.y_end == 20.0
    assert template.dimensions.y_sampling == 120

    # properties
    # axis_system
    sensor1.axis_system = [10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sensor1.commit()
    assert radiance_properties.axis_system == [
        10,
        50,
        20,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    assert sensor1.axis_system == [10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    # observer_point
    sensor1.observer_point = [20, 30, 50]
    assert sensor1.observer_point == [
        20,
        30,
        50,
    ]
    sensor1.commit()
    assert radiance_properties.observer_point == [
        20,
        30,
        50,
    ]

    sensor1.observer_point = None  # cancel observer point chosen previously
    sensor1.commit()
    assert radiance_properties.observer_point == []

    # layer_type_source
    sensor1.set_layer_type_source()
    sensor1.commit()
    assert radiance_properties.HasField("layer_type_source")

    # layer_type_face
    sensor1.set_layer_type_face().set_sca_filtering_mode_intersected_one_time().layers = [
        sensor.BaseSensor.FaceLayer(
            name="Layer.1", geometries=[GeoRef.from_native_link("TheBodyB")]
        ),
        sensor.BaseSensor.FaceLayer(
            name="Layer.2",
            geometries=[
                GeoRef.from_native_link("TheBodyC/TheFaceC1"),
                GeoRef.from_native_link("TheBodyC/TheFaceC2"),
            ],
        ),
    ]
    sensor1.commit()
    assert radiance_properties.HasField("layer_type_face")
    assert (
        radiance_properties.layer_type_face.sca_filtering_mode
        == radiance_properties.layer_type_face.EnumSCAFilteringType.IntersectedOneTime
    )
    assert len(radiance_properties.layer_type_face.layers) == 2
    assert radiance_properties.layer_type_face.layers[0].name == "Layer.1"
    assert radiance_properties.layer_type_face.layers[0].geometries.geo_paths == ["TheBodyB"]
    assert radiance_properties.layer_type_face.layers[1].name == "Layer.2"
    assert radiance_properties.layer_type_face.layers[1].geometries.geo_paths == [
        "TheBodyC/TheFaceC1",
        "TheBodyC/TheFaceC2",
    ]

    # layer_type_face -> chose other filtering mode
    sensor1.set_layer_type_face().set_sca_filtering_mode_last_impact()
    sensor1.commit()
    assert (
        radiance_properties.layer_type_face.sca_filtering_mode
        == radiance_properties.layer_type_face.EnumSCAFilteringType.LastImpact
    )

    # layer_type_sequence
    sensor1.set_layer_type_sequence().maximum_nb_of_sequence = 5
    sensor1.set_layer_type_sequence().set_define_sequence_per_faces()
    sensor1.commit()
    assert radiance_properties.HasField("layer_type_sequence")
    assert radiance_properties.layer_type_sequence.maximum_nb_of_sequence == 5
    assert (
        radiance_properties.layer_type_sequence.define_sequence_per
        == radiance_properties.layer_type_sequence.EnumSequenceType.Faces
    )

    sensor1.set_layer_type_sequence().set_define_sequence_per_geometries()
    sensor1.commit()
    assert (
        radiance_properties.layer_type_sequence.define_sequence_per
        == radiance_properties.layer_type_sequence.EnumSequenceType.Geometries
    )

    # layer_type_none
    sensor1.set_layer_type_none()
    sensor1.commit()
    assert radiance_properties.HasField("layer_type_none")


@pytest.mark.supported_speos_versions(min=252)
def test_create_xmpintensity_sensor(speos: Speos):
    """Test creation of XMP Intensity sensor."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="TheBodyB")
    body_b.create_face(name="TheFaceF").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_c = root_part.create_body(name="TheBodyC")
    body_c.create_face(name="TheFaceC1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_c.create_face(name="TheFaceC2").set_vertices([1, 0, 0, 2, 0, 0, 1, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    # Default value
    sensor1 = p.create_sensor(name="Intensity.1", feature_type=SensorXMPIntensity)
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("intensity_sensor_template")
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template

    assert sensor_template.HasField("sensor_type_photometric")
    assert sensor_template.HasField("intensity_orientation_x_as_meridian")
    assert sensor_template.intensity_orientation_x_as_meridian.HasField("intensity_dimensions")
    assert sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.x_start == -45.0
    assert sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.x_end == 45.0
    assert (
        sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.x_sampling == 180
    )
    assert sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.y_start == -30.0
    assert sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.y_end == 30.0
    assert (
        sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.y_sampling == 120
    )

    assert sensor1._sensor_instance.HasField("intensity_properties")
    inte_properties = sensor1._sensor_instance.intensity_properties
    assert inte_properties.axis_system == [
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    assert inte_properties.HasField("layer_type_none")

    # sensor_type_colorimetric
    # default wavelengths range
    sensor1.set_type_colorimetric()
    sensor1.commit()

    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.HasField("sensor_type_colorimetric")
    assert sensor_template.sensor_type_colorimetric.HasField("wavelengths_range")
    assert sensor_template.sensor_type_colorimetric.wavelengths_range.w_start == 400
    assert sensor_template.sensor_type_colorimetric.wavelengths_range.w_end == 700
    assert sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling == 13
    # chosen wavelengths range
    wl_range = sensor1.set_type_colorimetric().set_wavelengths_range()
    wl_range.start = 450
    wl_range.end = 800
    wl_range.sampling = 15
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.sensor_type_colorimetric.wavelengths_range.w_start == 450
    assert sensor_template.sensor_type_colorimetric.wavelengths_range.w_end == 800
    assert sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling == 15

    # sensor_type_radiometric
    sensor1.set_type_radiometric()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.HasField("sensor_type_radiometric")

    # sensor_type_spectral
    # default wavelengths range
    sensor1.set_type_spectral()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.HasField("sensor_type_spectral")
    assert sensor_template.sensor_type_spectral.HasField("wavelengths_range")
    assert sensor_template.sensor_type_spectral.wavelengths_range.w_start == 400
    assert sensor_template.sensor_type_spectral.wavelengths_range.w_end == 700
    assert sensor_template.sensor_type_spectral.wavelengths_range.w_sampling == 13
    # chosen wavelengths range
    wl_range = sensor1.set_type_spectral().set_wavelengths_range()
    wl_range.start = 450
    wl_range.end = 800
    wl_range.sampling = 15
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.sensor_type_spectral.wavelengths_range.w_start == 450
    assert sensor_template.sensor_type_spectral.wavelengths_range.w_end == 800
    assert sensor_template.sensor_type_spectral.wavelengths_range.w_sampling == 15

    # sensor_type_photometric
    sensor1.set_type_photometric()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.HasField("sensor_type_photometric")

    # dimensions: x-meridian
    """
    sensor1.set_dimensions().set_x_start(value=-10).set_x_end(value=10).set_x_sampling(
        value=60
    ).set_y_start(value=-20).set_y_end(value=20).set_y_sampling(value=120)
    """
    sensor1.x_start = -10
    sensor1.x_end = 10
    sensor1.x_sampling = 60
    sensor1.y_start = -20
    sensor1.y_end = 20
    sensor1.y_sampling = 120
    sensor1.commit()

    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.intensity_orientation_x_as_meridian.HasField("intensity_dimensions")
    assert sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.x_start == -10.0
    assert sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.x_end == 10.0
    assert sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.x_sampling == 60
    assert sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.y_start == -20.0
    assert sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.y_end == 20.0
    assert (
        sensor_template.intensity_orientation_x_as_meridian.intensity_dimensions.y_sampling == 120
    )

    # dimensions: x-parallel
    sensor1.set_orientation_x_as_parallel()
    sensor1.x_start = -11
    sensor1.x_end = 11
    sensor1.x_sampling = 62
    sensor1.y_start = -21
    sensor1.y_end = 21
    sensor1.y_sampling = 122
    sensor1.commit()

    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.intensity_orientation_x_as_parallel.HasField("intensity_dimensions")
    assert sensor_template.intensity_orientation_x_as_parallel.intensity_dimensions.x_start == -11.0
    assert sensor_template.intensity_orientation_x_as_parallel.intensity_dimensions.x_end == 11.0
    assert sensor_template.intensity_orientation_x_as_parallel.intensity_dimensions.x_sampling == 62
    assert sensor_template.intensity_orientation_x_as_parallel.intensity_dimensions.y_start == -21.0
    assert sensor_template.intensity_orientation_x_as_parallel.intensity_dimensions.y_end == 21.0
    assert (
        sensor_template.intensity_orientation_x_as_parallel.intensity_dimensions.y_sampling == 122
    )

    # dimensions: conoscopic
    sensor1.set_orientation_conoscopic()
    sensor1.theta_max = 63
    sensor1.theta_sampling = 123
    sensor1.commit()

    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.intensity_orientation_conoscopic.HasField(
        "conoscopic_intensity_dimensions"
    )
    assert (
        sensor_template.intensity_orientation_conoscopic.conoscopic_intensity_dimensions.theta_max
        == 63.0
    )
    assert (
        sensor_template.intensity_orientation_conoscopic.conoscopic_intensity_dimensions.sampling
        == 123.0
    )

    # dimensions: reset
    sensor1.set_orientation_x_as_meridian()

    # properties
    # axis_system
    sensor1.axis_system = [10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sensor1.commit()
    assert inte_properties.axis_system == [
        10,
        50,
        20,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]

    # result file format

    # near field settings
    sensor1.near_field = True
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.HasField("near_field")

    sensor1.cell_distance = 1
    sensor1.cell_diameter = 2
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.near_field.cell_distance == 1
    assert sensor_template.near_field.cell_integration_angle == math.degrees(math.atan(2 / 2 / 1))

    sensor1.near_field = False
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert ~sensor_template.HasField("near_field")

    # viewing direction
    sensor1.set_viewing_direction_from_sensor()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.HasField("from_sensor_looking_at_source")

    sensor1.set_viewing_direction_from_source()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().intensity_sensor_template
    assert sensor_template.HasField("from_source_looking_at_sensor")

    # layer_type_source
    sensor1.set_layer_type_source()
    sensor1.commit()
    assert inte_properties.HasField("layer_type_source")

    # layer_type_face
    layer_type = sensor1.set_layer_type_face().set_sca_filtering_mode_intersected_one_time()
    if isinstance(layer_type, BaseSensor.LayerTypeFace):
        pass
    layer_type.layers = [
        sensor.BaseSensor.FaceLayer(
            name="Layer.1", geometries=[GeoRef.from_native_link("TheBodyB")]
        ),
        sensor.BaseSensor.FaceLayer(
            name="Layer.2",
            geometries=[
                GeoRef.from_native_link("TheBodyC/TheFaceC1"),
                GeoRef.from_native_link("TheBodyC/TheFaceC2"),
            ],
        ),
    ]
    sensor1.commit()
    assert inte_properties.HasField("layer_type_face")
    assert (
        inte_properties.layer_type_face.sca_filtering_mode
        == inte_properties.layer_type_face.EnumSCAFilteringType.IntersectedOneTime
    )
    assert len(inte_properties.layer_type_face.layers) == 2
    assert inte_properties.layer_type_face.layers[0].name == "Layer.1"
    assert inte_properties.layer_type_face.layers[0].geometries.geo_paths == ["TheBodyB"]
    assert inte_properties.layer_type_face.layers[1].name == "Layer.2"
    assert inte_properties.layer_type_face.layers[1].geometries.geo_paths == [
        "TheBodyC/TheFaceC1",
        "TheBodyC/TheFaceC2",
    ]

    sensor1.set_layer_type_face().set_sca_filtering_mode_last_impact()
    sensor1.commit()
    assert (
        inte_properties.layer_type_face.sca_filtering_mode
        == inte_properties.layer_type_face.EnumSCAFilteringType.LastImpact
    )

    # layer_type_sequence
    layer_type = sensor1.set_layer_type_sequence()
    layer_type.maximum_nb_of_sequence = 5
    layer_type.set_define_sequence_per_faces()
    sensor1.commit()
    assert inte_properties.HasField("layer_type_sequence")
    assert inte_properties.layer_type_sequence.maximum_nb_of_sequence == 5
    assert (
        inte_properties.layer_type_sequence.define_sequence_per
        == inte_properties.layer_type_sequence.EnumSequenceType.Faces
    )

    layer_type.set_define_sequence_per_geometries()
    sensor1.commit()
    assert (
        inte_properties.layer_type_sequence.define_sequence_per
        == inte_properties.layer_type_sequence.EnumSequenceType.Geometries
    )

    # layer_type_none
    sensor1.set_layer_type_none()
    sensor1.commit()
    assert inte_properties.HasField("layer_type_none")

    # output_face_geometries
    sensor1.delete()


@pytest.mark.supported_speos_versions(min=252)
def test_load_intensity_sensor(speos: Speos):
    """Test load of Intensity sensor."""
    p = Project(
        speos=speos,
        path=str(Path(test_path) / "Intensity_test.speos" / "Intensity_test.speos"),
    )
    sensors = p.find(name=".*", name_regex=True, feature_type=SensorXMPIntensity)
    assert len(sensors) == 4
    sensor_color = sensors[0]
    sensor_photo = sensors[2]
    sensor_spectral = sensors[1]
    sensor_radio = sensors[3]
    assert isinstance(sensor_color, SensorXMPIntensity)
    assert isinstance(sensor_photo, SensorXMPIntensity)
    assert isinstance(sensor_spectral, SensorXMPIntensity)
    assert isinstance(sensor_radio, SensorXMPIntensity)
    assert sensor_color.x_start == -13
    assert sensor_color.x_end == 13
    assert sensor_color.x_sampling == 26
    assert sensor_color.y_start == -14
    assert sensor_color.y_end == 14
    assert sensor_color.y_sampling == 28
    assert sensor_color.type == "Colorimetric"
    assert sensor_photo.type == "Photometric"
    assert sensor_spectral.type == "Spectral"
    assert sensor_radio.type == "Radiometric"
    assert isinstance(sensor_color.colorimetric, BaseSensor.Colorimetric)
    assert isinstance(sensor_spectral.spectral, BaseSensor.Spectral)
    seq_layer = sensor_spectral.layer
    face_layer = sensor_color.layer
    assert isinstance(face_layer, BaseSensor.LayerTypeFace)
    assert sensor_photo.layer == LayerTypes.by_source
    assert isinstance(seq_layer, BaseSensor.LayerTypeSequence)
    assert sensor_radio.layer == "none"
    assert seq_layer.maximum_nb_of_sequence == 5
    assert isinstance(face_layer.layers[0], BaseSensor.FaceLayer)
    wl_range = sensor_color.set_type_colorimetric().set_wavelengths_range()
    assert wl_range.start == 400
    assert wl_range.end == 700
    assert wl_range.sampling == 16
    assert sensor_color._sensor_template.intensity_sensor_template.HasField(
        "intensity_orientation_x_as_meridian"
    )
    assert sensor_photo._sensor_template.intensity_sensor_template.HasField(
        "intensity_orientation_x_as_parallel"
    )
    assert sensor_radio._sensor_template.intensity_sensor_template.HasField(
        "intensity_orientation_conoscopic"
    )
    assert sensor_photo.near_field
    assert sensor_photo.cell_diameter == 1
    assert sensor_photo.cell_distance == 15
    assert sensor_photo.axis_system == [0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0]
    assert sensor_radio.axis_system == ORIGIN


@pytest.mark.supported_speos_versions(min=252)
def test_load_3d_irradiance_sensor(speos: Speos):
    """Test load of 3d irradiance sensor."""
    p = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism_3D.speos"),
    )
    sensor_3d = p.find(name=".*", name_regex=True, feature_type=Sensor3DIrradiance)[0]
    assert isinstance(sensor_3d, Sensor3DIrradiance)
    assert isinstance(sensor_3d.Photometric, Sensor3DIrradiance.Photometric)
    assert sensor_3d.type == SensorTypes.photometric.capitalize()
    assert sensor_3d.layer == LayerTypes.none


def test_load_radiance_sensor(speos: Speos):
    """Test load of radiance sensor."""
    p = Project(
        speos=speos,
        path=str(Path(test_path) / "Radiance.1.speos" / "Radiance.1.speos"),
    )
    sensors = p.find(name=".*", name_regex=True, feature_type=SensorRadiance)
    defaults = RadianceSensorParameters()
    assert len(sensors) == 4
    sensor_color = sensors[3]
    sensor_photo = sensors[0]
    sensor_spectral = sensors[2]
    sensor_radio = sensors[1]
    assert isinstance(sensor_color, SensorRadiance)
    assert isinstance(sensor_photo, SensorRadiance)
    assert isinstance(sensor_spectral, SensorRadiance)
    assert isinstance(sensor_radio, SensorRadiance)
    assert sensor_color.type == "Colorimetric"
    assert sensor_photo.type == "Photometric"
    assert sensor_spectral.type == "Spectral"
    assert sensor_radio.type == "Radiometric"
    assert isinstance(sensor_color.colorimetric, BaseSensor.Colorimetric)
    assert isinstance(sensor_spectral.spectral, BaseSensor.Spectral)
    assert sensor_color.dimensions.x_start == -5
    assert sensor_color.dimensions.x_end == 5
    assert sensor_color.dimensions.x_sampling == 20
    assert sensor_color.dimensions.y_start == -5
    assert sensor_color.dimensions.y_end == 5
    assert sensor_color.dimensions.y_sampling == 20
    assert sensor_radio.dimensions.x_start == -5
    assert sensor_radio.dimensions.x_end == 5
    assert sensor_radio.dimensions.x_sampling == 20
    assert sensor_radio.dimensions.y_start == -5
    assert sensor_radio.dimensions.y_end == 5
    assert sensor_radio.dimensions.y_sampling == 20
    assert sensor_spectral.dimensions.x_start == -5
    assert sensor_spectral.dimensions.x_end == 5
    assert sensor_spectral.dimensions.x_sampling == 20
    assert sensor_spectral.dimensions.y_start == -5
    assert sensor_spectral.dimensions.y_end == 5
    assert sensor_spectral.dimensions.y_sampling == 20
    assert sensor_photo.dimensions.x_start == defaults.dimensions.x_start
    assert sensor_photo.dimensions.x_end == defaults.dimensions.x_end
    assert sensor_photo.dimensions.x_sampling == defaults.dimensions.x_sampling
    assert sensor_photo.dimensions.y_start == defaults.dimensions.y_start
    assert sensor_photo.dimensions.y_end == defaults.dimensions.y_end
    assert sensor_photo.dimensions.y_sampling == defaults.dimensions.y_sampling
    assert sensor_color.focal == 200
    assert sensor_photo.focal == 250
    assert sensor_spectral.focal == 200
    assert sum(np.array(sensor_radio.observer_point) - np.array([0, 0, 20])) ** 2 < 1e-6
    seq_layer = sensor_color.layer
    face_layer = sensor_spectral.layer
    assert isinstance(face_layer, BaseSensor.LayerTypeFace)
    assert (
        face_layer._layer_type_face.sca_filtering_mode
        == face_layer._layer_type_face.EnumSCAFilteringType.IntersectedOneTime
    )
    assert sensor_radio.layer == LayerTypes.by_source
    assert isinstance(seq_layer, BaseSensor.LayerTypeSequence)
    assert sensor_photo.layer == "none"
    assert seq_layer.maximum_nb_of_sequence == 10
    assert isinstance(face_layer.layers[0], BaseSensor.FaceLayer)
    assert (
        seq_layer._layer_type_sequence.define_sequence_per
        == seq_layer._layer_type_sequence.EnumSequenceType.Geometries
    )
    wl_range = sensor_color.set_type_colorimetric().set_wavelengths_range()
    wl_defaults = WavelengthsRangeParameters()
    assert wl_range.start == wl_defaults.start
    assert wl_range.end == wl_defaults.end
    assert wl_range.sampling == wl_defaults.sampling
    wl_range = sensor_spectral.set_type_spectral().set_wavelengths_range()
    assert wl_range.start == 380
    assert wl_range.end == 780
    assert wl_range.sampling == 21
    assert sensor_photo.axis_system == ORIGIN
    assert (
        sum(
            np.array(sensor_color.axis_system)
            - np.array(
                [
                    0,
                    0,
                    2,
                    np.sqrt(2) / 2,
                    np.sqrt(2) / 2,
                    0,
                    -np.sqrt(2) / 2,
                    np.sqrt(2) / 2,
                    0,
                    0,
                    0,
                    1,
                ]
            )
        )
        ** 2
        < 1e-6
    )


def test_load_irradiance_sensor(speos: Speos):
    """Test load of radiance sensor."""
    p = Project(
        speos=speos,
        path=str(Path(test_path) / "Irradiance.1.speos" / "Irradiance.1.speos"),
    )
    sensors = p.find(name=".*", name_regex=True, feature_type=SensorIrradiance)
    defaults = RadianceSensorParameters()
    assert len(sensors) == 5
    sensor_default = sensors[0]
    sensor_color = sensors[2]
    sensor_photo = sensors[4]
    sensor_spectral = sensors[3]
    sensor_radio = sensors[1]
    assert isinstance(sensor_color, SensorIrradiance)
    assert isinstance(sensor_photo, SensorIrradiance)
    assert isinstance(sensor_default, SensorIrradiance)
    assert isinstance(sensor_spectral, SensorIrradiance)
    assert isinstance(sensor_radio, SensorIrradiance)
    assert isinstance(sensor_color.colorimetric, BaseSensor.Colorimetric)
    assert isinstance(sensor_spectral.spectral, BaseSensor.Spectral)
    assert sensor_color.type == "Colorimetric"
    assert sensor_default.type == "Photometric"
    assert sensor_photo.type == "Photometric"
    assert sensor_spectral.type == "Spectral"
    assert sensor_radio.type == "Radiometric"
    assert sensor_color.dimensions.x_start == -10
    assert sensor_color.dimensions.x_end == 10
    assert sensor_color.dimensions.x_sampling == 10
    assert sensor_color.dimensions.y_start == -10
    assert sensor_color.dimensions.y_end == 10
    assert sensor_color.dimensions.y_sampling == 10
    assert sensor_radio.dimensions.x_start == -10
    assert sensor_radio.dimensions.x_end == 10
    assert sensor_radio.dimensions.x_sampling == 10
    assert sensor_radio.dimensions.y_start == -10
    assert sensor_radio.dimensions.y_end == 10
    assert sensor_radio.dimensions.y_sampling == 10
    assert sensor_spectral.dimensions.x_start == -10
    assert sensor_spectral.dimensions.x_end == 10
    assert sensor_spectral.dimensions.x_sampling == 10
    assert sensor_spectral.dimensions.y_start == -10
    assert sensor_spectral.dimensions.y_end == 10
    assert sensor_spectral.dimensions.y_sampling == 10
    assert sensor_photo.dimensions.x_start == defaults.dimensions.x_start
    assert sensor_photo.dimensions.x_end == defaults.dimensions.x_end
    assert sensor_photo.dimensions.x_sampling == defaults.dimensions.x_sampling
    assert sensor_photo.dimensions.y_start == defaults.dimensions.y_start
    assert sensor_photo.dimensions.y_end == defaults.dimensions.y_end
    assert sensor_photo.dimensions.y_sampling == defaults.dimensions.y_sampling
    assert sensor_default.dimensions.x_start == defaults.dimensions.x_start
    assert sensor_default.dimensions.x_end == defaults.dimensions.x_end
    assert sensor_default.dimensions.x_sampling == defaults.dimensions.x_sampling
    assert sensor_default.dimensions.y_start == defaults.dimensions.y_start
    assert sensor_default.dimensions.y_end == defaults.dimensions.y_end
    assert sensor_default.dimensions.y_sampling == defaults.dimensions.y_sampling
    assert sensor_default.layer == LayerTypes.none
    assert sensor_radio.layer == LayerTypes.by_polarization
    inc_layer = sensor_color.layer
    assert isinstance(inc_layer, BaseSensor.LayerTypeIncidenceAngle)
    assert inc_layer.sampling == 25
    assert sensor_spectral.layer == LayerTypes.by_source
    seq_layer = sensor_photo.layer
    assert seq_layer.maximum_nb_of_sequence == 7
    assert (
        seq_layer._layer_type_sequence.define_sequence_per
        == seq_layer._layer_type_sequence.EnumSequenceType.Geometries
    )
    wl_range = sensor_color.set_type_colorimetric().set_wavelengths_range()
    wl_defaults = WavelengthsRangeParameters()
    assert wl_range.start == 380
    assert wl_range.end == 780
    assert wl_range.sampling == 17
    wl_range = sensor_spectral.set_type_spectral().set_wavelengths_range()
    assert wl_range.start == wl_defaults.start
    assert wl_range.end == wl_defaults.end
    assert wl_range.sampling == wl_defaults.sampling
    assert sensor_color.axis_system == ORIGIN
    assert (
        sum(
            np.array(sensor_photo.axis_system)
            - np.array(
                [
                    0,
                    0,
                    2,
                    np.sqrt(2) / 2,
                    np.sqrt(2) / 2,
                    0,
                    -np.sqrt(2) / 2,
                    np.sqrt(2) / 2,
                    0,
                    0,
                    0,
                    1,
                ]
            )
        )
        ** 2
        < 1e-6
    )


@pytest.mark.supported_speos_versions(min=252)
def test_create_3d_irradiance_sensor(speos: Speos):
    """Test creation of 3d irradiance sensor."""
    p = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism.speos"),
    )
    body = p.find(name="PrismBody", name_regex=True, feature_type=Body)[0]
    sensor_3d = p.create_sensor(name="3d", feature_type=Sensor3DIrradiance)
    sensor_3d.geometries = [body.geo_path]
    sensor_3d.geometries = [body]
    sensor_3d.commit()

    # when creating 3D irradiance, default properties:
    # photometric
    # planar integration
    # layer type none
    # measure reflection, transmission, absorption
    backend_photometric_info = sensor_3d.sensor_template_link.get()
    assert sensor_3d.sensor_template_link is not None
    assert backend_photometric_info.name == "3d"
    assert backend_photometric_info.HasField("irradiance_3d")
    assert backend_photometric_info.irradiance_3d.HasField("type_photometric")
    assert backend_photometric_info.irradiance_3d.type_photometric.HasField(
        "integration_type_planar"
    )
    photometric_info = backend_photometric_info.irradiance_3d.type_photometric
    assert photometric_info.integration_type_planar.reflection
    assert photometric_info.integration_type_planar.transmission
    assert photometric_info.integration_type_planar.absorption
    assert sensor_3d._sensor_instance.HasField("irradiance_3d_properties")
    assert sensor_3d._sensor_instance.irradiance_3d_properties.geometries.geo_paths == [
        "PrismBody:1130610277"
    ]
    assert sensor_3d._sensor_instance.irradiance_3d_properties.HasField("layer_type_none")

    # change integration to radial
    sensor_3d.set_type_photometric().set_integration_radial()
    sensor_3d.commit()
    backend_photometric_info = sensor_3d.sensor_template_link.get()
    assert backend_photometric_info.irradiance_3d.HasField("type_photometric")
    assert backend_photometric_info.irradiance_3d.type_photometric.HasField(
        "integration_type_radial"
    )

    # change back to planar
    # reflection, transmission, absorption as default
    # absorption is False after being set
    sensor_3d.set_type_photometric().set_integration_planar().absorption = False
    sensor_3d.commit()
    backend_photometric_info = sensor_3d.sensor_template_link.get()
    photometric_info = backend_photometric_info.irradiance_3d.type_photometric
    assert photometric_info.integration_type_planar.reflection
    assert photometric_info.integration_type_planar.transmission
    assert not photometric_info.integration_type_planar.absorption

    # when change type into radiometric, default properties:
    # radiometric
    # planar integration
    # layer type none
    sensor_3d.set_type_radiometric()
    sensor_3d.commit()
    backend_radiometric_info = sensor_3d.sensor_template_link.get()
    assert backend_radiometric_info.irradiance_3d.HasField("type_radiometric")
    radiometric_info = backend_radiometric_info.irradiance_3d.type_radiometric
    assert radiometric_info.HasField("integration_type_planar")
    assert radiometric_info.integration_type_planar.reflection
    assert radiometric_info.integration_type_planar.transmission
    assert radiometric_info.integration_type_planar.absorption

    # change integration type
    sensor_3d.set_type_radiometric().set_integration_radial()
    sensor_3d.commit()
    radiometric_info = sensor_3d.sensor_template_link.get().irradiance_3d.type_radiometric
    assert radiometric_info.HasField("integration_type_radial")

    # change back to planar
    # reflection, transmission, absorption as default
    # absorption is False after being set
    sensor_3d.set_type_radiometric().set_integration_planar().absorption = False
    sensor_3d.commit()
    backend_radiometric_info = sensor_3d.sensor_template_link.get()
    photometric_info = backend_radiometric_info.irradiance_3d.type_radiometric
    assert photometric_info.integration_type_planar.reflection
    assert photometric_info.integration_type_planar.transmission
    assert not photometric_info.integration_type_planar.absorption

    # when change type into colorimetric, default properties:
    # colorimetric
    color_parameters = ColorimetricParameters()
    # wavelength start 400 with end 700
    # layer type none
    sensor_3d.set_type_colorimetric()
    sensor_3d.commit()
    assert sensor_3d.sensor_template_link.get().irradiance_3d.HasField("type_colorimetric")
    colorimetric_info = sensor_3d.sensor_template_link.get().irradiance_3d.type_colorimetric
    assert colorimetric_info.wavelength_start == color_parameters.wavelength_range.start
    assert colorimetric_info.wavelength_end == color_parameters.wavelength_range.end
    wavelengths_range = sensor_3d.set_type_colorimetric().set_wavelengths_range()
    wavelengths_range.start = 500
    sensor_3d.commit()
    colorimetric_info = sensor_3d.sensor_template_link.get().irradiance_3d.type_colorimetric
    assert sensor_3d.get(key="wavelength_start") == 500
    assert colorimetric_info.wavelength_start == 500

    # change back to planar
    # reflection, transmission, absorption as default
    # absorption is False after being set
    sensor_3d.set_type_photometric().set_integration_planar().absorption = False
    sensor_3d.commit()
    backend_photometric_info = sensor_3d.sensor_template_link.get()
    photometric_info = backend_photometric_info.irradiance_3d.type_photometric
    assert photometric_info.integration_type_planar.reflection
    assert photometric_info.integration_type_planar.transmission
    assert not photometric_info.integration_type_planar.absorption

    # change layer as source
    sensor_3d.set_layer_type_source()
    sensor_3d.commit()
    assert sensor_3d._sensor_instance.irradiance_3d_properties.HasField("layer_type_source")

    # change rayfile options
    sensor_3d.set_ray_file_type_classic()
    sensor_3d.commit()
    assert sensor_3d._sensor_instance.irradiance_3d_properties.ray_file_type == 1
    sensor_3d.set_ray_file_type_polarization()
    sensor_3d.commit()
    assert sensor_3d._sensor_instance.irradiance_3d_properties.ray_file_type == 2
    sensor_3d.set_ray_file_type_tm25()
    sensor_3d.commit()
    assert sensor_3d._sensor_instance.irradiance_3d_properties.ray_file_type == 3
    sensor_3d.set_ray_file_type_tm25_no_polarization()
    sensor_3d.commit()
    assert sensor_3d._sensor_instance.irradiance_3d_properties.ray_file_type == 4

    sim = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
    sim.set_sensor_paths(["Irradiance.1:564", "3d"])
    sim.commit()
    assert sim._simulation_instance.sensor_paths == ["Irradiance.1:564", "3d"]
    sim.delete()


def test_commit_sensor(speos: Speos):
    """Test commit of sensor."""
    p = Project(speos=speos)

    # Create
    sensor1 = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    assert sensor1.sensor_template_link is None
    assert len(p.scene_link.get().sensors) == 0

    # Commit
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("irradiance_sensor_template")
    assert len(p.scene_link.get().sensors) == 1
    assert p.scene_link.get().sensors[0] == sensor1._sensor_instance

    # Change only in local not committed
    sensor1.axis_system = [10, 10, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert p.scene_link.get().sensors[0] != sensor1._sensor_instance

    sensor1.delete()


def test_reset_sensor(speos: Speos):
    """Test reset of sensor."""
    p = Project(speos=speos)

    # Create + commit
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=SensorIrradiance)
    sensor_parameter = IrradianceSensorParameters()
    sensor1.commit()
    assert (
        sensor1._sensor_template.irradiance_sensor_template.dimensions.x_start
        == sensor_parameter.dimensions.x_start
    )  # local
    assert (
        sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_start
        == sensor_parameter.dimensions.x_start
    )  # server
    assert sensor1._sensor_instance.irradiance_properties.axis_system == ORIGIN  # local
    assert p.scene_link.get().sensors[0].irradiance_properties.axis_system == ORIGIN  # server

    sensor1.dimensions.x_start = 0
    sensor1.axis_system = [1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sensor1._sensor_template.irradiance_sensor_template.dimensions.x_start == 0  # local
    assert (
        sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_start == -50
    )  # server
    assert sensor1._sensor_instance.irradiance_properties.axis_system == [
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]  # local
    assert p.scene_link.get().sensors[0].irradiance_properties.axis_system == ORIGIN  # server

    # Ask for reset
    sensor1.reset()
    assert (
        sensor1._sensor_template.irradiance_sensor_template.dimensions.x_start
        == sensor_parameter.dimensions.x_start
    )  # local
    assert (
        sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_start
        == sensor_parameter.dimensions.x_start
    )  # server
    assert sensor1._sensor_instance.irradiance_properties.axis_system == ORIGIN  # local
    assert p.scene_link.get().sensors[0].irradiance_properties.axis_system == ORIGIN  # server

    sensor1.delete()


@pytest.mark.supported_speos_versions(min=251)
def test_irradiance_modify_after_reset(speos: Speos):
    """Test reset of irradiance sensor, and then modify."""
    p = Project(speos=speos)
    wl = WavelengthsRangeParameters()
    sensor_parameter = IrradianceSensorParameters()
    # Create + commit
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=SensorIrradiance)
    sensor1.set_type_spectral()
    sensor1.set_layer_type_sequence()
    sensor1.commit()
    assert isinstance(sensor1, SensorIrradiance)

    # Ask for reset
    sensor1.reset()

    # Modify after a reset
    # Template
    assert sensor1._sensor_template.irradiance_sensor_template.HasField("illuminance_type_planar")
    sensor1.set_illuminance_type_radial()
    assert sensor1._sensor_template.irradiance_sensor_template.HasField("illuminance_type_radial")
    # Intermediate class for type : spectral
    assert (
        sensor1._sensor_template.irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start
        == wl.start
    )
    sensor1.set_type_spectral().set_wavelengths_range().start = 500
    assert (
        sensor1._sensor_template.irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start
        == 500
    )
    # Intermediate class for dimensions
    assert (
        sensor1._sensor_template.irradiance_sensor_template.dimensions.x_start
        == sensor_parameter.dimensions.x_start
    )
    sensor1.set_dimensions().x_start = -100
    assert sensor1._sensor_template.irradiance_sensor_template.dimensions.x_start == -100

    # Props
    assert sensor1._sensor_instance.irradiance_properties.axis_system == ORIGIN
    sensor1.axis_system = [50, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sensor1._sensor_instance.irradiance_properties.axis_system == [
        50,
        20,
        10,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    # Intermediate class for layer type
    layer_parameters = LayerBySequenceParameters()
    assert (
        sensor1._sensor_instance.irradiance_properties.layer_type_sequence.maximum_nb_of_sequence
        == layer_parameters.maximum_nb_of_sequence
    )
    sensor1.set_layer_type_sequence().maximum_nb_of_sequence = 15
    assert (
        sensor1._sensor_instance.irradiance_properties.layer_type_sequence.maximum_nb_of_sequence
        == 15
    )

    sensor1.delete()


@pytest.mark.supported_speos_versions(min=251)
def test_radiance_modify_after_reset(speos: Speos):
    """Test reset of radiance sensor, and then modify."""
    p = Project(speos=speos)
    sensor_parameter = RadianceSensorParameters()
    wl = WavelengthsRangeParameters()
    # Create + commit
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=SensorRadiance)
    assert isinstance(sensor1, SensorRadiance)
    sensor1.set_type_colorimetric()
    sensor1.set_layer_type_sequence()
    sensor1.commit()

    # Ask for reset
    sensor1.reset()

    # Modify after a reset
    # Template
    assert sensor1._sensor_template.radiance_sensor_template.focal == sensor_parameter.focal_length
    sensor1.focal = 100
    assert sensor1._sensor_template.radiance_sensor_template.focal == 100
    # Intermediate class for type : colorimetric
    assert (
        sensor1._sensor_template.radiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_start
        == wl.start
    )
    sensor1.set_type_colorimetric().set_wavelengths_range().start = 500
    assert (
        sensor1._sensor_template.radiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_start
        == 500
    )
    assert (
        sensor1._sensor_template.radiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_end
        == wl.end
    )
    sensor1.set_type_colorimetric().set_wavelengths_range().start = 500
    assert (
        sensor1._sensor_template.radiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_start
        == 500
    )
    # Intermediate class for dimensions
    assert (
        sensor1._sensor_template.radiance_sensor_template.dimensions.x_start
        == sensor_parameter.dimensions.x_start
    )
    sensor1.set_dimensions().x_start = -100
    assert sensor1._sensor_template.radiance_sensor_template.dimensions.x_start == -100
    assert sensor1.set_dimensions().x_start == -100

    assert (
        sensor1._sensor_template.radiance_sensor_template.dimensions.x_end
        == sensor_parameter.dimensions.x_end
    )
    sensor1.set_dimensions().x_end = 100
    assert sensor1._sensor_template.radiance_sensor_template.dimensions.x_end == 100
    assert sensor1.set_dimensions().x_end == 100

    assert (
        sensor1._sensor_template.radiance_sensor_template.dimensions.y_start
        == sensor_parameter.dimensions.y_start
    )
    sensor1.set_dimensions().y_start = -100
    assert sensor1._sensor_template.radiance_sensor_template.dimensions.y_start == -100
    assert sensor1.set_dimensions().y_start == -100

    assert (
        sensor1._sensor_template.radiance_sensor_template.dimensions.y_end
        == sensor_parameter.dimensions.y_end
    )
    sensor1.set_dimensions().y_end = 100
    assert sensor1._sensor_template.radiance_sensor_template.dimensions.y_end == 100
    assert sensor1.set_dimensions().y_end == 100

    ## Props
    assert sensor1._sensor_instance.radiance_properties.axis_system == ORIGIN
    sensor1.axis_system = [50, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sensor1._sensor_instance.radiance_properties.axis_system == [
        50,
        20,
        10,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    # Intermediate class for layer type
    layer_parameters = LayerBySequenceParameters()
    assert (
        sensor1._sensor_instance.radiance_properties.layer_type_sequence.maximum_nb_of_sequence
        == layer_parameters.maximum_nb_of_sequence
    )
    sensor1.set_layer_type_sequence().maximum_nb_of_sequence = 15
    assert (
        sensor1._sensor_instance.radiance_properties.layer_type_sequence.maximum_nb_of_sequence
        == 15
    )

    sensor1.delete()


@pytest.mark.supported_speos_versions(min=251)
def test_camera_modify_after_reset(speos: Speos):
    """Test reset of camera sensor, and then modify."""
    p = Project(speos=speos)
    sensor_parameter = CameraSensorParameters()
    # Create + commit
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=SensorCamera)
    assert isinstance(sensor1, SensorCamera)
    color = sensor1.set_mode_photometric().set_mode_color()
    color.set_balance_mode_user_white()
    color.red_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityRed.spectrum"
    )
    color.green_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityGreen.spectrum"
    )
    color.blue_spectrum_file_uri = str(
        Path(test_path) / "CameraInputFiles" / "CameraSensitivityBlue.spectrum"
    )
    sensor1.set_mode_photometric().set_layer_type_source()
    sensor1.commit()

    # Ask for reset
    sensor1.reset()

    # Modify after a reset
    # Template
    assert (
        sensor1._sensor_template.camera_sensor_template.focal_length
        == sensor_parameter.focal_length
    )
    sensor1.focal_length = 40
    assert sensor1._sensor_template.camera_sensor_template.focal_length == 40
    # Intermediate class for mode : photometric + wavelengths
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_start
        == sensor_parameter.sensor_type_parameters.wavelength_range.start
    )
    sensor1.set_mode_photometric().set_wavelengths_range().start = 500
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_start
        == 500
    )
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_end
        == sensor_parameter.sensor_type_parameters.wavelength_range.end
    )
    sensor1.set_mode_photometric().set_wavelengths_range().end = 800
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_end
        == 800
    )
    # Intermediate class for color mode + balance mode
    user_white = BalanceModeUserWhiteParameters()
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain
        == user_white.blue_gain
    )
    color = sensor1.set_mode_photometric().set_mode_color()
    white_mode = color.set_balance_mode_user_white()
    white_mode.blue_gain = 0.5
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain
        == 0.5
    )

    # Props
    assert sensor1._sensor_instance.camera_properties.axis_system == sensor_parameter.axis_system
    sensor1.axis_system = [50, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sensor1._sensor_instance.camera_properties.axis_system == [
        50,
        20,
        10,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]

    sensor1.delete()


@pytest.mark.supported_speos_versions(min=252)
def test_xmpintensity_modify_after_reset(speos: Speos):
    """Test reset of intensity sensor, and then modify."""
    p = Project(speos=speos)

    # Create + commit
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=SensorXMPIntensity)
    sensor1.set_layer_type_sequence()
    sensor1.set_type_spectral()
    sensor1.commit()
    assert isinstance(sensor1, SensorXMPIntensity)

    # Ask for reset
    sensor1.reset()

    # Modify after a reset
    # Template
    assert sensor1._sensor_template.intensity_sensor_template.HasField(
        "intensity_orientation_x_as_meridian"
    )
    sensor1.set_orientation_x_as_parallel()
    assert sensor1._sensor_template.intensity_sensor_template.HasField(
        "intensity_orientation_x_as_parallel"
    )
    # Intermediate class for type : spectral
    assert (
        sensor1._sensor_template.intensity_sensor_template.sensor_type_spectral.wavelengths_range.w_start
        == 400
    )
    sensor1.set_type_spectral().set_wavelengths_range().start = 500
    assert (
        sensor1._sensor_template.intensity_sensor_template.sensor_type_spectral.wavelengths_range.w_start
        == 500
    )
    # Intermediate class for dimensions
    assert (
        sensor1._sensor_template.intensity_sensor_template.intensity_orientation_x_as_parallel.intensity_dimensions.x_start
        == -30
    )
    sensor1.x_start = -31
    assert (
        sensor1._sensor_template.intensity_sensor_template.intensity_orientation_x_as_parallel.intensity_dimensions.x_start
        == -31
    )

    # Props
    assert sensor1._sensor_instance.intensity_properties.axis_system == [
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    sensor1.axis_system = [50, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sensor1._sensor_instance.intensity_properties.axis_system == [
        50,
        20,
        10,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    # Intermediate class for layer type
    assert (
        sensor1._sensor_instance.intensity_properties.layer_type_sequence.maximum_nb_of_sequence
        == 10
    )
    sensor1.set_layer_type_sequence().maximum_nb_of_sequence = 15
    assert (
        sensor1._sensor_instance.intensity_properties.layer_type_sequence.maximum_nb_of_sequence
        == 15
    )

    sensor1.delete()


def test_delete_sensor(speos: Speos):
    """Test delete of sensor."""
    p = Project(speos=speos)

    # Create + commit
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=SensorIrradiance)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().HasField("irradiance_sensor_template")
    assert sensor1._sensor_template.HasField("irradiance_sensor_template")  # local
    assert len(p.scene_link.get().sensors) == 1
    assert p.scene_link.get().sensors[0].HasField("irradiance_properties")
    assert sensor1._sensor_instance.HasField("irradiance_properties")  # local

    # Delete
    sensor1.delete()
    assert sensor1._unique_id is None
    assert len(sensor1._sensor_instance.metadata) == 0

    assert sensor1.sensor_template_link is None
    assert sensor1._sensor_template.HasField("irradiance_sensor_template")  # local

    assert len(p.scene_link.get().sensors) == 0
    assert sensor1._sensor_instance.HasField("irradiance_properties")  # local


def test_get_sensor(speos: Speos, capsys: pytest.CaptureFixture[str]):
    """Test get of a sensor."""
    p = Project(speos=speos)
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=SensorIrradiance)
    sensor2 = p.create_sensor(name="Sensor.2", feature_type=SensorRadiance)
    sensor3 = p.create_sensor(name="Sensor.3", feature_type=SensorCamera)
    sensor4 = p.create_sensor(name="Sensor.4", feature_type=SensorXMPIntensity)
    # test when key exists
    name1 = sensor1.get(key="name")
    assert name1 == "Sensor.1"
    property_info = sensor2.get(key="integration_angle")
    assert property_info is not None
    property_info = sensor3.get(key="axis_system")
    assert property_info is not None
    property_info = sensor4.get(key="name")
    assert property_info is not None

    # test when key does not exist
    get_result1 = sensor1.get(key="geometry")
    stdout, stderr = capsys.readouterr()
    assert get_result1 is None
    assert "Used key: geometry not found in key list" in stdout
    get_result2 = sensor2.get(key="geometry")
    stdout, stderr = capsys.readouterr()
    assert get_result2 is None
    assert "Used key: geometry not found in key list" in stdout
    get_result3 = sensor3.get(key="geometry")
    stdout, stderr = capsys.readouterr()
    assert get_result3 is None
    assert "Used key: geometry not found in key list" in stdout
    get_result4 = sensor4.get(key="geometry")
    stdout, stderr = capsys.readouterr()
    assert get_result4 is None
    assert "Used key: geometry not found in key list" in stdout


@pytest.mark.supported_speos_versions(min=252)
def test_create_by_parameters(speos: Speos):
    """Test creating sensor with new parameter class."""
    p = Project(speos=speos)
    wavelength_params = WavelengthsRangeParameters(start=380, end=780, sampling=21)
    spectral_params = SpectralParameters(wavelength_range=wavelength_params)
    colorimetric_params = ColorimetricParameters(wavelength_range=wavelength_params)
    dim_params = DimensionsParameters(
        x_start=-10, x_end=10, x_sampling=20, y_start=-20, y_end=20, y_sampling=40
    )
    int_dim_params_con = IntensitySensorDimensionsConoscopic(theta_max=25, theta_sampling=50)
    int_dim_params_para = IntensitySensorDimensionsXAsParallel(
        x_start=-10, x_end=10, x_sampling=20, y_start=-20, y_end=20, y_sampling=40
    )
    int_dim_params_meridian = IntensitySensorDimensionsXAsMeridian(
        x_start=-10, x_end=10, x_sampling=20, y_start=-20, y_end=20, y_sampling=40
    )
    near_field = NearfieldParameters(cell_diameter=1, cell_distance=10)
    layer_seq = LayerBySequenceParameters(
        maximum_nb_of_sequence=5, sequence_type=SequenceTypes.by_geometry
    )
    # intensity
    int_sensor_params = [
        IntensityXMPSensorParameters(
            dimensions=int_dim_params_con,
            axis_system=[0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=SensorTypes.photometric,
            orientation=IntensitySensorOrientationTypes.conoscopic,
            viewing_direction=IntensitySensorViewingTypes.from_source,
            layer_type=LayerTypes.none,
            near_field_parameters=near_field,
        ),
        IntensityXMPSensorParameters(
            dimensions=int_dim_params_para,
            axis_system=[1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=colorimetric_params,
            orientation=IntensitySensorOrientationTypes.x_as_parallel,
            viewing_direction=IntensitySensorViewingTypes.from_sensor,
            layer_type=LayerTypes.by_source,
        ),
        IntensityXMPSensorParameters(
            dimensions=int_dim_params_meridian,
            axis_system=[2, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=SensorTypes.radiometric,
            orientation=IntensitySensorOrientationTypes.x_as_meridian,
            viewing_direction=IntensitySensorViewingTypes.from_source,
            layer_type=layer_seq,
        ),
        IntensityXMPSensorParameters(
            dimensions=int_dim_params_con,
            axis_system=[3, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=spectral_params,
            orientation=IntensitySensorOrientationTypes.conoscopic,
            viewing_direction=IntensitySensorViewingTypes.from_source,
            layer_type=LayerByFaceParameters(),
        ),
    ]

    for i, para in enumerate(int_sensor_params):
        s = p.create_sensor(f"IntSensor.{i}", feature_type=SensorXMPIntensity, parameters=para)
        if i != 3:
            s.commit()
        assert s.axis_system == para.axis_system
        if isinstance(para.sensor_type, ColorimetricParameters):
            assert s.type.lower() == "colorimetric"
            assert (
                s.colorimetric.set_wavelengths_range().start
                == colorimetric_params.wavelength_range.start
            )
        elif isinstance(para.sensor_type, SpectralParameters):
            assert s.type.lower() == "spectral"
            assert (
                s.spectral.set_wavelengths_range().start == spectral_params.wavelength_range.start
            )
        else:
            assert s.type.lower() == para.sensor_type

    rad_sensor_params = [
        RadianceSensorParameters(
            dimensions=dim_params,
            axis_system=[0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=SensorTypes.photometric,
            layer_type=LayerTypes.none,
            observer=[0, 20, 20],
        ),
        RadianceSensorParameters(
            dimensions=dim_params,
            axis_system=[1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=colorimetric_params,
            layer_type=LayerTypes.by_source,
            focal_length=200,
        ),
        RadianceSensorParameters(
            dimensions=dim_params,
            axis_system=[2, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=SensorTypes.radiometric,
            layer_type=layer_seq,
            integration_angle=10,
        ),
        RadianceSensorParameters(
            dimensions=dim_params,
            axis_system=[3, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=spectral_params,
            layer_type=LayerByFaceParameters(),
        ),
    ]
    for i, para in enumerate(rad_sensor_params):
        s = p.create_sensor(f"RadSensor.{i}", feature_type=SensorRadiance, parameters=para)
        if i != 3:
            s.commit()
        assert s.axis_system == para.axis_system
        assert s.focal == para.focal_length
        assert s.observer_point == [] if para.observer is None else para.observer
        assert s.integration_angle == para.integration_angle
        assert s.dimensions.x_start == para.dimensions.x_start
        assert s.dimensions.y_start == para.dimensions.y_start
        assert s.dimensions.x_end == para.dimensions.x_end
        assert s.dimensions.y_end == para.dimensions.y_end
        assert s.dimensions.y_sampling == para.dimensions.y_sampling
        assert s.dimensions.x_sampling == para.dimensions.x_sampling
        if isinstance(para.sensor_type, ColorimetricParameters):
            assert s.type.lower() == "colorimetric"
            assert (
                s.colorimetric.set_wavelengths_range().start
                == colorimetric_params.wavelength_range.start
            )
        elif isinstance(para.sensor_type, SpectralParameters):
            assert s.type.lower() == "spectral"
            assert (
                s.spectral.set_wavelengths_range().start == spectral_params.wavelength_range.start
            )
        else:
            assert s.type.lower() == para.sensor_type

    irr_sensor_params = [
        IrradianceSensorParameters(
            dimensions=dim_params,
            axis_system=[0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=SensorTypes.photometric,
            layer_type=LayerByIncidenceAngleParameters(25),
            integration_type=IntegrationTypes.radial,
            rayfile_type=RayfileTypes.tm25_no_polarization,
        ),
        IrradianceSensorParameters(
            dimensions=dim_params,
            axis_system=[1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=colorimetric_params,
            layer_type=LayerTypes.by_source,
            integration_type=IntegrationTypes.semi_cylindrical,
            rayfile_type=RayfileTypes.tm25,
            integration_direction=[np.sqrt(2) / 2, np.sqrt(2) / 2, 0],
        ),
        IrradianceSensorParameters(
            dimensions=dim_params,
            axis_system=[2, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=SensorTypes.radiometric,
            layer_type=layer_seq,
            integration_type=IntegrationTypes.cylindrical,
            rayfile_type=RayfileTypes.classic,
        ),
        IrradianceSensorParameters(
            dimensions=dim_params,
            axis_system=[3, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            sensor_type=spectral_params,
            layer_type=LayerByFaceParameters(),
            integration_type=IntegrationTypes.planar,
            rayfile_type=RayfileTypes.polarization,
            integration_direction=[np.sqrt(2) / 2, np.sqrt(2) / 2, 0],
        ),
    ]
    for i, para in enumerate(irr_sensor_params):
        s = p.create_sensor(f"IrrSensor.{i}", feature_type=SensorIrradiance, parameters=para)
        if i != 3:
            s.commit()
        assert isinstance(s, SensorIrradiance)
        assert s.axis_system == para.axis_system
        assert (
            s.integration_direction == []
            if para.integration_direction is None
            else para.integration_direction
        )
        assert s.dimensions.x_start == para.dimensions.x_start
        assert s.dimensions.y_start == para.dimensions.y_start
        assert s.dimensions.x_end == para.dimensions.x_end
        assert s.dimensions.y_end == para.dimensions.y_end
        assert s.dimensions.y_sampling == para.dimensions.y_sampling
        assert s.dimensions.x_sampling == para.dimensions.x_sampling
        match para.rayfile_type:
            case RayfileTypes.none:
                assert (
                    s._sensor_instance.irradiance_properties.ray_file_type
                    == s._sensor_instance.EnumRayFileType.RayFileNone
                )
            case RayfileTypes.classic:
                assert (
                    s._sensor_instance.irradiance_properties.ray_file_type
                    == s._sensor_instance.EnumRayFileType.RayFileClassic
                )
            case RayfileTypes.polarization:
                assert (
                    s._sensor_instance.irradiance_properties.ray_file_type
                    == s._sensor_instance.EnumRayFileType.RayFilePolarization
                )
            case RayfileTypes.tm25:
                assert (
                    s._sensor_instance.irradiance_properties.ray_file_type
                    == s._sensor_instance.EnumRayFileType.RayFileTM25
                )
            case RayfileTypes.tm25_no_polarization:
                assert (
                    s._sensor_instance.irradiance_properties.ray_file_type
                    == s._sensor_instance.EnumRayFileType.RayFileTM25NoPolarization
                )
        if isinstance(para.sensor_type, ColorimetricParameters):
            assert s.type.lower() == "colorimetric"
            assert (
                s.colorimetric.set_wavelengths_range().start
                == colorimetric_params.wavelength_range.start
            )
        elif isinstance(para.sensor_type, SpectralParameters):
            assert s.type.lower() == "spectral"
            assert (
                s.spectral.set_wavelengths_range().start == spectral_params.wavelength_range.start
            )
        else:
            assert s.type.lower() == para.sensor_type
    irr3d_sensor_params = [
        Irradiance3DSensorParameters(
            sensor_type=SensorTypes.photometric,
            layer_type=LayerTypes.none,
            integration_type=IntegrationTypes.radial,
            rayfile_type=RayfileTypes.tm25_no_polarization,
        ),
        Irradiance3DSensorParameters(
            sensor_type=colorimetric_params,
            layer_type=LayerTypes.by_source,
            integration_type=IntegrationTypes.planar,
            rayfile_type=RayfileTypes.tm25,
        ),
        Irradiance3DSensorParameters(
            sensor_type=SensorTypes.radiometric,
            integration_type=IntegrationTypes.planar,
            rayfile_type=RayfileTypes.classic,
            measures=MeasuresParameters(False, False, True),
        ),
        Irradiance3DSensorParameters(
            integration_type=IntegrationTypes.planar,
            rayfile_type=RayfileTypes.polarization,
            measures=MeasuresParameters(True, True, True),
        ),
        Irradiance3DSensorParameters(
            sensor_type=SensorTypes.radiometric,
            integration_type=IntegrationTypes.radial,
            rayfile_type=RayfileTypes.classic,
        ),
    ]
    for i, para in enumerate(irr3d_sensor_params):
        s = p.create_sensor(f"Irr3DSensor.{i}", feature_type=Sensor3DIrradiance, parameters=para)
        assert isinstance(s, Sensor3DIrradiance)
        match para.rayfile_type:
            case RayfileTypes.none:
                assert (
                    s._sensor_instance.irradiance_3d_properties.ray_file_type
                    == s._sensor_instance.EnumRayFileType.RayFileNone
                )
            case RayfileTypes.classic:
                assert (
                    s._sensor_instance.irradiance_3d_properties.ray_file_type
                    == s._sensor_instance.EnumRayFileType.RayFileClassic
                )
            case RayfileTypes.polarization:
                assert (
                    s._sensor_instance.irradiance_3d_properties.ray_file_type
                    == s._sensor_instance.EnumRayFileType.RayFilePolarization
                )
            case RayfileTypes.tm25:
                assert (
                    s._sensor_instance.irradiance_3d_properties.ray_file_type
                    == s._sensor_instance.EnumRayFileType.RayFileTM25
                )
            case RayfileTypes.tm25_no_polarization:
                assert (
                    s._sensor_instance.irradiance_3d_properties.ray_file_type
                    == s._sensor_instance.EnumRayFileType.RayFileTM25NoPolarization
                )
        if isinstance(para.sensor_type, ColorimetricParameters):
            assert s.type.lower() == "colorimetric"
            assert isinstance(s.colorimetric, Sensor3DIrradiance.Colorimetric)
            assert (
                s.colorimetric.set_wavelengths_range().start
                == colorimetric_params.wavelength_range.start
            )
        elif para.sensor_type == SensorTypes.photometric:
            assert s.type.lower() == SensorTypes.photometric
            assert isinstance(s.photometric, Sensor3DIrradiance.Photometric)
            if para.integration_type == IntegrationTypes.planar:
                assert isinstance(s.photometric._integration_type, Sensor3DIrradiance.Measures)
                assert s.photometric._integration_type.reflection == para.measures.reflection
                assert s.photometric._integration_type.transmission == para.measures.transmission
                assert s.photometric._integration_type.absorption == para.measures.absorption
            elif para.integration_type == IntegrationTypes.radial:
                assert s.set_type_photometric()._integration_type.lower() == para.integration_type
        elif para.sensor_type == SensorTypes.radiometric:
            assert isinstance(s._type, Sensor3DIrradiance.Radiometric)
            assert s.type.lower() == SensorTypes.radiometric
            if para.integration_type == IntegrationTypes.planar:
                assert isinstance(
                    s.set_type_radiometric()._integration_type, Sensor3DIrradiance.Measures
                )
                assert (
                    s.set_type_radiometric()._integration_type.reflection
                    == para.measures.reflection
                )
                assert (
                    s.set_type_radiometric()._integration_type.transmission
                    == para.measures.transmission
                )
                assert (
                    s.set_type_radiometric()._integration_type.absorption
                    == para.measures.absorption
                )
            elif para.integration_type == IntegrationTypes.radial:
                assert s.set_type_radiometric()._integration_type.lower() == para.integration_type
