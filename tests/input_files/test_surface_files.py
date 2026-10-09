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

from dataclasses import is_dataclass
import warnings

import pytest

from ansys.speos.core import (
    CoatedSurfaceFile,
    CoatedSurfaceSample,
    ScatteringSurfaceFile,
    ScatteringSurfaceSample,
    SimpleScatteringSurfaceFile,
)
from ansys.speos.core.input_files.coated_surface import _COATING_FIELDS
from ansys.speos.core.input_files.scattering_surface import (
    _CONTRIBUTIONS as CONTRIBUTIONS,
    _WIDTHS as WIDTHS,
)
from tests.input_files import ASSETS_DIR, read_lines


@pytest.mark.parametrize("model_class", [CoatedSurfaceFile, ScatteringSurfaceFile])
@pytest.mark.parametrize("counts", ["2.5 2", "2 2.5", "2.0 2", "2 2e0", "0 2", "2 -1", "inf 2"])
def test_surface_count_headers_are_strict(model_class, counts, tmp_path):
    """Both surface formats validate paired counts before consuming the grid."""
    path = tmp_path / ("invalid" + model_class.EXTENSION)
    path.write_text(f"{model_class.HEADER}\ndescription\n{counts}\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"line 3: expected an integer"):
        model_class.load(path)


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


def test_scattering_surface_needs_the_full_incidence_range(documented_scattering_surface):
    """Speos needs the incidences to span 0 to 90 degrees."""
    with pytest.raises(ValueError, match="0 and 90 degrees"):
        documented_scattering_surface.incident_angles = [0.0, 45.0, 60.0]
    assert documented_scattering_surface.incident_angles == [0.0, 45.0, 90.0]


def test_scattering_surface_needs_two_wavelengths():
    """Speos needs at least two wavelengths."""
    with pytest.raises(ValueError, match="two wavelengths"):
        ScatteringSurfaceFile(
            wavelengths=[400.0],
            incident_angles=[0.0, 90.0],
            samples=[[ScatteringSurfaceSample()], [ScatteringSurfaceSample()]],
        )


def test_scattering_surface_warns_for_an_over_unity_budget(documented_scattering_surface):
    """Negative measured absorption warns without discarding the contribution."""
    with pytest.warns(UserWarning, match="absorption is negative.*-40"):
        documented_scattering_surface.samples[0][0].lambertian_reflection = 80.0
    assert documented_scattering_surface.samples[0][0].lambertian_reflection == 80.0


@pytest.mark.parametrize("name", CONTRIBUTIONS + WIDTHS)
def test_scattering_surface_sample_validated_properties(name):
    """Every sample property accepts valid values and rejects invalid assignments atomically."""
    sample = ScatteringSurfaceSample()
    assert getattr(sample, name) == 0.0
    setattr(sample, name, 20.0)
    assert getattr(sample, name) == 20.0
    for value in (-1.0, 101.0, float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match=name):
            setattr(sample, name, value)
        assert getattr(sample, name) == 20.0
        with pytest.raises(ValueError, match=name):
            ScatteringSurfaceSample(**{name: value})


@pytest.mark.parametrize("name", CONTRIBUTIONS)
def test_scattering_surface_sample_budget_is_validated_for_each_contribution(name):
    """Each contribution accepts a negative measured absorption with a warning."""
    other = next(entry for entry in CONTRIBUTIONS if entry != name)
    sample = ScatteringSurfaceSample(**{other: 80.0, name: 20.0})
    assert sample.absorption == 0.0
    with pytest.warns(UserWarning, match="absorption"):
        setattr(sample, name, 21.0)
    assert getattr(sample, name) == 21.0
    with pytest.warns(UserWarning, match="absorption"):
        ScatteringSurfaceSample(**{other: 80.0, name: 21.0})
    setattr(sample, other, 70.0)
    setattr(sample, name, 30.0)
    assert sample.absorption == 0.0


@pytest.mark.parametrize("name", WIDTHS)
def test_scattering_surface_sample_width_bounds(name):
    """Gaussian widths include 90 degrees but reject wider lobes."""
    sample = ScatteringSurfaceSample(**{name: 90.0})
    assert getattr(sample, name) == 90.0
    with pytest.raises(ValueError, match="90 degrees"):
        setattr(sample, name, 90.1)
    assert getattr(sample, name) == 90.0


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("wavelengths", [600.0, 400.0], "sorted"),
        ("wavelengths", [400.0, float("nan")], "finite"),
        ("wavelengths", [400.0, float("inf")], "finite"),
        ("wavelengths", [400.0, 500.0, 600.0], "one entry per wavelength"),
        ("incident_angles", [90.0, 0.0], "sorted"),
        ("incident_angles", [0.0, 90.0, 91.0], "between 0 and 90"),
        ("incident_angles", [0.0, float("nan"), 90.0], "between 0 and 90"),
        ("incident_angles", [0.0, 90.0], "one row per angle"),
        ("description", "first\nsecond", "single line"),
        ("description", "first\rsecond", "single line"),
        ("description", "first\u2028second", "single line"),
        ("samples", [[ScatteringSurfaceSample()]], "one row per angle"),
        ("samples", [[ScatteringSurfaceSample()]] * 3, "one entry per wavelength"),
    ],
)
def test_scattering_surface_file_assignment_is_atomic(
    documented_scattering_surface, name, value, message
):
    """Invalid file property assignments preserve the previous value."""
    previous = getattr(documented_scattering_surface, name)
    with pytest.raises(ValueError, match=message):
        setattr(documented_scattering_surface, name, value)
    assert getattr(documented_scattering_surface, name) == previous


def test_scattering_surface_file_rejects_wrong_types(documented_scattering_surface):
    """Descriptions and grid entries must have the expected types."""
    with pytest.raises(TypeError, match="string"):
        documented_scattering_surface.description = 12
    with pytest.raises(TypeError, match="ScatteringSurfaceSample"):
        documented_scattering_surface.samples = [[object()]]
    documented_scattering_surface.validate()


def test_scattering_surface_copies_list_containers(documented_scattering_surface):
    """Input and output lists cannot bypass validation while samples remain editable."""
    wavelengths = documented_scattering_surface.wavelengths
    angles = documented_scattering_surface.incident_angles
    samples = documented_scattering_surface.samples
    surface = ScatteringSurfaceFile(wavelengths, angles, samples)
    wavelengths.clear()
    angles.clear()
    samples[0].clear()
    samples.clear()
    surface.wavelengths.clear()
    surface.incident_angles.clear()
    surface.samples[0].clear()
    surface.samples.clear()
    surface.validate()
    surface.samples[0][0].specular_reflection = 25.0
    assert surface.samples[0][0].specular_reflection == 25.0
    grid = surface.samples
    grid[0][0] = ScatteringSurfaceSample()
    surface.samples = grid
    assert surface.samples[0][0].absorption == 100.0


def test_scattering_surface_staged_construction_and_resize(tmp_path):
    """Empty defaults allow staged construction but cannot be saved as a complete file."""
    surface = ScatteringSurfaceFile()
    assert not is_dataclass(surface)
    assert not is_dataclass(ScatteringSurfaceSample())
    assert surface.wavelengths == surface.incident_angles == surface.samples == []
    assert surface.description == "Scattering surface"
    with pytest.raises(ValueError, match="two wavelengths"):
        surface.save(tmp_path / "empty.scattering")
    assert not (tmp_path / "empty.scattering").exists()
    surface.samples = [[ScatteringSurfaceSample()] * 2 for _ in range(2)]
    surface.wavelengths = [400.0, 700.0]
    surface.incident_angles = [0.0, 90.0]
    surface.validate()
    surface.samples = []
    surface.wavelengths = [400.0, 550.0, 700.0]
    surface.incident_angles = [0.0, 45.0, 90.0]
    surface.samples = [[ScatteringSurfaceSample()] * 3 for _ in range(3)]
    surface.description = ""
    path = surface.save(tmp_path / "resized.scattering")
    assert ScatteringSurfaceFile.load(path) == surface


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
    with pytest.raises(ValueError, match="reflection_s must be between 0 and 100"):
        documented_coated_surface.samples[0][0].reflection_s = 120.0
    assert documented_coated_surface.samples[0][0].reflection_s == 31.9


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


def test_simple_scattering_shared_equality_contract():
    """Shared equality retains value comparison, strict types, and unhashable models."""
    surface = SimpleScatteringSurfaceFile(lambertian=50.0)
    other = SimpleScatteringSurfaceFile(lambertian=50.0)
    assert surface is not other
    assert surface == other
    other.lambertian = 40.0
    assert surface != other
    assert surface.__eq__(object()) is NotImplemented
    assert surface.__hash__ is None
    with pytest.raises(TypeError):
        hash(surface)

    class DerivedSurface(SimpleScatteringSurfaceFile):
        """A derived surface used to verify exact-type comparison."""

    derived = DerivedSurface(lambertian=50.0)
    assert surface.__eq__(derived) is NotImplemented
    assert derived.__eq__(surface) is NotImplemented
    assert surface != derived
    assert derived == DerivedSurface(lambertian=50.0)


def test_simple_scattering_rejects_an_unknown_mode_at_construction():
    """An unknown simple-scattering mode must be rejected during construction."""
    with pytest.raises(ValueError, match="mode must be one of"):
        SimpleScatteringSurfaceFile(mode="Diffuse")


def test_simple_scattering_rejects_an_over_unity_budget(tmp_path):
    """The Lambertian and Gaussian shares of a side must not exceed 100%."""
    with pytest.raises(ValueError, match="must not sum to more than 100"):
        SimpleScatteringSurfaceFile(lambertian=60.0, gaussian=60.0)


@pytest.mark.parametrize("name", _COATING_FIELDS)
def test_coated_sample_setters_are_atomic(name):
    """Each coating contribution validates without imposing a polarization budget."""
    with pytest.warns(UserWarning, match="absorption_[ps]"):
        sample = CoatedSurfaceSample(80.0, 80.0, 80.0, 80.0)
    assert sample.absorption_p == -60.0
    for value in (-1.0, 101.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            setattr(sample, name, value)
        assert getattr(sample, name) == 80.0


@pytest.mark.parametrize("excess", [0.01, 40.0])
@pytest.mark.parametrize("polarization", ["p", "s", None])
def test_negative_absorption_warns_and_round_trips(excess, polarization, tmp_path):
    """Measured negative absorption survives construction, assignment, validation and I/O."""
    if polarization is None:
        sample_class = ScatteringSurfaceSample
        file_class = ScatteringSurfaceFile
        fields = {"specular_reflection": 60.0, "specular_transmission": 40.0 + excess}
        absorption_name = "absorption"
        changed_name = "specular_transmission"
    else:
        sample_class = CoatedSurfaceSample
        file_class = CoatedSurfaceFile
        fields = {f"reflection_{polarization}": 60.0, f"transmission_{polarization}": 40 + excess}
        absorption_name = f"absorption_{polarization}"
        changed_name = f"transmission_{polarization}"
    with pytest.warns(UserWarning, match=absorption_name):
        sample = sample_class(**fields)
    with pytest.warns(UserWarning, match=absorption_name):
        setattr(sample, changed_name, 40.0 + excess)
    with pytest.warns(UserWarning, match=absorption_name):
        sample.validate()
    assert getattr(sample, absorption_name) == pytest.approx(-excess)
    with pytest.warns(UserWarning, match=absorption_name):
        surface = file_class([400.0, 700.0], [0.0, 90.0], [[sample, sample], [sample, sample]])
    with pytest.warns(UserWarning, match=absorption_name):
        path = surface.save(tmp_path / ("measured" + file_class.EXTENSION))
    with pytest.warns(UserWarning, match=absorption_name):
        assert file_class.load(path) == surface


@pytest.mark.parametrize("total", [90.0, 100.0, 100.0 + 5e-10])
@pytest.mark.parametrize("sample_class", [CoatedSurfaceSample, ScatteringSurfaceSample])
def test_absorption_rounding_noise_does_not_warn(sample_class, total):
    """Valid budgets and sub-tolerance rounding noise do not emit warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        if sample_class is CoatedSurfaceSample:
            sample = sample_class(60.0, total - 60.0, 60.0, total - 60.0)
        else:
            sample = sample_class(specular_reflection=60.0, specular_transmission=total - 60.0)
        sample.validate()


def test_coated_grid_setters_copy_and_validate():
    """Coatings allow one sample and arbitrary incidence endpoints, but validate the grid."""
    row = [CoatedSurfaceSample()]
    surface = CoatedSurfaceFile([550.0], [45.0], [row])
    row.clear()
    surface.samples[0].clear()
    surface.wavelengths.clear()
    surface.validate()
    for name, values in (
        ("wavelengths", [700.0, 400.0]),
        ("incident_angles", [91.0]),
        ("samples", [[object()]]),
    ):
        previous = getattr(surface, name)
        with pytest.raises((ValueError, TypeError)):
            setattr(surface, name, values)
        assert getattr(surface, name) == previous


@pytest.mark.parametrize(
    ("model_class", "name"),
    [(CoatedSurfaceSample, "reflection_p"), (SimpleScatteringSurfaceFile, "absorption")],
)
@pytest.mark.parametrize("value", (0, 25.5, 100, "12.5"))
def test_shared_percentage_setters_preserve_conversion(model_class, name, value):
    """Shared percentage validation retains float conversion and inclusive boundaries."""
    model = model_class()
    setattr(model, name, value)
    assert getattr(model, name) == float(value)
    assert isinstance(getattr(model, name), float)


@pytest.mark.parametrize(
    ("samples", "message"),
    [
        ([[CoatedSurfaceSample()], [CoatedSurfaceSample()]], "one row per angle"),
        ([[CoatedSurfaceSample(), CoatedSurfaceSample()]], "one entry per wavelength"),
    ],
)
def test_coated_grid_dimensions_reject_assignments_atomically(samples, message):
    """Shared grid checks reject mismatched dimensions without replacing existing samples."""
    surface = CoatedSurfaceFile([550.0], [45.0], [[CoatedSurfaceSample()]])
    previous = surface.samples
    with pytest.raises(ValueError, match=message):
        surface.samples = samples
    assert surface.samples == previous


def test_simple_scattering_mode_switch_validates_candidate_budget():
    """An inactive second side is checked when enabling Both mode without losing state."""
    surface = SimpleScatteringSurfaceFile(lambertian_transmission=80.0, gaussian_transmission=80.0)
    with pytest.raises(ValueError, match="sum"):
        surface.mode = "Both"
    assert surface.mode == "Reflection"
    surface.gaussian_transmission = 20.0
    surface.mode = "Both"
    with pytest.raises(ValueError, match="sum"):
        surface.gaussian_transmission = 21.0
    assert surface.gaussian_transmission == 20.0
    surface.reflection = 50.0
    assert not surface.fresnel
    surface.reflection = None
    assert surface.fresnel


@pytest.mark.parametrize(
    "name",
    (
        "absorption",
        "lambertian",
        "gaussian",
        "gaussian_fwhm",
        "lambertian_transmission",
        "gaussian_transmission",
        "gaussian_fwhm_transmission",
        "reflection",
    ),
)
def test_simple_scattering_setters_reject_nonfinite_values(name):
    """Every numeric surface property rejects nonfinite assignments atomically."""
    surface = SimpleScatteringSurfaceFile()
    previous = getattr(surface, name)
    with pytest.raises(ValueError):
        setattr(surface, name, float("inf"))
    assert getattr(surface, name) == previous
