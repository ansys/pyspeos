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

"""
Test source template.
"""

import os

from conftest import test_path

from ansys.api.speos.sensor.v1 import camera_sensor_pb2, common_pb2, irradiance_sensor_pb2
from ansys.speos.core.sensor_template import SensorTemplate
from ansys.speos.core.speos import Speos


def test_sensor_template(speos: Speos):
    """Test the sensor template."""
    assert speos.client.healthy is True

    # Get DB
    sensor_t_db = (
        speos.client.sensor_templates()
    )  # Create sensor_templates stub from client channel

    camera_input_files_path = os.path.join(test_path, "CameraInputFiles")
    red_spectrum = os.path.join(camera_input_files_path, "CameraSensitivityRed.spectrum")
    green_spectrum = os.path.join(camera_input_files_path, "CameraSensitivityGreen.spectrum")
    blue_spectrum = os.path.join(camera_input_files_path, "CameraSensitivityBlue.spectrum")
    transmittance = os.path.join(camera_input_files_path, "CameraTransmittance.spectrum")
    distortion = os.path.join(camera_input_files_path, "CameraDistortion_130deg.OPTDistortion")

    # Camera sensor template mode monochrome
    camera_t0 = sensor_t_db.create(
        message=SensorTemplate(
            name="camera_monochrome",
            description="Camera sensor template mode monochrome",
            camera_sensor_template=camera_sensor_pb2.CameraSensorTemplate(
                sensor_mode_photometric=camera_sensor_pb2.SensorCameraModePhotometric(
                    acquisition_integration=0.01,
                    acquisition_lag_time=0,
                    transmittance_file_uri=transmittance,
                    gamma_correction=2.2,
                    png_bits=camera_sensor_pb2.PNG_16,
                    color_mode_monochromatic=camera_sensor_pb2.SensorCameraColorModeMonochromatic(
                        spectrum_file_uri=green_spectrum
                    ),
                    wavelengths_range=common_pb2.WavelengthsRange(
                        w_start=400, w_end=800, w_sampling=10
                    ),
                ),
                focal_length=4,
                imager_distance=10,
                f_number=30,
                distortion_file_uri=distortion,
                horz_pixel=640,
                vert_pixel=480,
                width=5,
                height=5,
            ),
        )
    )
    assert camera_t0.key != ""

    # Camera sensor template mode color with balance mode none
    camera_t1 = sensor_t_db.create(
        message=SensorTemplate(
            name="camera_color",
            description="Camera sensor template mode color with balance mode none",
            camera_sensor_template=camera_sensor_pb2.CameraSensorTemplate(
                sensor_mode_photometric=camera_sensor_pb2.SensorCameraModePhotometric(
                    acquisition_integration=0.01,
                    acquisition_lag_time=0,
                    transmittance_file_uri=transmittance,
                    gamma_correction=2.2,
                    png_bits=camera_sensor_pb2.PNG_16,
                    color_mode_color=camera_sensor_pb2.SensorCameraColorModeColor(
                        red_spectrum_file_uri=red_spectrum,
                        green_spectrum_file_uri=green_spectrum,
                        blue_spectrum_file_uri=blue_spectrum,
                        balance_mode_none=camera_sensor_pb2.SensorCameraBalanceModeNone(),
                    ),
                    wavelengths_range=common_pb2.WavelengthsRange(
                        w_start=400, w_end=800, w_sampling=10
                    ),
                ),
                focal_length=4,
                imager_distance=10,
                f_number=30,
                distortion_file_uri=distortion,
                horz_pixel=640,
                vert_pixel=480,
                width=5,
                height=5,
            ),
        )
    )
    assert camera_t1.key != ""

    # Camera sensor template mode color with balance mode greyworld
    camera_t2 = sensor_t_db.create(
        message=SensorTemplate(
            name="camera_color_greyworld",
            description="Camera sensor template mode color with balance mode greyworld",
            camera_sensor_template=camera_sensor_pb2.CameraSensorTemplate(
                sensor_mode_photometric=camera_sensor_pb2.SensorCameraModePhotometric(
                    acquisition_integration=0.01,
                    acquisition_lag_time=0,
                    transmittance_file_uri=transmittance,
                    gamma_correction=2.2,
                    png_bits=camera_sensor_pb2.PNG_16,
                    color_mode_color=camera_sensor_pb2.SensorCameraColorModeColor(
                        red_spectrum_file_uri=red_spectrum,
                        green_spectrum_file_uri=green_spectrum,
                        blue_spectrum_file_uri=blue_spectrum,
                        balance_mode_greyworld=camera_sensor_pb2.SensorCameraBalanceModeGreyworld(),
                    ),
                    wavelengths_range=common_pb2.WavelengthsRange(
                        w_start=400, w_end=800, w_sampling=10
                    ),
                ),
                focal_length=4,
                imager_distance=10,
                f_number=30,
                distortion_file_uri=distortion,
                horz_pixel=640,
                vert_pixel=480,
                width=5,
                height=5,
            ),
        )
    )
    assert camera_t2.key != ""

    # Camera sensor template mode color with balance mode userwhite
    camera_t3 = sensor_t_db.create(
        message=SensorTemplate(
            name="camera_color_userwhite",
            description="Camera sensor template mode color with balance mode userwhite",
            camera_sensor_template=camera_sensor_pb2.CameraSensorTemplate(
                sensor_mode_photometric=camera_sensor_pb2.SensorCameraModePhotometric(
                    acquisition_integration=0.01,
                    acquisition_lag_time=0,
                    transmittance_file_uri=transmittance,
                    gamma_correction=2.2,
                    png_bits=camera_sensor_pb2.PNG_16,
                    color_mode_color=camera_sensor_pb2.SensorCameraColorModeColor(
                        red_spectrum_file_uri=red_spectrum,
                        green_spectrum_file_uri=green_spectrum,
                        blue_spectrum_file_uri=blue_spectrum,
                        balance_mode_userwhite=camera_sensor_pb2.SensorCameraBalanceModeUserwhite(
                            red_gain=1, green_gain=1, blue_gain=1
                        ),
                    ),
                    wavelengths_range=common_pb2.WavelengthsRange(
                        w_start=400, w_end=800, w_sampling=10
                    ),
                ),
                focal_length=4,
                imager_distance=10,
                f_number=30,
                distortion_file_uri=distortion,
                horz_pixel=640,
                vert_pixel=480,
                width=5,
                height=5,
            ),
        )
    )
    assert camera_t3.key != ""

    # Irradiance sensor template photometric
    irradiance_t0 = sensor_t_db.create(
        message=SensorTemplate(
            name="irradiance_photometric",
            description="Irradiance sensor template photometric",
            irradiance_sensor_template=irradiance_sensor_pb2.IrradianceSensorTemplate(
                sensor_type_photometric=common_pb2.SensorTypePhotometric(),
                illuminance_type_planar=common_pb2.IlluminanceTypePlanar(),
                dimensions=common_pb2.SensorDimensions(
                    x_start=-50.0,
                    x_end=50.0,
                    x_sampling=100,
                    y_start=-50.0,
                    y_end=50.0,
                    y_sampling=100,
                ),
            ),
        )
    )
    assert irradiance_t0.key != ""

    # Irradiance sensor template colorimetric -> wavelengths_range is needed
    irradiance_t1 = sensor_t_db.create(
        message=SensorTemplate(
            name="irradiance_colorimetric",
            description="Irradiance sensor template colorimetric",
            irradiance_sensor_template=irradiance_sensor_pb2.IrradianceSensorTemplate(
                sensor_type_colorimetric=common_pb2.SensorTypeColorimetric(
                    wavelengths_range=common_pb2.WavelengthsRange(
                        w_start=400, w_end=800, w_sampling=10
                    )
                ),
                illuminance_type_planar=common_pb2.IlluminanceTypePlanar(),
                dimensions=common_pb2.SensorDimensions(
                    x_start=-50.0,
                    x_end=50.0,
                    x_sampling=100,
                    y_start=-50.0,
                    y_end=50.0,
                    y_sampling=100,
                ),
            ),
        )
    )
    assert irradiance_t1.key != ""

    camera_t0.delete()
    camera_t1.delete()
    camera_t2.delete()
    camera_t3.delete()
    irradiance_t0.delete()
    irradiance_t1.delete()
