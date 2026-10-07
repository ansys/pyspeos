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

from typing import ClassVar, List

from ansys.speos.core.input_files._base import (
    LineReader,
    SpeosTextFileFormat,
    _data_line,
    _finite_values,
    _matching_grid,
    _percentage,
    _property_name,
    _read_grid,
    _single_line,
    _ValueComparable,
    _wavelength_line,
    check_percentage,
)


class CoatedSurfaceSample(_ValueComparable):
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

    def __init__(
        self,
        reflection_p: float = 0.0,
        transmission_p: float = 0.0,
        reflection_s: float = 0.0,
        transmission_s: float = 0.0,
    ) -> None:
        self.reflection_p = reflection_p
        self.transmission_p = transmission_p
        self.reflection_s = reflection_s
        self.transmission_s = transmission_s

    @property
    def reflection_p(self) -> float:
        """Reflected P polarization, in percent.

        Returns
        -------
        float
            Contribution between 0 and 100.
        """
        return self._reflection_p

    @reflection_p.setter
    def reflection_p(self, value: float) -> None:
        self._reflection_p = _percentage(_property_name(CoatedSurfaceSample.reflection_p), value)

    @property
    def transmission_p(self) -> float:
        """Transmitted P polarization, in percent.

        Returns
        -------
        float
            Contribution between 0 and 100.
        """
        return self._transmission_p

    @transmission_p.setter
    def transmission_p(self, value: float) -> None:
        self._transmission_p = _percentage(
            _property_name(CoatedSurfaceSample.transmission_p), value
        )

    @property
    def reflection_s(self) -> float:
        """Reflected S polarization, in percent.

        Returns
        -------
        float
            Contribution between 0 and 100.
        """
        return self._reflection_s

    @reflection_s.setter
    def reflection_s(self, value: float) -> None:
        self._reflection_s = _percentage(_property_name(CoatedSurfaceSample.reflection_s), value)

    @property
    def transmission_s(self) -> float:
        """Transmitted S polarization, in percent.

        Returns
        -------
        float
            Contribution between 0 and 100.
        """
        return self._transmission_s

    @transmission_s.setter
    def transmission_s(self, value: float) -> None:
        self._transmission_s = _percentage(
            _property_name(CoatedSurfaceSample.transmission_s), value
        )

    _COATING_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(reflection_p),
        _property_name(transmission_p),
        _property_name(reflection_s),
        _property_name(transmission_s),
    )
    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = _COATING_FIELDS

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
        for name in self._COATING_FIELDS:
            check_percentage(name, getattr(self, name))


_COATING_FIELDS = CoatedSurfaceSample._COATING_FIELDS


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
    List getters copy the containers, while sample objects remain shared and editable
    through validated properties. To resize a populated grid, clear :attr:`samples`, set
    the axes, then assign the new grid. Empty lists allow drafts; :meth:`save` requires
    complete axes and samples.

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

    def __init__(
        self,
        wavelengths: List[float] | None = None,
        incident_angles: List[float] | None = None,
        samples: List[List[CoatedSurfaceSample]] | None = None,
        description: str = "Coated surface",
    ) -> None:
        self._wavelengths: List[float] = []
        self._incident_angles: List[float] = []
        self._samples: List[List[CoatedSurfaceSample]] = []
        self.wavelengths = wavelengths if wavelengths is not None else []
        self.incident_angles = incident_angles if incident_angles is not None else []
        self.samples = samples if samples is not None else []
        self.description = description

    @property
    def wavelengths(self) -> List[float]:
        """Sorted wavelengths in nm, returned as a copy.

        Returns
        -------
        List[float]
            Finite wavelengths, or an empty draft column.
        """
        return self._wavelengths.copy()

    @wavelengths.setter
    def wavelengths(self, values: List[float]) -> None:
        values = _finite_values(_property_name(CoatedSurfaceFile.wavelengths), values)
        if sorted(values) != values:
            raise ValueError("wavelengths must be sorted in increasing order.")
        self._check_grid(self._samples, self._incident_angles, values)
        self._wavelengths = values

    @property
    def incident_angles(self) -> List[float]:
        """Sorted incidence angles in degrees, returned as a copy.

        Returns
        -------
        List[float]
            Angles between 0 and 90, or an empty draft column.
        """
        return self._incident_angles.copy()

    @incident_angles.setter
    def incident_angles(self, values: List[float]) -> None:
        values = _finite_values(_property_name(CoatedSurfaceFile.incident_angles), values)
        if sorted(values) != values:
            raise ValueError("incident_angles must be sorted in increasing order.")
        if any(not 0.0 <= value <= 90.0 for value in values):
            raise ValueError("incident_angles must be between 0 and 90 degrees.")
        self._check_grid(self._samples, values, self._wavelengths)
        self._incident_angles = values

    @property
    def samples(self) -> List[List[CoatedSurfaceSample]]:
        """Sample grid with copied containers and shared samples.

        Returns
        -------
        List[List[CoatedSurfaceSample]]
            Rows per incidence and columns per wavelength.
        """
        return [row.copy() for row in self._samples]

    @samples.setter
    def samples(self, values: List[List[CoatedSurfaceSample]]) -> None:
        values = [list(row) for row in values]
        for row in values:
            for sample in row:
                if not isinstance(sample, CoatedSurfaceSample):
                    raise TypeError("samples must contain CoatedSurfaceSample objects.")
                sample.validate()
        self._check_grid(values, self._incident_angles, self._wavelengths)
        self._samples = values

    @property
    def description(self) -> str:
        """Single-line description.

        Returns
        -------
        str
            Free text written after the header.
        """
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = _single_line(value)

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(wavelengths),
        _property_name(incident_angles),
        _property_name(samples),
        _property_name(description),
    )

    @staticmethod
    def _check_grid(samples, angles, wavelengths) -> None:
        _matching_grid(
            "samples",
            samples,
            row_count=len(angles) if samples and angles else None,
            column_count=len(wavelengths) if wavelengths else None,
            row_axis="angle of incidence",
        )

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
        _matching_grid(
            "samples",
            self._samples,
            row_count=len(self._incident_angles),
            column_count=len(self._wavelengths),
            row_axis="angle of incidence",
            incidences=self._incident_angles,
        )
        for row in self._samples:
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
