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
    MaterialConstringence,
    MaterialDispersionCurve,
    MaterialFile,
    MaterialKettlerHelmholtz,
    MaterialSellmeier,
    VolumeScatteringDoubleHenyeyGreenstein,
    VolumeScatteringGegenbauer,
    VolumeScatteringHenyeyGreenstein,
    VolumeScatteringUserDefined,
)
from tests.input_files import read_lines


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
