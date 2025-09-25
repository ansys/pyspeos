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

"""Test basic intensity template database connection."""

from pathlib import Path

import pytest

from ansys.api.speos.common.v1 import data_pb2
from ansys.speos.core.kernel.intensity_template import ProtoIntensityTemplate
from ansys.speos.core.speos import Speos
from tests.conftest import test_path


@pytest.mark.supported_speos_versions(min=252)
def test_intensity_template(speos: Speos):
    """Test the intensity template."""
    assert speos.client.healthy is True
    # Get DB
    intens_t_db = (
        speos.client.intensity_templates()
    )  # Create intensity template stub from client channel

    # Library
    intens_t_lib = intens_t_db.create(
        message=ProtoIntensityTemplate(
            name="library_0",
            description="library intensity template",
            library=ProtoIntensityTemplate.Library(
                intensity_file_uri=str(Path(test_path) / "IES_C_DETECTOR.ies")
            ),
        )
    )
    assert intens_t_lib.key != ""

    # Lambertian (cos with N = 1.0)

    intens_t_lamb = intens_t_db.create(
        message=ProtoIntensityTemplate(
            name="lambertian_0",
            description="lambertian intensity template",
            cos=ProtoIntensityTemplate.Cos(N=1.0, total_angle=180.0),
        )
    )
    assert intens_t_lamb.key != ""

    # Cos
    intens_t_cos = intens_t_db.create(
        message=ProtoIntensityTemplate(
            name="cos_0",
            description="cos intensity template",
            cos=ProtoIntensityTemplate.Cos(N=3.0, total_angle=180.0),
        )
    )
    assert intens_t_cos.key != ""

    # Symmetric gaussian
    intens_t_sym_gauss = intens_t_db.create(
        message=ProtoIntensityTemplate(
            name="symmetric_gaussian_0",
            description="symmetric gaussian intensity template",
            gaussian=ProtoIntensityTemplate.Gaussian(
                FWHM_angle_x=30.0, FWHM_angle_y=30.0, total_angle=180.0
            ),
        )
    )
    assert intens_t_sym_gauss.key != ""

    # Asymmetric gaussian
    intens_t_asym_gauss = intens_t_db.create(
        message=ProtoIntensityTemplate(
            name="asymmetric_gaussian_0",
            description="asymmetric gaussian intensity template",
            gaussian=ProtoIntensityTemplate.Gaussian(
                FWHM_angle_x=30.0, FWHM_angle_y=20.0, total_angle=180.0
            ),
        )
    )
    assert intens_t_asym_gauss.key != ""

    # Delete all intensity_templates from DB
    for intens_t in intens_t_db.list():
        intens_t.delete()


def test_action_get_library_type_info(speos: Speos):
    """Test the intensity template action : get_library_type_info."""
    assert speos.client.healthy is True

    # Get DB
    intens_t_db = (
        speos.client.intensity_templates()
    )  # Create intensity template stub from client channel

    # Library
    intens_t_lib = intens_t_db.create(
        message=ProtoIntensityTemplate(
            name="library_0",
            description="library intensity template",
            library=ProtoIntensityTemplate.Library(
                intensity_file_uri=str(Path(test_path) / "IES_C_DETECTOR.ies")
            ),
        )
    )

    # Get flux
    flux = intens_t_lib.get_library_type_info().flux
    assert flux.magnitude == data_pb2.Magnitude.luminous_flux
    assert flux.unit == data_pb2.Unit.lumens
    assert flux.values[0] == 3966.7947473514782
