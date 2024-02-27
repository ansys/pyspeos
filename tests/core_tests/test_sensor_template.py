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
Test source template.
"""
import os

import pytest

from ansys.speos.core.sensor_template import SensorTemplateFactory
from ansys.speos.core.speos import Speos
from conftest import test_path


def test_sensor_template_factory(speos: Speos):
    """Test the sensor template factory."""
    assert speos.client.healthy is True

    # Get DB
    sensor_t_db = speos.client.sensor_templates()  # Create sensor_templates stub from client channel

    camera_input_files_path = os.path.join(test_path, "CameraInputFiles")
    red_spectrum = os.path.join(camera_input_files_path, "CameraSensitivityRed.spectrum")
    green_spectrum = os.path.join(camera_input_files_path, "CameraSensitivityGreen.spectrum")
    blue_spectrum = os.path.join(camera_input_files_path, "CameraSensitivityBlue.spectrum")
    transmittance = os.path.join(camera_input_files_path, "CameraTransmittance.spectrum")
    distortion = os.path.join(camera_input_files_path, "CameraDistortion_130deg.OPTDistortion")

    # Camera sensor template mode monochrome
    camera_t0 = sensor_t_db.create(
        message=SensorTemplateFactory.camera(
            name="camera_monochrome",
            description="Camera sensor template mode monochrome",
            settings=SensorTemplateFactory.CameraSettings(gamma_correction=2.2, focal_length=4, imager_distance=10, f_number=30),
            dimensions=SensorTemplateFactory.CameraDimensions(horz_pixel=640, vert_pixel=480, width=5, height=5),
            distorsion_file_uri=distortion,
            transmittance_file_uri=transmittance,
            spectrum_file_uris=[green_spectrum],
            wavelengths_range=SensorTemplateFactory.WavelengthsRange(start=400, end=800, sampling=10),
        )
    )
    assert camera_t0.key != ""

    # Camera sensor template mode color with balance mode none
    camera_t1 = sensor_t_db.create(
        message=SensorTemplateFactory.camera(
            name="camera_color",
            description="Camera sensor template mode color with balance mode none",
            settings=SensorTemplateFactory.CameraSettings(gamma_correction=2.2, focal_length=4, imager_distance=10, f_number=30),
            dimensions=SensorTemplateFactory.CameraDimensions(horz_pixel=640, vert_pixel=480, width=5, height=5),
            distorsion_file_uri=distortion,
            transmittance_file_uri=transmittance,
            spectrum_file_uris=[red_spectrum, green_spectrum, blue_spectrum],
            wavelengths_range=SensorTemplateFactory.WavelengthsRange(start=400, end=800, sampling=10),
        )
    )
    assert camera_t1.key != ""

    # Camera sensor template mode color with balance mode greyworld
    camera_t2 = sensor_t_db.create(
        message=SensorTemplateFactory.camera(
            name="camera_color_greyworld",
            description="Camera sensor template mode color with balance mode greyworld",
            settings=SensorTemplateFactory.CameraSettings(gamma_correction=2.2, focal_length=4, imager_distance=10, f_number=30),
            dimensions=SensorTemplateFactory.CameraDimensions(horz_pixel=640, vert_pixel=480, width=5, height=5),
            distorsion_file_uri=distortion,
            transmittance_file_uri=transmittance,
            spectrum_file_uris=[red_spectrum, green_spectrum, blue_spectrum],
            wavelengths_range=SensorTemplateFactory.WavelengthsRange(start=400, end=800, sampling=10),
            camera_balance_mode=SensorTemplateFactory.CameraBalanceMode(type=SensorTemplateFactory.CameraBalanceMode.Type.GreyWorld),
        )
    )
    assert camera_t2.key != ""

    # Camera sensor template mode color with balance mode userwhite
    camera_t3 = sensor_t_db.create(
        message=SensorTemplateFactory.camera(
            name="camera_color_userwhite",
            description="Camera sensor template mode color with balance mode userwhite",
            settings=SensorTemplateFactory.CameraSettings(gamma_correction=2.2, focal_length=4, imager_distance=10, f_number=30),
            dimensions=SensorTemplateFactory.CameraDimensions(horz_pixel=640, vert_pixel=480, width=5, height=5),
            distorsion_file_uri=distortion,
            transmittance_file_uri=transmittance,
            spectrum_file_uris=[red_spectrum, green_spectrum, blue_spectrum],
            wavelengths_range=SensorTemplateFactory.WavelengthsRange(start=400, end=800, sampling=10),
            camera_balance_mode=SensorTemplateFactory.CameraBalanceMode(
                type=SensorTemplateFactory.CameraBalanceMode.Type.UserWhiteBalance, values=[1, 1, 1]
            ),
        )
    )
    assert camera_t3.key != ""

    # Camera sensor template mode color with balance mode userwhite -> forgot to give gain values
    with pytest.raises(ValueError) as exc:
        sensor_t_db.create(
            message=SensorTemplateFactory.camera(
                name="camera_color_userwhite",
                description="Camera sensor template mode color with balance mode userwhite",
                settings=SensorTemplateFactory.CameraSettings(gamma_correction=2.2, focal_length=4, imager_distance=10, f_number=30),
                dimensions=SensorTemplateFactory.CameraDimensions(horz_pixel=640, vert_pixel=480, width=5, height=5),
                distorsion_file_uri=distortion,
                transmittance_file_uri=transmittance,
                spectrum_file_uris=[red_spectrum, green_spectrum, blue_spectrum],
                wavelengths_range=SensorTemplateFactory.WavelengthsRange(start=400, end=800, sampling=10),
                camera_balance_mode=SensorTemplateFactory.CameraBalanceMode(
                    type=SensorTemplateFactory.CameraBalanceMode.Type.UserWhiteBalance
                ),
            )
        )
    assert exc.value.args[0] == "For userwhite balance mode, three values are expected: [red_gain, green_gain, blue_gain]"

    # Irradiance sensor template photometric
    irradiance_t0 = sensor_t_db.create(
        message=SensorTemplateFactory.irradiance(
            name="irradiance_photometric",
            description="Irradiance sensor template photometric",
            type=SensorTemplateFactory.Type.Photometric,
            illuminance_type=SensorTemplateFactory.IlluminanceType.Planar,
            dimensions=SensorTemplateFactory.Dimensions(
                x_start=-50.0, x_end=50.0, x_sampling=100, y_start=-50.0, y_end=50.0, y_sampling=100
            ),
        )
    )
    assert irradiance_t0.key != ""

    # Irradiance sensor template colorimetric -> wavelengths_range is needed
    irradiance_t1 = sensor_t_db.create(
        message=SensorTemplateFactory.irradiance(
            name="irradiance_colorimetric",
            description="Irradiance sensor template colorimetric",
            type=SensorTemplateFactory.Type.Colorimetric,
            illuminance_type=SensorTemplateFactory.IlluminanceType.Planar,
            dimensions=SensorTemplateFactory.Dimensions(
                x_start=-50.0, x_end=50.0, x_sampling=100, y_start=-50.0, y_end=50.0, y_sampling=100
            ),
            wavelengths_range=SensorTemplateFactory.WavelengthsRange(start=400, end=800, sampling=10),
        )
    )
    assert irradiance_t1.key != ""

    # Irradiance sensor template colorimetric -> wavelengths_range is needed but not provided
    with pytest.raises(ValueError) as exc:
        sensor_t_db.create(
            message=SensorTemplateFactory.irradiance(
                name="irradiance_colorimetric",
                description="Irradiance sensor template colorimetric",
                type=SensorTemplateFactory.Type.Colorimetric,
                illuminance_type=SensorTemplateFactory.IlluminanceType.Planar,
                dimensions=SensorTemplateFactory.Dimensions(
                    x_start=-50.0, x_end=50.0, x_sampling=100, y_start=-50.0, y_end=50.0, y_sampling=100
                ),
            )
        )
    assert exc.value.args[0] == "For colorimetric type, please provide wavelengths_range parameter"

    camera_t0.delete()
    camera_t1.delete()
    camera_t2.delete()
    camera_t3.delete()
    irradiance_t0.delete()
    irradiance_t1.delete()
