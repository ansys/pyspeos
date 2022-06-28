"""This module allows pytest to perform unit testing.

Usage:
.. code::
   $ pytest
   $ pytest -vx

With coverage.
.. code::
   $ pytest --cov ansys.pyoptics.speos

"""
import math
import os

import ansys.api.speos.bsdf.v1.bsdf_creation_pb2_grpc as bsdf_creation__v1__pb2_grpc

from ansys.pyoptics import speos
from ansys.pyoptics.speos.modules.bsdf_reader import bsdf_analysis
from conftest import config, test_path
import helper

input_file_name = os.path.join(test_path, "Gaussian Fresnel 10 deg.anisotropicbsdf")
bsdf_output_file_name = os.path.join(test_path, "Test.bsdf180")
tmp_file_name = os.path.join(test_path, "R_test.anisotropicbsdf")
spectral_output_file_name = os.path.join(test_path, "Test.brdf")
anisotropic_output_file_name = os.path.join(test_path, "Assembled.anisotropicbsdf")
stub = speos.get_stub_insecure_channel(
    port=config.get("SpeosServerPort"), stub_type=bsdf_creation__v1__pb2_grpc.BsdfCreationServiceStub
)


class Test_bsdf:
    def test_bsdf180(self):
        bsdf_request = bsdf_analysis.bsdf180(input_file_name, input_file_name, bsdf_output_file_name)
        stub.BuildBsdf180(bsdf_request)
        assert helper.does_file_exist(bsdf_request.output_file_name)
        helper.remove_file(bsdf_request.output_file_name)

    def test_spectral(self):
        spectral_request = bsdf_analysis.spectral(tmp_file_name, spectral_output_file_name, [400, 700])
        stub.BuildSpectralBsdf(spectral_request)
        assert helper.does_file_exist(spectral_request.output_file_name)
        helper.remove_file(spectral_request.output_file_name)

    def test_anisotropic(self):
        anisotropic = bsdf_analysis.Anisotropic(tmp_file_name, anisotropic_output_file_name, [0.0, math.pi / 2])
        stub.BuildAnisotropicBsdf(anisotropic)
        assert helper.does_file_exist(anisotropic.output_file_name)
        helper.remove_file(anisotropic.output_file_name)
