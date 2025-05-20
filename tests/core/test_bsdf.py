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

"""Unit tests for PySpeos BSDF module."""

from pathlib import Path

from google.protobuf.empty_pb2 import Empty
import numpy as np
import pytest

from ansys.speos.core import Speos, bsdf
from ansys.speos.core.bsdf import AnisotropicBSDF, BxdfDatapoint
from tests.conftest import test_path
from tests.helper import does_file_exist, remove_file


def create_bsdf_data_point(is_brdf, incident_angle, anisotropy):
    """Create a BxDFDatapoint."""
    nb_theta = 10
    nb_phi = 37
    thetas = np.zeros(nb_theta)
    phis = np.zeros(nb_phi)
    bxdf = np.zeros((nb_theta, nb_phi))
    if is_brdf:
        for t in range(nb_theta):
            thetas[t] = t * np.pi * 0.5 / (nb_theta - 1)
            for p in range(nb_phi):
                phis[p] = p * 2 * np.pi / (nb_phi - 1)
                bxdf[t, p] = np.cos(thetas[t]) / np.pi
    else:
        for t in range(nb_theta):
            thetas[t] = np.pi * 0.5 * (1 + t / (nb_theta - 1))
            for p in range(nb_phi):
                phis[p] = p * 2 * np.pi / (nb_phi - 1)
                bxdf[t, p] = abs(np.cos(thetas[t]) / np.pi)
    datapoint = bsdf.BxdfDatapoint(is_brdf, 0, thetas, phis, bxdf, 0.5, anisotropy)
    datapoint.set_incident_angle(0, False)
    datapoint.set_incident_angle(incident_angle)
    return datapoint


def create_anisotropicbsdf(speos: Speos):
    """Create an anisotropic bsdf as Class object."""
    nb_lambda = 10
    spectrum = np.zeros((2, nb_lambda))
    for w in range(nb_lambda):
        spectrum[0, w] = 380.0 + w * (780.0 - 380.0) / (nb_lambda - 1)
        spectrum[1, w] = 0.5
    nb_incidence = 5
    anisotropy = np.radians([90, 0])
    incidence_angles = []
    for i in range(nb_incidence):
        incidence_angles.insert(0, i * 85 / (nb_incidence - 1))
    ani_bsdf = AnisotropicBSDF(speos)
    ani_bsdf.spectrum_incidence = [0, 0]
    ani_bsdf.spectrum_anisotropy = [0, 0]
    ani_bsdf.description = "PySpeos Unittest"
    ani_bsdf.anisotropy_vector = [1, 0, 0]
    brdf = []
    btdf = []
    for angle in anisotropy:
        for incident_angle in incidence_angles:
            brdf.append(create_bsdf_data_point(True, incident_angle, angle))
            btdf.append(create_bsdf_data_point(False, incident_angle, angle))
    ani_bsdf.brdf = brdf
    ani_bsdf.btdf = btdf
    ani_bsdf.reflection_spectrum = spectrum
    ani_bsdf.transmission_spectrum = spectrum
    ani_bsdf.commit()
    return ani_bsdf


def compare_bsdf_data_point(bsdfdata1: BxdfDatapoint, bsdfdata2: BxdfDatapoint):
    """COmpare a BXDF Datapoint."""
    test_list = []
    # test_list.append(bsdfdata1.tis == bsdfdata2.tis)
    test_list.append(bsdfdata1.anisotropy == bsdfdata2.anisotropy)
    test_list.append(approx_arrays(bsdfdata1.theta_values, bsdfdata2.theta_values))
    test_list.append(approx_arrays(bsdfdata1.phi_values, bsdfdata2.phi_values))
    test_list.append(approx_arrays(bsdfdata1.bxdf, bsdfdata2.bxdf))
    test_list.append(approx_comparison(bsdfdata1.incident_angle, bsdfdata2.incident_angle))
    test_list.append(bsdfdata1.is_brdf == bsdfdata2.is_brdf)
    if all(test_list):
        return True
    else:
        return False


def approx_comparison(value1, value2):
    """Approximation comparison for floats."""
    return np.fabs(value1 - value2) < 1e-6


def approx_arrays(value1, values2):
    """Approximation comparison for arrays."""
    return all(np.isclose(value1, values2, atol=1e-4).flatten())


def compare_anisotropic_bsdf(bsdf1: AnisotropicBSDF, bsdf2: AnisotropicBSDF):
    """Compare an Anisotropic bsdf."""
    test_list = []
    bsdf1_data = [
        bsdf1.description,
        bsdf1.anisotropic_angles,
        bsdf1.incident_angles,
        bsdf1.has_reflection,
        bsdf1.has_transmission,
        bsdf1.spectrum_anisotropy,
        bsdf1.spectrum_incidence,
        bsdf1.anisotropy_vector,
        bsdf1.nb_incidents,
    ]
    bsdf2_data = [
        bsdf2.description,
        bsdf2.anisotropic_angles,
        bsdf2.incident_angles,
        bsdf2.has_reflection,
        bsdf2.has_transmission,
        bsdf2.spectrum_anisotropy,
        bsdf2.spectrum_incidence,
        bsdf2.anisotropy_vector,
        bsdf2.nb_incidents,
    ]
    for item1, item2 in zip(bsdf1_data, bsdf2_data):
        test_list.append(item1 == item2)
    if bsdf1.has_reflection and bsdf2.has_reflection:
        test_list.append(approx_arrays(bsdf1.reflection_spectrum, bsdf2.reflection_spectrum))
        for brdf1data, brdf2data in zip(bsdf1.brdf, bsdf2.brdf):
            test_list.append(compare_bsdf_data_point(brdf1data, brdf2data))
    if bsdf1.has_transmission and bsdf2.has_transmission:
        test_list.append(approx_arrays(bsdf1.transmission_spectrum, bsdf2.transmission_spectrum))
        for btdf1data, btdf2data in zip(bsdf1.btdf, bsdf2.btdf):
            test_list.append(compare_bsdf_data_point(btdf1data, btdf2data))
    if all(test_list):
        return True
    else:
        return False


def test_anisotropic_bsdf(speos: Speos):
    """Unit test for anisotropic bsdf class."""
    initial_bsdf = create_anisotropicbsdf(speos)
    bsdf_path = Path(test_path) / "Test_Lambertian_bsdf.anisotropicbsdf"
    initial_bsdf.save(bsdf_path)

    # check save
    assert does_file_exist(str(bsdf_path))

    # compare loaded with created
    exported_bsdf = AnisotropicBSDF(speos, bsdf_path)
    assert compare_anisotropic_bsdf(initial_bsdf, exported_bsdf)

    # remove transmission
    exported_bsdf.has_transmission = False
    assert not compare_anisotropic_bsdf(initial_bsdf, exported_bsdf)

    # compare only reflective
    initial_bsdf.has_transmission = False
    assert compare_anisotropic_bsdf(initial_bsdf, exported_bsdf)

    # change spectrum incidence
    exported_bsdf.spectrum_incidence = np.radians(5)
    exported_bsdf.spectrum_anisotropy = np.radians(2)
    assert not compare_anisotropic_bsdf(initial_bsdf, exported_bsdf)

    # test reset
    exported_bsdf.reset()
    initial_bsdf.reset()
    assert compare_anisotropic_bsdf(initial_bsdf, exported_bsdf)

    # test commit True/false
    # change value
    exported_bsdf.spectrum_incidence = [np.radians(5), np.radians(5)]
    exported_bsdf.spectrum_anisotropy = [np.radians(2), np.radians(2)]

    # save non changed file
    bsdf_path2 = Path(test_path) / "Test_Lambertian_bsdf2"
    bsdf_path2 = exported_bsdf.save(bsdf_path2, commit=False)
    assert does_file_exist(str(bsdf_path2))

    # save changed file
    bsdf_path3 = Path(test_path) / "Test_Lambertian_bsdf3"
    bsdf_path3 = exported_bsdf.save(bsdf_path3, commit=True)
    assert does_file_exist(str(bsdf_path3))

    # load and compare files
    bsdf2 = AnisotropicBSDF(speos, bsdf_path2)
    bsdf3 = AnisotropicBSDF(speos, bsdf_path3)
    assert compare_anisotropic_bsdf(initial_bsdf, bsdf2)
    assert not compare_anisotropic_bsdf(bsdf2, bsdf3)
    remove_file(str(bsdf_path))
    remove_file(str(bsdf_path2))
    remove_file(str(bsdf_path3))


def test_anisotropic_bsdf_interpolation_enhancement(speos: Speos):
    """Unit test for anisotropic bsdf interpolation class."""
    # test automatic interpolation enhancement
    input_file = Path(test_path) / "Gaussian Fresnel 10 deg.anisotropicbsdf"
    output_file = Path(test_path) / "Gaussian Fresnel 10 deg interpolation test.anisotropicbsdf"
    initial_bsdf = AnisotropicBSDF(speos=speos, file_path=input_file)

    # test indices setting and cones data generation
    automatic_interpolation_settings = initial_bsdf.interpolation_enhancement(
        index_1=1.0, index_2=1.5
    )
    assert automatic_interpolation_settings.index1 == 1
    assert automatic_interpolation_settings.index2 == 1.5

    # test setting the index values
    automatic_interpolation_settings.index1 = 1.5
    automatic_interpolation_settings.index2 = 1
    assert automatic_interpolation_settings.index1 == 1.5
    assert automatic_interpolation_settings.index2 == 1

    # test methods retrieving the automated reflection and transmission interpolation settings
    cons_reflection_data = automatic_interpolation_settings.get_reflection_interpolation_settings
    cons_transmission_data = (
        automatic_interpolation_settings.get_transmission_interpolation_settings
    )
    cons_data = initial_bsdf._stub.GetSpecularInterpolationEnhancementData(
        Empty()
    )  # retrieve data using kernel method

    for cons_key_index, cons_key in enumerate(cons_reflection_data.keys()):
        for incidence_key_index, incidence_key in enumerate(cons_reflection_data[cons_key].keys()):
            assert (
                cons_data.reflection.anisotropic_samples[cons_key_index]
                .incidence_samples[incidence_key_index]
                .cone_half_angle
                == cons_reflection_data[cons_key][incidence_key]["half_angle"]
            )
            assert (
                cons_data.reflection.anisotropic_samples[cons_key_index]
                .incidence_samples[incidence_key_index]
                .cone_height
                == cons_reflection_data[cons_key][incidence_key]["height"]
            )

    for cons_key_index, cons_key in enumerate(cons_transmission_data.keys()):
        for incidence_key_index, incidence_key in enumerate(
            cons_transmission_data[cons_key].keys()
        ):
            assert (
                cons_data.transmission.anisotropic_samples[cons_key_index]
                .incidence_samples[incidence_key_index]
                .cone_half_angle
                == cons_transmission_data[cons_key][incidence_key]["half_angle"]
            )
            assert (
                cons_data.transmission.anisotropic_samples[cons_key_index]
                .incidence_samples[incidence_key_index]
                .cone_height
                == cons_transmission_data[cons_key][incidence_key]["height"]
            )

    # test modifying the interpolation setting dictionary
    # test cannot change a key's value if the value is a fixed dictionary
    with pytest.raises(ValueError, match="Cannot update key 0.0 with a FixedKeyDict as value"):
        cons_transmission_data["0.0"] = 0
    # test cannot add a new key
    with pytest.raises(KeyError, match="Cannot add new key: 1.0 is not allowed."):
        cons_reflection_data["1.0"] = 2
    # test modifying the interpolation settings and apply settings
    cons_reflection_data["0.0"]["0.0"]["half_angle"] = 0.523
    cons_reflection_data["0.0"]["0.0"]["height"] = 0.5
    automatic_interpolation_settings.set_interpolation_settings(
        is_brdf=True, settings=cons_reflection_data
    )
    new_cons_reflection_data = (
        automatic_interpolation_settings.get_reflection_interpolation_settings
    )
    assert new_cons_reflection_data["0.0"]["0.0"]["half_angle"] == 0.523
    assert new_cons_reflection_data["0.0"]["0.0"]["height"] == 0.5

    # test the interpolation enhancement settings in a saved bsdf file
    initial_bsdf.save(output_file)
    saved_bsdf = AnisotropicBSDF(speos=speos, file_path=output_file)
    saved_cons_reflection_data = saved_bsdf._stub.GetSpecularInterpolationEnhancementData(Empty())
    assert approx_comparison(
        value1=saved_cons_reflection_data.reflection.anisotropic_samples[0]
        .incidence_samples[0]
        .cone_half_angle,
        value2=0.523,
    )
    assert approx_comparison(
        value1=saved_cons_reflection_data.reflection.anisotropic_samples[0]
        .incidence_samples[0]
        .cone_height,
        value2=0.5,
    )


def test_bsdf180_creation(speos: Speos):
    """Unit test for create bsdf180 method."""
    input_file = Path(test_path) / "Gaussian Fresnel 10 deg.anisotropicbsdf"
    output_file_1 = Path(test_path) / "Test_bsdf180_1"
    output_file_2 = Path(test_path) / "Test_bsdf180_2.bsdf180"
    output_file_1 = bsdf.create_bsdf180(speos, output_file_1, input_file, input_file)
    assert does_file_exist(str(output_file_1))
    bsdf.create_bsdf180(speos, output_file_2, input_file, input_file)
    assert does_file_exist(str(output_file_2))
    remove_file(str(output_file_1))
    remove_file(str(output_file_2))


def test_spectral_brdf_creation(speos: Speos):
    """Unit test for create spectral brdf method."""
    input_file = [
        Path(test_path) / "R_test.anisotropicbsdf",
        Path(test_path) / "R_test.anisotropicbsdf",
    ]
    wl_list = [400.0, 700.0]
    output_file_1 = Path(test_path) / "Test_brdf_1"
    output_file_2 = Path(test_path) / "Test_brdf_2.brdf"
    output_file_1 = bsdf.create_spectral_brdf(speos, output_file_1, wl_list, input_file)
    assert does_file_exist(str(output_file_1))
    bsdf.create_spectral_brdf(speos, output_file_2, wl_list, input_file)
    assert does_file_exist(str(output_file_2))
    remove_file(str(output_file_1))
    remove_file(str(output_file_2))


def test_anisotropic_bsdf_creation(speos: Speos):
    """Unit test for create anisotropic bsdf method."""
    input_file = [
        Path(test_path) / "R_test.anisotropicbsdf",
        Path(test_path) / "R_test.anisotropicbsdf",
        Path(test_path) / "R_test.anisotropicbsdf",
    ]
    ani_list = [np.radians(0), np.radians(90), np.radians(180)]
    output_file_1 = Path(test_path) / "Test_brdf_1"
    output_file_2 = Path(test_path) / "Test_brdf_2.anisotropicbsdf"
    output_file_1 = bsdf.create_anisotropic_bsdf(speos, output_file_1, ani_list, input_file)
    assert does_file_exist(str(output_file_1))
    bsdf.create_anisotropic_bsdf(speos, output_file_2, ani_list, input_file, fix_disparity=True)
    assert does_file_exist(str(output_file_2))
    remove_file(str(output_file_1))
    remove_file(str(output_file_2))
