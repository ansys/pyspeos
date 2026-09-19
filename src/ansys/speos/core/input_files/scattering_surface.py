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

"""Provides the Speos ``*.scattering`` input file format."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import List

from ansys.speos.core.input_files._base import (
    _DEGREES,
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
class ScatteringSurfaceSample:
    """Scattering contributions of a surface at one angle of incidence and one wavelength.

    Every contribution is a percentage of the incident light. What is left once the six
    contributions are summed is absorbed, see :attr:`absorption`.

    Parameters
    ----------
    specular_reflection : float, optional
        Specularly reflected part, in percent. By default, ``0.0``.
    specular_transmission : float, optional
        Specularly transmitted part, in percent. By default, ``0.0``.
    lambertian_reflection : float, optional
        Lambertian reflected part, in percent. By default, ``0.0``.
    lambertian_transmission : float, optional
        Lambertian transmitted part, in percent. By default, ``0.0``.
    gaussian_reflection : float, optional
        Gaussian reflected part, in percent. By default, ``0.0``.
    gaussian_transmission : float, optional
        Gaussian transmitted part, in percent. By default, ``0.0``.
    gaussian_fwhm_incidence_reflection : float, optional
        Full width at half maximum of the reflected Gaussian lobe in the incidence plane,
        in degrees. By default, ``0.0``.
    gaussian_fwhm_incidence_transmission : float, optional
        Full width at half maximum of the transmitted Gaussian lobe in the incidence
        plane, in degrees. By default, ``0.0``.
    gaussian_fwhm_perpendicular_reflection : float, optional
        Full width at half maximum of the reflected Gaussian lobe in the perpendicular
        plane, in degrees. By default, ``0.0``.
    gaussian_fwhm_perpendicular_transmission : float, optional
        Full width at half maximum of the transmitted Gaussian lobe in the perpendicular
        plane, in degrees. By default, ``0.0``.
    """

    specular_reflection: float = field(default=0.0, metadata=_PERCENT)
    specular_transmission: float = field(default=0.0, metadata=_PERCENT)
    lambertian_reflection: float = field(default=0.0, metadata=_PERCENT)
    lambertian_transmission: float = field(default=0.0, metadata=_PERCENT)
    gaussian_reflection: float = field(default=0.0, metadata=_PERCENT)
    gaussian_transmission: float = field(default=0.0, metadata=_PERCENT)
    gaussian_fwhm_incidence_reflection: float = field(default=0.0, metadata=_DEGREES)
    gaussian_fwhm_incidence_transmission: float = field(default=0.0, metadata=_DEGREES)
    gaussian_fwhm_perpendicular_reflection: float = field(default=0.0, metadata=_DEGREES)
    gaussian_fwhm_perpendicular_transmission: float = field(default=0.0, metadata=_DEGREES)

    @property
    def absorption(self) -> float:
        """Absorbed part of the incident light, in percent.

        Returns
        -------
        float
            Complement to 100 of the six reflection and transmission contributions.
        """
        return 100.0 - sum(_tagged(self, _PERCENT).values())

    def validate(self) -> None:
        """Check the contributions of the sample.

        Raises
        ------
        ValueError
            If a contribution is outside the 0 to 100 range, a full width at half maximum
            is outside the 0 to 90 degrees range, or :attr:`absorption` is negative.
        """
        for name, value in _tagged(self, _PERCENT).items():
            check_percentage(name, value)
        for name, angle in _tagged(self, _DEGREES).items():
            if not 0.0 <= angle <= 90.0:
                raise ValueError(f"{name} must be between 0 and 90 degrees, got {angle}.")
        if self.absorption < 0.0:
            raise ValueError(
                "The reflection and transmission contributions must not sum to more than "
                f"100, got an absorption of {self.absorption}."
            )


@dataclass
class ScatteringSurfaceFile(SpeosTextFileFormat):
    """Speos ``*.scattering`` file, a scattering surface varying with angle and wavelength.

    The file holds one :class:`ScatteringSurfaceSample` per angle of incidence and per
    wavelength, stored in ``samples[incidence_index][wavelength_index]``.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths of the samples, in nm, sorted in increasing order. At least two
        wavelengths are required. By default, ``[]``.
    incident_angles : List[float], optional
        Angles of incidence of the samples, in degrees, sorted in increasing order.
        ``0`` and ``90`` are required. By default, ``[]``.
    samples : List[List[ScatteringSurfaceSample]], optional
        Contributions, one row per angle of incidence and one column per wavelength.
        By default, ``[]``.
    description : str, optional
        Free text written on the second line of the file. By default,
        ``"Scattering surface"``.

    Examples
    --------
    >>> from ansys.speos.core.input_files.scattering_surface import (
    ...     ScatteringSurfaceFile,
    ...     ScatteringSurfaceSample,
    ... )
    >>> grey = ScatteringSurfaceSample(lambertian_reflection=50.0)
    >>> surface = ScatteringSurfaceFile(
    ...     wavelengths=[400.0, 700.0],
    ...     incident_angles=[0.0, 90.0],
    ...     samples=[[grey, grey], [grey, grey]],
    ... )
    >>> surface.save("grey.scattering")
    """

    wavelengths: List[float] = field(default_factory=list)
    incident_angles: List[float] = field(default_factory=list)
    samples: List[List[ScatteringSurfaceSample]] = field(default_factory=list)
    description: str = "Scattering surface"

    EXTENSION = ".scattering"
    HEADER = "OPTIS - Scattering surface file v1.0"
    HEADER_PREFIX = "OPTIS - Scattering surface file"

    def validate(self) -> None:
        """Check the surface against the constraints of the ``*.scattering`` format.

        Raises
        ------
        ValueError
            If fewer than two wavelengths are given, the angles of incidence do not span
            0 to 90 degrees, the sample grid does not match the wavelengths and angles, or
            a sample holds invalid contributions.
        """
        if len(self.wavelengths) < 2:
            raise ValueError("At least two wavelengths are required.")
        if sorted(self.wavelengths) != list(self.wavelengths):
            raise ValueError("wavelengths must be sorted in increasing order.")
        if sorted(self.incident_angles) != list(self.incident_angles):
            raise ValueError("incident_angles must be sorted in increasing order.")
        if 0.0 not in self.incident_angles or 90.0 not in self.incident_angles:
            raise ValueError("incident_angles must hold both 0 and 90 degrees.")
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
        # The sample fields are declared in file order, reflection then transmission.
        names = [entry.name for entry in fields(ScatteringSurfaceSample)]
        rows = list(zip(names[::2], names[1::2]))
        for angle, row in zip(self.incident_angles, self.samples):
            for index, (reflection, transmission) in enumerate(rows):
                values = [
                    value
                    for sample in row
                    for value in (getattr(sample, reflection), getattr(sample, transmission))
                ]
                lines.append(_data_line(values, incidence=angle if index == 0 else None))
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> ScatteringSurfaceFile:
        description = reader.next_line()
        angle_count, wavelength_count = (int(value) for value in reader.next_floats(count=2))
        wavelengths = reader.next_floats(count=wavelength_count)
        blocks = _read_grid(reader, angle_count, row_count=5, value_count=2 * wavelength_count)

        incident_angles, samples = [], []
        for block in blocks:
            incident_angles.append(block[0][0])
            specular, lambertian, gaussian, fwhm_incidence, fwhm_perpendicular = block[1:]
            row = []
            for index in range(wavelength_count):
                low, high = 2 * index, 2 * index + 2
                row.append(
                    ScatteringSurfaceSample(
                        *specular[low:high],
                        *lambertian[low:high],
                        *gaussian[low:high],
                        *fwhm_incidence[low:high],
                        *fwhm_perpendicular[low:high],
                    )
                )
            samples.append(row)
        return cls(
            wavelengths=wavelengths,
            incident_angles=incident_angles,
            samples=samples,
            description=description,
        )
