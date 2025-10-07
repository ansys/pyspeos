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

"""Unit tests for spectral BSDF service."""

import math
from pathlib import Path

import ansys.api.speos.bsdf.v1.spectral_bsdf_pb2 as spectral_bsdf__v1__pb2
import ansys.api.speos.bsdf.v1.spectral_bsdf_pb2_grpc as spectral_bsdf__v1__pb2_grpc
from google.protobuf.empty_pb2 import Empty

from ansys.speos.core.speos import Speos
from tests.conftest import test_path
import tests.helper as helper


def create_spectral_bsdf() -> spectral_bsdf__v1__pb2.SpectralBsdfData:
    """Create simple spectral bsdf."""
    bsdf = spectral_bsdf__v1__pb2.SpectralBsdfData(description="test description")
    nbw = 7
    nbi = 10
    for i in range(nbi):
        bsdf.incidence_samples.append(i * math.pi * 0.5 / (nbi - 1))
    for w in range(nbw):
        bsdf.wavelength_samples.append(360.0 + w * (780.0 - 360.0) / (nbw - 1))
        for i in range(nbi):
            iw = bsdf.wavelength_incidence_samples.add()

            # iw.reflection
            nb_theta = 10
            nb_phi = 37
            iw.reflection.integral = 0.5
            for p in range(nb_phi):
                iw.reflection.phi_samples.append(p * 2 * math.pi / (nb_phi - 1))
            for t in range(nb_theta):
                iw.reflection.theta_samples.append(t * math.pi * 0.5 / (nb_theta - 1))
                for p in range(nb_phi):
                    iw.reflection.bsdf_cos_theta.append(
                        0.5 * math.cos(iw.reflection.theta_samples[t]) / math.pi
                    )

            # iw.transmission
            nb_theta = 10
            nb_phi = 37
            iw.transmission.integral = 0.5
            for p in range(nb_phi):
                iw.transmission.phi_samples.append(p * 2 * math.pi / (nb_phi - 1))
            for t in range(nb_theta):
                iw.transmission.theta_samples.append(math.pi * 0.5 * (1 + t / (nb_theta - 1)))
                for p in range(nb_phi):
                    iw.transmission.bsdf_cos_theta.append(
                        0.5 * abs(math.cos(iw.transmission.theta_samples[t])) / math.pi
                    )

    return bsdf


def approx_cmp(a, b):
    """Approximated comparison of two numbers."""
    return math.fabs(a - b) < 1e-6


def compare_diagram(a, b):
    """Approximated comparison of intensity diagrams."""
    if len(a.theta_samples) != len(b.theta_samples):
        return False
    for i, j in zip(a.theta_samples, b.theta_samples):
        if not approx_cmp(i, j):
            return False
    if len(a.phi_samples) != len(b.phi_samples):
        return False
    for i, j in zip(a.phi_samples, b.phi_samples):
        if not approx_cmp(i, j):
            return False
    if len(a.bsdf_cos_theta) != len(b.bsdf_cos_theta):
        return False
    for i, j in zip(a.bsdf_cos_theta, b.bsdf_cos_theta):
        if not approx_cmp(i, j):
            return False
    if a.integral != b.integral:
        return False
    return True


def compare_spectral_bsdf(bsdf1, bsdf2):
    """Compare two spectral bsdf."""
    if bsdf1.description != bsdf2.description:
        return False
    if len(bsdf1.incidence_samples) != len(bsdf2.incidence_samples):
        return False
    for a, b in zip(bsdf1.incidence_samples, bsdf2.incidence_samples):
        if not approx_cmp(a, b):
            return False
    if len(bsdf1.wavelength_samples) != len(bsdf2.wavelength_samples):
        return False
    for a, b in zip(bsdf1.wavelength_samples, bsdf2.wavelength_samples):
        if a != b:
            return False
    for a, b in zip(bsdf1.wavelength_incidence_samples, bsdf2.wavelength_incidence_samples):
        if not compare_diagram(a.reflection, b.reflection) or not compare_diagram(
            a.transmission, b.transmission
        ):
            return False
    return True


def compare_specular_enhancement_data(c1, c2):
    """Compare Specular enhancement data."""
    if c1.incidence_nb != c2.incidence_nb:
        return False
    if c1.wavelength_nb != c2.wavelength_nb:
        return False
    if c1.refractive_index_1 != c2.refractive_index_1:
        return False
    if c1.refractive_index_2 != c2.refractive_index_2:
        return False
    if len(c1.wavelength_incidence_samples) != len(c2.wavelength_incidence_samples):
        return False
    for s1, s2 in zip(c1.wavelength_incidence_samples, c2.wavelength_incidence_samples):
        if not approx_cmp(s1.reflection.cone_half_angle, s2.reflection.cone_half_angle):
            return False
        if s1.reflection.cone_height != s2.reflection.cone_height:
            return False
        if not approx_cmp(s1.transmission.cone_half_angle, s2.transmission.cone_half_angle):
            return False
        if s1.transmission.cone_height != s2.transmission.cone_height:
            return False
    return True


def test_grpc_spectral_bsdf(speos: Speos):
    """Test to check Spectral bsdf service."""
    stub = spectral_bsdf__v1__pb2_grpc.SpectralBsdfServiceStub(speos.client.channel)

    file_name = spectral_bsdf__v1__pb2.FileName()

    # Creating spectral bsdf protocol buffer
    bsdf = create_spectral_bsdf()

    # Sending protocol buffer to server
    stub.Import(bsdf)
    file_name.file_name = str(Path(test_path) / "Spectral.serialized")

    # Exporting to {file_name.file_name}
    stub.ExportFile(file_name)
    assert helper.does_file_exist(file_name.file_name)

    # Reading {file_name.file_name} back
    stub.ImportFile(file_name)

    helper.remove_file(file_name.file_name)

    # Exporting anisotropic bsdf protocol buffer
    bsdf2 = stub.Export(Empty())

    assert compare_spectral_bsdf(bsdf, bsdf2)
    file_name.file_name = str(Path(test_path) / "Lambert.anisotropicbsdf")

    # Writing as {file_name.file_name}
    stub.Save(file_name)
    assert helper.does_file_exist(file_name.file_name)

    # Reading {file_name.file_name} back
    stub.Load(file_name)
    helper.remove_file(file_name.file_name)

    # Exporting anisotropic bsdf protocol buffer
    bsdf3 = stub.Export(Empty())

    assert compare_spectral_bsdf(bsdf, bsdf3)

    # conoscopic map
    cm = spectral_bsdf__v1__pb2.ConoscopicMap()
    cm.output_file_name = str(Path(test_path) / "test_conoscopic_spectral.xmp")
    cm.wavelength = 555.0
    cm.side = spectral_bsdf__v1__pb2.ConoscopicMap.TRANSMISSION
    cm.resolution = 512
    stub.ExportToConoscopicMap(cm)
    assert helper.does_file_exist(cm.output_file_name)
    helper.remove_file(cm.output_file_name)

    # computing cones
    indices = spectral_bsdf__v1__pb2.RefractiveIndices(
        refractive_index_1=1.0, refractive_index_2=1.5
    )
    stub.GenerateSpecularInterpolationEnhancementData(indices)

    # getting cones - checking indices
    cones = stub.GetSpecularInterpolationEnhancementData(Empty())
    assert cones.refractive_index_1 == indices.refractive_index_1
    assert cones.refractive_index_2 == indices.refractive_index_2

    # changing some values
    cones.wavelength_incidence_samples[0].reflection.cone_half_angle = 0.5
    cones.wavelength_incidence_samples[0].reflection.cone_height = 0.001

    # setting cones back
    stub.SetSpecularInterpolationEnhancementData(cones)

    file_name.file_name = str(Path(test_path) / "tmp_autocut.anisotropicbsdf")
    # writing result in {file_name.file_name}
    stub.Save(file_name)
    assert helper.does_file_exist(file_name.file_name)

    # reading {file_name.file_name} back
    stub.Load(file_name)
    helper.remove_file(file_name.file_name)

    # getting cones again
    cones2 = stub.GetSpecularInterpolationEnhancementData(Empty())

    # comparing cones to previous ones
    assert compare_specular_enhancement_data(cones, cones2)
