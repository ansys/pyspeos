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

from dataclasses import astuple, dataclass, field
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
class MaterialMetallicCurve:
    """Dispersion of a metal given by its complex refractive index.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths of the curve, in nm. By default, ``[]``.
    indices : List[float], optional
        Real part n of the refractive index at each wavelength. By default, ``[]``.
    extinctions : List[float], optional
        Extinction coefficient k at each wavelength. By default, ``[]``.
    """

    wavelengths: List[float] = field(default_factory=list)
    indices: List[float] = field(default_factory=list)
    extinctions: List[float] = field(default_factory=list)

    KEYWORD: ClassVar[str] = "Dispersion_Curve"
    """Keyword identifying the model in a ``*.material`` file."""

    def _to_lines(self) -> List[str]:
        _check_columns(
            {
                "wavelengths": self.wavelengths,
                "indices": self.indices,
                "extinctions": self.extinctions,
            }
        )
        lines = [self.KEYWORD, str(len(self.wavelengths))]
        lines.extend(
            " ".join(format_number(value) for value in row)
            for row in zip(self.wavelengths, self.indices, self.extinctions)
        )
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialMetallicCurve:
        wavelengths, indices, extinctions = [], [], []
        for _ in range(reader.next_int()):
            wavelength, index, extinction = reader.next_floats(count=3)
            wavelengths.append(wavelength)
            indices.append(index)
            extinctions.append(extinction)
        return cls(wavelengths=wavelengths, indices=indices, extinctions=extinctions)


@dataclass
class MaterialBirefringentCurve:
    """Refractive indices of a birefringent material along its three axes.

    Speos does not make the indices of a birefringent material vary with the wavelength
    when they are given explicitly, so a single index per axis is stored.

    Parameters
    ----------
    wavelength : float, optional
        Wavelength the indices are given at, in nm. By default, ``550.0``.
    index_a : float, optional
        Refractive index along the ``a`` axis. By default, ``1.5``.
    index_b : float, optional
        Refractive index along the ``b`` axis. By default, ``1.5``.
    index_c : float, optional
        Refractive index along the ``c`` axis. By default, ``1.5``.
    optical_class : int, optional
        ``0`` for a negative uniaxial material, ``1`` for a positive uniaxial one and
        ``2`` for a biaxial one. By default, ``0``.
    """

    wavelength: float = 550.0
    index_a: float = 1.5
    index_b: float = 1.5
    index_c: float = 1.5
    optical_class: int = 0

    KEYWORD: ClassVar[str] = "Dispersion_Curve"
    """Keyword identifying the model in a ``*.material`` file."""

    def _to_lines(self) -> List[str]:
        return [
            self.KEYWORD,
            "1",
            f"{format_number(self.wavelength)} {format_number(self.index_a)}",
            str(self.optical_class),
            f"{format_number(self.index_b)} {format_number(self.index_c)}",
        ]

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialBirefringentCurve:
        count = reader.next_int()
        if count != 1:
            raise reader.error(
                "the indices of a birefringent material do not vary with the wavelength, "
                f"expected a single wavelength, got {count}."
            )
        wavelength, index_a = reader.next_floats(count=2)
        optical_class = reader.next_int()
        index_b, index_c = reader.next_floats(count=2)
        return cls(
            wavelength=wavelength,
            index_a=index_a,
            index_b=index_b,
            index_c=index_c,
            optical_class=optical_class,
        )


@dataclass
class MaterialBirefringentSellmeier:
    """Dispersion of a birefringent material given by the Sellmeier coefficients.

    Parameters
    ----------
    a, b, c : MaterialSellmeier, optional
        Coefficients of the index along the ``a``, ``b`` and ``c`` axes. By default, a
        :class:`MaterialSellmeier` model with null coefficients.
    optical_class : int, optional
        ``0`` for a negative uniaxial material, ``1`` for a positive uniaxial one and
        ``2`` for a biaxial one. By default, ``0``.
    """

    a: MaterialSellmeier = field(default_factory=MaterialSellmeier)
    b: MaterialSellmeier = field(default_factory=MaterialSellmeier)
    c: MaterialSellmeier = field(default_factory=MaterialSellmeier)
    optical_class: int = 0

    KEYWORD: ClassVar[str] = MaterialSellmeier.KEYWORD
    """Keyword identifying the model in a ``*.material`` file."""

    COEFFICIENTS: ClassVar[type] = MaterialSellmeier
    """Model holding the coefficients of a single axis."""

    def _to_lines(self) -> List[str]:
        return _birefringent_coefficient_lines(self)

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialBirefringentSellmeier:
        return _read_birefringent_coefficients(cls, reader)


@dataclass
class MaterialBirefringentKettlerHelmholtz:
    """Dispersion of a birefringent material given by the Kettler-Helmholtz coefficients.

    Parameters
    ----------
    a, b, c : MaterialKettlerHelmholtz, optional
        Coefficients of the index along the ``a``, ``b`` and ``c`` axes. By default, a
        :class:`MaterialKettlerHelmholtz` model with null coefficients.
    optical_class : int, optional
        ``0`` for a negative uniaxial material, ``1`` for a positive uniaxial one and
        ``2`` for a biaxial one. By default, ``0``.
    """

    a: MaterialKettlerHelmholtz = field(default_factory=MaterialKettlerHelmholtz)
    b: MaterialKettlerHelmholtz = field(default_factory=MaterialKettlerHelmholtz)
    c: MaterialKettlerHelmholtz = field(default_factory=MaterialKettlerHelmholtz)
    optical_class: int = 0

    KEYWORD: ClassVar[str] = MaterialKettlerHelmholtz.KEYWORD
    """Keyword identifying the model in a ``*.material`` file."""

    COEFFICIENTS: ClassVar[type] = MaterialKettlerHelmholtz
    """Model holding the coefficients of a single axis."""

    def _to_lines(self) -> List[str]:
        return _birefringent_coefficient_lines(self)

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialBirefringentKettlerHelmholtz:
        return _read_birefringent_coefficients(cls, reader)


MaterialBirefringence = Union[
    MaterialBirefringentCurve,
    MaterialBirefringentSellmeier,
    MaterialBirefringentKettlerHelmholtz,
]
"""Dispersion models accepted by a birefringent :class:`MaterialFile`."""

_COEFFICIENT_COUNT = 6
"""Number of coefficients an analytic dispersion model holds for a single axis."""


def _birefringent_coefficient_lines(model) -> List[str]:
    """Write the coefficients of an axis as one number per line.

    The ``a`` axis comes first, then the optical class, then the ``b`` and the ``c`` axes
    interleaved coefficient by coefficient.
    """
    lines = [model.KEYWORD]
    lines.extend(format_number(value) for value in astuple(model.a))
    lines.append(str(model.optical_class))
    for value_b, value_c in zip(astuple(model.b), astuple(model.c)):
        lines.extend((format_number(value_b), format_number(value_c)))
    return lines


def _read_birefringent_coefficients(model_class, reader: LineReader):
    """Read the coefficients of the three axes of a birefringent material."""
    coefficients = model_class.COEFFICIENTS
    axis_a = coefficients(*(reader.next_floats(count=1)[0] for _ in range(_COEFFICIENT_COUNT)))
    optical_class = reader.next_int()
    interleaved = [reader.next_floats(count=1)[0] for _ in range(2 * _COEFFICIENT_COUNT)]
    return model_class(
        a=axis_a,
        b=coefficients(*interleaved[0::2]),
        c=coefficients(*interleaved[1::2]),
        optical_class=optical_class,
    )


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


def _is_type(material_type: str, expected: str) -> bool:
    """Tell whether a material type line names the expected flavor of the format."""
    return material_type.strip().lower() == expected.lower()


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

    :attr:`material_type` selects the flavor of the format, and with it the models
    :attr:`dispersion` accepts. A metallic material holds nothing but the complex
    refractive index of the metal, while a birefringent one holds an index per axis, the
    orientation of these axes and an absorption curve per axis.

    Parameters
    ----------
    description : str, optional
        Free text written on the second line of the file. By default, ``""``.
    material_type : str, optional
        Type of material, one of ``"Isotropic"``, ``"Metallic"`` or ``"Birefringent"``.
        By default, ``"Isotropic"``.
    dispersion : Union[MaterialDispersion, MaterialBirefringence, MaterialMetallicCurve], optional
        How the refractive index varies with the wavelength. A metallic material needs a
        :class:`MaterialMetallicCurve` and a birefringent one needs one of the
        :obj:`MaterialBirefringence` models. By default, a :class:`MaterialConstringence`
        model.
    absorption_wavelengths : List[float], optional
        Wavelengths of the absorption curve, in nm. Left empty by a metallic material,
        whose extinction coefficient already holds the absorption. By default, ``[]``.
    absorption_values : List[float], optional
        Absorption coefficient at each wavelength, in mm-1. For a birefringent material,
        the absorption along the ``a`` axis. By default, ``[]``.
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
    axis_j : List[float], optional
        Direction of the ``b`` axis of a birefringent material. Ignored by the other
        flavors. By default, ``[1.0, 0.0, 0.0]``.
    axis_k : List[float], optional
        Direction of the ``c`` axis of a birefringent material. Ignored by the other
        flavors. By default, ``[0.0, 1.0, 0.0]``.
    absorption_values_b : List[float], optional
        Absorption of a birefringent material along its ``b`` axis, one value per
        wavelength of the absorption curve. By default, ``[]``.
    absorption_values_c : List[float], optional
        Absorption of a birefringent material along its ``c`` axis, one value per
        wavelength of the absorption curve. By default, ``[]``.

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
    dispersion: Union[MaterialDispersion, MaterialBirefringence, MaterialMetallicCurve] = field(
        default_factory=MaterialConstringence
    )
    absorption_wavelengths: List[float] = field(default_factory=list, metadata=_ABSORPTION)
    absorption_values: List[float] = field(default_factory=list, metadata=_ABSORPTION)
    measured_concentration: float = 1.0
    user_concentration: float = 1.0
    scattering_wavelengths: List[float] = field(default_factory=list, metadata=_DIFFUSION)
    scattering_values: List[float] = field(default_factory=list, metadata=_DIFFUSION)
    scattering: Optional[VolumeScattering] = None
    axis_j: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0])
    axis_k: List[float] = field(default_factory=lambda: [0.0, 1.0, 0.0])
    absorption_values_b: List[float] = field(default_factory=list)
    absorption_values_c: List[float] = field(default_factory=list)

    EXTENSION = ".material"
    HEADER = "OPTIS - Material file v13"
    HEADER_PREFIX = "OPTIS - Material file"

    ISOTROPIC: ClassVar[str] = "Isotropic"
    """Material type of the default flavor of the format."""

    METALLIC: ClassVar[str] = "Metallic"
    """Material type of the metallic flavor of the format."""

    BIREFRINGENT: ClassVar[str] = "Birefringent"
    """Material type of the birefringent flavor of the format."""

    DISPERSIONS: ClassVar[tuple] = (
        MaterialConstringence,
        MaterialDispersionCurve,
        MaterialSellmeier,
        MaterialKettlerHelmholtz,
    )
    """Dispersion models the file can hold."""

    BIREFRINGENT_DISPERSIONS: ClassVar[tuple] = (
        MaterialBirefringentCurve,
        MaterialBirefringentSellmeier,
        MaterialBirefringentKettlerHelmholtz,
    )
    """Dispersion models a birefringent material can hold."""

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
            If the dispersion model does not match :attr:`material_type`, if the
            absorption curve is empty or inconsistent, if a scattering phase function is
            set without a matching diffusion curve, or if a metallic material carries data
            the format cannot store.
        """
        if self._has_type(self.METALLIC):
            self._validate_metallic()
            return
        self._validate_dispersion()
        _check_columns(_tagged(self, _ABSORPTION))
        if self._has_type(self.BIREFRINGENT):
            self._validate_birefringent()
        if self.scattering is None:
            return
        _check_columns(_tagged(self, _DIFFUSION))
        self.scattering.validate()

    def _has_type(self, material_type: str) -> bool:
        return _is_type(self.material_type, material_type)

    def _validate_dispersion(self) -> None:
        """Check that the dispersion model belongs to the flavor of the material type."""
        expected = (
            self.BIREFRINGENT_DISPERSIONS if self._has_type(self.BIREFRINGENT) else self.DISPERSIONS
        )
        if not isinstance(self.dispersion, expected):
            raise ValueError(
                f"A {self.material_type!r} material needs one of "
                f"{[model.__name__ for model in expected]}, got "
                f"{type(self.dispersion).__name__}."
            )

    def _validate_metallic(self) -> None:
        """Check a metallic material, which holds nothing but its complex index."""
        if not isinstance(self.dispersion, MaterialMetallicCurve):
            raise ValueError(
                "A metallic material needs a MaterialMetallicCurve, got "
                f"{type(self.dispersion).__name__}."
            )
        _check_columns(
            {
                "wavelengths": self.dispersion.wavelengths,
                "indices": self.dispersion.indices,
                "extinctions": self.dispersion.extinctions,
            }
        )
        if self.absorption_wavelengths or self.absorption_values:
            raise ValueError(
                "A metallic material has no absorption curve, its extinction coefficient "
                "already holds the absorption."
            )
        if self.scattering is not None or self.scattering_wavelengths or self.scattering_values:
            raise ValueError("A metallic material cannot scatter light in its volume.")

    def _validate_birefringent(self) -> None:
        """Check the axes and the per axis absorption of a birefringent material."""
        if not isinstance(self.dispersion, self.BIREFRINGENT_DISPERSIONS):
            raise ValueError(
                f"A {self.material_type!r} material needs one of "
                f"{[model.__name__ for model in self.BIREFRINGENT_DISPERSIONS]}, got "
                f"{type(self.dispersion).__name__}."
            )
        if self.dispersion.optical_class not in (0, 1, 2):
            raise ValueError(
                "optical_class must be 0 for a negative uniaxial material, 1 for a positive "
                f"uniaxial one or 2 for a biaxial one, got {self.dispersion.optical_class}."
            )
        for name in ("axis_j", "axis_k"):
            axis = getattr(self, name)
            if len(axis) != 3:
                raise ValueError(f"{name} must hold 3 coordinates, got {len(axis)}.")
        expected = len(self.absorption_wavelengths)
        for name in ("absorption_values_b", "absorption_values_c"):
            values = getattr(self, name)
            if len(values) != expected:
                raise ValueError(
                    f"{name} must hold one value per absorption wavelength, expected "
                    f"{expected}, got {len(values)}."
                )

    def _to_lines(self) -> List[str]:
        lines = [self.description, self.material_type]
        lines.extend(self.dispersion._to_lines())
        if self._has_type(self.METALLIC):
            return lines

        birefringent = self._has_type(self.BIREFRINGENT)
        if birefringent:
            lines.append(" ".join(format_number(value) for value in self.axis_j))
            lines.append(" ".join(format_number(value) for value in self.axis_k))
        lines.append(str(len(self.absorption_wavelengths)))
        lines.extend(
            f"{format_number(wavelength)} {format_number(value)}"
            for wavelength, value in zip(self.absorption_wavelengths, self.absorption_values)
        )
        if birefringent:
            lines.extend(
                f"{format_number(value_b)} {format_number(value_c)}"
                for value_b, value_c in zip(self.absorption_values_b, self.absorption_values_c)
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
        metallic = _is_type(material_type, cls.METALLIC)
        birefringent = _is_type(material_type, cls.BIREFRINGENT)

        keyword = reader.next_data_line()
        if metallic:
            if keyword.lower() != MaterialMetallicCurve.KEYWORD.lower():
                raise reader.error(
                    "a metallic material needs a "
                    f"{MaterialMetallicCurve.KEYWORD!r} index variation mode, got {keyword!r}."
                )
            return cls(
                description=description,
                material_type=material_type,
                dispersion=MaterialMetallicCurve._from_lines(reader),
            )

        candidates = cls.BIREFRINGENT_DISPERSIONS if birefringent else cls.DISPERSIONS
        models = {model.KEYWORD.lower(): model for model in candidates}
        if keyword.lower() not in models:
            raise reader.error(f"unknown index variation mode {keyword!r}.")
        dispersion = models[keyword.lower()]._from_lines(reader)

        axes = [reader.next_floats(count=3), reader.next_floats(count=3)] if birefringent else []

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
        )
        if birefringent:
            material.axis_j, material.axis_k = axes
            for _ in absorption_wavelengths:
                value_b, value_c = reader.next_floats(count=2)
                material.absorption_values_b.append(value_b)
                material.absorption_values_c.append(value_c)
        material.measured_concentration = reader.next_floats(count=1)[0]
        material.user_concentration = reader.next_floats(count=1)[0]

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
