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
Test basic intensity template database connection.
"""
import os

from ansys.speos.core.intensity_template import IntensityTemplateFactory
from ansys.speos.core.speos import Speos
from conftest import test_path


def test_intensity_template_factory(speos: Speos):
    """Test the intensity template factory."""
    assert speos.client.healthy is True
    # Get DB
    intens_t_db = speos.client.intensity_templates()  # Create intensity template stub from client channel

    # Library
    intens_t_lib = intens_t_db.create(
        message=IntensityTemplateFactory.library(
            name="library_0",
            description="library intensity template",
            file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies"),
        )
    )
    assert intens_t_lib.key != ""

    # Lambertian
    intens_t_lamb = intens_t_db.create(
        message=IntensityTemplateFactory.lambertian(name="lambertian_0", description="lambertian intensity template", total_angle=180.0)
    )
    assert intens_t_lamb.key != ""

    # Cos
    intens_t_cos = intens_t_db.create(
        message=IntensityTemplateFactory.cos(name="cos_0", description="cos intensity template", N=3.0, total_angle=180.0)
    )
    assert intens_t_cos.key != ""

    # SymmetricGaussian
    intens_t_sym_gauss = intens_t_db.create(
        message=IntensityTemplateFactory.symmetric_gaussian(
            name="symmetric_gaussian_0",
            description="symmetric gaussian intensity template",
            FWHM_angle=30.0,
            total_angle=180.0,
        )
    )
    assert intens_t_sym_gauss.key != ""

    # AsymmetricGaussian
    intens_t_asym_gauss = intens_t_db.create(
        message=IntensityTemplateFactory.asymmetric_gaussian(
            name="asymmetric_gaussian_0",
            description="asymmetric gaussian intensity template",
            FWHM_angle_x=30.0,
            FWHM_angle_y=20.0,
            total_angle=180.0,
        )
    )
    assert intens_t_asym_gauss.key != ""

    # Delete all intensity_templates from DB
    for intens_t in intens_t_db.list():
        intens_t.delete()
