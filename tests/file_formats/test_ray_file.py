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

"""Test the ray file formats."""

import math

import pytest

from ansys.speos.core import Ray, RayFile
from tests.file_formats import ASSETS_DIR, read_lines

SPEOS_RAY_FILE = ASSETS_DIR / "Rays.ray"
"""Binary ray file produced by Speos, holding 45462 rays."""


@pytest.fixture
def documented_rays():
    """Build the five rays used as an example by the Speos documentation."""
    return RayFile(
        rays=[
            Ray(position=(-0.5, 0.4, 0.4), direction=(0.5, -0.1, 0.7), wavelength=555.0),
            Ray(position=(0.7, -0.5, 12.0), direction=(0.2, -0.4, 0.2), wavelength=555.0),
            Ray(position=(0.8, -0.2, 18.0), direction=(-0.5, -0.4, 0.7), wavelength=532.0),
            Ray(position=(-0.1, 0.5, 4.0), direction=(0.5, 0.2, 0.7), wavelength=452.0),
            Ray(position=(1.7, -0.8, 2.0), direction=(0.2, -0.4, 0.6), wavelength=633.0),
        ]
    )


def _normalize(ray_file):
    """Scale every ray direction to a unit vector, as Speos expects."""
    for ray in ray_file.rays:
        norm = math.dist((0.0, 0.0, 0.0), ray.direction)
        ray.direction = tuple(value / norm for value in ray.direction)
    return ray_file


def test_read_a_binary_file_produced_by_speos():
    """A binary file produced by Speos must be read back into an equivalent model."""
    ray_file = RayFile.load(SPEOS_RAY_FILE)

    assert len(ray_file.rays) == 45462
    assert ray_file.radiant_flux == pytest.approx(4.017658, abs=1e-6)
    assert ray_file.luminous_flux == pytest.approx(450.082, abs=1e-3)

    first = ray_file.rays[0]
    assert first.position == pytest.approx((-0.3158256, 1.568328, 31.98986), abs=1e-6)
    assert first.direction == pytest.approx((-0.9279028, 0.2778881, -0.2485452), abs=1e-6)
    assert first.wavelength == pytest.approx(800.1143, abs=1e-4)
    assert first.energy == pytest.approx(1.0)


def test_round_trip_a_binary_file_produced_by_speos(tmp_path):
    """Reading and writing a binary file produced by Speos must be lossless."""
    path = RayFile.load(SPEOS_RAY_FILE).save(tmp_path / "copy.ray")

    assert path.read_bytes() == SPEOS_RAY_FILE.read_bytes()


def test_binary_round_trip_keeps_the_flux(documented_rays, tmp_path):
    """The total fluxes must survive a binary write and read."""
    _normalize(documented_rays)
    documented_rays.radiant_flux = 2.5
    documented_rays.luminous_flux = 280.0

    read_back = RayFile.load(documented_rays.save(tmp_path / "rays.ray"))

    assert read_back.radiant_flux == pytest.approx(2.5)
    assert read_back.luminous_flux == pytest.approx(280.0)
    assert len(read_back.rays) == 5


def test_text_write_matches_the_documented_layout(tmp_path):
    """A written text file must match the layout described by the Speos documentation."""
    rays = RayFile(
        rays=[Ray(position=(-0.5, 0.4, 0.4), direction=(0.0, 0.0, 1.0), wavelength=555.0)]
    )
    path = rays.save_text(tmp_path / "rays.txt")

    assert read_lines(path) == ["1", "1 -0.5 0.4 0.4 0 0 1 555 1"]


def test_text_round_trip(documented_rays, tmp_path):
    """Reading back a written text file must give equivalent rays."""
    _normalize(documented_rays)
    path = documented_rays.save_text(tmp_path / "rays.txt")

    assert RayFile.load_text(path).rays == documented_rays.rays


def test_text_round_trip_with_polarization(tmp_path):
    """A polarized text file must carry the five extra values of each ray."""
    rays = RayFile(
        rays=[
            Ray(
                position=(0.0, 0.0, 0.0),
                direction=(0.0, 0.0, 1.0),
                wavelength=633.0,
                polarization=(1.0, 0.0, 0.0, 0.5, 1.0),
            )
        ]
    )
    path = rays.save_text(tmp_path / "polarized.txt")

    assert read_lines(path)[1].split() == [
        "1",
        "0",
        "0",
        "0",
        "0",
        "0",
        "1",
        "633",
        "1",
        "1",
        "0",
        "0",
        "0.5",
        "1",
    ]
    assert RayFile.load_text(path).rays == rays.rays


def test_a_partially_polarized_file_is_rejected(tmp_path):
    """Speos cannot mix polarized and unpolarized rays in one file."""
    rays = RayFile(
        rays=[
            Ray(polarization=(1.0, 0.0, 0.0, 0.5, 0.0)),
            Ray(),
        ]
    )

    with pytest.raises(ValueError, match="every ray or no ray"):
        rays.save_text(tmp_path / "mixed.txt")


def test_a_direction_that_is_not_a_unit_vector_is_rejected(tmp_path):
    """Speos stores the direction as cosines, so it must be a unit vector."""
    rays = RayFile(rays=[Ray(direction=(1.0, 1.0, 1.0))])

    with pytest.raises(ValueError, match="unit vector"):
        rays.save(tmp_path / "invalid.ray")


def test_an_empty_ray_file_is_rejected(tmp_path):
    """A ray file must hold at least one ray."""
    with pytest.raises(ValueError, match="at least one ray"):
        RayFile().save(tmp_path / "empty.ray")


def test_a_truncated_binary_file_is_reported(tmp_path):
    """Reading must report a binary file whose ray records are incomplete."""
    path = tmp_path / "truncated.ray"
    path.write_bytes(SPEOS_RAY_FILE.read_bytes()[:-7])

    with pytest.raises(ValueError, match="not a binary Speos ray file"):
        RayFile.load(path)


def test_an_inconsistent_text_file_is_reported(tmp_path):
    """Reading must report a text file whose ray count does not match its content."""
    path = tmp_path / "inconsistent.txt"
    path.write_text("3\n1 0 0 0 0 0 1 555 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="declares 3 rays but holds 1"):
        RayFile.load_text(path)
