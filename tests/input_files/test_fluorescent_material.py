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

"""Test fluorescent material and pigment input files."""

import pytest

from ansys.speos.core import (
    FluorescentPigment,
    FluorescentPigmentFile,
    FluorescentSpectrum,
    MaterialDispersionCurve,
    MaterialFile,
    MaterialType,
    VolumeScatteringHenyeyGreenstein,
)
from tests.input_files import ASSETS_DIR, read_lines

DEFAULT_DYE_LINES = [
    "OPTIS - Fluorescent pigment file v3.0",
    "Fluorescent pigment",
    "ISOTROPIC",
    "1",
    "0",
    "OPTIS - Spectrum file v1",
    "Default spectrum : edit or load -->",
    "3",
    "350\t0",
    "360\t0.1",
    "370\t0",
    "OPTIS - Spectrum file v1",
    "Default spectrum : edit or load -->",
    "3",
    "350\t95",
    "360\t95",
    "370\t95",
    "OPTIS - Spectrum file v1",
    "Default spectrum : edit or load -->",
    "3",
    "350\t0",
    "360\t0.095",
    "370\t0",
    "OPTIS - Spectrum file v1",
    "Default spectrum : edit or load -->",
    "3",
    "400\t0",
    "500\t100",
    "600\t0",
    "0",
    "0",
]


def test_fluorescent_material_defaults_match_the_editor(tmp_path):
    """A new fluorescent material has the editor's curves and an empty dye table."""
    material = MaterialFile(material_type=MaterialType.fluorescent)

    assert material.description == "Fluorescent Material"
    assert material.dispersion == MaterialDispersionCurve(
        wavelengths=[486.0, 532.0, 643.0], indices=[1.5, 1.5, 1.5]
    )
    assert material.absorption_wavelengths == [486.0, 532.0, 643.0]
    assert material.absorption_values == [0.0, 0.0, 0.0]
    assert material.measured_concentration == material.user_concentration == 1.0
    assert material.scattering is None
    assert material.fluorescent_pigments == []

    with pytest.raises(ValueError, match="requires at least one pigment"):
        material.save(tmp_path / "empty-fluorescence.material")


def test_default_dye_matches_speos_pigment_file(tmp_path):
    """The default dye writes the editor's four spectra and settings."""
    dye = FluorescentPigmentFile()
    path = dye.save(tmp_path / "default.dye")

    expected = [FluorescentPigmentFile.HEADER]
    for line in DEFAULT_DYE_LINES[1:]:
        expected.append(line)
        if line == "OPTIS - Spectrum file v1":
            expected.append("0")
    assert read_lines(path) == expected
    assert FluorescentPigmentFile.load(path) == dye


def test_standalone_speos_dye_round_trips(tmp_path):
    """Standalone dyes use a different header and add a flag to each spectrum."""
    reference = ASSETS_DIR / "input_files" / "Fluorescent.dye"
    dye = FluorescentPigmentFile.load(reference)
    assert dye.spectrum_selection_code == 1
    assert read_lines(dye.save(tmp_path / "loaded.dye")) == read_lines(reference)


def test_fluorescent_material_with_one_dye_matches_editor_file(tmp_path):
    """A dye row includes both concentrations and its embedded pigment data."""
    pigment = FluorescentPigment(dye=FluorescentPigmentFile())
    material = MaterialFile(
        material_type=MaterialType.fluorescent,
        fluorescent_pigments=[pigment],
    )
    path = material.save(tmp_path / "one-dye.material")

    assert read_lines(path) == [
        "OPTIS - Material file v13",
        "Fluorescent Material",
        "Fluorescent",
        "Dispersion_Curve",
        "3",
        "486 1.5",
        "532 1.5",
        "643 1.5",
        "3",
        "486 0",
        "532 0",
        "643 0",
        "1",
        "1",
        "0",
        "1",
        "1",
        *DEFAULT_DYE_LINES,
    ]
    assert MaterialFile.load(path) == material


def test_fluorescent_spectrum_allows_absorption_values_above_percent_range():
    """Absorption and excitance spectra use units that are not percentages."""
    spectrum = FluorescentSpectrum(
        wavelengths=[400.0, 500.0],
        values=[125.0, 200.0],
    )
    spectrum.validate()

    with pytest.raises(ValueError, match="same length"):
        spectrum.values = [1.0]


def test_speos_multiple_dye_file_round_trips(tmp_path):
    """Preserve both concentrations, spectrum selections, and embedded spectra."""
    reference = ASSETS_DIR / "input_files" / "Fluorescent.material"
    material = MaterialFile.load(reference)
    first, second, third = material.fluorescent_pigments
    assert (first.measured_concentration, first.user_concentration) == (1, 1)
    assert (second.measured_concentration, second.user_concentration) == (2, 2)
    assert (third.measured_concentration, third.user_concentration) == (3, 7)
    assert (first.dye.spectrum_selection_code, second.dye.spectrum_selection_code) == (0, 2)
    assert second.dye.absorption_spectrum.wavelengths == [350, 360, 366, 370]
    assert second.dye.absorption_spectrum.values == [0, 0, 0.11875, 0]
    assert read_lines(material.save(tmp_path / "multiple-dye.material")) == read_lines(reference)


def test_pigment_changes_are_validated(tmp_path):
    """Reject invalid shared data and changes that would lose a pigment."""
    material = MaterialFile(
        material_type=MaterialType.fluorescent, fluorescent_pigments=[FluorescentPigment()]
    )
    with pytest.raises(ValueError, match="Clear fluorescent_pigments"):
        material.material_type = MaterialType.isotropic
    assert material.material_type is MaterialType.fluorescent
    pigment = material.fluorescent_pigments[0]
    pigment.dye.absorption_spectrum.values = []
    with pytest.raises(ValueError, match="same length"):
        material.save(tmp_path / "invalid.material")


def test_fluorescent_material_can_have_bulk_scattering(tmp_path):
    """The pigment table follows the complete volume-scattering block."""
    material = MaterialFile(
        material_type=MaterialType.fluorescent,
        scattering=VolumeScatteringHenyeyGreenstein(),
        fluorescent_pigments=[FluorescentPigment()],
    )
    path = material.save(tmp_path / "scattering.material")
    assert MaterialFile.load(path) == material


def test_default_dye_spectra_are_independent():
    """Editing a default dye never alters another dye."""
    first = FluorescentPigmentFile()
    second = FluorescentPigmentFile()
    first.absorption_spectrum.values = [0, 3, 0]
    assert second.absorption_spectrum.values == [0, 0.1, 0]
    with pytest.raises(TypeError, match="FluorescentSpectrum"):
        first.absorption_spectrum = None
    with pytest.raises(ValueError, match="selection codes"):
        first.spectrum_selection_code = 4
    assert first.spectrum_selection_code == 0


def test_reader_rejects_truncated_or_unsupported_dye_data(tmp_path):
    """Do not silently drop unsupported records or accept an incomplete dye list."""
    reference = ASSETS_DIR / "input_files" / "Fluorescent.material"
    lines = read_lines(reference)
    lines[15] = "4"
    path = tmp_path / "truncated.material"
    path.write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected end of file"):
        MaterialFile.load(path)

    reference = ASSETS_DIR / "input_files" / "Fluorescent.dye"
    lines = read_lines(reference)
    lines[6] = "1"
    path = tmp_path / "unsupported.dye"
    path.write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported standalone dye spectrum option"):
        FluorescentPigmentFile.load(path)


def test_non_fluorescent_material_rejects_dye_entries():
    """Dye entries are restricted to fluorescent materials."""
    with pytest.raises(ValueError, match="only supported for a fluorescent material"):
        MaterialFile(fluorescent_pigments=[FluorescentPigment()])
