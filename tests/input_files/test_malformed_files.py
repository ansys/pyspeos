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

"""Check that reading a malformed input file fails clearly instead of crashing oddly.

The round-trip and reference-file tests only ever read files that are valid, so they
never exercise the ``ValueError``/``FileNotFoundError`` paths of :class:`LineReader` and
of the ``_from_lines``/``validate`` methods. This module feeds deliberately broken
content to the readers and checks that the resulting error names the problem and, when
relevant, the offending line, so a user pointed at a bad file gets an actionable message.
"""

import pytest

from ansys.speos.core import (
    CoatedSurfaceFile,
    MaterialConstringence,
    MaterialDispersionCurve,
    MaterialFile,
    SimpleScatteringSurfaceFile,
    SpectrumFile,
    Texture3DMappingFile,
    VolumeScatteringDoubleHenyeyGreenstein,
    VolumeScatteringHenyeyGreenstein,
    VolumeScatteringUserDefined,
)
from ansys.speos.core.input_files._base import LineReader
from tests.input_files import ASSETS_DIR

VALID_MATERIAL = """OPTIS - Material file v13
Test material
Isotropic
Constringence
57.2
1.49
1
550 0.001
1
1
0
"""
"""A minimal, valid ``*.material`` file, used as a base for the broken variants below."""


def write(tmp_path, name, content):
    """Write raw text content to ``tmp_path / name`` and return the path."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.parametrize("token", ["1.9", "2.0", "2e0", "nan", "inf", "-inf", "oops"])
@pytest.mark.parametrize("paired", [False, True])
def test_integer_readers_reject_non_integer_tokens(token, paired):
    """Scalar and paired integer fields reject the same malformed spellings."""
    reader = LineReader(["", f"1 {token}" if paired else token], "counts.txt")
    with pytest.raises(ValueError, match=r"counts.txt, line 2: expected an integer"):
        if paired:
            reader.next_ints(count=2)
        else:
            reader.next_int()


def test_integer_readers_keep_precision_and_enforce_count_limits():
    """Integer parsing is exact and rejects invalid arity and count minima."""
    assert LineReader(["9007199254740993"]).next_int() == 9007199254740993
    assert LineReader(["+2 003"]).next_ints(count=2, minimum=1) == [2, 3]
    assert LineReader(["0"]).next_int(minimum=0) == 0
    for values in ("0", "-1"):
        with pytest.raises(ValueError, match="at least 1"):
            LineReader([values]).next_int(minimum=1)
    with pytest.raises(ValueError, match="expected 2 values, got 1"):
        LineReader(["2"]).next_ints(count=2)
    with pytest.raises(ValueError, match="expected 1 values, got 2"):
        LineReader(["2 3"]).next_int()


@pytest.mark.parametrize("token", ["nan", "inf", "-inf", "1e999"])
def test_float_reader_rejects_nonfinite_values_with_location(token):
    """Nonfinite numeric data fails at the shared reader with a physical line number."""
    with pytest.raises(ValueError, match=r"values.txt, line 2:.*finite"):
        LineReader(["", f"1 {token}"], "values.txt").next_floats(count=2)


def test_float_reader_retains_scientific_notation():
    """Strict counts do not restrict genuine floating-point fields."""
    assert LineReader(["2.0 2e-3"]).next_floats(count=2) == [2.0, 0.002]


@pytest.mark.parametrize("token", ["0", "-1", "1.5", "1.0", "1e0", "inf"])
@pytest.mark.parametrize("model_class", [MaterialFile, SpectrumFile, Texture3DMappingFile])
def test_file_sample_counts_use_shared_integer_validation(model_class, token, tmp_path):
    """Material, spectrum, and texture counts fail before their data rows are consumed."""
    if model_class is MaterialFile:
        content = VALID_MATERIAL.replace("\n1\n550 0.001", f"\n{token}\n550 0.001")
    elif model_class is SpectrumFile:
        content = f"{model_class.HEADER}\ndescription\n{token}\n"
    else:
        content = f"{model_class.HEADER}\n{token}\n"
    path = write(tmp_path, "invalid" + model_class.EXTENSION, content)
    with pytest.raises(ValueError, match=r"line \d+: expected an integer"):
        model_class.load(path)


@pytest.mark.parametrize("wavelength_count", [0, 1])
def test_user_defined_phase_preserves_nonspectral_count_sentinels(wavelength_count):
    """Zero and one wavelength counts still represent a nonspectral phase function."""
    reader = LineReader([str(wavelength_count), "1", "0 1"])
    model = VolumeScatteringUserDefined._from_lines(reader)
    model.validate()
    assert model.wavelengths == []
    assert model.values == [[1.0]]


def test_missing_file_is_reported_as_such(tmp_path):
    """Loading a file that does not exist must raise FileNotFoundError, not crash."""
    missing = tmp_path / "does_not_exist.material"

    with pytest.raises(FileNotFoundError, match="does_not_exist.material"):
        MaterialFile.load(missing)


def test_wrong_header_is_reported(tmp_path):
    """A file that does not start with the expected header must be rejected clearly."""
    path = write(tmp_path, "wrong_header.coated", "Not a Speos file\n")

    with pytest.raises(ValueError, match="expected a header starting with"):
        CoatedSurfaceFile.load(path)


def test_truncated_file_reports_unexpected_end_of_file(tmp_path):
    """A file cut short must be reported as truncated instead of raising an IndexError."""
    path = write(tmp_path, "truncated.material", "OPTIS - Material file v13\n")

    with pytest.raises(ValueError, match="unexpected end of file"):
        MaterialFile.load(path)


def test_non_numeric_value_is_reported(tmp_path):
    """A non-numeric token where a float is expected must name the offending value."""
    content = VALID_MATERIAL.replace("57.2", "not-a-number")
    path = write(tmp_path, "bad_number.material", content)

    with pytest.raises(ValueError, match=r"expected numbers, got 'not-a-number'"):
        MaterialFile.load(path)


def test_wrong_value_count_is_reported(tmp_path):
    """A line holding more or fewer values than expected must say how many were expected."""
    content = VALID_MATERIAL.replace("550 0.001", "550 0.001 0.002")
    path = write(tmp_path, "bad_count.material", content)

    with pytest.raises(ValueError, match=r"expected 2 values, got 3"):
        MaterialFile.load(path)


def test_non_integer_count_is_reported(tmp_path):
    """A count line holding text instead of an integer must say so explicitly."""
    content = VALID_MATERIAL.replace("\n1\n550 0.001", "\nabsorption\n550 0.001")
    path = write(tmp_path, "bad_int.material", content)

    with pytest.raises(ValueError, match=r"expected an integer, got 'absorption'"):
        MaterialFile.load(path)


def test_error_message_names_the_file_and_the_line(tmp_path):
    """Every parsing error must point at the file and the line so it can be located."""
    content = VALID_MATERIAL.replace("57.2", "oops")
    path = write(tmp_path, "locate_me.material", content)

    with pytest.raises(ValueError, match=r"locate_me\.material, line \d+:") as excinfo:
        MaterialFile.load(path)
    assert str(path) in str(excinfo.value)


def test_simple_scattering_rejects_an_unknown_mode_when_reading(tmp_path):
    """Reading (not only writing) a simple scattering surface must reject a bad mode."""
    content = "OPTIS - Simple scattering surface file v2.0\ndesc\nDiffuse\n0 100 0 0\n"
    path = write(tmp_path, "bad_mode.simplescattering", content)

    with pytest.raises(ValueError, match="expected one of .*, got 'Diffuse'"):
        SimpleScatteringSurfaceFile.load(path)


def test_material_rejects_an_unknown_dispersion_keyword(tmp_path):
    """Reading a material with an index variation mode Speos does not define must fail."""
    content = VALID_MATERIAL.replace("Constringence", "Quantum")
    path = write(tmp_path, "bad_dispersion.material", content)

    with pytest.raises(ValueError, match="unknown index variation mode 'Quantum'"):
        MaterialFile.load(path)


def test_material_rejects_an_unsupported_scattering_model_id(tmp_path):
    """A scattering block with a model id Speos never wrote must be rejected clearly."""
    content = VALID_MATERIAL.replace(
        "1\n1\n0\n",
        "1\n1\n1\nOPTIS - Volumic Scattering file v1\n99\n1\n550 0.1\n0.9\n",
    )
    path = write(tmp_path, "bad_model.material", content)

    with pytest.raises(ValueError, match="unsupported scattering phase function 99"):
        MaterialFile.load(path)


def test_dispersion_curve_needs_matching_wavelengths_and_indices(tmp_path):
    """A dispersion curve with mismatched wavelength and index lists must be rejected."""
    with pytest.raises(ValueError, match="same length"):
        MaterialDispersionCurve(wavelengths=[480.0, 650.0], indices=[1.5])


def test_user_defined_phase_function_needs_at_least_one_angle(tmp_path):
    """A user defined phase function without any angle must be rejected, not silently empty."""
    material = MaterialFile(
        absorption_wavelengths=[550.0],
        absorption_values=[0.0],
        scattering_wavelengths=[550.0],
        scattering_values=[0.1],
        scattering=VolumeScatteringUserDefined(),
    )

    with pytest.raises(ValueError, match="needs angles"):
        material.save(tmp_path / "invalid.material")


def test_phase_function_needs_wavelengths_for_more_than_one_set(tmp_path):
    """Several anisotropy factors without matching wavelengths must be rejected."""
    with pytest.raises(ValueError, match="wavelengths is required"):
        VolumeScatteringHenyeyGreenstein(anisotropies=[0.8, 0.9])


def test_phase_function_columns_must_have_the_same_length(tmp_path):
    """Mismatched column lengths inside a phase function must be reported, not misread."""
    with pytest.raises(ValueError, match="must have the same length"):
        VolumeScatteringDoubleHenyeyGreenstein(
            wavelengths=[480.0, 650.0],
            anisotropies_1=[0.8, 0.9],
            anisotropies_2=[0.8],
            ratios=[0.5, 0.5],
        )


def test_constringence_reads_bad_numeric_tokens_with_a_precise_location(tmp_path):
    """A dispersion sub-model must report exactly which of its own values is invalid."""
    content = VALID_MATERIAL.replace("1.49", "N/A")
    path = write(tmp_path, "bad_index.material", content)

    with pytest.raises(ValueError, match=r"expected numbers, got 'N/A'"):
        MaterialFile.load(path)
    # Sanity check that the un-mutated model still parses, to isolate the mutation itself.
    assert (
        MaterialConstringence(57.2, 1.49)
        == MaterialFile.load(write(tmp_path, "good_index.material", VALID_MATERIAL)).dispersion
    )


def test_an_encrypted_material_is_rejected():
    """An encrypted file carries the usual header, so only its payload gives it away."""
    encrypted = ASSETS_DIR / "input_files" / "Encrypted.material"

    with pytest.raises(ValueError, match="cannot read encrypted Speos input files"):
        MaterialFile.load(encrypted)


def test_every_text_format_rejects_a_binary_payload(tmp_path):
    """The encrypted file guard protects every text format, not only the materials."""
    path = tmp_path / "encrypted.spectrum"
    path.write_bytes(b"OPTIS - Spectrum file v1.0\n\x00\x01\x02\x03")

    with pytest.raises(ValueError, match="not a plain text file"):
        SpectrumFile.load(path)
