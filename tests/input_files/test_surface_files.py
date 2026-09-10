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

"""Test the surface optical property file formats."""

import pytest

from ansys.speos.core import (
    CoatedSurfaceFile,
    CoatedSurfaceSample,
    ScatteringSurfaceFile,
    ScatteringSurfaceSample,
    SimpleScatteringSurfaceFile,
)
from tests.input_files import ASSETS_DIR, read_lines


@pytest.fixture
def documented_scattering_surface():
    """Build the scattering surface used as an example by the Speos documentation.

    At normal incidence and 400 nm the surface reflects 30% specularly and 20% in a
    Lambertian way, transmits 20% specularly and 10% in a Lambertian way, and absorbs the
    remaining 20%. At 45 degrees and 600 nm it reflects and transmits 20% in a Gaussian
    lobe and absorbs 60%.
    """
    blank = ScatteringSurfaceSample()
    at_400 = ScatteringSurfaceSample(
        specular_reflection=30.0,
        specular_transmission=20.0,
        lambertian_reflection=20.0,
        lambertian_transmission=10.0,
    )
    at_600 = ScatteringSurfaceSample(
        gaussian_reflection=20.0,
        gaussian_transmission=20.0,
        gaussian_fwhm_incidence_reflection=30.0,
        gaussian_fwhm_incidence_transmission=5.0,
        gaussian_fwhm_perpendicular_reflection=5.0,
        gaussian_fwhm_perpendicular_transmission=30.0,
    )
    return ScatteringSurfaceFile(
        wavelengths=[400.0, 600.0],
        incident_angles=[0.0, 45.0, 90.0],
        samples=[[at_400, blank], [blank, at_600], [blank, blank]],
    )


def test_scattering_surface_write_matches_the_documented_layout(
    documented_scattering_surface, tmp_path
):
    """A written file must match the layout described by the Speos documentation."""
    path = documented_scattering_surface.save(tmp_path / "surface.scattering")

    assert path.suffix == ScatteringSurfaceFile.EXTENSION
    assert read_lines(path) == [
        "OPTIS - Scattering surface file v1.0",
        "Scattering surface",
        "3 2",
        "\t400\t\t600\t\t",
        "0\t30\t20\t0\t0\t",
        "\t20\t10\t0\t0\t",
        "\t0\t0\t0\t0\t",
        "\t0\t0\t0\t0\t",
        "\t0\t0\t0\t0\t",
        "45\t0\t0\t0\t0\t",
        "\t0\t0\t0\t0\t",
        "\t0\t0\t20\t20\t",
        "\t0\t0\t30\t5\t",
        "\t0\t0\t5\t30\t",
        "90\t0\t0\t0\t0\t",
        "\t0\t0\t0\t0\t",
        "\t0\t0\t0\t0\t",
        "\t0\t0\t0\t0\t",
        "\t0\t0\t0\t0\t",
    ]


def test_scattering_surface_round_trip(documented_scattering_surface, tmp_path):
    """Reading back a written file must give an equivalent model."""
    path = documented_scattering_surface.save(tmp_path / "surface.scattering")

    assert ScatteringSurfaceFile.load(path) == documented_scattering_surface


def test_scattering_surface_absorption_completes_the_budget(documented_scattering_surface):
    """The absorption must be the complement to 100 of the other contributions."""
    samples = documented_scattering_surface.samples

    assert samples[0][0].absorption == pytest.approx(20.0)
    assert samples[1][1].absorption == pytest.approx(60.0)
    assert samples[2][0].absorption == pytest.approx(100.0)


def test_scattering_surface_needs_the_full_incidence_range(documented_scattering_surface, tmp_path):
    """Speos needs the incidences to span 0 to 90 degrees."""
    documented_scattering_surface.incident_angles = [0.0, 45.0, 60.0]

    with pytest.raises(ValueError, match="0 and 90 degrees"):
        documented_scattering_surface.save(tmp_path / "surface.scattering")


def test_scattering_surface_needs_two_wavelengths(tmp_path):
    """Speos needs at least two wavelengths."""
    surface = ScatteringSurfaceFile(
        wavelengths=[400.0],
        incident_angles=[0.0, 90.0],
        samples=[[ScatteringSurfaceSample()], [ScatteringSurfaceSample()]],
    )

    with pytest.raises(ValueError, match="two wavelengths"):
        surface.save(tmp_path / "surface.scattering")


def test_scattering_surface_rejects_an_over_unity_budget(documented_scattering_surface, tmp_path):
    """The reflection and transmission contributions must not exceed 100%."""
    documented_scattering_surface.samples[0][0].lambertian_reflection = 80.0

    with pytest.raises(ValueError, match="absorption of -40"):
        documented_scattering_surface.save(tmp_path / "surface.scattering")


@pytest.fixture
def documented_coated_surface():
    """Build the coating used as an example by the Speos documentation."""
    rows = {
        0.0: [(31.9, 68.1), (1.5, 98.5), (25.7, 74.3)],
        50.0: [(11.3, 88.7), (11.4, 88.6), (23.3, 76.7)],
        70.0: [(15.0, 85.0), (15.2, 84.8), (26.3, 73.7)],
        90.0: [(100.0, 0.0), (100.0, 0.0), (100.0, 0.0)],
    }
    return CoatedSurfaceFile(
        wavelengths=[480.0, 580.0, 780.0],
        incident_angles=list(rows),
        samples=[
            [
                CoatedSurfaceSample(reflection, transmission, reflection, transmission)
                for reflection, transmission in row
            ]
            for row in rows.values()
        ],
        description="Coating File Example",
    )


def test_coated_surface_write_matches_the_documented_layout(documented_coated_surface, tmp_path):
    """A written file must match the layout described by the Speos documentation."""
    path = documented_coated_surface.save(tmp_path / "coating.coated")

    assert path.suffix == CoatedSurfaceFile.EXTENSION
    assert read_lines(path) == [
        "OPTIS - Coated surface file v1.0",
        "Coating File Example",
        "4 3",
        "\t480\t\t580\t\t780\t\t",
        "0\t31.9\t68.1\t1.5\t98.5\t25.7\t74.3\t",
        "\t31.9\t68.1\t1.5\t98.5\t25.7\t74.3\t",
        "50\t11.3\t88.7\t11.4\t88.6\t23.3\t76.7\t",
        "\t11.3\t88.7\t11.4\t88.6\t23.3\t76.7\t",
        "70\t15\t85\t15.2\t84.8\t26.3\t73.7\t",
        "\t15\t85\t15.2\t84.8\t26.3\t73.7\t",
        "90\t100\t0\t100\t0\t100\t0\t",
        "\t100\t0\t100\t0\t100\t0\t",
    ]


def test_coated_surface_round_trip(documented_coated_surface, tmp_path):
    """Reading back a written file must give an equivalent model."""
    path = documented_coated_surface.save(tmp_path / "coating.coated")

    assert CoatedSurfaceFile.load(path) == documented_coated_surface


def test_coated_surface_rejects_an_out_of_range_value(documented_coated_surface, tmp_path):
    """Each coating value stays a percentage.

    A polarization summing to more than 100 percent is not rejected though: the coating
    sample published by Ansys does overrun it, see ``test_reference_files``.
    """
    documented_coated_surface.samples[0][0].reflection_s = 120.0

    with pytest.raises(ValueError, match="reflection_s must be between 0 and 100"):
        documented_coated_surface.save(tmp_path / "coating.coated")


@pytest.mark.parametrize(
    ("file_name", "mode", "lambertian", "gaussian_fwhm"),
    [
        ("L100 2.simplescattering", "Reflection", 100.0, 5.0),
        ("Texture.1.speos/100% transparent.simplescattering", "Transmission", 0.0, 25.0),
    ],
)
def test_simple_scattering_read_files_produced_by_speos(file_name, mode, lambertian, gaussian_fwhm):
    """A file produced by Speos must be read back into an equivalent model."""
    surface = SimpleScatteringSurfaceFile.load(ASSETS_DIR / file_name)

    assert surface.mode == mode
    assert surface.absorption == 0.0
    assert surface.lambertian == lambertian
    assert surface.gaussian == 0.0
    assert surface.gaussian_fwhm == gaussian_fwhm
    assert surface.description == "Scattering surface"


def test_simple_scattering_round_trip_a_file_produced_by_speos(tmp_path):
    """Reading and writing a file produced by Speos must not lose any data."""
    surface = SimpleScatteringSurfaceFile.load(ASSETS_DIR / "L100 2.simplescattering")
    path = surface.save(tmp_path / "copy.simplescattering")

    assert read_lines(path) == read_lines(ASSETS_DIR / "L100 2.simplescattering")
    assert SimpleScatteringSurfaceFile.load(path) == surface


def test_simple_scattering_both_sides_with_a_fresnel_split(tmp_path):
    """The two-sided flavor must leave line 4 empty and flag the Fresnel split."""
    surface = SimpleScatteringSurfaceFile(
        mode="Both",
        absorption=10.0,
        lambertian=20.0,
        gaussian=30.0,
        gaussian_fwhm=4.0,
        lambertian_transmission=40.0,
        gaussian_transmission=50.0,
        gaussian_fwhm_transmission=8.0,
    )
    path = surface.save(tmp_path / "both.simplescattering")

    assert surface.fresnel is True
    assert read_lines(path) == [
        "OPTIS - Simple scattering surface file v2.0",
        "Scattering surface",
        "Both",
        "",
        "10 20 40 30 50",
        "4 8",
        "1",
    ]
    assert SimpleScatteringSurfaceFile.load(path) == surface


def test_simple_scattering_both_sides_with_an_explicit_split(tmp_path):
    """Setting a reflection share must replace the Fresnel split by that value."""
    surface = SimpleScatteringSurfaceFile(
        mode="Both", lambertian=10.0, lambertian_transmission=20.0, reflection=35.0
    )
    path = surface.save(tmp_path / "both.simplescattering")

    assert surface.fresnel is False
    assert read_lines(path)[-2:] == ["0", "35"]
    assert SimpleScatteringSurfaceFile.load(path) == surface


def test_simple_scattering_rejects_an_unknown_mode(tmp_path):
    """Only the three modes known by Speos are accepted."""
    with pytest.raises(ValueError, match="mode must be one of"):
        SimpleScatteringSurfaceFile(mode="Diffuse").save(tmp_path / "invalid.simplescattering")


def test_simple_scattering_rejects_an_over_unity_budget(tmp_path):
    """The Lambertian and Gaussian shares of a side must not exceed 100%."""
    surface = SimpleScatteringSurfaceFile(lambertian=60.0, gaussian=60.0)

    with pytest.raises(ValueError, match="must not sum to more than 100"):
        surface.save(tmp_path / "invalid.simplescattering")
