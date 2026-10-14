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

"""Test the ``*.spectrum`` file format."""

import pytest

from ansys.speos.core import Spectrum, SpectrumFile
from tests.input_files import ASSETS_DIR, read_lines


def test_write_matches_the_documented_layout(tmp_path):
    """A written file must match the layout described by the Speos documentation."""
    path = SpectrumFile(
        wavelengths=[360.0, 830.0], values=[4.0, 4.0], description="Reflection 4%"
    ).save(tmp_path / "reflection.spectrum")

    assert path.suffix == SpectrumFile.EXTENSION
    assert read_lines(path) == [
        "OPTIS - Spectrum file v1",
        "Reflection 4%",
        "2",
        "360\t4",
        "830\t4",
    ]


def test_read_a_file_produced_by_speos():
    """A file produced by Speos must be read back into an equivalent model."""
    spectrum = SpectrumFile.load(ASSETS_DIR / "R04.spectrum")

    assert spectrum.description == "Reflection 4%"
    assert spectrum.wavelengths == [360.0, 830.0]
    assert spectrum.values == [4.0, 4.0]


def test_round_trip_a_file_produced_by_speos(tmp_path):
    """Reading and writing a file produced by Speos must not lose any data."""
    spectrum = SpectrumFile.load(ASSETS_DIR / "R04.spectrum")

    assert SpectrumFile.load(spectrum.save(tmp_path / "copy.spectrum")) == spectrum


def test_from_sampled_reuses_the_feature_data():
    """A sampled spectrum feature must be convertible into a spectrum file."""
    spectrum = Spectrum(speos_client=None, name="LED")
    sampled = spectrum.set_sampled()
    sampled.wavelengths = [400.0, 700.0]
    sampled.values = [10.0, 90.0]

    spectrum_file = SpectrumFile.from_sampled(spectrum)

    assert spectrum_file.description == "LED"
    assert spectrum_file.wavelengths == [400.0, 700.0]
    assert spectrum_file.values == [10.0, 90.0]


def test_from_sampled_rejects_other_spectrum_types():
    """Only a sampled spectrum feature can be turned into a spectrum file."""
    spectrum = Spectrum(speos_client=None, name="Laser")
    spectrum.set_monochromatic()

    with pytest.raises(ValueError, match="set_sampled"):
        SpectrumFile.from_sampled(spectrum)


@pytest.mark.parametrize(
    ("parameters", "message"),
    [
        ({"wavelengths": [400.0], "values": [120.0]}, "between 0 and 100"),
        ({"wavelengths": [400.0], "values": [-1.0]}, "between 0 and 100"),
        (
            {"wavelengths": [1.0] * 32768, "values": [1.0] * 32768},
            "more than 32767 samples",
        ),
    ],
)
def test_invalid_spectra_are_rejected_at_construction(parameters, message):
    """Invalid spectral data must be rejected during construction."""
    with pytest.raises(ValueError, match=message):
        SpectrumFile(**parameters)


@pytest.mark.parametrize(
    ("parameters", "message"),
    [
        ({"wavelengths": [400.0], "values": []}, "same length"),
        ({}, "at least one sample"),
    ],
)
def test_incomplete_spectra_cannot_be_saved(parameters, message, tmp_path):
    """Incomplete spectra can be constructed but must be rejected when saving."""
    spectrum = SpectrumFile(**parameters)
    path = tmp_path / "invalid.spectrum"

    with pytest.raises(ValueError, match=message):
        spectrum.save(path)

    assert not path.exists()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("values", [-1.0]),
        ("values", [float("nan")]),
        ("wavelengths", [float("inf")]),
        ("wavelengths", [400.0, 500.0]),
        ("description", "first\nsecond"),
    ],
)
def test_spectrum_setters_preserve_state_on_failure(name, value):
    """Rejected assignments do not change the previous property value."""
    spectrum = SpectrumFile([400.0], [50.0])
    previous = getattr(spectrum, name)
    with pytest.raises(ValueError):
        setattr(spectrum, name, value)
    assert getattr(spectrum, name) == previous


def test_spectrum_lists_are_copied_and_can_be_resized():
    """Copied containers protect data while clearing permits staged resizing."""
    wavelengths, values = [700.0, 400.0], [100.0, 50.0]
    spectrum = SpectrumFile(wavelengths, values)
    wavelengths.clear()
    values.clear()
    spectrum.values.clear()
    spectrum.wavelengths.clear()
    spectrum.validate()
    spectrum.values = []
    spectrum.wavelengths = [550.0]
    spectrum.values = [25.0]
    spectrum.validate()
    assert spectrum == SpectrumFile([550.0], [25.0])


@pytest.mark.parametrize("value", ("line\n", "line\r", "line\r\n", "line\u2028", "line\x85"))
def test_descriptions_reject_trailing_line_separators(value):
    """Description validation rejects line separators even at the end of the string."""
    spectrum = SpectrumFile(description="previous")
    with pytest.raises(ValueError, match="single line"):
        spectrum.description = value
    assert spectrum.description == "previous"


def test_columns_reject_text_sequences():
    """A numeric sequence cannot be supplied as a string of numeric characters."""
    spectrum = SpectrumFile([400.0], [50.0])
    with pytest.raises(TypeError, match="numeric sequence"):
        spectrum.values = "123"
    assert spectrum.values == [50.0]


def test_a_file_with_a_foreign_header_is_rejected(tmp_path):
    """Reading must refuse a file that is not a spectrum file."""
    path = tmp_path / "foreign.spectrum"
    path.write_text("OPTIS - Material file v13\n\n0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="OPTIS - Spectrum"):
        SpectrumFile.load(path)


def test_a_missing_file_is_reported(tmp_path):
    """Reading must report a missing file rather than returning an empty model."""
    with pytest.raises(FileNotFoundError):
        SpectrumFile.load(tmp_path / "absent.spectrum")
