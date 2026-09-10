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

"""Provides the Speos ``*.coated`` input file format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ansys.speos.core.input_files._base import (
    _PERCENT,
    LineReader,
    SpeosTextFileFormat,
    _data_line,
    _read_grid,
    _tagged,
    _wavelength_line,
    check_percentage,
)


@dataclass
class CoatedSurfaceSample:
    """Coating response at one angle of incidence and one wavelength.

    Parameters
    ----------
    reflection_p : float, optional
        Reflected part of the P polarization, in percent. By default, ``0.0``.
    transmission_p : float, optional
        Transmitted part of the P polarization, in percent. By default, ``0.0``.
    reflection_s : float, optional
        Reflected part of the S polarization, in percent. By default, ``0.0``.
    transmission_s : float, optional
        Transmitted part of the S polarization, in percent. By default, ``0.0``.
    """

    reflection_p: float = field(default=0.0, metadata=_PERCENT)
    transmission_p: float = field(default=0.0, metadata=_PERCENT)
    reflection_s: float = field(default=0.0, metadata=_PERCENT)
    transmission_s: float = field(default=0.0, metadata=_PERCENT)

    @property
    def absorption_p(self) -> float:
        """Absorbed part of the P polarization, in percent.

        Returns
        -------
        float
            Complement to 100 of the P reflection and transmission.
        """
        return 100.0 - self.reflection_p - self.transmission_p

    @property
    def absorption_s(self) -> float:
        """Absorbed part of the S polarization, in percent.

        Returns
        -------
        float
            Complement to 100 of the S reflection and transmission.
        """
        return 100.0 - self.reflection_s - self.transmission_s

    def validate(self) -> None:
        """Check the coating response of the sample.

        Raises
        ------
        ValueError
            If a value is outside the 0 to 100 range.

        Notes
        -----
        A negative :attr:`absorption_p` or :attr:`absorption_s` is not rejected: the
        coating samples published by Ansys do overrun 100 percent on a polarization, and
        the Coated Surface Editor only flags it.
        """
        for name, value in _tagged(self, _PERCENT).items():
            check_percentage(name, value)


@dataclass
class CoatedSurfaceFile(SpeosTextFileFormat):
    """Speos ``*.coated`` file, a non-scattering coating varying with angle and wavelength.

    The file holds one :class:`CoatedSurfaceSample` per angle of incidence and per
    wavelength, stored in ``samples[incidence_index][wavelength_index]``.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths of the samples, in nm, sorted in increasing order. By default, ``[]``.
    incident_angles : List[float], optional
        Angles of incidence of the samples, in degrees, sorted in increasing order.
        By default, ``[]``.
    samples : List[List[CoatedSurfaceSample]], optional
        Coating responses, one row per angle of incidence and one column per wavelength.
        By default, ``[]``.
    description : str, optional
        Free text written on the second line of the file. By default, ``"Coated surface"``.

    Notes
    -----
    A Speos coating is only valid for the rays crossing the interface in one direction.

    Examples
    --------
    >>> from ansys.speos.core.input_files.coated_surface import (
    ...     CoatedSurfaceFile,
    ...     CoatedSurfaceSample,
    ... )
    >>> sample = CoatedSurfaceSample(31.9, 68.1, 31.9, 68.1)
    >>> CoatedSurfaceFile(
    ...     wavelengths=[480.0, 780.0],
    ...     incident_angles=[0.0, 90.0],
    ...     samples=[[sample, sample], [sample, sample]],
    ... ).save("mirror.coated")
    """

    wavelengths: List[float] = field(default_factory=list)
    incident_angles: List[float] = field(default_factory=list)
    samples: List[List[CoatedSurfaceSample]] = field(default_factory=list)
    description: str = "Coated surface"

    EXTENSION = ".coated"
    HEADER = "OPTIS - Coated surface file v1.0"
    HEADER_PREFIX = "OPTIS - Coated surface file"

    def validate(self) -> None:
        """Check the coating against the constraints of the ``*.coated`` format.

        Raises
        ------
        ValueError
            If no wavelength or angle of incidence is given, they are not sorted, the
            sample grid does not match them, or a sample holds invalid values.
        """
        if not self.wavelengths:
            raise ValueError("At least one wavelength is required.")
        if not self.incident_angles:
            raise ValueError("At least one angle of incidence is required.")
        if sorted(self.wavelengths) != list(self.wavelengths):
            raise ValueError("wavelengths must be sorted in increasing order.")
        if sorted(self.incident_angles) != list(self.incident_angles):
            raise ValueError("incident_angles must be sorted in increasing order.")
        if any(not 0.0 <= angle <= 90.0 for angle in self.incident_angles):
            raise ValueError("incident_angles must be between 0 and 90 degrees.")
        if len(self.samples) != len(self.incident_angles):
            raise ValueError(
                f"samples must hold one row per angle of incidence, expected "
                f"{len(self.incident_angles)} rows, got {len(self.samples)}."
            )
        for angle, row in zip(self.incident_angles, self.samples):
            if len(row) != len(self.wavelengths):
                raise ValueError(
                    f"At {angle} degrees, samples must hold one entry per wavelength, "
                    f"expected {len(self.wavelengths)}, got {len(row)}."
                )
            for sample in row:
                sample.validate()

    def _to_lines(self) -> List[str]:
        lines = [
            self.description,
            f"{len(self.incident_angles)} {len(self.wavelengths)}",
            _wavelength_line(self.wavelengths, values_per_wavelength=2),
        ]
        for angle, row in zip(self.incident_angles, self.samples):
            polarization_p = [
                value for sample in row for value in (sample.reflection_p, sample.transmission_p)
            ]
            polarization_s = [
                value for sample in row for value in (sample.reflection_s, sample.transmission_s)
            ]
            lines.append(_data_line(polarization_p, incidence=angle))
            lines.append(_data_line(polarization_s))
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> CoatedSurfaceFile:
        description = reader.next_line()
        angle_count, wavelength_count = (int(value) for value in reader.next_floats(count=2))
        wavelengths = reader.next_floats(count=wavelength_count)
        blocks = _read_grid(reader, angle_count, row_count=2, value_count=2 * wavelength_count)

        incident_angles, samples = [], []
        for block in blocks:
            incident_angles.append(block[0][0])
            polarization_p, polarization_s = block[1:]
            samples.append(
                [
                    CoatedSurfaceSample(
                        *polarization_p[2 * index : 2 * index + 2],
                        *polarization_s[2 * index : 2 * index + 2],
                    )
                    for index in range(wavelength_count)
                ]
            )
        return cls(
            wavelengths=wavelengths,
            incident_angles=incident_angles,
            samples=samples,
            description=description,
        )
