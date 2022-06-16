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

import ansys.api.speos.bsdf.v1.spectral_bsdf_pb2 as spectral_bsdf__v1__pb2
import ansys.api.speos.bsdf.v1.spectral_bsdf_pb2_grpc as spectral_bsdf__v1__pb2_grpc
import helper
from conftest import config, test_path
from google.protobuf.empty_pb2 import Empty

from ansys.pyoptics import speos


def createSpectralBsdf() -> spectral_bsdf__v1__pb2.SpectralBsdfData:
    bsdf = spectral_bsdf__v1__pb2.SpectralBsdfData(description="test description")
    nbw = 7
    nbi = 10
    for i in range(nbi):
        bsdf.incidence_samples.append(i * math.pi * 0.5 / (nbi - 1))
    for w in range(nbw):
        bsdf.wavelength_samples.append(360.0 + w * (780.0 - 360.0) / (nbw - 1))
        for i in range(nbi):
            IW = bsdf.wavelength_incidence_samples.add()

            # IW.reflection
            nb_theta = 10
            nb_phi = 37
            IW.reflection.integral = 0.5
            for p in range(nb_phi):
                IW.reflection.phi_samples.append(p * 2 * math.pi / (nb_phi - 1))
            for t in range(nb_theta):
                IW.reflection.theta_samples.append(t * math.pi * 0.5 / (nb_theta - 1))
                for p in range(nb_phi):
                    IW.reflection.bsdf_cos_theta.append(0.5 * math.cos(IW.reflection.theta_samples[t]) / math.pi)

            # IW.transmission
            nb_theta = 10
            nb_phi = 37
            IW.transmission.integral = 0.5
            for p in range(nb_phi):
                IW.transmission.phi_samples.append(p * 2 * math.pi / (nb_phi - 1))
            for t in range(nb_theta):
                IW.transmission.theta_samples.append(math.pi * 0.5 * (1 + t / (nb_theta - 1)))
                for p in range(nb_phi):
                    IW.transmission.bsdf_cos_theta.append(
                        0.5 * abs(math.cos(IW.transmission.theta_samples[t])) / math.pi
                    )

    return bsdf


def approx_cmp(a, b):
    return math.fabs(a - b) < 1e-6


def compareDiagram(a, b):
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


def compareSpectralBsdf(bsdf1, bsdf2):
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
        if not compareDiagram(a.reflection, b.reflection) or not compareDiagram(a.transmission, b.transmission):
            return False
    return True


def compareSpecularEnhancementData(c1, c2):
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


def test_grpc_spectral_bsdf():
    stub = speos.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=spectral_bsdf__v1__pb2_grpc.SpectralBsdfServiceStub
    )

    file_name = spectral_bsdf__v1__pb2.FileName()

    # Creating spectral bsdf protocol buffer
    bsdf = createSpectralBsdf()

    # Sending protocol buffer to server
    stub.Import(bsdf)
    file_name.file_name = os.path.join(test_path, "Spectral.serialized")

    # Exporting to {file_name.file_name}
    stub.ExportFile(file_name)
    assert helper.does_file_exist(file_name.file_name)

    # Reading {file_name.file_name} back
    stub.ImportFile(file_name)

    helper.remove_file(file_name.file_name)

    # Exporting anisotropic bsdf protocol buffer
    bsdf2 = stub.Export(Empty())

    assert compareSpectralBsdf(bsdf, bsdf2)
    file_name.file_name = os.path.join(test_path, "Lambert.anisotropicbsdf")

    # Writing as {file_name.file_name}
    stub.Save(file_name)
    assert helper.does_file_exist(file_name.file_name)

    # Reading {file_name.file_name} back
    stub.Load(file_name)
    helper.remove_file(file_name.file_name)

    # Exporting anisotropic bsdf protocol buffer
    bsdf3 = stub.Export(Empty())

    assert compareSpectralBsdf(bsdf, bsdf3)

    # conoscopic map
    cm = spectral_bsdf__v1__pb2.ConoscopicMap()
    cm.output_file_name = os.path.join(test_path, "test_conoscopic_spectral.xmp")
    cm.wavelength = 555.0
    cm.side = spectral_bsdf__v1__pb2.ConoscopicMap.TRANSMISSION
    cm.resolution = 512
    stub.ExportToConoscopicMap(cm)
    assert helper.does_file_exist(cm.output_file_name)
    helper.remove_file(cm.output_file_name)

    # computing cones
    indices = spectral_bsdf__v1__pb2.RefractiveIndices(refractive_index_1=1.0, refractive_index_2=1.5)
    stub.GenerateSpecularInterpolationEnhancementData(indices)

    # getting cones
    cones = stub.GetSpecularInterpolationEnhancementData(Empty())
    assert cones.refractive_index_1 == indices.refractive_index_1
    assert cones.refractive_index_2 == indices.refractive_index_2

    # changing some values
    cones.wavelength_incidence_samples[0].reflection.cone_half_angle = 0.5
    cones.wavelength_incidence_samples[0].reflection.cone_height = 0.001

    # setting cones back
    stub.SetSpecularInterpolationEnhancementData(cones)

    file_name.file_name = os.path.join(test_path, "tmp_autocut.anisotropicbsdf")
    # writing result in {file_name.file_name}
    stub.Save(file_name)
    assert helper.does_file_exist(file_name.file_name)

    # reading {file_name.file_name} back
    stub.Load(file_name)
    helper.remove_file(file_name.file_name)

    # getting cones again
    cones2 = stub.GetSpecularInterpolationEnhancementData(Empty())

    # comparing cones to previous ones
    assert compareSpecularEnhancementData(cones, cones2)
