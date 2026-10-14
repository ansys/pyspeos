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
import struct

import pytest

from ansys.speos.core import Ray, RayFile
from tests.input_files import ASSETS_DIR, read_lines

SPEOS_RAY_FILE = ASSETS_DIR / "Rays.ray"
"""Binary ray file produced by Speos, holding 45462 rays."""


def _sdf_bytes(records, *, identifier=1010, source_flux=3.0, ray_set_flux=3.0):
    """Pack an independent SDF fixture using the published field offsets."""
    header = bytearray(208)
    struct.pack_into("<II", header, 0, identifier, len(records))
    header[8:108] = b"Independent SDF fixture".ljust(100, b" ")
    struct.pack_into("<ff", header, 108, source_flux, ray_set_flux)
    struct.pack_into("<I", header, 136, 4)
    struct.pack_into("<II", header, 192, 2, 0)
    return bytes(header) + b"".join(struct.pack("<8f", *row) for row in records)


def test_sdf_export_matches_independent_binary_layout(tmp_path):
    """SDF output converts wavelengths and allocates absolute watts from relative weights."""
    model = RayFile(
        [Ray(energy=1.0, wavelength=500.0), Ray(position=(1.0, 2.0, 3.0), energy=0.5)],
        radiant_flux=3.0,
    )
    path = model.save_sdf(tmp_path / "source.sdf")
    content = path.read_bytes()
    assert len(content) == 208 + 2 * 32
    assert struct.unpack_from("<II", content) == (1010, 2)
    assert len(content[8:108]) == 100
    assert content[8:108].decode("ascii").strip() == "Converted from Speos by PySpeos."
    assert struct.unpack_from("<ff", content, 108) == (3.0, 3.0)
    assert struct.unpack_from("<I", content, 136) == (4,)
    assert struct.unpack_from("<II", content, 192) == (2, 0)
    assert struct.unpack_from("<8f", content, 208) == pytest.approx((0, 0, 0, 0, 0, 1, 2, 0.5))
    assert struct.unpack_from("<8f", content, 240) == pytest.approx((1, 2, 3, 0, 0, 1, 1, 0.555))
    assert [ray.energy for ray in model.rays] == [1.0, 0.5]


@pytest.mark.parametrize("identifier", [1010, 8675309])
def test_sdf_import_normalizes_record_weights_and_retains_ray_set_power(identifier, tmp_path):
    """SDF import handles unnormalized records and a partial source ray set."""
    path = tmp_path / "independent.sdf"
    records = [(1, 2, 3, 0, 0, 1, 4, 0.5), (4, 5, 6, 1, 0, 0, 2, 0.633)]
    path.write_bytes(_sdf_bytes(records, identifier=identifier, source_flux=10.0))
    model = RayFile.load_sdf(path)
    assert model.radiant_flux == 3.0
    assert model.luminous_flux == 683.0
    assert model.rays[0].position == (1.0, 2.0, 3.0)
    assert model.rays[1].direction == (1.0, 0.0, 0.0)
    assert [ray.energy for ray in model.rays] == pytest.approx([2 / 3, 1 / 3])
    assert [ray.wavelength for ray in model.rays] == pytest.approx([500.0, 633.0])
    assert RayFile.load_sdf(path, luminous_flux=112.0).luminous_flux == 112.0
    read_back = RayFile.load_sdf(model.save_sdf(tmp_path / "copy.sdf"))
    assert [ray.energy for ray in read_back.rays] == pytest.approx([2 / 3, 1 / 3])
    assert read_back.radiant_flux == model.radiant_flux


@pytest.mark.parametrize("energies", [[1.0, 1.0], [0.0, 0.0]])
def test_sdf_zero_power_round_trip(energies, tmp_path):
    """A dark ray set retains geometry and wavelengths without dividing by zero."""
    model = RayFile([Ray(energy=energy) for energy in energies], radiant_flux=0.0)
    loaded = RayFile.load_sdf(model.save_sdf(tmp_path / "dark.sdf"))
    assert loaded.radiant_flux == 0.0
    assert [ray.energy for ray in loaded.rays] == [0.0, 0.0]
    assert [ray.wavelength for ray in loaded.rays] == pytest.approx([555.0, 555.0])


@pytest.mark.parametrize(
    "model, message",
    [
        (RayFile(), "at least one ray"),
        (RayFile([Ray(energy=0)], radiant_flux=1), "nonzero"),
        (RayFile([Ray()], radiant_flux=-1), "nonnegative"),
        (RayFile([Ray(wavelength=0)]), "positive"),
        (RayFile([Ray(polarization=(1, 0, 0, 0, 1))]), "polarization"),
        (RayFile([Ray(position=(1e100, 0, 0))]), "32-bit"),
        (RayFile([Ray()], radiant_flux=1e100), "32-bit"),
        (RayFile([Ray(wavelength=1e-100)]), "underflow"),
        (RayFile([Ray()], radiant_flux=1e-100), "underflow"),
    ],
)
def test_sdf_invalid_export_does_not_overwrite(model, message, tmp_path):
    """Invalid SDF data is rejected before creating or truncating the output."""
    path = tmp_path / "protected.sdf"
    path.write_bytes(b"existing data")
    with pytest.raises(ValueError, match=message):
        model.save_sdf(path)
    assert path.read_bytes() == b"existing data"
    missing = tmp_path / "missing.sdf"
    with pytest.raises(ValueError, match=message):
        model.save_sdf(missing)
    assert not missing.exists()


@pytest.mark.parametrize(
    "offset, format_code, value, message",
    [
        (0, "I", 42, "identifier"),
        (4, "I", 0, "count"),
        (4, "I", 2, "count"),
        (136, "I", 0, "millimeters"),
        (192, "I", 0, "spectral"),
        (196, "I", 1, "spectral"),
        (140, "f", 1.0, "transforms"),
        (164, "f", 2.0, "transforms"),
        (108, "f", -1.0, "nonnegative"),
        (112, "f", -1.0, "nonnegative"),
        (116, "f", float("nan"), "finite"),
        (208, "f", float("inf"), "finite"),
        (228, "f", 0.0, "unit vector"),
        (232, "f", -1.0, "nonnegative"),
        (232, "f", 0.0, "nonzero"),
        (236, "f", 0.0, "positive"),
    ],
)
def test_sdf_invalid_header_or_record_is_rejected(offset, format_code, value, message, tmp_path):
    """Unsupported headers and invalid record values produce explicit errors."""
    content = bytearray(_sdf_bytes([(0, 0, 0, 0, 0, 1, 3, 0.555)]))
    struct.pack_into("<" + format_code, content, offset, value)
    path = tmp_path / "invalid.sdf"
    path.write_bytes(content)
    with pytest.raises(ValueError, match=message):
        RayFile.load_sdf(path)


@pytest.mark.parametrize("size", [0, 100, 207, 209, 239, 241])
def test_sdf_truncation_and_extra_bytes_are_rejected(size, tmp_path):
    """The declared SDF ray count must match the complete binary payload exactly."""
    content = _sdf_bytes([(0, 0, 0, 0, 0, 1, 3, 0.555)])
    path = tmp_path / "truncated.sdf"
    path.write_bytes(content[:size] if size <= len(content) else content + b"extra")
    with pytest.raises(ValueError, match="header|file size"):
        RayFile.load_sdf(path)


def test_sdf_missing_file_raises_file_not_found(tmp_path):
    """A missing SDF file raises the documented filesystem error."""
    with pytest.raises(FileNotFoundError):
        RayFile.load_sdf(tmp_path / "missing.sdf")


@pytest.fixture
def documented_rays():
    """Build the five rays used as an example by the Speos documentation."""
    return RayFile(
        rays=[
            Ray(
                position=(-0.5, 0.4, 0.4), direction=_normalize((0.5, -0.1, 0.7)), wavelength=555.0
            ),
            Ray(
                position=(0.7, -0.5, 12.0), direction=_normalize((0.2, -0.4, 0.2)), wavelength=555.0
            ),
            Ray(
                position=(0.8, -0.2, 18.0),
                direction=_normalize((-0.5, -0.4, 0.7)),
                wavelength=532.0,
            ),
            Ray(position=(-0.1, 0.5, 4.0), direction=_normalize((0.5, 0.2, 0.7)), wavelength=452.0),
            Ray(
                position=(1.7, -0.8, 2.0), direction=_normalize((0.2, -0.4, 0.6)), wavelength=633.0
            ),
        ]
    )


def _normalize(direction):
    """Normalize a direction before constructing a validated ray."""
    norm = math.hypot(*direction)
    return tuple(value / norm for value in direction)


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
    with pytest.raises(ValueError, match="unit vector"):
        Ray(direction=(1.0, 1.0, 1.0))


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("position", (1.0, 2.0)),
        ("direction", (0.0, 0.0, 0.0)),
        ("polarization", (1.0, 2.0)),
        ("wavelength", float("inf")),
        ("energy", float("nan")),
    ],
)
def test_ray_setters_validate_atomically(name, value):
    """Invalid ray values are rejected before replacing the previous value."""
    ray = Ray()
    previous = getattr(ray, name)
    with pytest.raises(ValueError):
        setattr(ray, name, value)
    assert getattr(ray, name) == previous
    with pytest.raises(ValueError):
        Ray(**{name: value})


def test_ray_direction_tolerance_and_copied_collection():
    """Direction tolerance is retained and the file copies its ray container."""
    ray = Ray(direction=(0.0, 0.0, 1.0005))
    values = [ray]
    ray_file = RayFile(values)
    values.clear()
    ray_file.rays.clear()
    assert ray_file.rays == [ray]
    with pytest.raises(ValueError):
        ray.direction = (0.0, 0.0, 1.002)
    with pytest.raises(TypeError):
        ray_file.rays = [object()]
    with pytest.raises(ValueError):
        ray_file.radiant_flux = float("inf")
    assert ray_file.radiant_flux == 1.0
    ray_file.rays[0].energy = 0.5
    assert ray.energy == 0.5


def test_empty_ray_files_cannot_be_saved(tmp_path):
    """An empty ray file can be constructed but must be rejected when saving."""
    ray_file = RayFile()
    path = tmp_path / "empty.ray"

    with pytest.raises(ValueError, match="at least one ray"):
        ray_file.save(path)

    assert not path.exists()


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


@pytest.mark.parametrize("count", ["0", "-1", "1.5", "1.0", "1e0", "inf", "nan"])
def test_text_ray_counts_are_positive_integers(count, tmp_path):
    """Ray counts use the same strict integer rules as other local file formats."""
    path = tmp_path / "invalid.txt"
    path.write_text(f"\n{count}\n1 0 0 0 0 0 1 555 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"line 2: expected an integer"):
        RayFile.load_text(path)


def test_text_ray_blank_lines_preserve_error_locations(tmp_path):
    """Blank lines remain accepted without changing physical line numbers in errors."""
    path = tmp_path / "rays.txt"
    path.write_text("\n1\n\n1 0 0 0 0 0 1 555 1\n\n", encoding="utf-8")
    assert RayFile.load_text(path).rays == [Ray()]
    for row, message in [
        ("1 0 0 0 0 0 1 nan 1", "finite"),
        ("1 0 0 0 0 0 1 555 2", "energy"),
        ("1 0 0 0 0 0 0 555 1", "unit vector"),
        ("1 0 0", "expected 9 values"),
    ]:
        path.write_text(f"\n1\n\n{row}\n", encoding="utf-8")
        with pytest.raises(ValueError, match=f"line 4:.*{message}"):
            RayFile.load_text(path)


@pytest.mark.parametrize("content", ["", "\n\n", "1\n", "1\n" + "1 0 0 0 0 0 1 555 1\n" * 2])
def test_text_ray_empty_or_mismatched_files_are_rejected(content, tmp_path):
    """Missing and extra ray lines cannot produce a loaded draft."""
    path = tmp_path / "invalid.txt"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="empty|declares 1 rays"):
        RayFile.load_text(path)


@pytest.mark.parametrize("mixed", [False, True])
@pytest.mark.parametrize("existing", [False, True])
def test_binary_save_rejects_any_polarization_without_writing(mixed, existing, tmp_path):
    """Neither fully nor partly polarized binary output can discard data or overwrite files."""
    rays = [Ray(polarization=(1.0, 0.0, 0.0, 0.5, 1.0))]
    if mixed:
        rays.append(Ray())
    path = tmp_path / "polarized.ray"
    if existing:
        path.write_bytes(b"original content")
    with pytest.raises(ValueError, match=r"polarization; use save_text\(\)"):
        RayFile(rays).save(path)
    if existing:
        assert path.read_bytes() == b"original content"
    else:
        assert not path.exists()


@pytest.mark.parametrize("marker_index", range(1, 6))
@pytest.mark.parametrize("value", [3.0, float("inf"), float("nan")])
def test_binary_header_markers_are_validated(marker_index, value, tmp_path):
    """Every marker in an otherwise valid binary ray file is checked."""
    path = RayFile([Ray()]).save(tmp_path / "invalid.ray")
    content = bytearray(path.read_bytes())
    struct.pack_into("<f", content, marker_index * 4, value)
    path.write_bytes(content)
    with pytest.raises(ValueError, match="invalid header markers"):
        RayFile.load(path)


def test_header_only_binary_ray_file_is_rejected(tmp_path):
    """The shared load validation rejects binary files without any rays."""
    path = tmp_path / "empty.ray"
    path.write_bytes(struct.pack("<7f", 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 683.0))
    with pytest.raises(ValueError, match="at least one ray"):
        RayFile.load(path)


@pytest.mark.parametrize("value", [-0.001, 1.001])
def test_ray_energy_bounds_are_atomic(value):
    """Out-of-range energy is rejected during construction and mutation."""
    ray = Ray(energy=0.5)
    with pytest.raises(ValueError, match="energy must be between 0 and 1"):
        ray.energy = value
    assert ray.energy == 0.5
    with pytest.raises(ValueError, match="energy must be between 0 and 1"):
        Ray(energy=value)


@pytest.mark.parametrize("value", [0.0, 1.0])
def test_ray_energy_endpoints_are_valid(value):
    """The closed energy interval includes both endpoints."""
    assert Ray(energy=value).energy == value
