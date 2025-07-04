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
from ansys.speos.core.bsdf import AnisotropicBSDF, BxdfDatapoint, SpectralBRDF
from tests.conftest import test_path
from tests.helper import clean_all_dbs, does_file_exist, remove_file


def create_lambertian_bsdf(is_brdf, nb_theta=5, nb_phi=5):
    """Create a lambertian Distribution as np.array."""
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
    return thetas, phis, bxdf


def create_bsdf_data_point(is_brdf, incident_angle, anisotropy, wavelength=555.0):
    """Create a BxDFDatapoint."""
    nb_theta = 91
    nb_phi = 361
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
    datapoint = bsdf.BxdfDatapoint(is_brdf, 0, thetas, phis, bxdf, 0.5, anisotropy, wavelength)
    datapoint.set_incident_angle(0, False)
    datapoint.set_incident_angle(incident_angle)
    return datapoint


def create_spectral_brdf(speos: Speos):
    """Create an spectral bsdf as Class object."""
    nb_lambda = 5
    spectrum = []
    for w in range(nb_lambda):
        spectrum.append(380.0 + w * (780.0 - 380.0) / (nb_lambda - 1))
    nb_incidence = 5
    incidence_angles = []
    for i in range(nb_incidence):
        incidence_angles.insert(0, i * 85 / (nb_incidence - 1))
    spectral_brdf = SpectralBRDF(speos)
    spectral_brdf.description = "PySpeos Unittest"
    spectral_brdf.anisotropy_vector = [1, 0, 0]
    brdf = []
    btdf = []
    for wl in spectrum:
        for incident_angle in incidence_angles:
            brdf.append(create_bsdf_data_point(True, incident_angle, 0, wl))
            btdf.append(create_bsdf_data_point(False, incident_angle, 0, wl))
    spectral_brdf.brdf = brdf
    spectral_brdf.btdf = btdf
    spectral_brdf.commit()
    return spectral_brdf


def create_anisotropic_bsdf(speos: Speos):
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
    test_list.append(bsdfdata1.wavelength == bsdfdata2.wavelength)
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


def compare_spectral_bsdf(bsdf1: SpectralBRDF, bsdf2: SpectralBRDF):
    """Compare an spectral bsdf."""
    test_list = []
    bsdf1_data = [
        bsdf1.description,
        bsdf1.wavelength,
        bsdf1.incident_angles,
        bsdf1.has_reflection,
        bsdf1.has_transmission,
        bsdf1.nb_incidents,
    ]
    bsdf2_data = [
        bsdf2.description,
        bsdf2.wavelength,
        bsdf2.incident_angles,
        bsdf2.has_reflection,
        bsdf2.has_transmission,
        bsdf2.nb_incidents,
    ]
    for item1, item2 in zip(bsdf1_data, bsdf2_data):
        test_list.append(item1 == item2)
    if bsdf1.has_reflection and bsdf2.has_reflection:
        for brdf1data, brdf2data in zip(bsdf1.brdf, bsdf2.brdf):
            test_list.append(compare_bsdf_data_point(brdf1data, brdf2data))
    if bsdf1.has_transmission and bsdf2.has_transmission:
        for btdf1data, btdf2data in zip(bsdf1.btdf, bsdf2.btdf):
            test_list.append(compare_bsdf_data_point(btdf1data, btdf2data))
    if all(test_list):
        return True
    else:
        return False


def test_anisotropic_bsdf(speos: Speos):
    """Unit test for anisotropic bsdf class."""
    initial_bsdf = create_anisotropic_bsdf(speos)
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
    assert initial_bsdf.interpolation_settings is None

    # test indices setting and cones data generation
    automatic_interpolation_settings = initial_bsdf.create_interpolation_enhancement(
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
    cons_transmission_data["0.0"]["0.0"]["half_angle"] = 0.523
    cons_transmission_data["0.0"]["0.0"]["height"] = 0.6
    automatic_interpolation_settings.set_interpolation_settings(
        is_brdf=True, settings=cons_reflection_data
    )
    automatic_interpolation_settings.set_interpolation_settings(
        is_brdf=False, settings=cons_transmission_data
    )
    new_cons_reflection_data = (
        automatic_interpolation_settings.get_reflection_interpolation_settings
    )
    new_cons_transmission_data = (
        automatic_interpolation_settings.get_transmission_interpolation_settings
    )
    assert new_cons_reflection_data["0.0"]["0.0"]["half_angle"] == 0.523
    assert new_cons_reflection_data["0.0"]["0.0"]["height"] == 0.5
    assert new_cons_transmission_data["0.0"]["0.0"]["half_angle"] == 0.523
    assert new_cons_transmission_data["0.0"]["0.0"]["height"] == 0.6

    # test the interpolation enhancement settings in a saved bsdf file
    initial_bsdf.save(output_file)
    clean_all_dbs(speos.client)
    saved_bsdf = AnisotropicBSDF(speos=speos, file_path=output_file)
    assert saved_bsdf.interpolation_settings is not None

    # test if the backend data is correct
    saved_cons_data = saved_bsdf._stub.GetSpecularInterpolationEnhancementData(Empty())
    assert (
        saved_cons_data.reflection.anisotropic_samples[0].incidence_samples[0].cone_half_angle
        == 0.523
    )
    assert approx_comparison(
        value1=saved_cons_data.reflection.anisotropic_samples[0]
        .incidence_samples[0]
        .cone_half_angle,
        value2=0.523,
    )
    assert approx_comparison(
        value1=saved_cons_data.reflection.anisotropic_samples[0].incidence_samples[0].cone_height,
        value2=0.5,
    )
    assert approx_comparison(
        value1=saved_cons_data.transmission.anisotropic_samples[0]
        .incidence_samples[0]
        .cone_half_angle,
        value2=0.523,
    )
    assert approx_comparison(
        value1=saved_cons_data.transmission.anisotropic_samples[0].incidence_samples[0].cone_height,
        value2=0.6,
    )

    # test if retrieving interpolation property is correct
    interpolation_settings = saved_bsdf.interpolation_settings
    interpolated_cons_reflection = interpolation_settings.get_reflection_interpolation_settings
    interpolated_cons_transmission = interpolation_settings.get_transmission_interpolation_settings
    assert interpolated_cons_reflection["0.0"]["0.0"]["half_angle"] == 0.523
    assert interpolated_cons_reflection["0.0"]["0.0"]["height"] == 0.5
    assert interpolated_cons_transmission["0.0"]["0.0"]["half_angle"] == 0.523
    assert interpolated_cons_transmission["0.0"]["0.0"]["height"] == 0.6

    # test if retrieving interpolation settings is correct with same index provided
    interpolation_settings = saved_bsdf.create_interpolation_enhancement(index_1=1.5, index_2=1.0)
    interpolated_cons_reflection = interpolation_settings.get_reflection_interpolation_settings
    interpolated_cons_transmission = interpolation_settings.get_transmission_interpolation_settings
    assert interpolated_cons_reflection["0.0"]["0.0"]["half_angle"] != 0.523
    assert interpolated_cons_reflection["0.0"]["0.0"]["height"] != 0.5
    assert interpolated_cons_transmission["0.0"]["0.0"]["half_angle"] != 0.523
    assert interpolated_cons_transmission["0.0"]["0.0"]["height"] != 0.6

    # test if retrieving interpolation settings is correct with different index provided
    interpolation_settings = saved_bsdf.create_interpolation_enhancement(index_1=1, index_2=1.5)
    interpolated_cons_reflection = interpolation_settings.get_reflection_interpolation_settings
    interpolated_cons_transmission = interpolation_settings.get_transmission_interpolation_settings
    assert interpolated_cons_reflection["0.0"]["0.0"]["half_angle"] != 0.523
    assert interpolated_cons_reflection["0.0"]["0.0"]["height"] != 0.5
    assert interpolated_cons_transmission["0.0"]["0.0"]["half_angle"] != 0.523
    assert interpolated_cons_transmission["0.0"]["0.0"]["height"] != 0.6


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


def test_bsdf_error_management(speos: Speos):
    """Unit test of most bsdf error."""
    # BXDF datapoint class
    nb_theta, nb_phi = 5, 5
    thetas, phis, brdf = create_lambertian_bsdf(False, nb_theta, nb_phi)
    data = BxdfDatapoint(False, 0, thetas, phis, brdf)
    with pytest.raises(ValueError, match="Phi values need to be between"):
        t_phi = data.phi_values.tolist()
        t_phi.append(7)
        data.phi_values = t_phi
    with pytest.raises(ValueError, match="Theta values for Transmission need to be between"):
        data.theta_values = t_phi
    t_phi = data.phi_values.tolist()
    t_phi.append(2)
    data.phi_values = t_phi
    assert data.bxdf is None
    with pytest.raises(ValueError, match="bxdf data has incorrect "):
        data.bxdf = brdf
    with pytest.raises(ValueError, match="bxdf data has to be "):
        data.bxdf = [-1, 2, 3]
    with pytest.raises(ValueError, match="Incident angle needs to be between"):
        data.incident_angle = 1.6
    data.is_brdf = True
    with pytest.raises(ValueError, match="Theta values for Reflection need to be between"):
        data.theta_values = t_phi
    with pytest.raises(ValueError, match="Anisotropy angle needs to be between"):
        data.anisotropy = 7
    thetas, phis, brdf = create_lambertian_bsdf(False, nb_theta, nb_phi)
    data_t = BxdfDatapoint(False, 0, thetas, phis, brdf)
    thetas, phis, brdf = create_lambertian_bsdf(True, nb_theta, nb_phi)
    data_r = BxdfDatapoint(True, 0, thetas, phis, brdf)
    new_bsdf = AnisotropicBSDF(speos)
    with pytest.raises(ValueError, match="One or multiple datapoints are transmission"):
        new_bsdf.brdf = [data_t]
    with pytest.raises(ValueError, match="One or multiple datapoints are reflection"):
        new_bsdf.btdf = [data_r]
    new_bsdf.brdf = [data_r]
    new_bsdf.btdf = [data_t]
    with pytest.raises(ValueError, match="You need to define the value for both reflection and "):
        new_bsdf.spectrum_anisotropy = 7.0
    with pytest.raises(ValueError, match="You need to define the value for both reflection and "):
        new_bsdf.spectrum_incidence = 7.0
    new_bsdf.has_transmission = False
    with pytest.raises(
        ValueError,
        match="You need to define the value in radian for both reflection and transmission",
    ):
        new_bsdf.spectrum_anisotropy = 7.0
    with pytest.raises(
        ValueError,
        match="You need to define the value in radian for both reflection and transmission",
    ):
        new_bsdf.spectrum_incidence = 7.0
    with pytest.raises(ValueError, match="You need the same number of wavelength and energy value"):
        new_bsdf.reflection_spectrum = [[1, 2], [1, 2, 3]]
    with pytest.raises(ValueError, match="You need the same number of wavelength and energy value"):
        new_bsdf.transmission_spectrum = [[1, 2, 3], [1, 2]]


def test_spectral_brdf(speos: Speos):
    """Unit test for anisotropic bsdf class."""
    initial_bsdf = create_spectral_brdf(speos)
    bsdf_path = Path(test_path) / "Test_Lambertian.brdf"
    initial_bsdf.save(bsdf_path)

    # check save
    assert does_file_exist(str(bsdf_path))

    # compare loaded with created
    exported_bsdf = SpectralBRDF(speos, bsdf_path)
    assert compare_spectral_bsdf(initial_bsdf, exported_bsdf)

    # remove transmission
    exported_bsdf.has_transmission = False
    assert not compare_spectral_bsdf(initial_bsdf, exported_bsdf)

    # compare only reflective
    initial_bsdf.has_transmission = False
    assert compare_spectral_bsdf(initial_bsdf, exported_bsdf)

    # test reset
    exported_bsdf.reset()
    initial_bsdf.reset()
    assert compare_spectral_bsdf(initial_bsdf, exported_bsdf)

    # remove transmission
    exported_bsdf.has_reflection = False
    assert not compare_spectral_bsdf(initial_bsdf, exported_bsdf)

    # compare only reflective
    initial_bsdf.has_reflection = False
    assert compare_spectral_bsdf(initial_bsdf, exported_bsdf)

    # test reset
    exported_bsdf.reset()
    initial_bsdf.reset()
    assert compare_spectral_bsdf(initial_bsdf, exported_bsdf)

    # test commit True/false
    # change value
    exported_bsdf.has_transmission = False

    # save non changed file
    bsdf_path2 = Path(test_path) / "Test_Lambertian_bsdf2"
    bsdf_path2 = exported_bsdf.save(bsdf_path2, commit=False)
    assert does_file_exist(str(bsdf_path2))

    # save changed file
    bsdf_path3 = Path(test_path) / "Test_Lambertian_bsdf3"
    bsdf_path3 = exported_bsdf.save(bsdf_path3, commit=True)
    assert does_file_exist(str(bsdf_path3))

    # load and compare files
    bsdf2 = SpectralBRDF(speos, bsdf_path2)
    bsdf3 = SpectralBRDF(speos, bsdf_path3)
    assert compare_spectral_bsdf(initial_bsdf, bsdf2)
    assert not compare_spectral_bsdf(bsdf2, bsdf3)

    # compare loaded with created
    exported_bsdf = SpectralBRDF(speos, bsdf_path)
    # test commit True/false
    # change value
    exported_bsdf.has_reflection = False

    # save non changed file
    bsdf_path4 = Path(test_path) / "Test_Lambertian_bsdf4"
    bsdf_path4 = exported_bsdf.save(bsdf_path4, commit=False)
    assert does_file_exist(str(bsdf_path4))

    # save changed file
    bsdf_path5 = Path(test_path) / "Test_Lambertian_bsdf5"
    bsdf_path5 = exported_bsdf.save(bsdf_path5, commit=True)
    assert does_file_exist(str(bsdf_path5))

    # load and compare files
    bsdf4 = SpectralBRDF(speos, bsdf_path4)
    bsdf5 = SpectralBRDF(speos, bsdf_path5)
    assert compare_spectral_bsdf(initial_bsdf, bsdf4)
    assert not compare_spectral_bsdf(bsdf4, bsdf5)
    remove_file(str(bsdf_path))
    remove_file(str(bsdf_path2))
    remove_file(str(bsdf_path3))
    remove_file(str(bsdf_path4))
    remove_file(str(bsdf_path5))


def test_spectral_bsdf_interpolation_enhancement(speos: Speos):
    """Unit test for anisotropic bsdf interpolation class."""
    # test automatic interpolation enhancement
    input_file = Path(test_path) / "Test_not_interpolated.brdf"
    output_file = Path(test_path) / "Test_interpolated.brdf"
    initial_bsdf = SpectralBRDF(speos=speos, file_path=input_file)
    assert initial_bsdf.interpolation_settings is None

    # test indices setting and cones data generation
    automatic_interpolation_settings = initial_bsdf.create_interpolation_enhancement(
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
                cons_data.wavelength_incidence_samples[
                    (cons_key_index + 1) * incidence_key_index
                ].reflection.cone_half_angle
                == cons_reflection_data[cons_key][incidence_key]["half_angle"]
            )
            assert (
                cons_data.wavelength_incidence_samples[
                    (cons_key_index + 1) * incidence_key_index
                ].reflection.cone_height
                == cons_reflection_data[cons_key][incidence_key]["height"]
            )

    for cons_key_index, cons_key in enumerate(cons_transmission_data.keys()):
        for incidence_key_index, incidence_key in enumerate(
            cons_transmission_data[cons_key].keys()
        ):
            assert (
                cons_data.wavelength_incidence_samples[
                    (cons_key_index + 1) * incidence_key_index
                ].transmission.cone_half_angle
                == cons_transmission_data[cons_key][incidence_key]["half_angle"]
            )
            assert (
                cons_data.wavelength_incidence_samples[
                    (cons_key_index + 1) * incidence_key_index
                ].transmission.cone_height
                == cons_transmission_data[cons_key][incidence_key]["height"]
            )

    # test modifying the interpolation setting dictionary
    # test cannot change a key's value if the value is a fixed dictionary
    with pytest.raises(ValueError, match="Cannot update key 380.0 with a FixedKeyDict as value"):
        cons_transmission_data["380.0"] = 0
    # test cannot add a new key
    with pytest.raises(KeyError, match="Cannot add new key: 1.0 is not allowed."):
        cons_reflection_data["1.0"] = 2
    # test modifying the interpolation settings and apply settings
    cons_reflection_data["380.0"]["0.0"]["half_angle"] = 0.523
    cons_reflection_data["380.0"]["0.0"]["height"] = 0.5
    cons_transmission_data["380.0"]["0.0"]["half_angle"] = 0.523
    cons_transmission_data["380.0"]["0.0"]["height"] = 0.6
    automatic_interpolation_settings.set_interpolation_settings(
        is_brdf=True, settings=cons_reflection_data
    )
    automatic_interpolation_settings.set_interpolation_settings(
        is_brdf=False, settings=cons_transmission_data
    )
    new_cons_reflection_data = (
        automatic_interpolation_settings.get_reflection_interpolation_settings
    )
    new_cons_transmission_data = (
        automatic_interpolation_settings.get_transmission_interpolation_settings
    )
    assert new_cons_reflection_data["380.0"]["0.0"]["half_angle"] == 0.523
    assert new_cons_reflection_data["380.0"]["0.0"]["height"] == 0.5
    assert new_cons_transmission_data["380.0"]["0.0"]["half_angle"] == 0.523
    assert new_cons_transmission_data["380.0"]["0.0"]["height"] == 0.6

    # test the interpolation enhancement settings in a saved bsdf file
    initial_bsdf.save(output_file)
    clean_all_dbs(speos.client)
    saved_bsdf = SpectralBRDF(speos=speos, file_path=output_file)
    assert saved_bsdf.interpolation_settings is not None

    # test if the backend data is correct
    saved_cons_data = saved_bsdf._stub.GetSpecularInterpolationEnhancementData(Empty())
    assert saved_cons_data.wavelength_incidence_samples[0].reflection.cone_half_angle == 0.523
    assert approx_comparison(
        value1=saved_cons_data.wavelength_incidence_samples[0].reflection.cone_half_angle,
        value2=0.523,
    )
    assert approx_comparison(
        value1=saved_cons_data.wavelength_incidence_samples[0].reflection.cone_height,
        value2=0.5,
    )
    assert approx_comparison(
        value1=saved_cons_data.wavelength_incidence_samples[0].transmission.cone_half_angle,
        value2=0.523,
    )
    assert approx_comparison(
        value1=saved_cons_data.wavelength_incidence_samples[0].transmission.cone_height,
        value2=0.6,
    )

    # test if retrieving interpolation property is correct
    interpolation_settings = saved_bsdf.interpolation_settings
    interpolated_cons_reflection = interpolation_settings.get_reflection_interpolation_settings
    interpolated_cons_transmission = interpolation_settings.get_transmission_interpolation_settings
    assert interpolated_cons_reflection["380.0"]["0.0"]["half_angle"] == 0.523
    assert interpolated_cons_reflection["380.0"]["0.0"]["height"] == 0.5
    assert interpolated_cons_transmission["380.0"]["0.0"]["half_angle"] == 0.523
    assert interpolated_cons_transmission["380.0"]["0.0"]["height"] == 0.6

    # test if retrieving interpolation settings is correct with same index provided
    interpolation_settings = saved_bsdf.create_interpolation_enhancement(index_1=1.5, index_2=1.0)
    interpolated_cons_reflection = interpolation_settings.get_reflection_interpolation_settings
    interpolated_cons_transmission = interpolation_settings.get_transmission_interpolation_settings
    assert interpolated_cons_reflection["380.0"]["0.0"]["half_angle"] != 0.523
    assert interpolated_cons_reflection["380.0"]["0.0"]["height"] != 0.5
    assert interpolated_cons_transmission["380.0"]["0.0"]["half_angle"] != 0.523
    assert interpolated_cons_transmission["380.0"]["0.0"]["height"] != 0.6

    # test if retrieving interpolation settings is correct with different index provided
    interpolation_settings = saved_bsdf.create_interpolation_enhancement(index_1=1, index_2=1.5)
    interpolated_cons_reflection = interpolation_settings.get_reflection_interpolation_settings
    interpolated_cons_transmission = interpolation_settings.get_transmission_interpolation_settings
    assert interpolated_cons_reflection["380.0"]["0.0"]["half_angle"] != 0.523
    assert interpolated_cons_reflection["380.0"]["0.0"]["height"] != 0.5
    assert interpolated_cons_transmission["380.0"]["0.0"]["half_angle"] != 0.523
    assert interpolated_cons_transmission["380.0"]["0.0"]["height"] != 0.6


def test_spectral_brdf_error_management(speos: Speos):
    """Unit test of most bsdf error."""
    # BXDF datapoint class
    nb_theta, nb_phi = 5, 5
    thetas, phis, brdf = create_lambertian_bsdf(False, nb_theta, nb_phi)
    data_t1 = BxdfDatapoint(False, 0, thetas, phis, brdf)
    data_t2 = BxdfDatapoint(False, 0.1, thetas, phis, brdf, wavelength=400)
    thetas, phis, brdf = create_lambertian_bsdf(True, nb_theta, nb_phi)
    data_r1 = BxdfDatapoint(True, 0, thetas, phis, brdf)
    data_r2 = BxdfDatapoint(True, 0.1, thetas, phis, brdf, wavelength=400)
    new_bsdf = SpectralBRDF(speos)
    new_bsdf.brdf = [data_r1, data_r2]
    new_bsdf.btdf = [data_t1]
    err = new_bsdf.sanity_check()
    assert (
        err == "Incidence and/or Wavelength information between reflection and transmission"
        " is not identical. "
    )
    with pytest.raises(
        ValueError,
        match="Incidence and/or Wavelength information between reflection and transmission"
        " is not identical",
    ):
        new_bsdf.commit()
    new_bsdf.has_reflection = False
    new_bsdf.btdf = [data_t1, data_t2]
    err = new_bsdf.sanity_check()
    assert err == (
        "The bsdf is missing information's for the for the following incidence angles one"
        " or more wavelengths are missing: [0.1, 0]. The bsdf is missing information's for"
        " the for the following wavelength one or more incidence angles are missing: [400, 555]. "
    )
    with pytest.raises(
        ValueError,
        match="The bsdf is missing information's for the for the following incidence angles one",
    ):
        new_bsdf.commit()
    new_bsdf.has_reflection = True
    new_bsdf.has_transmission = False
    new_bsdf.brdf = [data_r1, data_r2]
    err = new_bsdf.sanity_check()
    assert err == (
        "The bsdf is missing information's for the for the following incidence angles one"
        " or more wavelengths are missing: [0.1, 0]. The bsdf is missing information's for"
        " the for the following wavelength one or more incidence angles are missing: [400, 555]. "
    )
    with pytest.raises(
        ValueError,
        match="The bsdf is missing information's for the for the following incidence angles one",
    ):
        new_bsdf.commit()
