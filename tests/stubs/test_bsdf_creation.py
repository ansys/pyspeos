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

"""Unit test for BSDF creation service."""

import math
from pathlib import Path

import ansys.api.speos.bsdf.v1.bsdf_creation_pb2 as bsdf_creation__v1__pb2
import ansys.api.speos.bsdf.v1.bsdf_creation_pb2_grpc as bsdf_creation__v1__pb2_grpc

from ansys.speos.core.speos import Speos
from tests.conftest import test_path
import tests.helper as helper


def test_grpc_spectral_bsdf(speos: Speos):
    """Test for spectral bsdf service (*.BRDF)."""
    stub = bsdf_creation__v1__pb2_grpc.BsdfCreationServiceStub(speos.client.channel)

    # BSDF180
    bsdf180_request = bsdf_creation__v1__pb2.Bsdf180InputData()
    bsdf180_request.input_front_bsdf_file_name = str(
        Path(test_path) / "Gaussian Fresnel 10 deg.anisotropicbsdf"
    )
    bsdf180_request.input_opposite_bsdf_file_name = str(
        Path(test_path) / "Gaussian Fresnel 10 deg.anisotropicbsdf"
    )
    bsdf180_request.output_file_name = str(Path(test_path) / "Test.bsdf180")
    stub.BuildBsdf180(bsdf180_request)
    assert helper.does_file_exist(bsdf180_request.output_file_name)
    helper.remove_file(bsdf180_request.output_file_name)

    # spectral BSDF
    spectral_request = bsdf_creation__v1__pb2.SpectralBsdfInputData()
    tmp = spectral_request.input_anisotropic_samples.add()
    tmp.wavelength = 400.0
    tmp.file_name = str(Path(test_path) / "R_test.anisotropicbsdf")
    tmp = spectral_request.input_anisotropic_samples.add()
    tmp.wavelength = 700.0
    tmp.file_name = str(Path(test_path) / "R_test.anisotropicbsdf")
    spectral_request.output_file_name = str(Path(test_path) / "Test.brdf")
    stub.BuildSpectralBsdf(spectral_request)
    assert helper.does_file_exist(spectral_request.output_file_name)
    helper.remove_file(spectral_request.output_file_name)

    # anisotropic BSDF
    anisotropic_request = bsdf_creation__v1__pb2.AnisotropicBsdfInputData()
    temp = anisotropic_request.input_anisotropic_bsdf_samples.add()
    temp.anisotropic_angle = 0.0
    temp.file_name = str(Path(test_path) / "R_test.anisotropicbsdf")
    temp = anisotropic_request.input_anisotropic_bsdf_samples.add()
    temp.anisotropic_angle = math.pi / 2
    temp.file_name = str(Path(test_path) / "R_test.anisotropicbsdf")
    anisotropic_request.fix_disparity = False
    anisotropic_request.output_file_name = str(Path(test_path) / "Assembled.anisotropicbsdf")
    stub.BuildAnisotropicBsdf(anisotropic_request)
    assert helper.does_file_exist(anisotropic_request.output_file_name)
    helper.remove_file(anisotropic_request.output_file_name)
