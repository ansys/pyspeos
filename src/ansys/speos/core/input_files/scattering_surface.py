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

import math
from typing import ClassVar, List

from ansys.speos.core.input_files._base import (
    LineReader,
    SpeosTextFileFormat,
    _data_line,
    _property_name,
    _read_grid,
    _ValueComparable,
    _wavelength_line,
    check_percentage,
)


class ScatteringSurfaceSample(_ValueComparable):
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

    Raises
    ------
    ValueError
        If a percentage is outside 0 to 100, the total contribution exceeds 100, or a
        Gaussian width is outside 0 to 90 degrees.

    Notes
    -----
    Construction and property assignments validate before storing a value. To redistribute
    a fully allocated light budget, lower the outgoing contribution before raising another.
    """

    def __init__(
        self,
        specular_reflection: float = 0.0,
        specular_transmission: float = 0.0,
        lambertian_reflection: float = 0.0,
        lambertian_transmission: float = 0.0,
        gaussian_reflection: float = 0.0,
        gaussian_transmission: float = 0.0,
        gaussian_fwhm_incidence_reflection: float = 0.0,
        gaussian_fwhm_incidence_transmission: float = 0.0,
        gaussian_fwhm_perpendicular_reflection: float = 0.0,
        gaussian_fwhm_perpendicular_transmission: float = 0.0,
    ) -> None:
        self._specular_reflection: float = 0.0
        self._specular_transmission: float = 0.0
        self._lambertian_reflection: float = 0.0
        self._lambertian_transmission: float = 0.0
        self._gaussian_reflection: float = 0.0
        self._gaussian_transmission: float = 0.0
        self._gaussian_fwhm_incidence_reflection: float = 0.0
        self._gaussian_fwhm_incidence_transmission: float = 0.0
        self._gaussian_fwhm_perpendicular_reflection: float = 0.0
        self._gaussian_fwhm_perpendicular_transmission: float = 0.0
        self.specular_reflection = specular_reflection
        self.specular_transmission = specular_transmission
        self.lambertian_reflection = lambertian_reflection
        self.lambertian_transmission = lambertian_transmission
        self.gaussian_reflection = gaussian_reflection
        self.gaussian_transmission = gaussian_transmission
        self.gaussian_fwhm_incidence_reflection = gaussian_fwhm_incidence_reflection
        self.gaussian_fwhm_incidence_transmission = gaussian_fwhm_incidence_transmission
        self.gaussian_fwhm_perpendicular_reflection = gaussian_fwhm_perpendicular_reflection
        self.gaussian_fwhm_perpendicular_transmission = gaussian_fwhm_perpendicular_transmission

    def _set_contribution(self, name: str, value: float) -> None:
        value = float(value)
        check_percentage(name, value)
        absorption = 100.0 - sum(
            value if entry == name else getattr(self, entry) for entry in _CONTRIBUTIONS
        )
        if absorption < 0.0:
            raise ValueError(
                "The reflection and transmission contributions must not sum to more than "
                f"100, got an absorption of {absorption}."
            )
        setattr(self, "_" + name, value)

    def _set_width(self, name: str, value: float) -> None:
        value = float(value)
        if not 0.0 <= value <= 90.0:
            raise ValueError(f"{name} must be between 0 and 90 degrees, got {value}.")
        setattr(self, "_" + name, value)

    @property
    def specular_reflection(self) -> float:
        """Specularly reflected part, in percent.

        Returns
        -------
        float
            Contribution between 0 and 100, within the total 100 percent budget.
        """
        return self._specular_reflection

    @specular_reflection.setter
    def specular_reflection(self, value: float) -> None:
        self._set_contribution(_property_name(ScatteringSurfaceSample.specular_reflection), value)

    @property
    def specular_transmission(self) -> float:
        """Specularly transmitted part, in percent.

        Returns
        -------
        float
            Contribution between 0 and 100, within the total 100 percent budget.
        """
        return self._specular_transmission

    @specular_transmission.setter
    def specular_transmission(self, value: float) -> None:
        self._set_contribution(_property_name(ScatteringSurfaceSample.specular_transmission), value)

    @property
    def lambertian_reflection(self) -> float:
        """Lambertian reflected part, in percent.

        Returns
        -------
        float
            Contribution between 0 and 100, within the total 100 percent budget.
        """
        return self._lambertian_reflection

    @lambertian_reflection.setter
    def lambertian_reflection(self, value: float) -> None:
        self._set_contribution(_property_name(ScatteringSurfaceSample.lambertian_reflection), value)

    @property
    def lambertian_transmission(self) -> float:
        """Lambertian transmitted part, in percent.

        Returns
        -------
        float
            Contribution between 0 and 100, within the total 100 percent budget.
        """
        return self._lambertian_transmission

    @lambertian_transmission.setter
    def lambertian_transmission(self, value: float) -> None:
        self._set_contribution(
            _property_name(ScatteringSurfaceSample.lambertian_transmission), value
        )

    @property
    def gaussian_reflection(self) -> float:
        """Gaussian reflected part, in percent.

        Returns
        -------
        float
            Contribution between 0 and 100, within the total 100 percent budget.
        """
        return self._gaussian_reflection

    @gaussian_reflection.setter
    def gaussian_reflection(self, value: float) -> None:
        self._set_contribution(_property_name(ScatteringSurfaceSample.gaussian_reflection), value)

    @property
    def gaussian_transmission(self) -> float:
        """Gaussian transmitted part, in percent.

        Returns
        -------
        float
            Contribution between 0 and 100, within the total 100 percent budget.
        """
        return self._gaussian_transmission

    @gaussian_transmission.setter
    def gaussian_transmission(self, value: float) -> None:
        self._set_contribution(_property_name(ScatteringSurfaceSample.gaussian_transmission), value)

    @property
    def gaussian_fwhm_incidence_reflection(self) -> float:
        """Reflected Gaussian FWHM in the incidence plane, in degrees.

        Returns
        -------
        float
            Full width at half maximum between 0 and 90 degrees.
        """
        return self._gaussian_fwhm_incidence_reflection

    @gaussian_fwhm_incidence_reflection.setter
    def gaussian_fwhm_incidence_reflection(self, value: float) -> None:
        self._set_width(
            _property_name(ScatteringSurfaceSample.gaussian_fwhm_incidence_reflection), value
        )

    @property
    def gaussian_fwhm_incidence_transmission(self) -> float:
        """Transmitted Gaussian FWHM in the incidence plane, in degrees.

        Returns
        -------
        float
            Full width at half maximum between 0 and 90 degrees.
        """
        return self._gaussian_fwhm_incidence_transmission

    @gaussian_fwhm_incidence_transmission.setter
    def gaussian_fwhm_incidence_transmission(self, value: float) -> None:
        self._set_width(
            _property_name(ScatteringSurfaceSample.gaussian_fwhm_incidence_transmission), value
        )

    @property
    def gaussian_fwhm_perpendicular_reflection(self) -> float:
        """Reflected Gaussian FWHM in the perpendicular plane, in degrees.

        Returns
        -------
        float
            Full width at half maximum between 0 and 90 degrees.
        """
        return self._gaussian_fwhm_perpendicular_reflection

    @gaussian_fwhm_perpendicular_reflection.setter
    def gaussian_fwhm_perpendicular_reflection(self, value: float) -> None:
        self._set_width(
            _property_name(ScatteringSurfaceSample.gaussian_fwhm_perpendicular_reflection), value
        )

    @property
    def gaussian_fwhm_perpendicular_transmission(self) -> float:
        """Transmitted Gaussian FWHM in the perpendicular plane, in degrees.

        Returns
        -------
        float
            Full width at half maximum between 0 and 90 degrees.
        """
        return self._gaussian_fwhm_perpendicular_transmission

    @gaussian_fwhm_perpendicular_transmission.setter
    def gaussian_fwhm_perpendicular_transmission(self, value: float) -> None:
        self._set_width(
            _property_name(ScatteringSurfaceSample.gaussian_fwhm_perpendicular_transmission), value
        )

    _CONTRIBUTIONS: ClassVar[tuple[str, ...]] = (
        _property_name(specular_reflection),
        _property_name(specular_transmission),
        _property_name(lambertian_reflection),
        _property_name(lambertian_transmission),
        _property_name(gaussian_reflection),
        _property_name(gaussian_transmission),
    )
    _WIDTHS: ClassVar[tuple[str, ...]] = (
        _property_name(gaussian_fwhm_incidence_reflection),
        _property_name(gaussian_fwhm_incidence_transmission),
        _property_name(gaussian_fwhm_perpendicular_reflection),
        _property_name(gaussian_fwhm_perpendicular_transmission),
    )
    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = _CONTRIBUTIONS + _WIDTHS

    @property
    def absorption(self) -> float:
        """Absorbed part of the incident light, in percent.

        Returns
        -------
        float
            Complement to 100 of the six reflection and transmission contributions.
        """
        return 100.0 - sum(getattr(self, name) for name in _CONTRIBUTIONS)

    def validate(self) -> None:
        """Check the contributions of the sample.

        Raises
        ------
        ValueError
            If a contribution is outside the 0 to 100 range, a full width at half maximum
            is outside the 0 to 90 degrees range, or :attr:`absorption` is negative.
        """
        for name in _CONTRIBUTIONS:
            check_percentage(name, getattr(self, name))
        for name in _WIDTHS:
            angle = getattr(self, name)
            if not 0.0 <= angle <= 90.0:
                raise ValueError(f"{name} must be between 0 and 90 degrees, got {angle}.")
        if self.absorption < 0.0:
            raise ValueError(
                "The reflection and transmission contributions must not sum to more than "
                f"100, got an absorption of {self.absorption}."
            )


_CONTRIBUTIONS = ScatteringSurfaceSample._CONTRIBUTIONS
_WIDTHS = ScatteringSurfaceSample._WIDTHS
_SAMPLE_FIELDS = ScatteringSurfaceSample._EQUALITY_FIELDS


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

    Notes
    -----
    Empty lists allow staged construction, but :meth:`validate` and :meth:`save` require
    a complete surface. Nonempty assignments are checked against the configured axes
    and grid. To resize a populated grid, clear :attr:`samples`, assign the new axes,
    then assign the new grid. List getters return copies of the containers, while sample
    objects remain shared so their validated properties can be edited directly.

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

    def __init__(
        self,
        wavelengths: List[float] | None = None,
        incident_angles: List[float] | None = None,
        samples: List[List[ScatteringSurfaceSample]] | None = None,
        description: str = "Scattering surface",
    ) -> None:
        self._wavelengths: List[float] = []
        self._incident_angles: List[float] = []
        self._samples: List[List[ScatteringSurfaceSample]] = []
        self.wavelengths = wavelengths if wavelengths is not None else []
        self.incident_angles = incident_angles if incident_angles is not None else []
        self.samples = samples if samples is not None else []
        self.description = description

    @property
    def wavelengths(self) -> List[float]:
        """Wavelengths in nm, returned as a copy.

        Returns
        -------
        List[float]
            Sorted wavelengths. A nonempty assignment requires at least two finite values.
        """
        return self._wavelengths.copy()

    @wavelengths.setter
    def wavelengths(self, values: List[float]) -> None:
        values = [float(value) for value in values]
        if values:
            self._check_wavelengths(values)
        self._check_grid(self._samples, self._incident_angles, values)
        self._wavelengths = values

    @property
    def incident_angles(self) -> List[float]:
        """Angles of incidence in degrees, returned as a copy.

        Returns
        -------
        List[float]
            Sorted angles. A nonempty assignment must include 0 and 90 degrees.
        """
        return self._incident_angles.copy()

    @incident_angles.setter
    def incident_angles(self, values: List[float]) -> None:
        values = [float(value) for value in values]
        if values:
            self._check_angles(values)
        self._check_grid(self._samples, values, self._wavelengths)
        self._incident_angles = values

    @property
    def samples(self) -> List[List[ScatteringSurfaceSample]]:
        """Sample grid, returned with copied row containers.

        Returns
        -------
        List[List[ScatteringSurfaceSample]]
            One row per incidence and one column per wavelength. Sample objects remain
            shared and their properties can be updated through their validated setters.

        Notes
        -----
        Assign the grid back to this property to replace, add, or remove entries.
        """
        return [row.copy() for row in self._samples]

    @samples.setter
    def samples(self, values: List[List[ScatteringSurfaceSample]]) -> None:
        values = [list(row) for row in values]
        for row in values:
            for sample in row:
                if not isinstance(sample, ScatteringSurfaceSample):
                    raise TypeError("samples must contain ScatteringSurfaceSample objects.")
                sample.validate()
        self._check_grid(values, self._incident_angles, self._wavelengths)
        self._samples = values

    @property
    def description(self) -> str:
        """Free text written on the second line of the file.

        Returns
        -------
        str
            Description without line separators.
        """
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("description must be a string.")
        if len((value + "\n").splitlines()) != 1:
            raise ValueError("description must be a single line.")
        self._description = value

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(wavelengths),
        _property_name(incident_angles),
        _property_name(samples),
        _property_name(description),
    )

    @staticmethod
    def _check_wavelengths(values: List[float]) -> None:
        if len(values) < 2:
            raise ValueError("At least two wavelengths are required.")
        if any(not math.isfinite(value) for value in values):
            raise ValueError("wavelengths must be finite.")
        if sorted(values) != values:
            raise ValueError("wavelengths must be sorted in increasing order.")

    @staticmethod
    def _check_angles(values: List[float]) -> None:
        if any(not 0.0 <= angle <= 90.0 for angle in values):
            raise ValueError("incident_angles must be between 0 and 90 degrees.")
        if sorted(values) != values:
            raise ValueError("incident_angles must be sorted in increasing order.")
        if 0.0 not in values or 90.0 not in values:
            raise ValueError("incident_angles must hold both 0 and 90 degrees.")

    @staticmethod
    def _check_grid(
        samples: List[List[ScatteringSurfaceSample]],
        angles: List[float],
        wavelengths: List[float],
    ) -> None:
        if not samples:
            return
        if angles and len(samples) != len(angles):
            raise ValueError(
                f"samples must hold one row per angle of incidence, expected "
                f"{len(angles)} rows, got {len(samples)}."
            )
        for index, row in enumerate(samples):
            if wavelengths and len(row) != len(wavelengths):
                location = f"At {angles[index]} degrees" if angles else f"At row {index}"
                raise ValueError(
                    f"{location}, samples must hold one entry per wavelength, "
                    f"expected {len(wavelengths)}, got {len(row)}."
                )

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
        self._check_wavelengths(self._wavelengths)
        self._check_angles(self._incident_angles)
        if len(self._samples) != len(self._incident_angles):
            raise ValueError(
                f"samples must hold one row per angle of incidence, expected "
                f"{len(self._incident_angles)} rows, got {len(self._samples)}."
            )
        self._check_grid(self._samples, self._incident_angles, self._wavelengths)
        for row in self._samples:
            for sample in row:
                sample.validate()

    def _to_lines(self) -> List[str]:
        lines = [
            self.description,
            f"{len(self.incident_angles)} {len(self.wavelengths)}",
            _wavelength_line(self.wavelengths, values_per_wavelength=2),
        ]
        rows = list(zip(_SAMPLE_FIELDS[::2], _SAMPLE_FIELDS[1::2]))
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
        angle_count, wavelength_count = reader.next_ints(count=2, minimum=1)
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
