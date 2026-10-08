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

from typing import ClassVar, List, Optional, Union

from ansys.speos.core.input_files._base import (
    LineReader,
    SpeosTextFileFormat,
    _finite_number,
    _finite_values,
    _matching_columns,
    _matching_grid,
    _numeric_tuple,
    _property_name,
    _single_line,
    _ValueComparable,
    format_number,
)

_VOLUMIC_HEADER = "OPTIS - Volumic Scattering file v1"
"""Header opening the volume scattering block of a ``*.material`` file."""


def _curve_column(model, name: str, values: List[float], names: tuple[str, ...]) -> List[float]:
    """Validate a candidate column against the populated columns of a curve."""
    values = _finite_values(name, values)
    columns = {entry: values if entry == name else getattr(model, "_" + entry) for entry in names}
    _matching_columns(columns)
    return values


def _optical_class(value: int) -> int:
    """Validate the optical class without truncating a numeric value."""
    if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 1, 2):
        raise ValueError(
            "optical_class must be 0 for a negative uniaxial material, 1 for a positive "
            f"uniaxial one or 2 for a biaxial one, got {value}."
        )
    return value


def _axis_model(value, expected):
    """Check the model assigned to a birefringent axis."""
    if not isinstance(value, expected):
        raise TypeError(f"An axis needs {expected.__name__}, got {type(value).__name__}.")
    value.validate()
    return value


class MaterialConstringence(_ValueComparable):
    """Dispersion of a volume material given by its index and its Abbe number.

    Parameters
    ----------
    constringence : float, optional
        Abbe number, measured with the refractive index at the 587.5618 nm helium line.
        By default, ``57.2``.
    index : float, optional
        Refractive index at 587.6 nm. By default, ``1.49``.
    """

    def __init__(self, constringence: float = 57.2, index: float = 1.49) -> None:
        self.constringence = constringence
        self.index = index

    @property
    def constringence(self) -> float:
        """Abbe number.

        Returns
        -------
        float
            Finite constringence value.
        """
        return self._constringence

    @constringence.setter
    def constringence(self, value: float) -> None:
        self._constringence = _finite_number(
            _property_name(MaterialConstringence.constringence), value
        )

    @property
    def index(self) -> float:
        """Refractive index at 587.6 nm.

        Returns
        -------
        float
            Finite refractive index.
        """
        return self._index

    @index.setter
    def index(self, value: float) -> None:
        self._index = _finite_number(_property_name(MaterialConstringence.index), value)

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(constringence),
        _property_name(index),
    )

    def validate(self) -> None:
        """Check the finite dispersion parameters.

        Raises
        ------
        ValueError
            If a parameter is nonfinite.
        """
        _finite_number(_property_name(MaterialConstringence.constringence), self._constringence)
        _finite_number(_property_name(MaterialConstringence.index), self._index)

    KEYWORD: ClassVar[str] = "Constringence"
    """Keyword identifying the model in a ``*.material`` file."""

    def _to_lines(self) -> List[str]:
        return [self.KEYWORD, format_number(self.constringence), format_number(self.index)]

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialConstringence:
        return cls(
            constringence=reader.next_floats(count=1)[0], index=reader.next_floats(count=1)[0]
        )


class MaterialDispersionCurve(_ValueComparable):
    """Dispersion of a volume material given by an explicit index curve.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths of the curve, in nm. By default, ``[]``.
    indices : List[float], optional
        Refractive index at each wavelength. By default, ``[]``.
    """

    def __init__(
        self, wavelengths: List[float] | None = None, indices: List[float] | None = None
    ) -> None:
        self._wavelengths: List[float] = []
        self._indices: List[float] = []
        self.wavelengths = wavelengths if wavelengths is not None else []
        self.indices = indices if indices is not None else []

    @property
    def wavelengths(self) -> List[float]:
        """Curve wavelengths in nm, returned as a copy.

        Returns
        -------
        List[float]
            Finite wavelengths.
        """
        return self._wavelengths.copy()

    @wavelengths.setter
    def wavelengths(self, values: List[float]) -> None:
        self._wavelengths = _curve_column(
            self, _property_name(MaterialDispersionCurve.wavelengths), values, _CURVE_FIELDS
        )

    @property
    def indices(self) -> List[float]:
        """Refractive index column, returned as a copy.

        Returns
        -------
        List[float]
            Finite refractive indices.
        """
        return self._indices.copy()

    @indices.setter
    def indices(self, values: List[float]) -> None:
        self._indices = _curve_column(
            self, _property_name(MaterialDispersionCurve.indices), values, _CURVE_FIELDS
        )

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(wavelengths),
        _property_name(indices),
    )

    def validate(self) -> None:
        """Check that the curve is complete and its columns match.

        Raises
        ------
        ValueError
            If columns are empty or of unequal length.
        """
        if len(self._wavelengths) != len(self._indices) or not self._wavelengths:
            raise ValueError("wavelengths and indices must be non empty and of equal length.")

    KEYWORD: ClassVar[str] = "Dispersion_Curve"
    """Keyword identifying the model in a ``*.material`` file."""

    def _to_lines(self) -> List[str]:
        self.validate()
        lines = [self.KEYWORD, str(len(self.wavelengths))]
        lines.extend(
            f"{format_number(wavelength)} {format_number(index)}"
            for wavelength, index in zip(self.wavelengths, self.indices)
        )
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialDispersionCurve:
        wavelengths, indices = [], []
        for _ in range(reader.next_int(minimum=1)):
            wavelength, index = reader.next_floats(count=2)
            wavelengths.append(wavelength)
            indices.append(index)
        return cls(wavelengths=wavelengths, indices=indices)


class MaterialSellmeier(_ValueComparable):
    """Dispersion of a volume material given by the Sellmeier coefficients.

    Parameters
    ----------
    b1, b2, b3 : float, optional
        Numerator coefficients of the Sellmeier equation. By default, ``0.0``.
    c1, c2, c3 : float, optional
        Denominator coefficients of the Sellmeier equation. By default, ``0.0``.
    """

    def __init__(
        self,
        b1: float = 0.0,
        c1: float = 0.0,
        b2: float = 0.0,
        c2: float = 0.0,
        b3: float = 0.0,
        c3: float = 0.0,
    ) -> None:
        self.b1 = b1
        self.c1 = c1
        self.b2 = b2
        self.c2 = c2
        self.b3 = b3
        self.c3 = c3

    @property
    def b1(self) -> float:
        """First numerator coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._b1

    @b1.setter
    def b1(self, value: float) -> None:
        self._b1 = _finite_number(_property_name(MaterialSellmeier.b1), value)

    @property
    def c1(self) -> float:
        """First denominator coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._c1

    @c1.setter
    def c1(self, value: float) -> None:
        self._c1 = _finite_number(_property_name(MaterialSellmeier.c1), value)

    @property
    def b2(self) -> float:
        """Second numerator coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._b2

    @b2.setter
    def b2(self, value: float) -> None:
        self._b2 = _finite_number(_property_name(MaterialSellmeier.b2), value)

    @property
    def c2(self) -> float:
        """Second denominator coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._c2

    @c2.setter
    def c2(self, value: float) -> None:
        self._c2 = _finite_number(_property_name(MaterialSellmeier.c2), value)

    @property
    def b3(self) -> float:
        """Third numerator coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._b3

    @b3.setter
    def b3(self, value: float) -> None:
        self._b3 = _finite_number(_property_name(MaterialSellmeier.b3), value)

    @property
    def c3(self) -> float:
        """Third denominator coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._c3

    @c3.setter
    def c3(self, value: float) -> None:
        self._c3 = _finite_number(_property_name(MaterialSellmeier.c3), value)

    _FIELD_NAMES: ClassVar[tuple[str, ...]] = (
        _property_name(b1),
        _property_name(c1),
        _property_name(b2),
        _property_name(c2),
        _property_name(b3),
        _property_name(c3),
    )
    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = _FIELD_NAMES

    def validate(self) -> None:
        """Check all coefficients are finite.

        Raises
        ------
        ValueError
            If a coefficient is nonfinite.
        """
        for name in self._FIELD_NAMES:
            _finite_number(name, getattr(self, name))

    KEYWORD: ClassVar[str] = "SellMeier"
    """Keyword identifying the model in a ``*.material`` file."""

    def _to_lines(self) -> List[str]:
        coefficients = (self.b1, self.c1, self.b2, self.c2, self.b3, self.c3)
        return [self.KEYWORD, *(format_number(value) for value in coefficients)]

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialSellmeier:
        return cls(*(reader.next_floats(count=1)[0] for _ in range(6)))


class MaterialKettlerHelmholtz(_ValueComparable):
    """Dispersion of a glass given by the Kettler-Helmholtz coefficients.

    Parameters
    ----------
    a0, a1, a2, a3, a4, a5 : float, optional
        Coefficients of the Kettler-Helmholtz equation. By default, ``0.0``.
    """

    def __init__(
        self,
        a0: float = 0.0,
        a1: float = 0.0,
        a2: float = 0.0,
        a3: float = 0.0,
        a4: float = 0.0,
        a5: float = 0.0,
    ) -> None:
        self.a0 = a0
        self.a1 = a1
        self.a2 = a2
        self.a3 = a3
        self.a4 = a4
        self.a5 = a5

    @property
    def a0(self) -> float:
        """Constant coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._a0

    @a0.setter
    def a0(self, value: float) -> None:
        self._a0 = _finite_number(_property_name(MaterialKettlerHelmholtz.a0), value)

    @property
    def a1(self) -> float:
        """First coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._a1

    @a1.setter
    def a1(self, value: float) -> None:
        self._a1 = _finite_number(_property_name(MaterialKettlerHelmholtz.a1), value)

    @property
    def a2(self) -> float:
        """Second coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._a2

    @a2.setter
    def a2(self, value: float) -> None:
        self._a2 = _finite_number(_property_name(MaterialKettlerHelmholtz.a2), value)

    @property
    def a3(self) -> float:
        """Third coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._a3

    @a3.setter
    def a3(self, value: float) -> None:
        self._a3 = _finite_number(_property_name(MaterialKettlerHelmholtz.a3), value)

    @property
    def a4(self) -> float:
        """Fourth coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._a4

    @a4.setter
    def a4(self, value: float) -> None:
        self._a4 = _finite_number(_property_name(MaterialKettlerHelmholtz.a4), value)

    @property
    def a5(self) -> float:
        """Fifth coefficient.

        Returns
        -------
        float
            Finite coefficient.
        """
        return self._a5

    @a5.setter
    def a5(self, value: float) -> None:
        self._a5 = _finite_number(_property_name(MaterialKettlerHelmholtz.a5), value)

    _FIELD_NAMES: ClassVar[tuple[str, ...]] = (
        _property_name(a0),
        _property_name(a1),
        _property_name(a2),
        _property_name(a3),
        _property_name(a4),
        _property_name(a5),
    )
    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = _FIELD_NAMES

    def validate(self) -> None:
        """Check all coefficients are finite.

        Raises
        ------
        ValueError
            If a coefficient is nonfinite.
        """
        for name in self._FIELD_NAMES:
            _finite_number(name, getattr(self, name))

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


class MaterialMetallicCurve(_ValueComparable):
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

    def __init__(
        self,
        wavelengths: List[float] | None = None,
        indices: List[float] | None = None,
        extinctions: List[float] | None = None,
    ) -> None:
        self._wavelengths: List[float] = []
        self._indices: List[float] = []
        self._extinctions: List[float] = []
        self.wavelengths = wavelengths if wavelengths is not None else []
        self.indices = indices if indices is not None else []
        self.extinctions = extinctions if extinctions is not None else []

    @property
    def wavelengths(self) -> List[float]:
        """Curve wavelengths in nm, returned as a copy.

        Returns
        -------
        List[float]
            Finite wavelengths.
        """
        return self._wavelengths.copy()

    @wavelengths.setter
    def wavelengths(self, values: List[float]) -> None:
        self._wavelengths = _curve_column(
            self, _property_name(MaterialMetallicCurve.wavelengths), values, _METALLIC_FIELDS
        )

    @property
    def indices(self) -> List[float]:
        """Real refractive indices, returned as a copy.

        Returns
        -------
        List[float]
            Finite indices.
        """
        return self._indices.copy()

    @indices.setter
    def indices(self, values: List[float]) -> None:
        self._indices = _curve_column(
            self, _property_name(MaterialMetallicCurve.indices), values, _METALLIC_FIELDS
        )

    @property
    def extinctions(self) -> List[float]:
        """Extinction coefficients, returned as a copy.

        Returns
        -------
        List[float]
            Finite extinction coefficients.
        """
        return self._extinctions.copy()

    @extinctions.setter
    def extinctions(self, values: List[float]) -> None:
        self._extinctions = _curve_column(
            self, _property_name(MaterialMetallicCurve.extinctions), values, _METALLIC_FIELDS
        )

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(wavelengths),
        _property_name(indices),
        _property_name(extinctions),
    )

    def validate(self) -> None:
        """Check the complex index curve is complete.

        Raises
        ------
        ValueError
            If columns are empty or their lengths differ.
        """
        _matching_columns({name: getattr(self, "_" + name) for name in _METALLIC_FIELDS}, True)

    KEYWORD: ClassVar[str] = "Dispersion_Curve"
    """Keyword identifying the model in a ``*.material`` file."""

    def _to_lines(self) -> List[str]:
        _matching_columns(
            {name: getattr(self, name) for name in self._EQUALITY_FIELDS},
            complete=True,
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
        for _ in range(reader.next_int(minimum=1)):
            wavelength, index, extinction = reader.next_floats(count=3)
            wavelengths.append(wavelength)
            indices.append(index)
            extinctions.append(extinction)
        return cls(wavelengths=wavelengths, indices=indices, extinctions=extinctions)


class MaterialBirefringentCurve(_ValueComparable):
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

    def __init__(
        self,
        wavelength: float = 550.0,
        index_a: float = 1.5,
        index_b: float = 1.5,
        index_c: float = 1.5,
        optical_class: int = 0,
    ) -> None:
        self.wavelength = wavelength
        self.index_a = index_a
        self.index_b = index_b
        self.index_c = index_c
        self.optical_class = optical_class

    @property
    def wavelength(self) -> float:
        """Wavelength of the indices, in nm.

        Returns
        -------
        float
            Finite wavelength.
        """
        return self._wavelength

    @wavelength.setter
    def wavelength(self, value: float) -> None:
        self._wavelength = _finite_number(
            _property_name(MaterialBirefringentCurve.wavelength), value
        )

    @property
    def index_a(self) -> float:
        """Refractive index along the a axis.

        Returns
        -------
        float
            Finite index.
        """
        return self._index_a

    @index_a.setter
    def index_a(self, value: float) -> None:
        self._index_a = _finite_number(_property_name(MaterialBirefringentCurve.index_a), value)

    @property
    def index_b(self) -> float:
        """Refractive index along the b axis.

        Returns
        -------
        float
            Finite index.
        """
        return self._index_b

    @index_b.setter
    def index_b(self, value: float) -> None:
        self._index_b = _finite_number(_property_name(MaterialBirefringentCurve.index_b), value)

    @property
    def index_c(self) -> float:
        """Refractive index along the c axis.

        Returns
        -------
        float
            Finite index.
        """
        return self._index_c

    @index_c.setter
    def index_c(self, value: float) -> None:
        self._index_c = _finite_number(_property_name(MaterialBirefringentCurve.index_c), value)

    @property
    def optical_class(self) -> int:
        """Optical class of the material.

        Returns
        -------
        int
            0 for negative uniaxial, 1 for positive uniaxial, or 2 for biaxial.
        """
        return self._optical_class

    @optical_class.setter
    def optical_class(self, value: int) -> None:
        self._optical_class = _optical_class(value)

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(wavelength),
        _property_name(index_a),
        _property_name(index_b),
        _property_name(index_c),
        _property_name(optical_class),
    )

    def validate(self) -> None:
        """Check finite indices and the optical class.

        Raises
        ------
        ValueError
            If a numeric value or optical class is invalid.
        """
        for name in _BIREFRINGENT_FIELDS[:-1]:
            _finite_number(name, getattr(self, name))
        _optical_class(self._optical_class)

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


class MaterialBirefringentSellmeier(_ValueComparable):
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

    def __init__(
        self,
        a: MaterialSellmeier | None = None,
        b: MaterialSellmeier | None = None,
        c: MaterialSellmeier | None = None,
        optical_class: int = 0,
    ) -> None:
        self.a = a if a is not None else MaterialSellmeier()
        self.b = b if b is not None else MaterialSellmeier()
        self.c = c if c is not None else MaterialSellmeier()
        self.optical_class = optical_class

    @property
    def a(self) -> MaterialSellmeier:
        """Coefficients along the a axis.

        Returns
        -------
        MaterialSellmeier
            Shared validated coefficient model.
        """
        return self._a

    @a.setter
    def a(self, value: MaterialSellmeier) -> None:
        self._a = _axis_model(value, MaterialSellmeier)

    @property
    def b(self) -> MaterialSellmeier:
        """Coefficients along the b axis.

        Returns
        -------
        MaterialSellmeier
            Shared validated coefficient model.
        """
        return self._b

    @b.setter
    def b(self, value: MaterialSellmeier) -> None:
        self._b = _axis_model(value, MaterialSellmeier)

    @property
    def c(self) -> MaterialSellmeier:
        """Coefficients along the c axis.

        Returns
        -------
        MaterialSellmeier
            Shared validated coefficient model.
        """
        return self._c

    @c.setter
    def c(self, value: MaterialSellmeier) -> None:
        self._c = _axis_model(value, MaterialSellmeier)

    @property
    def optical_class(self) -> int:
        """Optical class of the material.

        Returns
        -------
        int
            0, 1, or 2.
        """
        return self._optical_class

    @optical_class.setter
    def optical_class(self, value: int) -> None:
        self._optical_class = _optical_class(value)

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(a),
        _property_name(b),
        _property_name(c),
        _property_name(optical_class),
    )

    def validate(self) -> None:
        """Check the three coefficient models and optical class.

        Raises
        ------
        ValueError
            If coefficients or optical class are invalid.
        """
        for model in (self._a, self._b, self._c):
            model.validate()
        _optical_class(self._optical_class)

    KEYWORD: ClassVar[str] = MaterialSellmeier.KEYWORD
    """Keyword identifying the model in a ``*.material`` file."""

    COEFFICIENTS: ClassVar[type] = MaterialSellmeier
    """Model holding the coefficients of a single axis."""

    def _to_lines(self) -> List[str]:
        return _birefringent_coefficient_lines(self)

    @classmethod
    def _from_lines(cls, reader: LineReader) -> MaterialBirefringentSellmeier:
        return _read_birefringent_coefficients(cls, reader)


class MaterialBirefringentKettlerHelmholtz(_ValueComparable):
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

    def __init__(
        self,
        a: MaterialKettlerHelmholtz | None = None,
        b: MaterialKettlerHelmholtz | None = None,
        c: MaterialKettlerHelmholtz | None = None,
        optical_class: int = 0,
    ) -> None:
        self.a = a if a is not None else MaterialKettlerHelmholtz()
        self.b = b if b is not None else MaterialKettlerHelmholtz()
        self.c = c if c is not None else MaterialKettlerHelmholtz()
        self.optical_class = optical_class

    @property
    def a(self) -> MaterialKettlerHelmholtz:
        """Coefficients along the a axis.

        Returns
        -------
        MaterialKettlerHelmholtz
            Shared validated coefficient model.
        """
        return self._a

    @a.setter
    def a(self, value: MaterialKettlerHelmholtz) -> None:
        self._a = _axis_model(value, MaterialKettlerHelmholtz)

    @property
    def b(self) -> MaterialKettlerHelmholtz:
        """Coefficients along the b axis.

        Returns
        -------
        MaterialKettlerHelmholtz
            Shared validated coefficient model.
        """
        return self._b

    @b.setter
    def b(self, value: MaterialKettlerHelmholtz) -> None:
        self._b = _axis_model(value, MaterialKettlerHelmholtz)

    @property
    def c(self) -> MaterialKettlerHelmholtz:
        """Coefficients along the c axis.

        Returns
        -------
        MaterialKettlerHelmholtz
            Shared validated coefficient model.
        """
        return self._c

    @c.setter
    def c(self, value: MaterialKettlerHelmholtz) -> None:
        self._c = _axis_model(value, MaterialKettlerHelmholtz)

    @property
    def optical_class(self) -> int:
        """Optical class of the material.

        Returns
        -------
        int
            0, 1, or 2.
        """
        return self._optical_class

    @optical_class.setter
    def optical_class(self, value: int) -> None:
        self._optical_class = _optical_class(value)

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(a),
        _property_name(b),
        _property_name(c),
        _property_name(optical_class),
    )

    def validate(self) -> None:
        """Check the three coefficient models and optical class.

        Raises
        ------
        ValueError
            If coefficients or optical class are invalid.
        """
        for model in (self._a, self._b, self._c):
            model.validate()
        _optical_class(self._optical_class)

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
    names = model.COEFFICIENTS._FIELD_NAMES
    lines.extend(format_number(getattr(model.a, name)) for name in names)
    lines.append(str(model.optical_class))
    for name in names:
        lines.extend((format_number(getattr(model.b, name)), format_number(getattr(model.c, name))))
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


class VolumeScatteringUserDefined(_ValueComparable):
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

    def __init__(
        self,
        wavelengths: List[float] | None = None,
        angles: List[float] | None = None,
        values: List[List[float]] | None = None,
    ) -> None:
        self._wavelengths: List[float] = []
        self._angles: List[float] = []
        self._values: List[List[float]] = []
        self.wavelengths = wavelengths if wavelengths is not None else []
        self.angles = angles if angles is not None else []
        self.values = values if values is not None else []

    @property
    def wavelengths(self) -> List[float]:
        """Spectral wavelengths in nm, returned as a copy.

        Returns
        -------
        List[float]
            Empty for a nonspectral function, otherwise at least two wavelengths.
        """
        return self._wavelengths.copy()

    @wavelengths.setter
    def wavelengths(self, values: List[float]) -> None:
        values = _finite_values(_property_name(VolumeScatteringUserDefined.wavelengths), values)
        if len(values) == 1:
            raise ValueError(
                "The format does not store a wavelength for a phase function holding a "
                "single value per angle, leave wavelengths empty."
            )
        self._check_grid(self._angles, self._values, values)
        self._wavelengths = values

    @property
    def angles(self) -> List[float]:
        """Scattering angles in degrees, returned as a copy.

        Returns
        -------
        List[float]
            Finite scattering angles.
        """
        return self._angles.copy()

    @angles.setter
    def angles(self, values: List[float]) -> None:
        values = _finite_values(_property_name(VolumeScatteringUserDefined.angles), values)
        self._check_grid(values, self._values, self._wavelengths)
        self._angles = values

    @property
    def values(self) -> List[List[float]]:
        """Relative intensities, returned with copied row containers.

        Returns
        -------
        List[List[float]]
            One row per angle, one column per wavelength or one nonspectral value.
        """
        return [row.copy() for row in self._values]

    @values.setter
    def values(self, values: List[List[float]]) -> None:
        values = [
            _finite_values(_property_name(VolumeScatteringUserDefined.values), row)
            for row in values
        ]
        self._check_grid(self._angles, values, self._wavelengths)
        self._values = values

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(wavelengths),
        _property_name(angles),
        _property_name(values),
    )

    @staticmethod
    def _check_grid(angles, values, wavelengths) -> None:
        _matching_grid(
            "values",
            values,
            row_count=len(angles) if angles and values else None,
            column_count=len(wavelengths) or 1,
        )

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
        _matching_grid(
            "values",
            self._values,
            row_count=len(self._angles),
            column_count=len(self._wavelengths) or 1,
            incidences=self._angles,
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
        wavelength_count = reader.next_int(minimum=0)
        angle_count = reader.next_int(minimum=1)
        wavelengths = reader.next_floats(count=wavelength_count) if wavelength_count > 1 else []
        angles, values = [], []
        for _ in range(angle_count):
            row = reader.next_floats(count=(wavelength_count or 1) + 1)
            angles.append(row[0])
            values.append(row[1:])
        return cls(wavelengths=wavelengths, angles=angles, values=values)


class VolumeScatteringHenyeyGreenstein(_ValueComparable):
    """Henyey-Greenstein scattering phase function.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths the anisotropy factor is given at, in nm. A single wavelength means
        that the phase function does not depend on the wavelength. By default, ``[]``.
    anisotropies : List[float], optional
        Anisotropy factor g at each wavelength, between -1 and 1. By default, ``[]``.
    """

    def __init__(
        self, wavelengths: List[float] | None = None, anisotropies: List[float] | None = None
    ) -> None:
        self._wavelengths: List[float] = []
        self._anisotropies: List[float] = []
        self.wavelengths = wavelengths if wavelengths is not None else []
        self.anisotropies = anisotropies if anisotropies is not None else []

    @property
    def wavelengths(self) -> List[float]:
        """Spectral wavelengths in nm, returned as a copy.

        Returns
        -------
        List[float]
            Empty for a nonspectral parameter set.
        """
        return self._wavelengths.copy()

    @wavelengths.setter
    def wavelengths(self, values: List[float]) -> None:
        self._wavelengths = _phase_candidate(
            self, _property_name(VolumeScatteringHenyeyGreenstein.wavelengths), values
        )

    @property
    def anisotropies(self) -> List[float]:
        """Anisotropy factors, returned as a copy.

        Returns
        -------
        List[float]
            Factors between -1 and 1.
        """
        return self._anisotropies.copy()

    @anisotropies.setter
    def anisotropies(self, values: List[float]) -> None:
        values = _finite_values(
            _property_name(VolumeScatteringHenyeyGreenstein.anisotropies), values
        )
        if any(not -1.0 <= value <= 1.0 for value in values):
            raise ValueError("anisotropies must be between -1 and 1.")
        self._anisotropies = _phase_candidate(
            self, _property_name(VolumeScatteringHenyeyGreenstein.anisotropies), values
        )

    _COLUMN_NAMES: ClassVar[tuple[str, ...]] = (_property_name(anisotropies),)
    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (_property_name(wavelengths), *_COLUMN_NAMES)

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


class VolumeScatteringDoubleHenyeyGreenstein(_ValueComparable):
    """Double Henyey-Greenstein scattering phase function.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths the factors are given at, in nm. A single wavelength means that the
        phase function does not depend on the wavelength. By default, ``[]``.
    anisotropies_1 : List[float], optional
        First anisotropy factor at each wavelength, between -1 and 1. By default, ``[]``.
    anisotropies_2 : List[float], optional
        Second anisotropy factor at each wavelength, between -1 and 1. By default, ``[]``.
    ratios : List[float], optional
        Weight between the first and the second anisotropy factor, at each wavelength.
        Values must be between 0 and 1. By default, ``[]``.
    """

    def __init__(
        self,
        wavelengths: List[float] | None = None,
        anisotropies_1: List[float] | None = None,
        anisotropies_2: List[float] | None = None,
        ratios: List[float] | None = None,
    ) -> None:
        self._wavelengths: List[float] = []
        self._anisotropies_1: List[float] = []
        self._anisotropies_2: List[float] = []
        self._ratios: List[float] = []
        self.wavelengths = wavelengths if wavelengths is not None else []
        self.anisotropies_1 = anisotropies_1 if anisotropies_1 is not None else []
        self.anisotropies_2 = anisotropies_2 if anisotropies_2 is not None else []
        self.ratios = ratios if ratios is not None else []

    @property
    def wavelengths(self) -> List[float]:
        """Spectral wavelengths in nm, returned as a copy.

        Returns
        -------
        List[float]
            Empty for a nonspectral parameter set.
        """
        return self._wavelengths.copy()

    @wavelengths.setter
    def wavelengths(self, values: List[float]) -> None:
        self._wavelengths = _phase_candidate(
            self, _property_name(VolumeScatteringDoubleHenyeyGreenstein.wavelengths), values
        )

    @property
    def anisotropies_1(self) -> List[float]:
        """First anisotropy column, returned as a copy.

        Returns
        -------
        List[float]
            Factors between -1 and 1.
        """
        return self._anisotropies_1.copy()

    @anisotropies_1.setter
    def anisotropies_1(self, values: List[float]) -> None:
        name = _property_name(VolumeScatteringDoubleHenyeyGreenstein.anisotropies_1)
        values = _phase_candidate(self, name, values)
        _check_phase_bounds(name, values, -1.0, 1.0)
        self._anisotropies_1 = values

    @property
    def anisotropies_2(self) -> List[float]:
        """Second anisotropy column, returned as a copy.

        Returns
        -------
        List[float]
            Factors between -1 and 1.
        """
        return self._anisotropies_2.copy()

    @anisotropies_2.setter
    def anisotropies_2(self, values: List[float]) -> None:
        name = _property_name(VolumeScatteringDoubleHenyeyGreenstein.anisotropies_2)
        values = _phase_candidate(self, name, values)
        _check_phase_bounds(name, values, -1.0, 1.0)
        self._anisotropies_2 = values

    @property
    def ratios(self) -> List[float]:
        """Mixture weights, returned as a copy.

        Returns
        -------
        List[float]
            Mixture weights between 0 and 1.
        """
        return self._ratios.copy()

    @ratios.setter
    def ratios(self, values: List[float]) -> None:
        name = _property_name(VolumeScatteringDoubleHenyeyGreenstein.ratios)
        values = _phase_candidate(self, name, values)
        _check_phase_bounds(name, values, 0.0, 1.0)
        self._ratios = values

    _COLUMN_NAMES: ClassVar[tuple[str, ...]] = (
        _property_name(anisotropies_1),
        _property_name(anisotropies_2),
        _property_name(ratios),
    )
    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (_property_name(wavelengths), *_COLUMN_NAMES)

    MODEL: ClassVar[int] = 5
    """Identifier of the model in a ``*.material`` file."""

    VOLUMIC_HEADER: ClassVar[str] = _VOLUMIC_HEADER
    """Header of the scattering block holding the model."""

    def validate(self) -> None:
        """Check the phase function.

        Raises
        ------
        ValueError
            If no factor is given, the lists do not match, an anisotropy is outside
            -1 to 1, or a mixture weight is outside 0 to 1.
        """
        _check_phase_function(self)
        for name in self._COLUMN_NAMES:
            minimum = 0.0 if name == _property_name(type(self).ratios) else -1.0
            _check_phase_bounds(name, getattr(self, "_" + name), minimum, 1.0)

    def _to_lines(self) -> List[str]:
        return _phase_function_lines(self)

    @classmethod
    def _from_lines(cls, reader: LineReader) -> VolumeScatteringDoubleHenyeyGreenstein:
        return _read_phase_function(cls, reader)


class VolumeScatteringGegenbauer(_ValueComparable):
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

    def __init__(
        self,
        wavelengths: List[float] | None = None,
        anisotropies: List[float] | None = None,
        alphas: List[float] | None = None,
    ) -> None:
        self._wavelengths: List[float] = []
        self._anisotropies: List[float] = []
        self._alphas: List[float] = []
        self.wavelengths = wavelengths if wavelengths is not None else []
        self.anisotropies = anisotropies if anisotropies is not None else []
        self.alphas = alphas if alphas is not None else []

    @property
    def wavelengths(self) -> List[float]:
        """Spectral wavelengths in nm, returned as a copy.

        Returns
        -------
        List[float]
            Empty for a nonspectral parameter set.
        """
        return self._wavelengths.copy()

    @wavelengths.setter
    def wavelengths(self, values: List[float]) -> None:
        self._wavelengths = _phase_candidate(
            self, _property_name(VolumeScatteringGegenbauer.wavelengths), values
        )

    @property
    def anisotropies(self) -> List[float]:
        """Anisotropy factors, returned as a copy.

        Returns
        -------
        List[float]
            Finite factors.
        """
        return self._anisotropies.copy()

    @anisotropies.setter
    def anisotropies(self, values: List[float]) -> None:
        self._anisotropies = _phase_candidate(
            self, _property_name(VolumeScatteringGegenbauer.anisotropies), values
        )

    @property
    def alphas(self) -> List[float]:
        """Alpha coefficients, returned as a copy.

        Returns
        -------
        List[float]
            Finite coefficients.
        """
        return self._alphas.copy()

    @alphas.setter
    def alphas(self, values: List[float]) -> None:
        self._alphas = _phase_candidate(
            self, _property_name(VolumeScatteringGegenbauer.alphas), values
        )

    _COLUMN_NAMES: ClassVar[tuple[str, ...]] = (
        _property_name(anisotropies),
        _property_name(alphas),
    )
    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (_property_name(wavelengths), *_COLUMN_NAMES)

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


def _check_phase_function(model) -> None:
    """Check the columns of a phase function against its optional wavelength list.

    Speos does not store the wavelength when the phase function holds a single set of
    parameters, so ``wavelengths`` must be left empty in that case.
    """
    columns = {name: getattr(model, "_" + name) for name in model._COLUMN_NAMES}
    _check_phase_data(model._wavelengths, columns, complete=True)


def _check_phase_bounds(name: str, values: List[float], minimum: float, maximum: float) -> None:
    """Check phase parameters against their model's physical bounds."""
    if any(not minimum <= value <= maximum for value in values):
        raise ValueError(
            f"{name} must be between {format_number(minimum)} and {format_number(maximum)}."
        )


def _phase_candidate(model, name: str, values: List[float]) -> List[float]:
    """Check a candidate phase column without changing its current model."""
    values = _finite_values(name, values)
    wavelengths = values if name == _property_name(type(model).wavelengths) else model._wavelengths
    columns = {
        entry: values if entry == name else getattr(model, "_" + entry)
        for entry in model._COLUMN_NAMES
    }
    _check_phase_data(wavelengths, columns)
    return values


def _check_phase_data(wavelengths, columns, complete: bool = False) -> None:
    """Check phase-column lengths and the nonspectral empty-wavelength sentinel."""
    _matching_columns(columns, complete)
    count = next((len(values) for values in columns.values() if values), 0)
    if not count:
        return
    if not wavelengths:
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
    if len(wavelengths) != count:
        raise ValueError(
            f"All phase columns must have the same length: wavelengths must hold one "
            f"entry per set of parameters, expected {count}, got {len(wavelengths)}."
        )


def _phase_function_lines(model) -> List[str]:
    """Write a phase function as a count followed by one line per wavelength."""
    columns = [getattr(model, "_" + name) for name in model._COLUMN_NAMES]
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
    names = model_class._COLUMN_NAMES
    count = reader.next_int(minimum=1)
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

    Notes
    -----
    Setters validate candidate data without partially updating the material. List getters
    return copies; dispersion and phase models remain shared with validated properties.
    Empty columns permit staged construction, while :meth:`validate` and :meth:`save`
    require complete data and recheck shared child models. To resize a curve, clear all
    dependent value columns before changing its wavelengths, then repopulate the columns.
    Likewise, clear all phase parameter columns before changing phase wavelengths.
    To change between isotropic, metallic and birefringent flavors, construct a new
    material with the matching dispersion model rather than changing the flavor in place.

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

    def __init__(
        self,
        description: str = "",
        material_type: str = "Isotropic",
        dispersion: Union[
            MaterialDispersion, MaterialBirefringence, MaterialMetallicCurve, None
        ] = None,
        absorption_wavelengths: List[float] | None = None,
        absorption_values: List[float] | None = None,
        measured_concentration: float = 1.0,
        user_concentration: float = 1.0,
        scattering_wavelengths: List[float] | None = None,
        scattering_values: List[float] | None = None,
        scattering: Optional[VolumeScattering] = None,
        axis_j: List[float] | None = None,
        axis_k: List[float] | None = None,
        absorption_values_b: List[float] | None = None,
        absorption_values_c: List[float] | None = None,
    ) -> None:
        material_type = self._checked_type(material_type)
        dispersion = dispersion if dispersion is not None else MaterialConstringence()
        self._check_dispersion(material_type, dispersion)
        self._material_type = material_type
        self._dispersion = dispersion
        self._absorption_wavelengths: List[float] = []
        self._absorption_values: List[float] = []
        self._absorption_values_b: List[float] = []
        self._absorption_values_c: List[float] = []
        self._scattering_wavelengths: List[float] = []
        self._scattering_values: List[float] = []
        self.description = description
        self.absorption_wavelengths = (
            absorption_wavelengths if absorption_wavelengths is not None else []
        )
        self.absorption_values = absorption_values if absorption_values is not None else []
        self.measured_concentration = measured_concentration
        self.user_concentration = user_concentration
        self.scattering_wavelengths = (
            scattering_wavelengths if scattering_wavelengths is not None else []
        )
        self.scattering_values = scattering_values if scattering_values is not None else []
        self.scattering = scattering
        self.axis_j = axis_j if axis_j is not None else [1.0, 0.0, 0.0]
        self.axis_k = axis_k if axis_k is not None else [0.0, 1.0, 0.0]
        self.absorption_values_b = absorption_values_b if absorption_values_b is not None else []
        self.absorption_values_c = absorption_values_c if absorption_values_c is not None else []

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

    @property
    def material_type(self) -> str:
        """Material flavor matching the dispersion model.

        Returns
        -------
        str
            Isotropic, Metallic, or Birefringent, preserving the supplied spelling.

        Notes
        -----
        Construct a new material to switch to a flavor requiring another dispersion type.
        """
        return self._material_type

    @material_type.setter
    def material_type(self, value: str) -> None:
        value = self._checked_type(value)
        self._check_dispersion(value, self._dispersion)
        self._material_type = value

    @classmethod
    def _checked_type(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("material_type must be a string.")
        if not any(
            _is_type(value, expected)
            for expected in (cls.ISOTROPIC, cls.METALLIC, cls.BIREFRINGENT)
        ):
            raise ValueError("material_type must be Isotropic, Metallic, or Birefringent.")
        return value

    @classmethod
    def _check_dispersion(cls, material_type: str, value) -> None:
        if _is_type(material_type, cls.METALLIC):
            if not isinstance(value, MaterialMetallicCurve):
                raise ValueError(
                    "A metallic material needs a MaterialMetallicCurve, got "
                    f"{type(value).__name__}."
                )
            return
        expected = (
            cls.BIREFRINGENT_DISPERSIONS
            if _is_type(material_type, cls.BIREFRINGENT)
            else cls.DISPERSIONS
        )
        if not isinstance(value, expected):
            raise ValueError(
                f"A {material_type!r} material needs one of "
                f"{[model.__name__ for model in expected]}, got {type(value).__name__}."
            )

    @property
    def dispersion(self) -> Union[MaterialDispersion, MaterialBirefringence, MaterialMetallicCurve]:
        """Dispersion model of this material flavor.

        Returns
        -------
        Union[MaterialDispersion, MaterialBirefringence, MaterialMetallicCurve]
            Shared model with locally validated properties.
        """
        return self._dispersion

    @dispersion.setter
    def dispersion(
        self, value: Union[MaterialDispersion, MaterialBirefringence, MaterialMetallicCurve]
    ) -> None:
        self._check_dispersion(self._material_type, value)
        self._dispersion = value

    def _column(self, name: str, values: List[float]) -> List[float]:
        values = _finite_values(name, values)
        if self._has_type(self.METALLIC) and values:
            if name in _ABSORPTION_NAMES:
                raise ValueError(
                    "A metallic material has no absorption curve, its extinction "
                    "coefficient already holds the absorption."
                )
            if name in _DIFFUSION_NAMES:
                raise ValueError("A metallic material cannot scatter light in its volume.")
        names = _DIFFUSION_NAMES if name in _DIFFUSION_NAMES else _ABSORPTION_NAMES
        columns = {
            entry: values if entry == name else getattr(self, "_" + entry) for entry in names
        }
        _matching_columns(columns)
        if name not in _DIFFUSION_NAMES and self._has_type(self.BIREFRINGENT):
            wavelengths = columns[_property_name(MaterialFile.absorption_wavelengths)]
            for entry in _AXIS_ABSORPTION_NAMES:
                axis_values = values if entry == name else getattr(self, "_" + entry)
                if wavelengths and axis_values and len(axis_values) != len(wavelengths):
                    raise ValueError(
                        f"{entry} must hold one value per absorption wavelength, "
                        f"expected {len(wavelengths)}, got {len(axis_values)}."
                    )
        return values

    @property
    def absorption_wavelengths(self) -> List[float]:
        """Absorption wavelengths in nm, returned as a copy.

        Returns
        -------
        List[float]
            Finite wavelengths.
        """
        return self._absorption_wavelengths.copy()

    @absorption_wavelengths.setter
    def absorption_wavelengths(self, values: List[float]) -> None:
        self._absorption_wavelengths = self._column(
            _property_name(MaterialFile.absorption_wavelengths), values
        )

    @property
    def absorption_values(self) -> List[float]:
        """Absorption coefficients in mm-1, returned as a copy.

        Returns
        -------
        List[float]
            Finite coefficients, along the a axis for a birefringent material.
        """
        return self._absorption_values.copy()

    @absorption_values.setter
    def absorption_values(self, values: List[float]) -> None:
        self._absorption_values = self._column(
            _property_name(MaterialFile.absorption_values), values
        )

    @property
    def measured_concentration(self) -> float:
        """Concentration at which absorption was measured.

        Returns
        -------
        float
            Finite concentration.
        """
        return self._measured_concentration

    @measured_concentration.setter
    def measured_concentration(self, value: float) -> None:
        self._measured_concentration = _finite_number(
            _property_name(MaterialFile.measured_concentration), value
        )

    @property
    def user_concentration(self) -> float:
        """Concentration to which absorption is scaled.

        Returns
        -------
        float
            Finite concentration.
        """
        return self._user_concentration

    @user_concentration.setter
    def user_concentration(self, value: float) -> None:
        self._user_concentration = _finite_number(
            _property_name(MaterialFile.user_concentration), value
        )

    @property
    def scattering_wavelengths(self) -> List[float]:
        """Diffusion wavelengths in nm, returned as a copy.

        Returns
        -------
        List[float]
            Finite wavelengths.
        """
        return self._scattering_wavelengths.copy()

    @scattering_wavelengths.setter
    def scattering_wavelengths(self, values: List[float]) -> None:
        self._scattering_wavelengths = self._column(
            _property_name(MaterialFile.scattering_wavelengths), values
        )

    @property
    def scattering_values(self) -> List[float]:
        """Diffusion coefficients in mm-1, returned as a copy.

        Returns
        -------
        List[float]
            Finite coefficients.
        """
        return self._scattering_values.copy()

    @scattering_values.setter
    def scattering_values(self, values: List[float]) -> None:
        self._scattering_values = self._column(
            _property_name(MaterialFile.scattering_values), values
        )

    @property
    def scattering(self) -> Optional[VolumeScattering]:
        """Volume scattering phase function.

        Returns
        -------
        Optional[VolumeScattering]
            Shared phase model, or None for a nonscattering material.
        """
        return self._scattering

    @scattering.setter
    def scattering(self, value: Optional[VolumeScattering]) -> None:
        if value is not None:
            if self._has_type(self.METALLIC):
                raise ValueError("A metallic material cannot scatter light in its volume.")
            if not isinstance(value, self.SCATTERINGS):
                raise TypeError("scattering must be a supported volume scattering model or None.")
        self._scattering = value

    @property
    def axis_j(self) -> List[float]:
        """Direction of the b axis, returned as a copy.

        Returns
        -------
        List[float]
            Three finite coordinates.
        """
        return list(self._axis_j)

    @axis_j.setter
    def axis_j(self, values: List[float]) -> None:
        self._axis_j = _numeric_tuple(_property_name(MaterialFile.axis_j), values)

    @property
    def axis_k(self) -> List[float]:
        """Direction of the c axis, returned as a copy.

        Returns
        -------
        List[float]
            Three finite coordinates.
        """
        return list(self._axis_k)

    @axis_k.setter
    def axis_k(self, values: List[float]) -> None:
        self._axis_k = _numeric_tuple(_property_name(MaterialFile.axis_k), values)

    @property
    def absorption_values_b(self) -> List[float]:
        """Absorption coefficients along b, returned as a copy.

        Returns
        -------
        List[float]
            Finite coefficients in mm-1.
        """
        return self._absorption_values_b.copy()

    @absorption_values_b.setter
    def absorption_values_b(self, values: List[float]) -> None:
        self._absorption_values_b = self._column(
            _property_name(MaterialFile.absorption_values_b), values
        )

    @property
    def absorption_values_c(self) -> List[float]:
        """Absorption coefficients along c, returned as a copy.

        Returns
        -------
        List[float]
            Finite coefficients in mm-1.
        """
        return self._absorption_values_c.copy()

    @absorption_values_c.setter
    def absorption_values_c(self, values: List[float]) -> None:
        self._absorption_values_c = self._column(
            _property_name(MaterialFile.absorption_values_c), values
        )

    _ABSORPTION_NAMES: ClassVar[tuple[str, ...]] = (
        _property_name(absorption_wavelengths),
        _property_name(absorption_values),
    )
    _DIFFUSION_NAMES: ClassVar[tuple[str, ...]] = (
        _property_name(scattering_wavelengths),
        _property_name(scattering_values),
    )
    _AXIS_ABSORPTION_NAMES: ClassVar[tuple[str, ...]] = (
        _property_name(absorption_values_b),
        _property_name(absorption_values_c),
    )
    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(description),
        _property_name(material_type),
        _property_name(dispersion),
        *_ABSORPTION_NAMES,
        _property_name(measured_concentration),
        _property_name(user_concentration),
        *_DIFFUSION_NAMES,
        _property_name(scattering),
        _property_name(axis_j),
        _property_name(axis_k),
        *_AXIS_ABSORPTION_NAMES,
    )

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
        self._dispersion.validate()
        _matching_columns(
            {name: getattr(self, "_" + name) for name in _ABSORPTION_NAMES}, complete=True
        )
        if self._has_type(self.BIREFRINGENT):
            self._validate_birefringent()
        if self.scattering is None:
            return
        _matching_columns(
            {name: getattr(self, "_" + name) for name in _DIFFUSION_NAMES}, complete=True
        )
        self.scattering.validate()

    def _has_type(self, material_type: str) -> bool:
        return _is_type(self.material_type, material_type)

    def _validate_dispersion(self) -> None:
        """Check that the dispersion model belongs to the flavor of the material type."""
        self._check_dispersion(self._material_type, self._dispersion)

    def _validate_metallic(self) -> None:
        """Check a metallic material, which holds nothing but its complex index."""
        self._check_dispersion(self.METALLIC, self._dispersion)
        self._dispersion.validate()
        if self.absorption_wavelengths or self.absorption_values:
            raise ValueError(
                "A metallic material has no absorption curve, its extinction coefficient "
                "already holds the absorption."
            )
        if self.scattering is not None or self.scattering_wavelengths or self.scattering_values:
            raise ValueError("A metallic material cannot scatter light in its volume.")

    def _validate_birefringent(self) -> None:
        """Check the axes and the per axis absorption of a birefringent material."""
        self._check_dispersion(self._material_type, self._dispersion)
        for name in (_property_name(MaterialFile.axis_j), _property_name(MaterialFile.axis_k)):
            axis = getattr(self, name)
            if len(axis) != 3:
                raise ValueError(f"{name} must hold 3 coordinates, got {len(axis)}.")
        expected = len(self.absorption_wavelengths)
        for name in self._AXIS_ABSORPTION_NAMES:
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
        for _ in range(reader.next_int(minimum=1)):
            wavelength, value = reader.next_floats(count=2)
            absorption_wavelengths.append(wavelength)
            absorption_values.append(value)

        absorption_values_b, absorption_values_c = [], []
        if birefringent:
            for _ in absorption_wavelengths:
                value_b, value_c = reader.next_floats(count=2)
                absorption_values_b.append(value_b)
                absorption_values_c.append(value_c)
        measured_concentration = reader.next_floats(count=1)[0]
        user_concentration = reader.next_floats(count=1)[0]
        scattering_wavelengths, scattering_values = [], []
        scattering = None
        if reader.next_int():
            header = reader.next_data_line()
            header_error = reader.error(
                f"expected the volumic-scattering header for the selected phase model, "
                f"got {header!r}."
            )
            model_id = reader.next_int()
            models = {model.MODEL: model for model in cls.SCATTERINGS}
            if model_id not in models:
                raise reader.error(f"unsupported scattering phase function {model_id}.")
            model_class = models[model_id]
            if header not in (model_class.VOLUMIC_HEADER, model_class.VOLUMIC_HEADER + ".0"):
                raise header_error
            for _ in range(reader.next_int(minimum=1)):
                wavelength, value = reader.next_floats(count=2)
                scattering_wavelengths.append(wavelength)
                scattering_values.append(value)
            scattering = model_class._from_lines(reader)
        return cls(
            description=description,
            material_type=material_type,
            dispersion=dispersion,
            absorption_wavelengths=absorption_wavelengths,
            absorption_values=absorption_values,
            measured_concentration=measured_concentration,
            user_concentration=user_concentration,
            scattering_wavelengths=scattering_wavelengths,
            scattering_values=scattering_values,
            scattering=scattering,
            axis_j=axes[0] if birefringent else None,
            axis_k=axes[1] if birefringent else None,
            absorption_values_b=absorption_values_b,
            absorption_values_c=absorption_values_c,
        )


_CURVE_FIELDS = MaterialDispersionCurve._EQUALITY_FIELDS
_SELLMEIER_FIELDS = MaterialSellmeier._FIELD_NAMES
_KETTLER_FIELDS = MaterialKettlerHelmholtz._FIELD_NAMES
_METALLIC_FIELDS = MaterialMetallicCurve._EQUALITY_FIELDS
_BIREFRINGENT_FIELDS = MaterialBirefringentCurve._EQUALITY_FIELDS
_ABSORPTION_NAMES = MaterialFile._ABSORPTION_NAMES
_DIFFUSION_NAMES = MaterialFile._DIFFUSION_NAMES
_AXIS_ABSORPTION_NAMES = MaterialFile._AXIS_ABSORPTION_NAMES
_MATERIAL_FIELDS = MaterialFile._EQUALITY_FIELDS
