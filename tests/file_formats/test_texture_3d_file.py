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

"""Test the ``*.OPT3DMapping`` file format."""

import pytest

from ansys.speos.core import Texture3DMappingFile, TexturePattern
from tests.file_formats import read_lines


@pytest.fixture
def documented_mapping():
    """Build a small mapping laid out like the one shown by the Speos documentation."""
    return Texture3DMappingFile(
        patterns=[
            TexturePattern(),
            TexturePattern(position=(1.5, 0.0, 0.0), scale=(1.0, 0.5, 2.0)),
        ]
    )


def test_write_matches_the_documented_layout(documented_mapping, tmp_path):
    """A written file must match the layout described by the Speos documentation."""
    path = documented_mapping.save(tmp_path / "texture.OPT3DMapping")

    assert path.suffix == Texture3DMappingFile.EXTENSION
    assert read_lines(path) == [
        "2",
        "0\t0\t0\t1\t0\t0\t0\t1\t0\t1\t1\t1",
        "1.5\t0\t0\t1\t0\t0\t0\t1\t0\t1\t0.5\t2",
    ]


def test_round_trip(documented_mapping, tmp_path):
    """Reading back a written file must give an equivalent model."""
    path = documented_mapping.save(tmp_path / "texture.OPT3DMapping")

    assert Texture3DMappingFile.load(path) == documented_mapping


def test_a_uniform_scale_writes_a_single_column(tmp_path):
    """The single scale factor flavor must write 10 columns instead of 12."""
    mapping = Texture3DMappingFile(
        patterns=[TexturePattern(scale=(0.5, 0.5, 0.5))], uniform_scale=True
    )
    path = mapping.save(tmp_path / "uniform.OPT3DMapping")

    assert read_lines(path) == ["1", "0\t0\t0\t1\t0\t0\t0\t1\t0\t0.5"]
    assert Texture3DMappingFile.load(path) == mapping


def test_a_uniform_scale_needs_equal_factors(tmp_path):
    """The single scale factor flavor cannot carry different factors per direction."""
    mapping = Texture3DMappingFile(
        patterns=[TexturePattern(scale=(1.0, 2.0, 3.0))], uniform_scale=True
    )

    with pytest.raises(ValueError, match="same scale factor"):
        mapping.save(tmp_path / "invalid.OPT3DMapping")


def test_an_empty_mapping_is_rejected(tmp_path):
    """A mapping must lay out at least one pattern."""
    with pytest.raises(ValueError, match="at least one pattern"):
        Texture3DMappingFile().save(tmp_path / "empty.OPT3DMapping")


def test_an_unexpected_column_count_is_reported(tmp_path):
    """Reading must report a pattern line that holds neither 10 nor 12 values."""
    path = tmp_path / "broken.OPT3DMapping"
    path.write_text("1\n0 0 0 1 0 0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="expected 10 or 12 values"):
        Texture3DMappingFile.load(path)
