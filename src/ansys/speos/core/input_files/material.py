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

"""Provides the Speos ``*.material`` input file format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, List, Mapping, Optional, Union

from ansys.speos.core.input_files._base import (
    LineReader,
    SpeosTextFileFormat,
    _tagged,
    _tagged_names,
    format_number,
)

_ABSORPTION = {"curve": "absorption"}
"""Field metadata of the two parallel columns of an absorption curve."""

_DIFFUSION = {"curve": "diffusion"}
"""Field metadata of the two parallel columns of a diffusion curve."""

_PHASE_COLUMN = {"column": "phase function"}
"""Field metadata of a parameter column of a scattering phase function."""

_VOLUMIC_HEADER = "OPTIS - Volumic Scattering file v1"
"""Header opening the volume scattering block of a ``*.material`` file."""


@dataclass
class MaterialConstringence:
    """Dispersion of a volume material given by its index and its Abbe number.

    Parameters
    ----------
    constringence : float, optional
        Abbe number, measured with the refractive index at the 587.5618 nm helium line.
        By default, ``57.2``.
    index : float, optional
        Refractive index at 587.6 nm. By default, ``1.49``.
    """

    constringence: float = 57.2
    index: float = 1.49

    KEYWORD: ClassVar[str] = "Constringence"
    """Keyword identifying the model in a ``*.material`` file."""

    def _to_lines(self) -> List[str]:
        return [self.KEYWORD, format_number(self.constringence), format_number(self.index)]

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialConstringence:
        return cls(
            constringence=reader.next_floats(count=1)[0], index=reader.next_floats(count=1)[0]
        )


@dataclass
class MaterialDispersionCurve:
    """Dispersion of a volume material given by an explicit index curve.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths of the curve, in nm. By default, ``[]``.
    indices : List[float], optional
        Refractive index at each wavelength. By default, ``[]``.
    """

    wavelengths: List[float] = field(default_factory=list)
    indices: List[float] = field(default_factory=list)

    KEYWORD: ClassVar[str] = "Dispersion_Curve"
    """Keyword identifying the model in a ``*.material`` file."""

    def _to_lines(self) -> List[str]:
        if len(self.wavelengths) != len(self.indices) or not self.wavelengths:
            raise ValueError("wavelengths and indices must be non empty and of equal length.")
        lines = [self.KEYWORD, str(len(self.wavelengths))]
        lines.extend(
            f"{format_number(wavelength)} {format_number(index)}"
            for wavelength, index in zip(self.wavelengths, self.indices)
        )
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialDispersionCurve:
        wavelengths, indices = [], []
        for _ in range(reader.next_int()):
            wavelength, index = reader.next_floats(count=2)
            wavelengths.append(wavelength)
            indices.append(index)
        return cls(wavelengths=wavelengths, indices=indices)


@dataclass
class MaterialSellmeier:
    """Dispersion of a volume material given by the Sellmeier coefficients.

    Parameters
    ----------
    b1, b2, b3 : float, optional
        Numerator coefficients of the Sellmeier equation. By default, ``0.0``.
    c1, c2, c3 : float, optional
        Denominator coefficients of the Sellmeier equation. By default, ``0.0``.
    """

    b1: float = 0.0
    c1: float = 0.0
    b2: float = 0.0
    c2: float = 0.0
    b3: float = 0.0
    c3: float = 0.0

    KEYWORD: ClassVar[str] = "SellMeier"
    """Keyword identifying the model in a ``*.material`` file."""

    def _to_lines(self) -> List[str]:
        coefficients = (self.b1, self.c1, self.b2, self.c2, self.b3, self.c3)
        return [self.KEYWORD, *(format_number(value) for value in coefficients)]

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialSellmeier:
        return cls(*(reader.next_floats(count=1)[0] for _ in range(6)))


@dataclass
class MaterialKettlerHelmholtz:
    """Dispersion of a glass given by the Kettler-Helmholtz coefficients.

    Parameters
    ----------
    a0, a1, a2, a3, a4, a5 : float, optional
        Coefficients of the Kettler-Helmholtz equation. By default, ``0.0``.
    """

    a0: float = 0.0
    a1: float = 0.0
    a2: float = 0.0
    a3: float = 0.0
    a4: float = 0.0
    a5: float = 0.0

    KEYWORD: ClassVar[str] = "Kettler-Helmotz"
    """Keyword identifying the model in a ``*.material`` file."""

    def _to_lines(self) -> List[str]:
        coefficients = (self.a0, self.a1, self.a2, self.a3, self.a4, self.a5)
        return [self.KEYWORD, *(format_number(value) for value in coefficients)]

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialKettlerHelmholtz:
        return cls(*(reader.next_floats(count=1)[0] for _ in range(6)))


MaterialDispersion = Union[
    MaterialConstringence,
    MaterialDispersionCurve,
    MaterialSellmeier,
    MaterialKettlerHelmholtz,
]
"""Dispersion models accepted by :class:`MaterialFile`."""


@dataclass
class VolumeScatteringUserDefined:
    """Scattering phase function given as a scattering efficiency per angle.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths the efficiency is given at, in nm. Leave it empty when the phase
        function does not depend on the wavelength, in which case each row of ``values``
        holds a single entry. By default, ``[]``.
    angles : List[float], optional
        Scattering angles theta, in degrees. By default, ``[]``.
    values : List[List[float]], optional
        Relative scattering intensity, one row per angle and one column per wavelength.
        By default, ``[]``.
    """

    wavelengths: List[float] = field(default_factory=list)
    angles: List[float] = field(default_factory=list)
    values: List[List[float]] = field(default_factory=list)

    MODEL: ClassVar[int] = 0
    """Identifier of the model in a ``*.material`` file."""

    VOLUMIC_HEADER: ClassVar[str] = _VOLUMIC_HEADER
    """Header of the scattering block holding the model."""

    def validate(self) -> None:
        """Check the phase function.

        Raises
        ------
        ValueError
            If no angle is given, or the value grid does not match the angles and the
            wavelengths.
        """
        if not self.angles:
            raise ValueError("A user defined phase function needs angles.")
        if len(self.wavelengths) == 1:
            raise ValueError(
                "The format does not store a wavelength for a phase function holding a "
                "single value per angle, leave wavelengths empty."
            )
        if len(self.values) != len(self.angles):
            raise ValueError(
                f"values must hold one row per angle, expected {len(self.angles)} rows, "
                f"got {len(self.values)}."
            )
        expected = len(self.wavelengths) or 1
        for angle, row in zip(self.angles, self.values):
            if len(row) != expected:
                raise ValueError(
                    f"At {angle} degrees, values must hold one entry per wavelength, "
                    f"expected {expected}, got {len(row)}."
                )

    def _to_lines(self) -> List[str]:
        lines = [str(len(self.wavelengths) or 1), str(len(self.angles))]
        if self.wavelengths:
            lines.append(" ".join(format_number(wavelength) for wavelength in self.wavelengths))
        lines.extend(
            " ".join(format_number(value) for value in (angle, *row))
            for angle, row in zip(self.angles, self.values)
        )
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> VolumeScatteringUserDefined:
        wavelength_count = reader.next_int()
        angle_count = reader.next_int()
        wavelengths = reader.next_floats(count=wavelength_count) if wavelength_count > 1 else []
        angles, values = [], []
        for _ in range(angle_count):
            row = reader.next_floats(count=(wavelength_count or 1) + 1)
            angles.append(row[0])
            values.append(row[1:])
        return cls(wavelengths=wavelengths, angles=angles, values=values)


@dataclass
class VolumeScatteringHenyeyGreenstein:
    """Henyey-Greenstein scattering phase function.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths the anisotropy factor is given at, in nm. A single wavelength means
        that the phase function does not depend on the wavelength. By default, ``[]``.
    anisotropies : List[float], optional
        Anisotropy factor g at each wavelength, between -1 and 1. By default, ``[]``.
    """

    wavelengths: List[float] = field(default_factory=list)
    anisotropies: List[float] = field(default_factory=list, metadata=_PHASE_COLUMN)

    MODEL: ClassVar[int] = 1
    """Identifier of the model in a ``*.material`` file."""

    VOLUMIC_HEADER: ClassVar[str] = _VOLUMIC_HEADER
    """Header of the scattering block holding the model."""

    def validate(self) -> None:
        """Check the phase function.

        Raises
        ------
        ValueError
            If no anisotropy factor is given, the lists do not match, or an anisotropy
            factor is outside the -1 to 1 range.
        """
        _check_phase_function(self)
        for anisotropy in self.anisotropies:
            if not -1.0 <= anisotropy <= 1.0:
                raise ValueError(f"anisotropies must be between -1 and 1, got {anisotropy}.")

    def _to_lines(self) -> List[str]:
        return _phase_function_lines(self)

    @classmethod
    def _from_lines(cls, reader: LineReader) -> VolumeScatteringHenyeyGreenstein:
        return _read_phase_function(cls, reader)


@dataclass
class VolumeScatteringDoubleHenyeyGreenstein:
    """Double Henyey-Greenstein scattering phase function.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths the factors are given at, in nm. A single wavelength means that the
        phase function does not depend on the wavelength. By default, ``[]``.
    anisotropies_1 : List[float], optional
        First anisotropy factor at each wavelength. By default, ``[]``.
    anisotropies_2 : List[float], optional
        Second anisotropy factor at each wavelength. By default, ``[]``.
    ratios : List[float], optional
        Weight between the first and the second anisotropy factor, at each wavelength.
        By default, ``[]``.
    """

    wavelengths: List[float] = field(default_factory=list)
    anisotropies_1: List[float] = field(default_factory=list, metadata=_PHASE_COLUMN)
    anisotropies_2: List[float] = field(default_factory=list, metadata=_PHASE_COLUMN)
    ratios: List[float] = field(default_factory=list, metadata=_PHASE_COLUMN)

    MODEL: ClassVar[int] = 5
    """Identifier of the model in a ``*.material`` file."""

    VOLUMIC_HEADER: ClassVar[str] = _VOLUMIC_HEADER
    """Header of the scattering block holding the model."""

    def validate(self) -> None:
        """Check the phase function.

        Raises
        ------
        ValueError
            If no factor is given or the lists do not match.
        """
        _check_phase_function(self)

    def _to_lines(self) -> List[str]:
        return _phase_function_lines(self)

    @classmethod
    def _from_lines(cls, reader: LineReader) -> VolumeScatteringDoubleHenyeyGreenstein:
        return _read_phase_function(cls, reader)


@dataclass
class VolumeScatteringGegenbauer:
    """Gegenbauer scattering phase function.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths the factors are given at, in nm. A single wavelength means that the
        phase function does not depend on the wavelength. By default, ``[]``.
    anisotropies : List[float], optional
        Anisotropy factor at each wavelength. By default, ``[]``.
    alphas : List[float], optional
        Alpha coefficient at each wavelength. By default, ``[]``.
    """

    wavelengths: List[float] = field(default_factory=list)
    anisotropies: List[float] = field(default_factory=list, metadata=_PHASE_COLUMN)
    alphas: List[float] = field(default_factory=list, metadata=_PHASE_COLUMN)

    MODEL: ClassVar[int] = 6
    """Identifier of the model in a ``*.material`` file."""

    VOLUMIC_HEADER: ClassVar[str] = "OPTIS - Volumic Scattering file v3"
    """Header of the scattering block, which the Gegenbauer model bumps to ``v3``."""

    def validate(self) -> None:
        """Check the phase function.

        Raises
        ------
        ValueError
            If no factor is given or the lists do not match.
        """
        _check_phase_function(self)

    def _to_lines(self) -> List[str]:
        return _phase_function_lines(self)

    @classmethod
    def _from_lines(cls, reader: LineReader) -> VolumeScatteringGegenbauer:
        return _read_phase_function(cls, reader)


VolumeScattering = Union[
    VolumeScatteringUserDefined,
    VolumeScatteringHenyeyGreenstein,
    VolumeScatteringDoubleHenyeyGreenstein,
    VolumeScatteringGegenbauer,
]
"""Scattering phase functions accepted by :class:`MaterialFile`."""


def _check_columns(columns: Mapping[str, List[float]]) -> None:
    """Check that named columns are non empty and hold the same number of values."""
    lengths = {name: len(values) for name, values in columns.items()}
    if len(set(lengths.values())) != 1:
        raise ValueError(f"All the columns must have the same length, got {lengths}.")
    if not next(iter(lengths.values())):
        raise ValueError(f"The columns {list(columns)} must not be empty.")


def _check_phase_function(model) -> None:
    """Check the columns of a phase function against its optional wavelength list.

    Speos does not store the wavelength when the phase function holds a single set of
    parameters, so ``wavelengths`` must be left empty in that case.
    """
    columns = _tagged(model, _PHASE_COLUMN)
    _check_columns(columns)
    count = len(next(iter(columns.values())))
    if not model.wavelengths:
        if count != 1:
            raise ValueError(
                "wavelengths is required as soon as the phase function holds more than one "
                f"set of parameters, got {count} sets."
            )
        return
    if count == 1:
        raise ValueError(
            "The format does not store a wavelength for a phase function holding a single "
            "set of parameters, leave wavelengths empty."
        )
    if len(model.wavelengths) != count:
        raise ValueError(
            f"wavelengths must hold one entry per set of parameters, expected {count}, "
            f"got {len(model.wavelengths)}."
        )


def _phase_function_lines(model) -> List[str]:
    """Write a phase function as a count followed by one line per wavelength."""
    columns = list(_tagged(model, _PHASE_COLUMN).values())
    lines = [str(len(columns[0]))]
    if not model.wavelengths:
        lines.append(" ".join(format_number(column[0]) for column in columns))
        return lines
    lines.extend(
        " ".join(format_number(value) for value in (wavelength, *values))
        for wavelength, *values in zip(model.wavelengths, *columns)
    )
    return lines


def _read_phase_function(model_class, reader: LineReader):
    """Read a phase function written as a count followed by one line per wavelength."""
    names = _tagged_names(model_class, _PHASE_COLUMN)
    count = reader.next_int()
    if count == 1:
        values = reader.next_floats(count=len(names))
        return model_class(**{name: [value] for name, value in zip(names, values)})

    wavelengths: List[float] = []
    columns: dict = {name: [] for name in names}
    for _ in range(count):
        wavelength, *values = reader.next_floats(count=len(names) + 1)
        wavelengths.append(wavelength)
        for name, value in zip(names, values):
            columns[name].append(value)
    return model_class(wavelengths=wavelengths, **columns)


@dataclass
class MaterialFile(SpeosTextFileFormat):
    """Speos ``*.material`` file, holding the volume optical properties of a body.

    The file always describes how the refractive index and the absorption vary with the
    wavelength. Setting :attr:`scattering` adds a volume scattering block, which turns the
    file into the scattering flavor of the format.

    Parameters
    ----------
    description : str, optional
        Free text written on the second line of the file. By default, ``""``.
    material_type : str, optional
        Type of material, for example ``"Isotropic"``, ``"Birefringent"``,
        ``"Fluorescent"`` or ``"Metallic"``. By default, ``"Isotropic"``.
    dispersion : MaterialDispersion, optional
        How the refractive index varies with the wavelength. By default, a
        :class:`MaterialConstringence` model.
    absorption_wavelengths : List[float], optional
        Wavelengths of the absorption curve, in nm. By default, ``[]``.
    absorption_values : List[float], optional
        Absorption coefficient at each wavelength, in mm-1. By default, ``[]``.
    measured_concentration : float, optional
        Concentration the absorption curve was measured at. By default, ``1.0``.
    user_concentration : float, optional
        Concentration the absorption curve is scaled to. By default, ``1.0``.
    scattering_wavelengths : List[float], optional
        Wavelengths of the diffusion curve, in nm. By default, ``[]``.
    scattering_values : List[float], optional
        Diffusion coefficient at each wavelength, in mm-1. By default, ``[]``.
    scattering : Optional[VolumeScattering], optional
        Scattering phase function. By default, ``None``, which writes a non-scattering
        material.

    Examples
    --------
    >>> from ansys.speos.core.input_files.material import MaterialFile, MaterialConstringence
    >>> MaterialFile(
    ...     description="PMMA",
    ...     dispersion=MaterialConstringence(constringence=57.2, index=1.49),
    ...     absorption_wavelengths=[486.0, 643.0],
    ...     absorption_values=[0.0001, 0.0005],
    ... ).save("pmma.material")
    """

    description: str = ""
    material_type: str = "Isotropic"
    dispersion: MaterialDispersion = field(default_factory=MaterialConstringence)
    absorption_wavelengths: List[float] = field(default_factory=list, metadata=_ABSORPTION)
    absorption_values: List[float] = field(default_factory=list, metadata=_ABSORPTION)
    measured_concentration: float = 1.0
    user_concentration: float = 1.0
    scattering_wavelengths: List[float] = field(default_factory=list, metadata=_DIFFUSION)
    scattering_values: List[float] = field(default_factory=list, metadata=_DIFFUSION)
    scattering: Optional[VolumeScattering] = None

    EXTENSION = ".material"
    HEADER = "OPTIS - Material file v13"
    HEADER_PREFIX = "OPTIS - Material file"

    DISPERSIONS: ClassVar[tuple] = (
        MaterialConstringence,
        MaterialDispersionCurve,
        MaterialSellmeier,
        MaterialKettlerHelmholtz,
    )
    """Dispersion models the file can hold."""

    SCATTERINGS: ClassVar[tuple] = (
        VolumeScatteringUserDefined,
        VolumeScatteringHenyeyGreenstein,
        VolumeScatteringDoubleHenyeyGreenstein,
        VolumeScatteringGegenbauer,
    )
    """Scattering phase functions the file can hold."""

    def validate(self) -> None:
        """Check the material against the constraints of the ``*.material`` format.

        Raises
        ------
        ValueError
            If the absorption curve is empty or inconsistent, or if a scattering phase
            function is set without a matching diffusion curve.
        """
        _check_columns(_tagged(self, _ABSORPTION))
        if self.scattering is None:
            return
        _check_columns(_tagged(self, _DIFFUSION))
        self.scattering.validate()

    def _to_lines(self) -> List[str]:
        lines = [self.description, self.material_type]
        lines.extend(self.dispersion._to_lines())
        lines.append(str(len(self.absorption_wavelengths)))
        lines.extend(
            f"{format_number(wavelength)} {format_number(value)}"
            for wavelength, value in zip(self.absorption_wavelengths, self.absorption_values)
        )
        lines.append(format_number(self.measured_concentration))
        lines.append(format_number(self.user_concentration))
        lines.append("1" if self.scattering is not None else "0")

        if self.scattering is None:
            return lines

        lines.append(self.scattering.VOLUMIC_HEADER)
        lines.append(str(self.scattering.MODEL))
        lines.append(str(len(self.scattering_wavelengths)))
        lines.extend(
            f"{format_number(wavelength)} {format_number(value)}"
            for wavelength, value in zip(self.scattering_wavelengths, self.scattering_values)
        )
        lines.extend(self.scattering._to_lines())
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialFile:
        description = reader.next_line()
        material_type = reader.next_data_line()

        keyword = reader.next_data_line()
        models = {model.KEYWORD.lower(): model for model in cls.DISPERSIONS}
        if keyword.lower() not in models:
            raise reader.error(f"unknown index variation mode {keyword!r}.")
        dispersion = models[keyword.lower()]._from_lines(reader)

        absorption_wavelengths, absorption_values = [], []
        for _ in range(reader.next_int()):
            wavelength, value = reader.next_floats(count=2)
            absorption_wavelengths.append(wavelength)
            absorption_values.append(value)

        material = cls(
            description=description,
            material_type=material_type,
            dispersion=dispersion,
            absorption_wavelengths=absorption_wavelengths,
            absorption_values=absorption_values,
            measured_concentration=reader.next_floats(count=1)[0],
            user_concentration=reader.next_floats(count=1)[0],
        )
        if not reader.next_int():
            return material

        reader.next_data_line()  # Header opening the volume scattering block.
        model_id = reader.next_int()
        for _ in range(reader.next_int()):
            wavelength, value = reader.next_floats(count=2)
            material.scattering_wavelengths.append(wavelength)
            material.scattering_values.append(value)

        models = {model.MODEL: model for model in cls.SCATTERINGS}
        if model_id not in models:
            raise reader.error(f"unsupported scattering phase function {model_id}.")
        material.scattering = models[model_id]._from_lines(reader)
        return material
