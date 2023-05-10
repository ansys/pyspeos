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

import ansys.api.speos.bsdf.v1.bsdf_creation_pb2 as bsdf_creation__v1__pb2
import ansys.api.speos.bsdf.v1.bsdf_creation_pb2_grpc as bsdf_creation__v1__pb2_grpc

# from ansys.api.speos import grpc_stub
from ansys.pyoptics.speos.speos import Speos
from conftest import test_path
import helper


def test_grpc_spectral_bsdf(speos: Speos):
    stub = bsdf_creation__v1__pb2_grpc.BsdfCreationServiceStub(speos.client.channel)

    # BSDF180
    bsdf180_request = bsdf_creation__v1__pb2.Bsdf180InputData()
    bsdf180_request.input_front_bsdf_file_name = os.path.join(test_path, "Gaussian Fresnel 10 deg.anisotropicbsdf")
    bsdf180_request.input_opposite_bsdf_file_name = os.path.join(test_path, "Gaussian Fresnel 10 deg.anisotropicbsdf")
    bsdf180_request.output_file_name = os.path.join(test_path, "Test.bsdf180")
    stub.BuildBsdf180(bsdf180_request)
    assert helper.does_file_exist(bsdf180_request.output_file_name)
    helper.remove_file(bsdf180_request.output_file_name)

    # spectral BSDF
    spectral_request = bsdf_creation__v1__pb2.SpectralBsdfInputData()
    tmp = spectral_request.input_anisotropic_samples.add()
    tmp.wavelength = 400.0
    tmp.file_name = os.path.join(test_path, "R_test.anisotropicbsdf")
    tmp = spectral_request.input_anisotropic_samples.add()
    tmp.wavelength = 700.0
    tmp.file_name = os.path.join(test_path, "R_test.anisotropicbsdf")
    spectral_request.output_file_name = os.path.join(test_path, "Test.brdf")
    stub.BuildSpectralBsdf(spectral_request)
    assert helper.does_file_exist(spectral_request.output_file_name)
    helper.remove_file(spectral_request.output_file_name)

    # anisotropic BSDF
    anisotropic_request = bsdf_creation__v1__pb2.AnisotropicBsdfInputData()
    temp = anisotropic_request.input_anisotropic_bsdf_samples.add()
    temp.anisotropic_angle = 0.0
    temp.file_name = os.path.join(test_path, "R_test.anisotropicbsdf")
    temp = anisotropic_request.input_anisotropic_bsdf_samples.add()
    temp.anisotropic_angle = math.pi / 2
    temp.file_name = os.path.join(test_path, "R_test.anisotropicbsdf")
    anisotropic_request.fix_disparity = False
    anisotropic_request.output_file_name = os.path.join(test_path, "Assembled.anisotropicbsdf")
    stub.BuildAnisotropicBsdf(anisotropic_request)
    assert helper.does_file_exist(anisotropic_request.output_file_name)
    helper.remove_file(anisotropic_request.output_file_name)
