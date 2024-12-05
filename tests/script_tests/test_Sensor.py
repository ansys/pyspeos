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
    sensor1 = p.create_sensor(name="Camera.1", feature_type=script.Camera)
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
    sensor1.set_focal_length(value=5.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.focal_length == 5.5

    # imager_distance
    sensor1.set_imager_distance(value=10.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.imager_distance == 10.5

    # f_number
    sensor1.set_f_number(value=20.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.f_number == 20.5

    # distortion_file_uri
    sensor1.set_distortion_file_uri(uri=os.path.join(test_path, "CameraInputFiles", "CameraDistortion_130deg.OPTDistortion"))
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.distortion_file_uri != ""

    # horz_pixel
    sensor1.set_horz_pixel(value=680)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.horz_pixel == 680

    # vert_pixel
    sensor1.set_vert_pixel(value=500)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.vert_pixel == 500

    # width
    sensor1.set_width(value=5.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.width == 5.5

    # height
    sensor1.set_height(value=5.3)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.height == 5.3

    # sensor_mode_geometric
    sensor1.set_mode_geometric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.HasField("sensor_mode_geometric")

    # sensor_mode_photometric
    sensor1.set_mode_photometric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.HasField("sensor_mode_photometric")

    # acquisition_integration
    sensor1.set_mode_photometric().set_acquisition_integration(value=0.03)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.acquisition_integration == 0.03

    # acquisition_lag_time
    sensor1.set_mode_photometric().set_acquisition_lag_time(value=0.1)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.acquisition_lag_time == 0.1

    # transmittance_file_uri
    sensor1.set_mode_photometric().set_transmittance_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraTransmittance.spectrum")
    )
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.transmittance_file_uri != ""

    # gamma_correction
    sensor1.set_mode_photometric().set_gamma_correction(value=2.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.gamma_correction == 2.5

    # png_bits
    sensor1.set_mode_photometric().set_png_bits_08()
    sensor1.commit()
    assert (
        sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_08
    )
    sensor1.set_mode_photometric().set_png_bits_10()
    sensor1.commit()
    assert (
        sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_10
    )
    sensor1.set_mode_photometric().set_png_bits_12()
    sensor1.commit()
    assert (
        sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_12
    )
    sensor1.set_mode_photometric().set_png_bits_16()
    sensor1.commit()
    assert (
        sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.png_bits
        == camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
    )

    # color_mode_monochromatic
    sensor1.set_mode_photometric().set_mode_monochromatic(
        spectrum_file_uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityBlue.spectrum")
    )
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.HasField("color_mode_monochromatic")
    assert mode_photometric.color_mode_monochromatic.spectrum_file_uri != ""

    # color_mode_color
    sensor1.set_mode_photometric().set_mode_color()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric.HasField("color_mode_color")

    # red_spectrum_file_uri
    sensor1.set_mode_photometric().set_mode_color().set_red_spectrum_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityRed.spectrum")
    )
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.red_spectrum_file_uri.endswith("CameraSensitivityRed.spectrum")

    # green_spectrum_file_uri
    sensor1.set_mode_photometric().set_mode_color().set_green_spectrum_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityGreen.spectrum")
    )
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.green_spectrum_file_uri.endswith("CameraSensitivityGreen.spectrum")

    # blue_spectrum_file_uri
    sensor1.set_mode_photometric().set_mode_color().set_blue_spectrum_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityBlue.spectrum")
    )
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.blue_spectrum_file_uri.endswith("CameraSensitivityBlue.spectrum")

    # balance_mode_greyworld
    sensor1.set_mode_photometric().set_mode_color().set_balance_mode_grey_world()
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_greyworld")

    # balance_mode_userwhite
    sensor1.set_mode_photometric().set_mode_color().set_balance_mode_user_white()
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_userwhite")
    assert mode_photometric.color_mode_color.balance_mode_userwhite.red_gain == 1
    assert mode_photometric.color_mode_color.balance_mode_userwhite.green_gain == 1
    assert mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain == 1

    sensor1.set_mode_photometric().set_mode_color().set_balance_mode_user_white().set_red_gain(value=2).set_green_gain(
        value=3
    ).set_blue_gain(value=4)
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.balance_mode_userwhite.red_gain == 2
    assert mode_photometric.color_mode_color.balance_mode_userwhite.green_gain == 3
    assert mode_photometric.color_mode_color.balance_mode_userwhite.blue_gain == 4

    # balance_mode_display
    sensor1.set_mode_photometric().set_mode_color().set_balance_mode_display_primaries()
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_display")
    assert mode_photometric.color_mode_color.balance_mode_display.red_display_file_uri == ""
    assert mode_photometric.color_mode_color.balance_mode_display.green_display_file_uri == ""
    assert mode_photometric.color_mode_color.balance_mode_display.blue_display_file_uri == ""

    sensor1.set_mode_photometric().set_mode_color().set_balance_mode_display_primaries().set_red_display_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityRed.spectrum")
    ).set_green_display_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityGreen.spectrum")
    ).set_blue_display_file_uri(
        uri=os.path.join(test_path, "CameraInputFiles", "CameraSensitivityBlue.spectrum")
    )
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.balance_mode_display.red_display_file_uri.endswith("CameraSensitivityRed.spectrum")
    assert mode_photometric.color_mode_color.balance_mode_display.green_display_file_uri.endswith("CameraSensitivityGreen.spectrum")
    assert mode_photometric.color_mode_color.balance_mode_display.blue_display_file_uri.endswith("CameraSensitivityBlue.spectrum")

    # balance_mode_none
    sensor1.set_mode_photometric().set_mode_color().set_balance_mode_none()
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.color_mode_color.HasField("balance_mode_none")

    # wavelengths_range
    sensor1.set_mode_photometric().set_wavelengths_range().set_start(value=430).set_end(value=750).set_sampling(value=15)
    sensor1.commit()
    mode_photometric = sensor1.sensor_template_link.get().camera_sensor_template.sensor_mode_photometric
    assert mode_photometric.wavelengths_range.w_start == 430
    assert mode_photometric.wavelengths_range.w_end == 750
    assert mode_photometric.wavelengths_range.w_sampling == 15

    # Properties

    # axis_system
    sensor1.set_axis_system(axis_system=[10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.axis_system == [10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    # Properties for camera photometric

    # trajectory_file_uri
    sensor1.set_mode_photometric().set_trajectory_file_uri(uri="TrajectoryFile")
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.trajectory_file_uri != ""

    # layer_type_source
    sensor1.set_mode_photometric().set_layer_type_source()
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.HasField("layer_type_source")

    # layer_type_none
    sensor1.set_mode_photometric().set_layer_type_none()
    sensor1.commit()
    assert sensor1._sensor_instance.camera_properties.HasField("layer_type_none")

    sensor1.delete()


def test_create_irradiance_sensor(speos: Speos):
    """Test creation of irradiance sensor."""
    p = script.Project(speos=speos)

    # Default value
    sensor1 = p.create_sensor(name="Irradiance.1", feature_type=script.Irradiance)
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("irradiance_sensor_template")
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("sensor_type_photometric")
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("illuminance_type_planar")
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("dimensions")
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_start == -50.0
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_end == 50.0
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_sampling == 100
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.y_start == -50.0
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.y_end == 50.0
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.y_sampling == 100
    assert sensor1._sensor_instance.HasField("irradiance_properties")
    assert sensor1._sensor_instance.irradiance_properties.axis_system == [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sensor1._sensor_instance.irradiance_properties.HasField("layer_type_none")
    assert sensor1._sensor_instance.irradiance_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFileNone
    assert sensor1._sensor_instance.irradiance_properties.integration_direction == []

    # sensor_type_colorimetric
    # default wavelengths range
    sensor1.set_type_colorimetric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("sensor_type_colorimetric")
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_colorimetric.HasField("wavelengths_range")
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_start == 400
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_end == 700
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling == 13
    # chosen wavelengths range
    sensor1.set_type_colorimetric().set_wavelengths_range().set_start(value=450).set_end(value=800).set_sampling(value=15)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_start == 450
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_end == 800
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling == 15

    # sensor_type_radiometric
    sensor1.set_type_radiometric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("sensor_type_radiometric")

    # sensor_type_spectral
    # default wavelengths range
    sensor1.set_type_spectral()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("sensor_type_spectral")
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_spectral.HasField("wavelengths_range")
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start == 400
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_end == 700
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_sampling == 13
    # chosen wavelengths range
    sensor1.set_type_spectral().set_wavelengths_range().set_start(value=450).set_end(value=800).set_sampling(value=15)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start == 450
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_end == 800
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.sensor_type_spectral.wavelengths_range.w_sampling == 15

    # sensor_type_photometric
    sensor1.set_type_photometric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("sensor_type_photometric")

    # illuminance_type_radial
    sensor1.set_illuminance_type_radial()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("illuminance_type_radial")

    # illuminance_type_hemispherical - bug to be fixed
    # sensor1.set_irradiance().set_illuminance_type_hemispherical()
    # sensor1.commit()
    # assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("illuminance_type_hemispherical")

    # illuminance_type_cylindrical
    sensor1.set_illuminance_type_cylindrical()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("illuminance_type_cylindrical")

    # illuminance_type_semi_cylindrical - bug to be fixed
    # sensor1.set_irradiance().set_illuminance_type_semi_cylindrical(integration_direction=[1,0,0])
    # sensor1.commit()
    # assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("illuminance_type_semi_cylindrical")

    # illuminance_type_planar
    sensor1.set_illuminance_type_planar(integration_direction=[0, 0, -1])
    sensor1.commit()
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("illuminance_type_planar")

    sensor1.set_illuminance_type_planar(integration_direction=None)  # cancel integration direction
    assert sensor1._sensor_instance.irradiance_properties.integration_direction == []

    # dimensions
    sensor1.dimensions.set_x_start(value=-10).set_x_end(value=10).set_x_sampling(value=60).set_y_start(value=-20).set_y_end(
        value=20
    ).set_y_sampling(value=120)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.HasField("dimensions")
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_start == -10.0
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_end == 10.0
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.x_sampling == 60
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.y_start == -20.0
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.y_end == 20.0
    assert sensor1.sensor_template_link.get().irradiance_sensor_template.dimensions.y_sampling == 120

    # properties
    # axis_system
    sensor1.set_axis_system([10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.axis_system == [10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    # ray_file_type
    sensor1.set_ray_file_type_classic()
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFileClassic

    sensor1.set_ray_file_type_polarization()
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFilePolarization

    sensor1.set_ray_file_type_tm25()
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFileTM25

    sensor1.set_ray_file_type_tm25_no_polarization()
    sensor1.commit()
    assert (
        sensor1._sensor_instance.irradiance_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFileTM25NoPolarization
    )

    sensor1.set_ray_file_type_none()
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.ray_file_type == sensor1._sensor_instance.EnumRayFileType.RayFileNone

    # layer_type_source
    sensor1.set_layer_type("source")
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.HasField("layer_type_source")

    # layer_type_face
    sensor1.set_layer_type("Face").set_sca_filtering_mode_intersected_one_time().set_layers(
        values=[
            script.sensor.BaseSensor.FaceLayer(name="Layer.1", geometries=[script.GeoRef.from_native_link("TheBodyB")]),
            script.sensor.BaseSensor.FaceLayer(
                name="Layer.2",
                geometries=[script.GeoRef.from_native_link("TheBodyC/TheFaceC1"), script.GeoRef.from_native_link("TheBodyC/TheFaceC2")],
            ),
        ]
    )
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.HasField("layer_type_face")
    assert (
        sensor1._sensor_instance.irradiance_properties.layer_type_face.sca_filtering_mode
        == sensor1._sensor_instance.irradiance_properties.layer_type_face.EnumSCAFilteringType.IntersectedOneTime
    )
    assert len(sensor1._sensor_instance.irradiance_properties.layer_type_face.layers) == 2
    assert sensor1._sensor_instance.irradiance_properties.layer_type_face.layers[0].name == "Layer.1"
    assert sensor1._sensor_instance.irradiance_properties.layer_type_face.layers[0].geometries.geo_paths == ["TheBodyB"]
    assert sensor1._sensor_instance.irradiance_properties.layer_type_face.layers[1].name == "Layer.2"
    assert sensor1._sensor_instance.irradiance_properties.layer_type_face.layers[1].geometries.geo_paths == [
        "TheBodyC/TheFaceC1",
        "TheBodyC/TheFaceC2",
    ]

    sensor1.set_layer_type("face").set_sca_filtering_mode_last_impact()
    sensor1.commit()
    assert (
        sensor1._sensor_instance.irradiance_properties.layer_type_face.sca_filtering_mode
        == sensor1._sensor_instance.irradiance_properties.layer_type_face.EnumSCAFilteringType.LastImpact
    )

    # layer_type_sequence
    sensor1.set_layer_type("sequence").set_maximum_nb_of_sequence(value=5).set_define_sequence_per_faces()
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.HasField("layer_type_sequence")
    assert sensor1._sensor_instance.irradiance_properties.layer_type_sequence.maximum_nb_of_sequence == 5
    assert (
        sensor1._sensor_instance.irradiance_properties.layer_type_sequence.define_sequence_per
        == sensor1._sensor_instance.irradiance_properties.layer_type_sequence.EnumSequenceType.Faces
    )

    sensor1.layer.set_define_sequence_per_geometries()
    sensor1.commit()
    assert (
        sensor1._sensor_instance.irradiance_properties.layer_type_sequence.define_sequence_per
        == sensor1._sensor_instance.irradiance_properties.layer_type_sequence.EnumSequenceType.Geometries
    )

    # layer_type_polarization
    sensor1.set_layer_type("polarization")
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.HasField("layer_type_polarization")

    # layer_type_incidence_angle
    sensor1.set_layer_type("incidence_angle").set_sampling(value=8)
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.HasField("layer_type_incidence_angle")
    assert sensor1._sensor_instance.irradiance_properties.layer_type_incidence_angle.sampling == 8

    # layer_type_none
    sensor1.set_layer_type()
    sensor1.commit()
    assert sensor1._sensor_instance.irradiance_properties.HasField("layer_type_none")

    # output_face_geometries
    sensor1.set_output_face_geometries(
        geometries=[
            script.GeoRef.from_native_link(geopath="TheBodyB/TheFaceB1"),
            script.GeoRef.from_native_link(geopath="TheBodyB/TheFaceB2"),
        ]
    )
    assert sensor1._sensor_instance.irradiance_properties.output_face_geometries.geo_paths == ["TheBodyB/TheFaceB1", "TheBodyB/TheFaceB2"]

    # output_face_geometries
    sensor1.delete()


def test_create_radiance_sensor(speos: Speos):
    """Test creation of radiance sensor."""
    p = script.Project(speos=speos)

    # Default value
    sensor1 = p.create_sensor(name="Radiance.1", feature_type=script.Radiance)
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("radiance_sensor_template")
    assert sensor1.sensor_template_link.get().name == "Radiance.1"
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField("sensor_type_photometric")
    assert sensor1.sensor_template_link.get().radiance_sensor_template.focal == 250
    assert sensor1.sensor_template_link.get().radiance_sensor_template.integration_angle == 5
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField("dimensions")
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.x_start == -50.0
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.x_end == 50.0
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.x_sampling == 100
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.y_start == -50.0
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.y_end == 50.0
    assert sensor1.sensor_template_link.get().radiance_sensor_template.dimensions.y_sampling == 100
    assert sensor1._sensor_instance.HasField("radiance_properties")
    assert sensor1._sensor_instance.radiance_properties.axis_system == [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sensor1._sensor_instance.radiance_properties.HasField("layer_type_none")
    assert sensor1._sensor_instance.radiance_properties.observer_point == []

    # sensor_type_radiometric
    sensor1.set_type_radiometric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField("sensor_type_radiometric")

    # sensor_type_spectral
    # default wavelengths range
    sensor1.set_type_spectral()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField("sensor_type_spectral")
    assert sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.HasField("wavelengths_range")
    assert sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start == 400
    assert sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_end == 700
    assert sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_sampling == 13
    # chosen wavelengths range
    sensor1.set_type_spectral().set_wavelengths_range().set_start(value=450).set_end(value=800).set_sampling(value=15)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_start == 450
    assert sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_end == 800
    assert sensor1.sensor_template_link.get().radiance_sensor_template.sensor_type_spectral.wavelengths_range.w_sampling == 15

    # sensor_type_photometric
    sensor1.set_type_photometric()
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.HasField("sensor_type_photometric")

    # focal
    sensor1.set_focal(value=150.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.focal == 150.5

    # integration_angle
    sensor1.set_integration_angle(value=4.5)
    sensor1.commit()
    assert sensor1.sensor_template_link.get().radiance_sensor_template.integration_angle == 4.5

    # dimensions
    sensor1.dimensions.set_x_start(value=-10).set_x_end(value=10).set_x_sampling(value=60).set_y_start(value=-20).set_y_end(
        value=20
    ).set_y_sampling(value=120)
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
    sensor1.set_axis_system([10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    sensor1.commit()
    assert sensor1._sensor_instance.radiance_properties.axis_system == [10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    # observer_point
    sensor1.set_observer_point([20, 30, 50])
    sensor1.commit()
    assert sensor1._sensor_instance.radiance_properties.observer_point == [20, 30, 50]

    sensor1.set_observer_point(value=None)  # cancel observer point chosen previously
    sensor1.commit()
    assert sensor1._sensor_instance.radiance_properties.observer_point == []

    # layer_type_source
    sensor1.set_layer_type("source")
    sensor1.commit()
    assert sensor1._sensor_instance.radiance_properties.HasField("layer_type_source")

    # layer_type_face
    sensor1.set_layer_type("FaCe").set_sca_filtering_mode_intersected_one_time().set_layers(
        values=[
            script.sensor.BaseSensor.FaceLayer(name="Layer.1", geometries=[script.GeoRef.from_native_link("TheBodyB")]),
            script.sensor.BaseSensor.FaceLayer(
                name="Layer.2",
                geometries=[script.GeoRef.from_native_link("TheBodyC/TheFaceC1"), script.GeoRef.from_native_link("TheBodyC/TheFaceC2")],
            ),
        ]
    )
    sensor1.commit()
    assert sensor1._sensor_instance.radiance_properties.HasField("layer_type_face")
    assert (
        sensor1._sensor_instance.radiance_properties.layer_type_face.sca_filtering_mode
        == sensor1._sensor_instance.radiance_properties.layer_type_face.EnumSCAFilteringType.IntersectedOneTime
    )
    assert len(sensor1._sensor_instance.radiance_properties.layer_type_face.layers) == 2
    assert sensor1._sensor_instance.radiance_properties.layer_type_face.layers[0].name == "Layer.1"
    assert sensor1._sensor_instance.radiance_properties.layer_type_face.layers[0].geometries.geo_paths == ["TheBodyB"]
    assert sensor1._sensor_instance.radiance_properties.layer_type_face.layers[1].name == "Layer.2"
    assert sensor1._sensor_instance.radiance_properties.layer_type_face.layers[1].geometries.geo_paths == [
        "TheBodyC/TheFaceC1",
        "TheBodyC/TheFaceC2",
    ]

    # layer_type_face -> chose other filtering mode
    sensor1.set_layer_type("FACE").set_sca_filtering_mode_last_impact()
    sensor1.commit()
    assert (
        sensor1._sensor_instance.radiance_properties.layer_type_face.sca_filtering_mode
        == sensor1._sensor_instance.radiance_properties.layer_type_face.EnumSCAFilteringType.LastImpact
    )

    # layer_type_face -> clear layers list
    sensor1.set_layer_type("fAcE").set_layers(values=[])  # clear layers list
    sensor1.commit()
    assert len(sensor1._sensor_instance.radiance_properties.layer_type_face.layers) == 0

    # layer_type_sequence
    sensor1.set_layer_type("sequence").set_maximum_nb_of_sequence(value=5).set_define_sequence_per_faces()
    sensor1.commit()
    assert sensor1._sensor_instance.radiance_properties.HasField("layer_type_sequence")
    assert sensor1._sensor_instance.radiance_properties.layer_type_sequence.maximum_nb_of_sequence == 5
    assert (
        sensor1._sensor_instance.radiance_properties.layer_type_sequence.define_sequence_per
        == sensor1._sensor_instance.radiance_properties.layer_type_sequence.EnumSequenceType.Faces
    )

    sensor1.layer.set_define_sequence_per_geometries()
    sensor1.commit()
    assert (
        sensor1._sensor_instance.radiance_properties.layer_type_sequence.define_sequence_per
        == sensor1._sensor_instance.radiance_properties.layer_type_sequence.EnumSequenceType.Geometries
    )

    # layer_type_none
    sensor1.set_layer_type()
    sensor1.commit()
    assert sensor1._sensor_instance.radiance_properties.HasField("layer_type_none")


def test_commit_sensor(speos: Speos):
    """Test commit of sensor."""
    p = script.Project(speos=speos)

    # Create
    sensor1 = p.create_sensor(name="Irradiance.1", feature_type=script.Irradiance)
    assert sensor1.sensor_template_link is None
    assert len(p.scene_link.get().sensors) == 0

    # Commit
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("irradiance_sensor_template")
    assert len(p.scene_link.get().sensors) == 1
    assert p.scene_link.get().sensors[0] == sensor1._sensor_instance

    # Change only in local not committed
    sensor1.set_axis_system([10, 10, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    assert p.scene_link.get().sensors[0] != sensor1._sensor_instance

    sensor1.delete()


def test_reset_sensor(speos: Speos):
    """Test reset of sensor."""
    p = script.Project(speos=speos)

    # Create + commit
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=script.Irradiance)
    sensor1.commit()
    assert sensor1.sensor_template_link is not None
    assert sensor1.sensor_template_link.get().HasField("irradiance_sensor_template")
    assert len(p.scene_link.get().sensors) == 1
    assert p.scene_link.get().sensors[0].HasField("irradiance_properties")

    # Ask for reset
    sensor1.reset()
    assert sensor1.sensor_template_link.get().HasField("irradiance_sensor_template")
    assert sensor1._sensor_template.HasField("irradiance_sensor_template")  # local template
    assert p.scene_link.get().sensors[0].HasField("irradiance_properties")
    assert sensor1._sensor_instance.HasField("irradiance_properties")  # local instance

    sensor1.delete()


def test_delete_sensor(speos: Speos):
    """Test delete of sensor."""
    p = script.Project(speos=speos)

    # Create + commit
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=script.Irradiance)
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
