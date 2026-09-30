# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

"""Test the ``*.material`` file format."""

import pytest

from ansys.speos.core import (
    MaterialBirefringentCurve,
    MaterialBirefringentKettlerHelmholtz,
    MaterialBirefringentSellmeier,
    MaterialConstringence,
    MaterialDispersionCurve,
    MaterialFile,
    MaterialKettlerHelmholtz,
    MaterialMetallicCurve,
    MaterialSellmeier,
    VolumeScatteringDoubleHenyeyGreenstein,
    VolumeScatteringGegenbauer,
    VolumeScatteringHenyeyGreenstein,
    VolumeScatteringUserDefined,
)
from tests.input_files import read_lines


@pytest.fixture
def metallic_material():
    """Build a metallic material, which holds nothing but its complex refractive index."""
    return MaterialFile(
        description="Gold",
        material_type="Metallic",
        dispersion=MaterialMetallicCurve(
            wavelengths=[486.0, 532.0, 643.0],
            indices=[1.0821, 0.55731, 0.18664],
            extinctions=[1.7661, 2.1222, 3.3662],
        ),
    )


@pytest.fixture
def birefringent_material():
    """Build a birefringent material with an absorption curve along its three axes."""
    return MaterialFile(
        description="Calcite",
        material_type="Birefringent",
        dispersion=MaterialBirefringentCurve(
            wavelength=550.0, index_a=1.5, index_b=1.51, index_c=1.65, optical_class=2
        ),
        absorption_wavelengths=[486.0, 532.0, 643.0],
        absorption_values=[0.1, 0.2, 0.3],
        absorption_values_b=[0.4, 0.5, 0.6],
        absorption_values_c=[0.7, 0.8, 0.9],
    )


@pytest.fixture
def documented_material():
    """Build the non-scattering material used as an example by the Speos documentation."""
    return MaterialFile(
        description="Material description",
        dispersion=MaterialConstringence(constringence=57.2, index=1.49),
        absorption_wavelengths=[486.0, 532.0, 643.0],
        absorption_values=[0.0001, 0.00015, 0.0005],
    )


def test_non_scattering_write_matches_the_documented_layout(documented_material, tmp_path):
    """A written file must match the layout described by the Speos documentation."""
    path = documented_material.save(tmp_path / "material.material")

    assert path.suffix == MaterialFile.EXTENSION
    assert read_lines(path) == [
        "OPTIS - Material file v13",
        "Material description",
        "Isotropic",
        "Constringence",
        "57.2",
        "1.49",
        "3",
        "486 0.0001",
        "532 0.00015",
        "643 0.0005",
        "1",
        "1",
        "0",
    ]


def test_non_scattering_round_trip(documented_material, tmp_path):
    """Reading back a written file must give an equivalent model."""
    path = documented_material.save(tmp_path / "material.material")

    assert MaterialFile.load(path) == documented_material


@pytest.mark.parametrize(
    ("dispersion", "expected"),
    [
        (MaterialConstringence(57.2, 1.49), ["Constringence", "57.2", "1.49"]),
        (
            MaterialDispersionCurve(wavelengths=[480.0, 650.0], indices=[1.51, 1.5]),
            ["Dispersion_Curve", "2", "480 1.51", "650 1.5"],
        ),
        (
            MaterialSellmeier(1.03961, 0.0060007, 0.231792, 0.0200179, 1.01047, 103.561),
            ["SellMeier", "1.03961", "0.0060007", "0.231792", "0.0200179", "1.01047", "103.561"],
        ),
        (
            MaterialKettlerHelmholtz(1.0, 0.01, 0.02, 0.005, 0.001, 0.0001),
            ["Kettler-Helmotz", "1", "0.01", "0.02", "0.005", "0.001", "0.0001"],
        ),
    ],
)
def test_every_dispersion_model_round_trips(dispersion, expected, tmp_path):
    """Each of the four index variation models must be written and read back."""
    material = MaterialFile(
        dispersion=dispersion, absorption_wavelengths=[550.0], absorption_values=[0.0]
    )
    path = material.save(tmp_path / "material.material")

    assert read_lines(path)[3 : 3 + len(expected)] == expected
    assert MaterialFile.load(path) == material


def test_henyey_greenstein_write_matches_the_documented_layout(tmp_path):
    """The Henyey-Greenstein scattering block must match the documented layout."""
    material = MaterialFile(
        description="Demo material",
        absorption_wavelengths=[550.0],
        absorption_values=[0.0],
        scattering_wavelengths=[480.0, 555.0, 650.0],
        scattering_values=[0.1, 0.1, 0.1],
        scattering=VolumeScatteringHenyeyGreenstein(
            wavelengths=[480.0, 555.0, 650.0], anisotropies=[0.8, 0.9, 0.9]
        ),
    )
    path = material.save(tmp_path / "hg.material")

    assert read_lines(path)[-11:] == [
        "1",
        "OPTIS - Volumic Scattering file v1",
        "1",
        "3",
        "480 0.1",
        "555 0.1",
        "650 0.1",
        "3",
        "480 0.8",
        "555 0.9",
        "650 0.9",
    ]
    assert MaterialFile.load(path) == material


def test_gegenbauer_bumps_the_scattering_block_version(tmp_path):
    """The Gegenbauer model needs the v3 flavor of the scattering block."""
    material = MaterialFile(
        absorption_wavelengths=[550.0],
        absorption_values=[0.0],
        scattering_wavelengths=[480.0],
        scattering_values=[0.1],
        scattering=VolumeScatteringGegenbauer(
            wavelengths=[480.0, 555.0, 650.0],
            anisotropies=[0.9, 0.95, 0.96],
            alphas=[0.45, 0.5, 0.51],
        ),
    )
    path = material.save(tmp_path / "gegenbauer.material")

    assert read_lines(path)[-8:] == [
        "OPTIS - Volumic Scattering file v3",
        "6",
        "1",
        "480 0.1",
        "3",
        "480 0.9 0.45",
        "555 0.95 0.5",
        "650 0.96 0.51",
    ]
    assert MaterialFile.load(path) == material


def test_double_henyey_greenstein_round_trips(tmp_path):
    """The double Henyey-Greenstein model must be written and read back."""
    material = MaterialFile(
        absorption_wavelengths=[550.0],
        absorption_values=[0.0],
        scattering_wavelengths=[480.0],
        scattering_values=[0.1],
        scattering=VolumeScatteringDoubleHenyeyGreenstein(
            wavelengths=[480.0, 555.0],
            anisotropies_1=[0.91, 0.8],
            anisotropies_2=[0.9, 0.95],
            ratios=[0.45, 0.5],
        ),
    )
    path = material.save(tmp_path / "dhg.material")

    assert read_lines(path)[-3:] == ["2", "480 0.91 0.9 0.45", "555 0.8 0.95 0.5"]
    assert MaterialFile.load(path) == material


def test_user_defined_phase_function_round_trips(tmp_path):
    """The user defined phase function must be written and read back."""
    material = MaterialFile(
        absorption_wavelengths=[550.0],
        absorption_values=[0.0],
        scattering_wavelengths=[480.0, 555.0, 650.0],
        scattering_values=[0.1, 0.1, 0.1],
        scattering=VolumeScatteringUserDefined(
            wavelengths=[480.0, 550.0, 650.0],
            angles=[0.0, 45.0, 90.0, 180.0],
            values=[
                [0.0, 0.0, 100.0],
                [0.0, 0.0, 100.0],
                [50.0, 100.0, 100.0],
                [100.0, 50.0, 100.0],
            ],
        ),
    )
    path = material.save(tmp_path / "user.material")

    assert read_lines(path)[-7:] == [
        "3",
        "4",
        "480 550 650",
        "0 0 0 100",
        "45 0 0 100",
        "90 50 100 100",
        "180 100 50 100",
    ]
    assert MaterialFile.load(path) == material


def test_a_material_needs_an_absorption_curve(tmp_path):
    """Speos always needs the absorption variation of the material."""
    with pytest.raises(ValueError, match="must not be empty"):
        MaterialFile().save(tmp_path / "empty.material")


def test_a_scattering_material_needs_a_diffusion_curve(tmp_path):
    """A scattering material needs the diffusion coefficient for each wavelength."""
    material = MaterialFile(
        absorption_wavelengths=[550.0],
        absorption_values=[0.0],
        scattering=VolumeScatteringHenyeyGreenstein(anisotropies=[0.5]),
    )

    with pytest.raises(ValueError, match="scattering_wavelengths"):
        material.save(tmp_path / "invalid.material")


def test_an_out_of_range_anisotropy_is_rejected(tmp_path):
    """The Henyey-Greenstein anisotropy factor lives between -1 and 1."""
    material = MaterialFile(
        absorption_wavelengths=[550.0],
        absorption_values=[0.0],
        scattering_wavelengths=[550.0],
        scattering_values=[0.1],
        scattering=VolumeScatteringHenyeyGreenstein(anisotropies=[1.5]),
    )

    with pytest.raises(ValueError, match="between -1 and 1"):
        material.save(tmp_path / "invalid.material")


def test_an_unknown_dispersion_keyword_is_reported(tmp_path):
    """Reading must report an index variation mode it does not know."""
    path = tmp_path / "unknown.material"
    path.write_text("OPTIS - Material file v13\nSomething\nIsotropic\nQuantum\n", encoding="utf-8")

    with pytest.raises(ValueError, match="unknown index variation mode"):
        MaterialFile.load(path)


def test_metallic_write_matches_the_speos_layout(metallic_material, tmp_path):
    """A metallic file stops after its index curve, the extinction holds the absorption."""
    path = metallic_material.save(tmp_path / "gold.material")

    assert read_lines(path) == [
        "OPTIS - Material file v13",
        "Gold",
        "Metallic",
        "Dispersion_Curve",
        "3",
        "486 1.0821 1.7661",
        "532 0.55731 2.1222",
        "643 0.18664 3.3662",
    ]
    assert MaterialFile.load(path) == metallic_material


def test_a_metallic_material_needs_an_index_curve(tmp_path):
    """A metallic material without its complex index cannot be written."""
    material = MaterialFile(material_type="Metallic", dispersion=MaterialMetallicCurve())

    with pytest.raises(ValueError, match="must not be empty"):
        material.save(tmp_path / "invalid.material")


def test_a_metallic_material_rejects_another_dispersion_model(tmp_path):
    """Speos only describes a metal by its complex refractive index."""
    material = MaterialFile(material_type="Metallic", dispersion=MaterialConstringence())

    with pytest.raises(ValueError, match="needs a MaterialMetallicCurve"):
        material.save(tmp_path / "invalid.material")


def test_a_metallic_material_rejects_an_absorption_curve(tmp_path, metallic_material):
    """The metallic flavor of the format has nowhere to store an absorption curve."""
    metallic_material.absorption_wavelengths = [550.0]
    metallic_material.absorption_values = [0.1]

    with pytest.raises(ValueError, match="no absorption curve"):
        metallic_material.save(tmp_path / "invalid.material")


def test_a_metallic_material_rejects_a_scattering(tmp_path, metallic_material):
    """The metallic flavor of the format has nowhere to store a volume scattering."""
    metallic_material.scattering = VolumeScatteringHenyeyGreenstein(anisotropies=[0.5])

    with pytest.raises(ValueError, match="cannot scatter light"):
        metallic_material.save(tmp_path / "invalid.material")


def test_a_metallic_file_rejects_another_dispersion_keyword(tmp_path):
    """Reading a metallic material given by an analytic model must fail clearly."""
    path = tmp_path / "bad_metal.material"
    path.write_text("OPTIS - Material file v13\nGold\nMetallic\nSellMeier\n", encoding="utf-8")

    with pytest.raises(ValueError, match="metallic material needs a 'Dispersion_Curve'"):
        MaterialFile.load(path)


def test_birefringent_curve_write_matches_the_speos_layout(birefringent_material, tmp_path):
    """The indices of the three axes frame the optical class, and each axis absorbs."""
    path = birefringent_material.save(tmp_path / "calcite.material")

    assert read_lines(path) == [
        "OPTIS - Material file v13",
        "Calcite",
        "Birefringent",
        "Dispersion_Curve",
        "1",
        "550 1.5",
        "2",
        "1.51 1.65",
        "1 0 0",
        "0 1 0",
        "3",
        "486 0.1",
        "532 0.2",
        "643 0.3",
        "0.4 0.7",
        "0.5 0.8",
        "0.6 0.9",
        "1",
        "1",
        "0",
    ]
    assert MaterialFile.load(path) == birefringent_material


def test_birefringent_sellmeier_interleaves_the_two_last_axes(birefringent_material, tmp_path):
    """The coefficients of the b and the c axes alternate, one number per line."""
    birefringent_material.dispersion = MaterialBirefringentSellmeier(
        a=MaterialSellmeier(1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
        b=MaterialSellmeier(10.0, 20.0, 30.0, 40.0, 50.0, 60.0),
        c=MaterialSellmeier(11.0, 21.0, 31.0, 41.0, 51.0, 61.0),
        optical_class=1,
    )
    path = birefringent_material.save(tmp_path / "sellmeier.material")

    assert read_lines(path)[3:23] == [
        "SellMeier",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "1",
        "10",
        "11",
        "20",
        "21",
        "30",
        "31",
        "40",
        "41",
        "50",
        "51",
        "60",
        "61",
    ]
    assert MaterialFile.load(path) == birefringent_material


def test_birefringent_kettler_helmholtz_round_trips(birefringent_material, tmp_path):
    """The Kettler-Helmholtz flavor uses the same layout as the Sellmeier one."""
    birefringent_material.dispersion = MaterialBirefringentKettlerHelmholtz(
        a=MaterialKettlerHelmholtz(2.4, -0.01, 0.001),
        b=MaterialKettlerHelmholtz(2.5, -0.02, 0.002),
        c=MaterialKettlerHelmholtz(2.6, -0.03, 0.003),
    )
    path = birefringent_material.save(tmp_path / "helmholtz.material")

    assert read_lines(path)[3] == "Kettler-Helmotz"
    assert MaterialFile.load(path) == birefringent_material


def test_a_birefringent_material_can_scatter(birefringent_material, tmp_path):
    """The scattering block closes a birefringent file the way it closes an isotropic one."""
    birefringent_material.scattering_wavelengths = [486.0]
    birefringent_material.scattering_values = [0.1]
    birefringent_material.scattering = VolumeScatteringHenyeyGreenstein(anisotropies=[0.9])
    path = birefringent_material.save(tmp_path / "scattering.material")

    assert read_lines(path)[-6:] == [
        "OPTIS - Volumic Scattering file v1",
        "1",
        "1",
        "486 0.1",
        "1",
        "0.9",
    ]
    assert MaterialFile.load(path) == birefringent_material


def test_a_birefringent_material_rejects_an_isotropic_dispersion(tmp_path):
    """An isotropic model cannot describe the three axes of a birefringent material."""
    material = MaterialFile(
        material_type="Birefringent",
        dispersion=MaterialConstringence(),
        absorption_wavelengths=[550.0],
        absorption_values=[0.0],
    )

    with pytest.raises(ValueError, match="MaterialBirefringentCurve"):
        material.save(tmp_path / "invalid.material")


def test_an_isotropic_material_rejects_a_birefringent_dispersion(tmp_path):
    """A birefringent model needs the birefringent flavor of the format."""
    material = MaterialFile(
        dispersion=MaterialBirefringentCurve(),
        absorption_wavelengths=[550.0],
        absorption_values=[0.0],
    )

    with pytest.raises(ValueError, match="MaterialConstringence"):
        material.save(tmp_path / "invalid.material")


def test_an_unknown_optical_class_is_rejected(birefringent_material, tmp_path):
    """Speos only knows the negative uniaxial, positive uniaxial and biaxial classes."""
    birefringent_material.dispersion.optical_class = 3

    with pytest.raises(ValueError, match="optical_class must be 0"):
        birefringent_material.save(tmp_path / "invalid.material")


def test_an_axis_needs_three_coordinates(birefringent_material, tmp_path):
    """The b and c axes are written as 3D directions."""
    birefringent_material.axis_k = [0.0, 1.0]

    with pytest.raises(ValueError, match="axis_k must hold 3 coordinates"):
        birefringent_material.save(tmp_path / "invalid.material")


def test_each_axis_absorbs_at_every_wavelength(birefringent_material, tmp_path):
    """The absorption along b and c share the wavelengths of the absorption along a."""
    birefringent_material.absorption_values_c = [0.7]

    with pytest.raises(ValueError, match="absorption_values_c must hold one value"):
        birefringent_material.save(tmp_path / "invalid.material")


def test_a_birefringent_index_curve_holds_a_single_wavelength(tmp_path):
    """Speos does not make the explicit indices of a birefringent material vary."""
    path = tmp_path / "two_wavelengths.material"
    path.write_text(
        "OPTIS - Material file v13\nCalcite\nBirefringent\nDispersion_Curve\n2\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expected a single wavelength, got 2"):
        MaterialFile.load(path)
