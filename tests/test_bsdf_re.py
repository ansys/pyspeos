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

from ansys.pyoptics.speos.modules.bsdf_reader import bsdf_analysis
from conftest import config, test_path
import helper

input_file_name = os.path.join(test_path, "Gaussian Fresnel 10 deg.anisotropicbsdf")
bsdf_output_file_name = os.path.join(test_path, "Test.bsdf180")
tmp_file_name = os.path.join(test_path, "R_test.anisotropicbsdf")
spectral_output_file_name = os.path.join(test_path, "Test.brdf")
anisotropic_output_file_name = os.path.join(test_path, "Assembled.anisotropicbsdf")

# bsdf file reader creation with port
bsdf_request = bsdf_analysis(config.get("SpeosServerPort"))


class Test_bsdf:
    def test_bsdf180(self):
        bsdf_request.bsdf180(input_file_name, input_file_name, bsdf_output_file_name)
        assert helper.does_file_exist(bsdf_output_file_name)
        helper.remove_file(bsdf_output_file_name)

    def test_spectral(self):
        bsdf_request.spectral(tmp_file_name, spectral_output_file_name, [400, 700])
        assert helper.does_file_exist(
            spectral_output_file_name,
        )
        helper.remove_file(
            spectral_output_file_name,
        )

    def test_anisotropic(self):
        bsdf_request.Anisotropic(tmp_file_name, anisotropic_output_file_name, [0.0, math.pi / 2])
        assert helper.does_file_exist(anisotropic_output_file_name)
        helper.remove_file(anisotropic_output_file_name)
