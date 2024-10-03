# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

"""
Test basic using sensor from script layer.
"""

import math
import os

from ansys.api.speos.sensor.v1 import camera_sensor_pb2

from ansys.speos.core.speos import Speos
import ansys.speos.script as script
from conftest import test_path


def test_create_camera_sensor(speos: Speos):
    """Test creation of camera sensor."""
    p = script.Project(speos=speos)

    # Default value
    sensor1 = p.create_sensor(name="Camera.1")
    sensor1.set_camera()
    sensor1.set_camera_properties()
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("camera_sensor_template")
    assert sensor1.sensor_template_link.get().camera_sensor_template.focal_length == 5.0
    assert sensor1.sensor_template_link.get().camera_sensor_template.imager_distance == 10
    assert sensor1.sensor_template_link.get().camera_sensor_template.distortion_file_uri == ""
    assert sensor1.sensor_template_link.get().camera_sensor_template.f_number == 20
    assert sensor1.sensor_template_link.get().camera_sensor_template.horz_pixel == 640
    assert sensor1.sensor_template_link.get().camera_sensor_template.vert_pixel == 480
    assert sensor1.sensor_template_link.get().camera_sensor_template.width == 5.0
    assert sensor1.sensor_template_link.get().camera_sensor_template.height == 5.0
    assert sensor1.sensor_template_link.get().camera_sensor_template.HasField("sensor_mode_photometric")
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.acquisition_integration == 0.01
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.acquisition_lag_time == 0.0
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.transmittance_file_uri == ""
    assert math.isclose(
        a=sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.gamma_correction, b=2.2, rel_tol=1.192092896e-07
    )
    assert (
        sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
    )
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.HasField("wavelengths_range")
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_start == 400
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_end == 700
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_sampling == 13
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.HasField("color_mode_color")
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.color_mode_color.red_spectrum_file_uri == ""
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.color_mode_color.green_spectrum_file_uri == ""
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.color_mode_color.blue_spectrum_file_uri == ""
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.color_mode_color.HasField("balance_mode_none")
    assert sensor1._sensor_instance.camera_properties.axis_system == [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sensor1._sensor_instance.camera_properties.trajectory_file_uri == ""
    assert sensor1._sensor_instance.camera_properties.HasField("layer_type_none")

    # focal_length
    sensor1.set_camera().set_focal_length(value=5.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.focal_length == 5.5

    # imager_distance
    sensor1.set_camera().set_imager_distance(value=10.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.imager_distance == 10.5

    # f_number
    sensor1.set_camera().set_f_number(value=20.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.f_number == 20.5

    # distortion_file_uri
    sensor1.set_camera().set_distortion_file_uri(uri=os.path.join(test_path, "CameraInputFiles", "CameraDistortion_130deg.OPTDistortion"))
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.distortion_file_uri != ""

    # horz_pixel
    sensor1.set_camera().set_horz_pixel(value=680)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.horz_pixel == 680

    # vert_pixel
    sensor1.set_camera().set_vert_pixel(value=500)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.vert_pixel == 500

    # width
    sensor1.set_camera().set_width(value=5.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.width == 5.5

    # height
    sensor1.set_camera().set_height(value=5.3)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.height == 5.3

    # sensor_mode_geometric
    sensor1.set_camera().set_mode_geometric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.HasField("sensor_mode_geometric")

    # sensor_mode_photometric
    sensor1.set_camera().set_mode_photometric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.HasField("sensor_mode_photometric")

    # acquisition_integration
    sensor1.set_camera().set_mode_photometric().set_acquisition_integration(value=0.03)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.acquisition_integration == 0.03

    # acquisition_lag_time
    sensor1.set_camera().set_mode_photometric().set_acquisition_lag_time(value=0.1)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.acquisition_lag_time == 0.1

    # transmittance_file_uri
    sensor1.set_camera().set_mode_photometric().set_transmittance_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraTransmittance.spectrum")
    )
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.transmittance_file_uri != ""

    # gamma_correction
    sensor1.set_camera().set_mode_photometric().set_gamma_correction(value=2.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.gamma_correction == 2.5

    # png_bits
    sensor1.set_camera().set_mode_photometric().set_png_bits_08()
    sensor1.commit()
    assert (
        sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_08
    )
    sensor1.set_camera().set_mode_photometric().set_png_bits_10()
    sensor1.commit()
    assert (
        sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_10
    )
    sensor1.set_camera().set_mode_photometric().set_png_bits_12()
    sensor1.commit()
    assert (
        sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_12
    )
    sensor1.set_camera().set_mode_photometric().set_png_bits_16()
    sensor1.commit()
    assert (
        sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
    )

    # color_mode_monochromatic
    sensor1.set_camera().set_mode_photometric().set_mode_monochromatic(
        spectrum_file_uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityBlue.spectrum")
    )
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.HasField("color_mode_monochromatic")
    assert mode_photometric.color_mode_monochromatic.spectrum_file_uri != ""

    # color_mode_color
    sensor1.set_camera().set_mode_photometric().set_mode_color()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.HasField("color_mode_color")

    # red_spectrum_file_uri
    sensor1.set_camera().set_mode_photometric().set_mode_color().set_red_spectrum_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityRed.spectrum")
    )
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.red_spectrum_file_uri.endswith("CameraSensitivityRed.spectrum")

    # green_spectrum_file_uri
    sensor1.set_camera().set_mode_photometric().set_mode_color().set_green_spectrum_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityGreen.spectrum")
    )
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.green_spectrum_file_uri.endswith("CameraSensitivityGreen.spectrum")

    # blue_spectrum_file_uri
    sensor1.set_camera().set_mode_photometric().set_mode_color().set_blue_spectrum_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityBlue.spectrum")
    )
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.blue_spectrum_file_uri.endswith("CameraSensitivityBlue.spectrum")

    # balance_mode_greyworld
    sensor1.set_camera().set_mode_photometric().set_mode_color().set_balance_mode_grey_world()
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_greyworld")

    # balance_mode_userwhite
    sensor1.set_camera().set_mode_photometric().set_mode_color().set_balance_mode_user_white()
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_userwhite")
    assert mode_photometric.color_mode_color.balance_mode_userwhite.red_gain == 1
    assert mode_photometric.color_mode_color.balance_mode_userwhite.green_gain == 1
    assert mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain == 1

    sensor1.set_camera().set_mode_photometric().set_mode_color().set_balance_mode_user_white().set_red_gain(value=2).set_green_gain(
        value=3
    ).set_blue_gain(value=4)
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.balance_mode_userwhite.red_gain == 2
    assert mode_photometric.color_mode_color.balance_mode_userwhite.green_gain == 3
    assert mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain == 4

    # balance_mode_display
    sensor1.set_camera().set_mode_photometric().set_mode_color().set_balance_mode_display_primaries()
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_display")
    assert mode_photometric.color_mode_color.balance_mode_display.red_display_file_uri == ""
    assert mode_photometric.color_mode_color.balance_mode_display.green_display_file_uri == ""
    assert mode_photometric.color_mode_color.balance_mode_display.blue_display_file_uri == ""

    sensor1.set_camera().set_mode_photometric().set_mode_color().set_balance_mode_display_primaries().set_red_spectrum_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityRed.spectrum")
    ).set_green_spectrum_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityGreen.spectrum")
    ).set_blue_spectrum_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityBlue.spectrum")
    )
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.balance_mode_display.red_display_file_uri.endswith("CameraSensitivityRed.spectrum")
    assert mode_photometric.color_mode_color.balance_mode_display.green_display_file_uri.endswith("CameraSensitivityGreen.spectrum")
    assert mode_photometric.color_mode_color.balance_mode_display.blue_display_file_uri.endswith("CameraSensitivityBlue.spectrum")

    # balance_mode_none
    sensor1.set_camera().set_mode_photometric().set_mode_color().set_balance_mode_none()
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_none")

    # wavelengths_range
    sensor1.set_camera().set_mode_photometric().set_wavelengths_range().set_start(value=430).set_end(value=750).set_sampling(value=15)
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.wavelengths_range.w_start == 430
    assert mode_photometric.wavelengths_range.w_end == 750
    assert mode_photometric.wavelengths_range.w_sampling == 15

    # Properties

    # axis_system
    sensor1.set_camera_properties().set_axis_system(axis_system=[10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.axis_system == [10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    # trajectory_file_uri
    sensor1.set_camera_properties().set_trajectory_file_uri(uri="TrajectoryFile")
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.trajectory_file_uri != ""

    # layer_type_source
    sensor1.set_camera_properties().set_layer_type_source()
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.HasField("layer_type_source")

    # layer_type_none
    sensor1.set_camera_properties().set_layer_type_none()
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.HasField("layer_type_none")

    sensor1.delete()
