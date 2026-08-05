# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

"""Test sensor template v2."""

from pathlib import Path

import pytest

from ansys.speos.core.generic.version_checker import server_version_checker
from ansys.speos.core.kernel.sensor_template_v2 import ProtoSensorTemplateV2
from ansys.speos.core.speos import Speos
from tests.conftest import test_path


@pytest.mark.skipif(
    not server_version_checker.is_version_supported(2027, 1, 0),
    reason="Sensor v2 requires Speos >= 2027.1.0",
)
def test_sensor_template_v2_camera(speos: Speos):
    """Test the camera sensor template v2."""
    assert speos.client.healthy is True

    # Get DB
    sensor_t_db = speos.client.sensor_templates_v2()

    camera_input_files_path = Path(test_path) / "CameraInputFiles"
    green_spectrum = str(camera_input_files_path / "CameraSensitivityGreen.spectrum")
    transmittance = str(camera_input_files_path / "CameraTransmittance.spectrum")
    distortion = str(camera_input_files_path / "CameraDistortion_130deg.OPTDistortion")

    # Create camera sensor template v2 with monochromatic mode
    camera_t0 = sensor_t_db.create(
        message=ProtoSensorTemplateV2(
            name="camera_monochrome_v2",
            description="Camera sensor template v2 mode monochromatic",
            camera=ProtoSensorTemplateV2.Camera(
                sensor_mode_photometric=ProtoSensorTemplateV2.Camera.ModePhotometric(
                    acquisition_integration=0.01,
                    acquisition_lag_time=0,
                    transmittance_spectrum_guid=transmittance,
                    gamma_correction=2.2,
                    png_bits=4,  # PNG_16
                    mode_monochromatic=ProtoSensorTemplateV2.Camera.ModePhotometric.ModeMonochromatic(
                        spectrum_guid=green_spectrum
                    ),
                    wavelengths_range=ProtoSensorTemplateV2.WavelengthsRange(
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

    # Read the camera sensor template
    camera_read = camera_t0.get()
    assert camera_read.name == "camera_monochrome_v2"
    assert camera_read.description == "Camera sensor template v2 mode monochromatic"
    assert camera_read.HasField("camera")

    # Update the camera sensor template
    camera_read.description = "Updated camera sensor template v2"
    camera_t0.set(camera_read)

    # Read again to verify the update
    camera_updated = camera_t0.get()
    assert camera_updated.description == "Updated camera sensor template v2"

    # Delete the camera sensor template
    camera_t0.delete()


@pytest.mark.skipif(
    not server_version_checker.is_version_supported(2027, 1, 0),
    reason="Sensor v2 requires Speos >= 2027.1.0",
)
def test_sensor_template_v2_irradiance(speos: Speos):
    """Test the irradiance sensor template v2."""
    assert speos.client.healthy is True

    # Get DB
    sensor_t_db = speos.client.sensor_templates_v2()

    # Create irradiance sensor template v2
    irr_t0 = sensor_t_db.create(
        message=ProtoSensorTemplateV2(
            name="irradiance_v2",
            description="Irradiance sensor template v2",
            irradiance=ProtoSensorTemplateV2.Irradiance(
                mode_photometric=ProtoSensorTemplateV2.ModePhotometric(),
                integration_type=1,  # INTEGRATION_TYPE_PLANAR
                dimensions=ProtoSensorTemplateV2.Dimensions(
                    x_start=-50,
                    x_end=50,
                    x_sampling=100,
                    y_start=-50,
                    y_end=50,
                    y_sampling=100,
                ),
            ),
        )
    )
    assert irr_t0.key != ""

    # Read the irradiance sensor template
    irr_read = irr_t0.get()
    assert irr_read.name == "irradiance_v2"
    assert irr_read.HasField("irradiance")

    # Delete the irradiance sensor template
    irr_t0.delete()


@pytest.mark.skipif(
    not server_version_checker.is_version_supported(2027, 1, 0),
    reason="Sensor v2 requires Speos >= 2027.1.0",
)
def test_sensor_template_v2_list(speos: Speos):
    """Test listing sensor template v2."""
    assert speos.client.healthy is True

    # Get DB
    sensor_t_db = speos.client.sensor_templates_v2()

    # Create multiple sensor templates
    irr_t1 = sensor_t_db.create(
        message=ProtoSensorTemplateV2(
            name="irradiance_v2_1",
            irradiance=ProtoSensorTemplateV2.Irradiance(
                mode_photometric=ProtoSensorTemplateV2.ModePhotometric(),
                integration_type=1,
                dimensions=ProtoSensorTemplateV2.Dimensions(
                    x_start=-50, x_end=50, x_sampling=100, y_start=-50, y_end=50, y_sampling=100
                ),
            ),
        )
    )
    irr_t2 = sensor_t_db.create(
        message=ProtoSensorTemplateV2(
            name="irradiance_v2_2",
            irradiance=ProtoSensorTemplateV2.Irradiance(
                mode_photometric=ProtoSensorTemplateV2.ModePhotometric(),
                integration_type=1,
                dimensions=ProtoSensorTemplateV2.Dimensions(
                    x_start=-50, x_end=50, x_sampling=100, y_start=-50, y_end=50, y_sampling=100
                ),
            ),
        )
    )

    # List all sensor templates
    all_templates = sensor_t_db.list()
    assert len(all_templates) >= 2
    assert irr_t1.key in [t.key for t in all_templates]
    assert irr_t2.key in [t.key for t in all_templates]

    # Clean up
    irr_t1.delete()
    irr_t2.delete()
