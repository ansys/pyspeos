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

"""Test basic using sensor."""

import math
from pathlib import Path

from ansys.api.speos.sensor.v1 import camera_sensor_pb2
from ansys.speos.core import Body, GeoRef, Project, Speos, sensor
from ansys.speos.core.generic.constants import ORIGIN, SENSOR
from ansys.speos.core.sensor import (
    Sensor3DIrradiance,
    SensorCamera,
    SensorIrradiance,
    SensorRadiance,
)
from ansys.speos.core.simulation import SimulationDirect
from tests.conftest import test_path


def test_create_camera_sensor(speos: Speos):
    """Test creation of camera sensor."""
    p = Project(speos=speos)

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
    assert camera_sensor_template.focal_length == SENSOR.CAMERASENSOR.FOCAL_LENGTH
    assert camera_sensor_template.imager_distance == SENSOR.CAMERASENSOR.IMAGER_DISTANCE
    assert camera_sensor_template.distortion_file_uri == ""
    assert camera_sensor_template.f_number == SENSOR.CAMERASENSOR.F_NUMBER
    assert camera_sensor_template.horz_pixel == SENSOR.CAMERASENSOR.HORZ_PIXEL
    assert camera_sensor_template.vert_pixel == SENSOR.CAMERASENSOR.VERT_PIXEL
    assert camera_sensor_template.width == SENSOR.CAMERASENSOR.WIDTH
    assert camera_sensor_template.height == SENSOR.CAMERASENSOR.HEIGHT
    assert camera_sensor_template.HasField("sensor_mode_photometric")
    mode_photometric = camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.acquisition_integration == SENSOR.CAMERASENSOR.ACQUISITION_INTEGRATION
    assert mode_photometric.acquisition_lag_time == SENSOR.CAMERASENSOR.ACQUISITION_LAG_TIME
    assert mode_photometric.transmittance_file_uri == ""
    assert math.isclose(
        a=mode_photometric.gamma_correction,
        b=SENSOR.CAMERASENSOR.GAMMA_CORRECTION,
        rel_tol=1.192092896e-07,
    )
    assert mode_photometric.png_bits == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
    assert mode_photometric.HasField("wavelengths_range")
    assert mode_photometric.wavelengths_range.w_start == SENSOR.WAVELENGTHSRANGE.START
    assert mode_photometric.wavelengths_range.w_end == SENSOR.WAVELENGTHSRANGE.END
    assert mode_photometric.wavelengths_range.w_sampling == SENSOR.WAVELENGTHSRANGE.SAMPLING
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
    assert sensor1._sensor_instance.camera_properties.axis_system == ORIGIN
    assert sensor1._sensor_instance.camera_properties.trajectory_file_uri == ""
    assert sensor1.set_mode_photometric().trajectory_file_uri == ""
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
    assert (
        mode_photometric.color_mode_color.balance_mode_userwhite.red_gain
        == SENSOR.CAMERASENSOR.GAIN
    )
    assert (
        mode_photometric.color_mode_color.balance_mode_userwhite.green_gain
        == SENSOR.CAMERASENSOR.GAIN
    )
    assert (
        mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain
        == SENSOR.CAMERASENSOR.GAIN
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

    # Default value
    sensor1 = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("irradiance_sensor_template")
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("sensor_type_photometric")
    assert sensor_template.HasField("illuminance_type_planar")
    assert sensor_template.HasField("dimensions")
    assert sensor_template.dimensions.x_start == SENSOR.DIMENSIONS.X_START
    assert sensor_template.dimensions.x_end == SENSOR.DIMENSIONS.X_END
    assert sensor_template.dimensions.x_sampling == SENSOR.DIMENSIONS.X_SAMPLING
    assert sensor_template.dimensions.y_start == SENSOR.DIMENSIONS.Y_START
    assert sensor_template.dimensions.y_end == SENSOR.DIMENSIONS.Y_END
    assert sensor_template.dimensions.y_sampling == SENSOR.DIMENSIONS.Y_SAMPLING
    assert sensor1._sensor_instance.HasField("irradiance_properties")
    irra_properties = sensor1._sensor_instance.irradiance_properties
    assert irra_properties.axis_system == ORIGIN
    assert irra_properties.HasField("layer_type_none")
    assert irra_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFileNone
    assert irra_properties.integration_direction == []

    # sensor_type_colorimetric
    # default wavelengths range
    sensor1.set_type_colorimetric()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("sensor_type_colorimetric")
    assert sensor_template.sensor_type_colorimetric.HasField("wavelengths_range")
    assert (
        sensor_template.sensor_type_colorimetric.wavelengths_range.w_start
        == SENSOR.WAVELENGTHSRANGE.START
    )
    assert (
        sensor_template.sensor_type_colorimetric.wavelengths_range.w_end
        == SENSOR.WAVELENGTHSRANGE.END
    )
    assert (
        sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling
        == SENSOR.WAVELENGTHSRANGE.SAMPLING
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

    # sensor_type_spectral
    # default wavelengths range
    sensor1.set_type_spectral()
    sensor1.commit()
    sensor_template = sensor1.sensor_template_link.get().irradiance_sensor_template
    assert sensor_template.HasField("sensor_type_spectral")
    assert sensor_template.sensor_type_spectral.HasField("wavelengths_range")
    assert (
        sensor_template.sensor_type_spectral.wavelengths_range.w_start
        == SENSOR.WAVELENGTHSRANGE.START
    )
    assert (
        sensor_template.sensor_type_spectral.wavelengths_range.w_end == SENSOR.WAVELENGTHSRANGE.END
    )
    assert (
        sensor_template.sensor_type_spectral.wavelengths_range.w_sampling
        == SENSOR.WAVELENGTHSRANGE.SAMPLING
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

    # Default value
    sensor1 = p.create_sensor(name="Radiance.1", feature_type=SensorRadiance)
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("radiance_sensor_template")
    assert sensor1.sensor_template_link.get().name == "Radiance.1"
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField(
        "sensor_type_photometric"
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.focal
        == SENSOR.RADIANCESENSOR.FOCAL_LENGTH
    )
    assert sensor1.focal == SENSOR.RADIANCESENSOR.FOCAL_LENGTH
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.integration_angle
        == SENSOR.RADIANCESENSOR.INTEGRATION_ANGLE
    )
    assert sensor1.integration_angle == SENSOR.RADIANCESENSOR.INTEGRATION_ANGLE
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField("dimensions")
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.x_start
        == SENSOR.DIMENSIONS.X_START
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.x_end
        == SENSOR.DIMENSIONS.X_END
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.x_sampling
        == SENSOR.DIMENSIONS.X_SAMPLING
    )
    assert sensor1.set_dimensions().x_sampling == SENSOR.DIMENSIONS.X_SAMPLING
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.y_start
        == SENSOR.DIMENSIONS.Y_START
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.y_end
        == SENSOR.DIMENSIONS.Y_END
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.y_sampling
        == SENSOR.DIMENSIONS.Y_SAMPLING
    )
    assert sensor1.set_dimensions().y_sampling == SENSOR.DIMENSIONS.Y_SAMPLING
    assert sensor1._sensor_instance.HasField("radiance_properties")
    radiance_properties = sensor1._sensor_instance.radiance_properties
    assert radiance_properties.axis_system == ORIGIN
    assert radiance_properties.HasField("layer_type_none")
    assert radiance_properties.observer_point == []

    # sensor_type_radiometric
    sensor1.set_type_radiometric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField(
        "sensor_type_radiometric"
    )

    # sensor_type_spectral
    # default wavelengths range
    sensor1.set_type_spectral()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField(
        "sensor_type_spectral"
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.HasField(
            "wavelengths_range"
        )
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start
        == SENSOR.WAVELENGTHSRANGE.START
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_end
        == SENSOR.WAVELENGTHSRANGE.END
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_sampling
        == SENSOR.WAVELENGTHSRANGE.SAMPLING
    )
    # chosen wavelengths range
    wavelengths_range = sensor1.set_type_spectral().set_wavelengths_range()
    wavelengths_range.start = 450
    wavelengths_range.end = 800
    wavelengths_range.sampling = 15
    sensor1.commit()
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start
        == 450
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_end
        == 800
    )
    assert (
        sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_sampling
        == 15
    )

    # sensor_type_photometric
    sensor1.set_type_photometric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField(
        "sensor_type_photometric"
    )

    # focal
    sensor1.focal = 150.5
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.focal == 150.5

    # integration_angle
    sensor1.integration_angle = 4.5
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.integration_angle == 4.5

    # dimensions
    sensor1.dimensions.x_start = -10
    sensor1.dimensions.x_end = 10
    sensor1.dimensions.x_sampling = 60
    sensor1.dimensions.y_start = -20
    sensor1.dimensions.y_end = 20
    sensor1.dimensions.y_sampling = 120
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField("dimensions")
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.x_start == -10.0
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.x_end == 10.0
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.x_sampling == 60
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.y_start == -20.0
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.y_end == 20.0
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.y_sampling == 120

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
    sensor1.set_layer_type_face().set_sca_filtering_mode_intersected_one_time().set_layers(
        values=[
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
    )
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


def test_load_3d_irradiance_sensor(speos: Speos):
    """Test load of 3d irradiance sensor."""
    p = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism_3D.speos"),
    )
    sensor_3d = p.find(name=".*", name_regex=True, feature_type=Sensor3DIrradiance)[0]
    assert sensor_3d is not None


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
    # wavelength start 400 with end 700
    # layer type none
    sensor_3d.set_type_colorimetric()
    sensor_3d.commit()
    assert sensor_3d.sensor_template_link.get().irradiance_3d.HasField("type_colorimetric")
    colorimetric_info = sensor_3d.sensor_template_link.get().irradiance_3d.type_colorimetric
    assert colorimetric_info.wavelength_start == SENSOR.WAVELENGTHSRANGE.START
    assert colorimetric_info.wavelength_end == SENSOR.WAVELENGTHSRANGE.END
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
    sensor1.commit()
    assert (
        sensor1._sensor_template.irradiance_sensor_template.dimensions.x_start
        == SENSOR.DIMENSIONS.X_START
    )  # local
    assert (
        sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_start
        == SENSOR.DIMENSIONS.X_START
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
        == SENSOR.DIMENSIONS.X_START
    )  # local
    assert (
        sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_start
        == SENSOR.DIMENSIONS.X_START
    )  # server
    assert sensor1._sensor_instance.irradiance_properties.axis_system == ORIGIN  # local
    assert p.scene_link.get().sensors[0].irradiance_properties.axis_system == ORIGIN  # server

    sensor1.delete()


def test_irradiance_modify_after_reset(speos: Speos):
    """Test reset of irradiance sensor, and then modify."""
    p = Project(speos=speos)

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
        == SENSOR.WAVELENGTHSRANGE.START
    )
    sensor1.set_type_spectral().set_wavelengths_range().start = 500
    assert (
        sensor1._sensor_template.irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start
        == 500
    )
    # Intermediate class for dimensions
    assert (
        sensor1._sensor_template.irradiance_sensor_template.dimensions.x_start
        == SENSOR.DIMENSIONS.X_START
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
    assert (
        sensor1._sensor_instance.irradiance_properties.layer_type_sequence.maximum_nb_of_sequence
        == SENSOR.LAYERTYPES.MAXIMUM_NB_OF_SEQUENCE
    )
    sensor1.set_layer_type_sequence().maximum_nb_of_sequence = 15
    assert (
        sensor1._sensor_instance.irradiance_properties.layer_type_sequence.maximum_nb_of_sequence
        == 15
    )

    sensor1.delete()


def test_radiance_modify_after_reset(speos: Speos):
    """Test reset of radiance sensor, and then modify."""
    p = Project(speos=speos)

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
    assert (
        sensor1._sensor_template.radiance_sensor_template.focal
        == SENSOR.RADIANCESENSOR.FOCAL_LENGTH
    )
    sensor1.focal = 100
    assert sensor1._sensor_template.radiance_sensor_template.focal == 100
    # Intermediate class for type : colorimetric
    assert (
        sensor1._sensor_template.radiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_start
        == SENSOR.WAVELENGTHSRANGE.START
    )
    sensor1.set_type_colorimetric().set_wavelengths_range().start = 500
    assert (
        sensor1._sensor_template.radiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_start
        == 500
    )
    assert (
        sensor1._sensor_template.radiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_end
        == SENSOR.WAVELENGTHSRANGE.END
    )
    sensor1.set_type_colorimetric().set_wavelengths_range().start = 500
    assert (
        sensor1._sensor_template.radiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_start
        == 500
    )
    # Intermediate class for dimensions
    assert (
        sensor1._sensor_template.radiance_sensor_template.dimensions.x_start
        == SENSOR.DIMENSIONS.X_START
    )
    sensor1.set_dimensions().x_start = -100
    assert sensor1._sensor_template.radiance_sensor_template.dimensions.x_start == -100
    assert sensor1.set_dimensions().x_start == -100

    assert (
        sensor1._sensor_template.radiance_sensor_template.dimensions.x_end
        == SENSOR.DIMENSIONS.X_END
    )
    sensor1.set_dimensions().x_end = 100
    assert sensor1._sensor_template.radiance_sensor_template.dimensions.x_end == 100
    assert sensor1.set_dimensions().x_end == 100

    assert (
        sensor1._sensor_template.radiance_sensor_template.dimensions.y_start
        == SENSOR.DIMENSIONS.Y_START
    )
    sensor1.set_dimensions().y_start = -100
    assert sensor1._sensor_template.radiance_sensor_template.dimensions.y_start == -100
    assert sensor1.set_dimensions().y_start == -100

    assert (
        sensor1._sensor_template.radiance_sensor_template.dimensions.y_end
        == SENSOR.DIMENSIONS.Y_END
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
    assert (
        sensor1._sensor_instance.radiance_properties.layer_type_sequence.maximum_nb_of_sequence
        == SENSOR.LAYERTYPES.MAXIMUM_NB_OF_SEQUENCE
    )
    sensor1.set_layer_type_sequence().maximum_nb_of_sequence = 15
    assert (
        sensor1._sensor_instance.radiance_properties.layer_type_sequence.maximum_nb_of_sequence
        == 15
    )

    sensor1.delete()


def test_camera_modify_after_reset(speos: Speos):
    """Test reset of camera sensor, and then modify."""
    p = Project(speos=speos)

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
        == SENSOR.CAMERASENSOR.FOCAL_LENGTH
    )
    sensor1.focal_length = 40
    assert sensor1._sensor_template.camera_sensor_template.focal_length == 40
    # Intermediate class for mode : photometric + wavelengths
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_start
        == SENSOR.WAVELENGTHSRANGE.START
    )
    sensor1.set_mode_photometric().set_wavelengths_range().start = 500
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_start
        == 500
    )
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_end
        == SENSOR.WAVELENGTHSRANGE.END
    )
    sensor1.set_mode_photometric().set_wavelengths_range().end = 800
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_end
        == 800
    )
    # Intermediate class for color mode + balance mode
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain
        == SENSOR.CAMERASENSOR.GAIN
    )
    color = sensor1.set_mode_photometric().set_mode_color()
    white_mode = color.set_balance_mode_user_white()
    white_mode.blue_gain = 0.5
    assert (
        sensor1._sensor_template.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain
        == 0.5
    )

    # Props
    assert sensor1._sensor_instance.camera_properties.axis_system == ORIGIN
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


def test_get_sensor(speos: Speos, capsys):
    """Test get of a sensor."""
    p = Project(speos=speos)
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=SensorIrradiance)
    sensor2 = p.create_sensor(name="Sensor.2", feature_type=SensorRadiance)
    sensor3 = p.create_sensor(name="Sensor.3", feature_type=SensorCamera)
    # test when key exists
    name1 = sensor1.get(key="name")
    assert name1 == "Sensor.1"
    property_info = sensor2.get(key="integration_angle")
    assert property_info is not None
    property_info = sensor3.get(key="axis_system")
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
