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

"""Unit test for anisotropic bsdf service."""

import math
from pathlib import Path

from google.protobuf.empty_pb2 import Empty

import ansys.api.speos.bsdf.v1.anisotropic_bsdf_pb2 as anisotropic_bsdf__v1__pb2
import ansys.api.speos.bsdf.v1.anisotropic_bsdf_pb2_grpc as anisotropic_bsdf__v1__pb2_grpc
from ansys.speos.core.speos import Speos
from tests.conftest import test_path
import tests.helper as helper


def create_anisotropic_bsdf():
    """Create a lambertian bsdf."""
    bsdf = anisotropic_bsdf__v1__pb2.AnisotropicBsdfData()

    # description
    bsdf.description = "test protobuf"

    # anisotropy vector
    bsdf.anisotropy_vector.x = 1.0
    bsdf.anisotropy_vector.y = 0.0
    bsdf.anisotropy_vector.z = 0.0

    # reflection spectrum
    bsdf.reflection.spectrum_incidence = math.radians(6.0)
    bsdf.reflection.spectrum_anisotropy = 0.0

    nb_lambda = 5
    for w in range(nb_lambda):
        pair = bsdf.reflection.spectrum.add()
        pair.wavelength = 360.0 + w * (780.0 - 360.0) / (nb_lambda - 1)
        pair.coefficient = 0.5

    # anisotropy sampling
    nb_anisotropy = 2
    for a in range(nb_anisotropy):
        slice = bsdf.reflection.anisotropic_samples.add()
        slice.anisotropic_sample = a * math.pi * 0.5 / (nb_anisotropy - 1)
        # incidence sampling
        nb_incidence = 10
        for i in range(nb_incidence):
            incidence_diag = slice.incidence_samples.add()
            incidence_diag.incidence_sample = i * math.pi * 0.5 / (nb_incidence - 1)
            # intensity diagrams
            nb_theta = 10
            nb_phi = 37
            for p in range(nb_phi):
                incidence_diag.phi_samples.append(p * 2 * math.pi / (nb_phi - 1))
            for t in range(nb_theta):
                incidence_diag.theta_samples.append(t * math.pi * 0.5 / (nb_theta - 1))
                for p in range(nb_phi):
                    incidence_diag.bsdf_cos_theta.append(
                        math.cos(incidence_diag.theta_samples[t]) / math.pi
                    )

    # transmission spectrum
    bsdf.transmission.spectrum_incidence = math.radians(6.0)
    bsdf.transmission.spectrum_anisotropy = 0.0

    nb_lambda = 5
    for w in range(nb_lambda):
        pair = bsdf.transmission.spectrum.add()
        pair.wavelength = 360.0 + w * (780.0 - 360.0) / (nb_lambda - 1)
        pair.coefficient = 0.5

    for a in range(nb_anisotropy):
        slice = bsdf.transmission.anisotropic_samples.add()
        slice.anisotropic_sample = a * math.pi * 0.5 / (nb_anisotropy - 1)
        # incidence sampling
        nb_incidence = 10
        for i in range(nb_incidence):
            incidence_diag = slice.incidence_samples.add()
            incidence_diag.incidence_sample = i * math.pi * 0.5 / (nb_incidence - 1)
            # intensity diagrams
            nb_theta = 10
            nb_phi = 37
            for p in range(nb_phi):
                incidence_diag.phi_samples.append(p * 2 * math.pi / (nb_phi - 1))
            for t in range(nb_theta):
                incidence_diag.theta_samples.append(math.pi * 0.5 * (1 + t / (nb_theta - 1)))
                for p in range(nb_phi):
                    incidence_diag.bsdf_cos_theta.append(
                        abs(math.cos(incidence_diag.theta_samples[t])) / math.pi
                    )
    return bsdf


def approx_cmp(a, b):
    """Approximated comparison of two numbers."""
    return math.fabs(a - b) < 1e-6


def compare_anisotropic_bsdf(bsdf1, bsdf2):
    """Compare 2 bsdf."""
    # description
    if bsdf1.description != bsdf2.description:
        return False

    # anisotropy vector
    if bsdf1.anisotropy_vector.x != bsdf2.anisotropy_vector.x:
        return False

    if bsdf1.anisotropy_vector.y != bsdf2.anisotropy_vector.y:
        return False

    if bsdf1.anisotropy_vector.z != bsdf2.anisotropy_vector.z:
        return False

    # reflection spectrum
    if not approx_cmp(bsdf1.reflection.spectrum_incidence, bsdf2.reflection.spectrum_incidence):
        return False

    if bsdf1.reflection.spectrum_anisotropy != bsdf2.reflection.spectrum_anisotropy:
        return False

    if len(bsdf1.reflection.spectrum) != len(bsdf2.reflection.spectrum):
        return False

    for w in range(len(bsdf1.reflection.spectrum)):
        if bsdf1.reflection.spectrum[w].wavelength != bsdf2.reflection.spectrum[w].wavelength:
            return False
        if bsdf1.reflection.spectrum[w].coefficient != bsdf2.reflection.spectrum[w].coefficient:
            return False

    # anisotropy sampling
    if len(bsdf1.reflection.anisotropic_samples) != len(bsdf2.reflection.anisotropic_samples):
        return False

    for a in range(len(bsdf1.reflection.anisotropic_samples)):
        slice1 = bsdf1.reflection.anisotropic_samples[a]
        slice2 = bsdf2.reflection.anisotropic_samples[a]

        if slice1.anisotropic_sample != slice2.anisotropic_sample:
            return False

        # incidence sampling
        if len(slice1.incidence_samples) != len(slice2.incidence_samples):
            return False

        for i in range(len(slice1.incidence_samples)):
            incidence_diag1 = slice1.incidence_samples[i]
            incidence_diag2 = slice2.incidence_samples[i]

            if incidence_diag1.incidence_sample != incidence_diag2.incidence_sample:
                return False

            # intensity diagrams
            if len(incidence_diag1.phi_samples) != len(incidence_diag2.phi_samples):
                return False

            for p in range(len(incidence_diag1.phi_samples)):
                if not approx_cmp(
                    incidence_diag1.phi_samples[p],
                    incidence_diag2.phi_samples[p],
                ):
                    return False

            if len(incidence_diag1.theta_samples) != len(incidence_diag2.theta_samples):
                return False

            for t in range(len(incidence_diag1.theta_samples)):
                if incidence_diag1.theta_samples[t] != incidence_diag2.theta_samples[t]:
                    return False
                for p in range(len(incidence_diag1.phi_samples)):
                    if not approx_cmp(
                        incidence_diag1.bsdf_cos_theta[t * len(incidence_diag1.phi_samples) + p],
                        incidence_diag2.bsdf_cos_theta[t * len(incidence_diag1.phi_samples) + p],
                    ):
                        return False

    # transmission spectrum
    if not approx_cmp(
        bsdf1.transmission.spectrum_incidence,
        bsdf2.transmission.spectrum_incidence,
    ):
        return False

    if bsdf1.transmission.spectrum_anisotropy != bsdf2.transmission.spectrum_anisotropy:
        return False

    if len(bsdf1.transmission.spectrum) != len(bsdf2.transmission.spectrum):
        return False

    for w in range(len(bsdf1.transmission.spectrum)):
        if bsdf1.transmission.spectrum[w].wavelength != bsdf2.transmission.spectrum[w].wavelength:
            return False
        if bsdf1.transmission.spectrum[w].coefficient != bsdf2.transmission.spectrum[w].coefficient:
            return False

    # anisotropy sampling
    if len(bsdf1.transmission.anisotropic_samples) != len(bsdf2.transmission.anisotropic_samples):
        return False

    for a in range(len(bsdf1.transmission.anisotropic_samples)):
        slice1 = bsdf1.transmission.anisotropic_samples[a]
        slice2 = bsdf2.transmission.anisotropic_samples[a]

        if slice1.anisotropic_sample != slice2.anisotropic_sample:
            return False

        # incidence sampling
        if len(slice1.incidence_samples) != len(slice2.incidence_samples):
            return False

        for i in range(len(slice1.incidence_samples)):
            incidence_diag1 = slice1.incidence_samples[i]
            incidence_diag2 = slice2.incidence_samples[i]

            if incidence_diag1.incidence_sample != incidence_diag2.incidence_sample:
                return False

            # intensity diagrams
            if len(incidence_diag1.phi_samples) != len(incidence_diag2.phi_samples):
                return False

            for p in range(len(incidence_diag1.phi_samples)):
                if not approx_cmp(
                    incidence_diag1.phi_samples[p],
                    incidence_diag2.phi_samples[p],
                ):
                    return False

            if len(incidence_diag1.theta_samples) != len(incidence_diag2.theta_samples):
                return False

            for t in range(len(incidence_diag1.theta_samples)):
                if not approx_cmp(
                    incidence_diag1.theta_samples[t],
                    incidence_diag2.theta_samples[t],
                ):
                    return False
                for p in range(len(incidence_diag1.phi_samples)):
                    if not approx_cmp(
                        incidence_diag1.bsdf_cos_theta[t * len(incidence_diag1.phi_samples) + p],
                        incidence_diag2.bsdf_cos_theta[t * len(incidence_diag1.phi_samples) + p],
                    ):
                        return False

    return True


def compare_enhancement_data(cones1, cones2):
    """Compare enhancement cones."""
    if len(cones1.anisotropic_samples) != len(cones2.anisotropic_samples):
        return False

    for [samples1, samples2] in zip(cones1.anisotropic_samples, cones2.anisotropic_samples):
        if len(samples1.incidence_samples) != len(samples2.incidence_samples):
            return False
        for [cone1, cone2] in zip(samples1.incidence_samples, samples2.incidence_samples):
            if not approx_cmp(cone1.cone_half_angle, cone2.cone_half_angle):
                return False
            if cone1.cone_height != cone2.cone_height:
                return False

    return True


def compare_specular_enhancement_data(data1, data2):
    """Compare specular enhancement information."""
    if (
        data1.refractive_index_1 != data2.refractive_index_1
        or data1.refractive_index_2 != data2.refractive_index_2
    ):
        return False

    return compare_enhancement_data(
        data1.reflection, data2.reflection
    ) and compare_enhancement_data(data1.transmission, data2.transmission)


def test_grpc_anisotropic_bsdf(speos: Speos):
    """Test for anisotropic bsdf service."""
    stub = anisotropic_bsdf__v1__pb2_grpc.AnisotropicBsdfServiceStub(speos.client.channel)

    # anisotropic bsdf
    file_name = anisotropic_bsdf__v1__pb2.FileName()

    # Creating anisotropic bsdf protocol buffer
    bsdf = create_anisotropic_bsdf()

    # Sending protocol buffer to server
    stub.Import(bsdf)
    file_name.file_name = str(Path(test_path) / "Lambert.serialized")

    # Exporting to {file_name.file_name}
    stub.ExportFile(file_name)
    assert helper.does_file_exist(file_name.file_name)

    # Reading {file_name.file_name} back
    stub.ImportFile(file_name)
    helper.remove_file(file_name.file_name)

    # Exporting anisotropic bsdf protocol buffer
    bsdf2 = stub.Export(Empty())

    assert compare_anisotropic_bsdf(bsdf, bsdf2)
    file_name.file_name = str(Path(test_path) / "Lambert.anisotropicbsdf")

    # Writing as {file_name.file_name}
    stub.Save(file_name)
    assert helper.does_file_exist(file_name.file_name)

    # Reading {file_name.file_name} back
    stub.Load(file_name)
    helper.remove_file(file_name.file_name)

    # Exporting anisotropic bsdf protocol buffer
    bsdf3 = stub.Export(Empty())

    assert compare_anisotropic_bsdf(bsdf, bsdf3)

    file_name.file_name = str(Path(test_path) / "Gaussian Fresnel 10 deg.anisotropicbsdf")
    # loading {file_name.file_name}
    stub.Load(file_name)

    # conoscopic map
    cm = anisotropic_bsdf__v1__pb2.ConoscopicMap()
    cm.output_file_name = str(Path(test_path) / "test_conoscopic_anisotropic.xmp")
    cm.wavelength = 555.0
    cm.anisotropic_angle = 0.0
    cm.side = anisotropic_bsdf__v1__pb2.ConoscopicMap.TRANSMISSION
    cm.resolution = 512
    stub.ExportToConoscopicMap(cm)
    assert helper.does_file_exist(cm.output_file_name)
    helper.remove_file(cm.output_file_name)

    # computing cones
    indices = anisotropic_bsdf__v1__pb2.RefractiveIndices(
        refractive_index_1=1.0, refractive_index_2=1.5
    )
    stub.GenerateSpecularInterpolationEnhancementData(indices)

    # getting cones
    cones = stub.GetSpecularInterpolationEnhancementData(Empty())
    assert cones.refractive_index_1 == indices.refractive_index_1
    assert cones.refractive_index_2 == indices.refractive_index_2

    # changing some values
    cones.reflection.anisotropic_samples[0].incidence_samples[0].cone_half_angle = 0.5
    cones.reflection.anisotropic_samples[0].incidence_samples[0].cone_height = 0.001

    # setting cones back
    stub.SetSpecularInterpolationEnhancementData(cones)

    file_name.file_name = str(Path(test_path) / "Gaussian Fresnel 10 deg_autocut.anisotropicbsdf")
    # writing result in {file_name.file_name}
    stub.Save(file_name)

    # reading {file_name.file_name} back
    stub.Load(file_name)

    # getting cones again
    cones2 = stub.GetSpecularInterpolationEnhancementData(Empty())

    # comparing cones to previous ones
    assert compare_specular_enhancement_data(cones, cones2)

    # generating retroreflection cones even if there's no retroreflection on this surface
    stub.GenerateRetroReflectionInterpolationEnhancementData(Empty())

    # getting the retro cones
    rc = stub.GetRetroReflectionInterpolationEnhancementData(Empty())

    # modifying some data
    rc.anisotropic_samples[0].incidence_samples[0].cone_half_angle = 0.7
    rc.anisotropic_samples[0].incidence_samples[0].cone_height = 0.0015

    # setting cones back
    stub.SetRetroReflectionInterpolationEnhancementData(rc)

    # writing result in {file_name.file_name}
    stub.Save(file_name)
    assert helper.does_file_exist(file_name.file_name)

    # reading {file_name.file_name} back
    stub.Load(file_name)
    helper.remove_file(file_name.file_name)

    # getting cones again
    rc2 = stub.GetRetroReflectionInterpolationEnhancementData(Empty())

    # comparing cones to previous ones
    assert compare_enhancement_data(rc, rc2)

    # white specular enabling and disabling
    wl = anisotropic_bsdf__v1__pb2.Wavelength()
    wl.wavelength = 632.0
    stub.EnableWhiteSpecular(wl)
    stub.DisableWhiteSpecular(Empty())

    # spectrum imports
    spi = anisotropic_bsdf__v1__pb2.SpectrumImport()
    spi.incidence_angle = 0.05
    spi.anisotropy_angle = 0.0
    spi.file_name = str(Path(test_path) / "R04.spectrum")
    stub.ImportReflectionSpectrum(spi)
    stub.ImportTransmissionSpectrum(spi)

    # Constant absorption
    stub.FreezeAbsorptionReflectionTransmissionCoefficients(Empty())
