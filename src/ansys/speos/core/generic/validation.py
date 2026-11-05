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

"""Dependency-independent numeric and collection validation helpers."""

from __future__ import annotations

import math
from typing import List, Sequence


def check_percentage(name: str, value: float) -> None:
    """Check that a value is a percentage expressed between 0 and 100.

    Parameters
    ----------
    name : str
        Name of the checked value, used in the error message.
    value : float
        Value to check.

    Raises
    ------
    ValueError
        If ``value`` is not within ``[0, 100]``.
    """
    if not 0.0 <= value <= 100.0:
        raise ValueError(f"{name} must be between 0 and 100, got {value}.")


def _finite_number(name: str, value: float) -> float:
    """Convert a numeric value without accepting nonfinite data.

    Parameters
    ----------
    name : str
        Name of the checked value, used in the error message.
    value : float
        Numeric value to convert and validate.

    Returns
    -------
    float
        Converted finite value.

    Raises
    ------
    TypeError
        If ``value`` cannot be converted to a float because of its type.
    ValueError
        If ``value`` cannot be parsed as a float or is not finite.
    """
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value}.")
    return value


def _percentage(name: str, value: float) -> float:
    """Convert and validate a finite percentage before storing it.

    Parameters
    ----------
    name : str
        Name of the checked value, used in the error message.
    value : float
        Percentage to convert and validate, between 0 and 100 inclusive.

    Returns
    -------
    float
        Converted finite percentage.

    Raises
    ------
    TypeError
        If ``value`` cannot be converted to a float because of its type.
    ValueError
        If ``value`` cannot be parsed as a float, is not finite, or is outside ``[0, 100]``.
    """
    value = _finite_number(name, value)
    check_percentage(name, value)
    return value


def _finite_values(name: str, values: Sequence[float]) -> List[float]:
    """Copy a numeric column while validating its entries.

    Parameters
    ----------
    name : str
        Name of the checked sequence, used in the error message.
    values : Sequence[float]
        Numeric entries to convert and validate. An empty sequence is accepted.

    Returns
    -------
    List[float]
        New list of finite floats in the supplied order.

    Raises
    ------
    TypeError
        If ``values`` is text or bytes, is not iterable, or an entry has a type that cannot
        be converted to a float.
    ValueError
        If an entry cannot be parsed as a float or is not finite.
    """
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be a numeric sequence, not text.")
    return [_finite_number(name, value) for value in values]


def _numeric_tuple(name: str, values: Sequence[float], count: int = 3) -> tuple[float, ...]:
    """Validate a fixed-size numeric vector and store it immutably.

    Parameters
    ----------
    name : str
        Name of the checked vector, used in the error message.
    values : Sequence[float]
        Numeric coordinates to convert and validate.
    count : int, optional
        Required number of coordinates. By default, ``3``.

    Returns
    -------
    tuple[float, ...]
        Immutable tuple of ``count`` finite floats in the supplied order.

    Raises
    ------
    TypeError
        If ``values`` is text or bytes, is not iterable, or a coordinate has a type that
        cannot be converted to a float.
    ValueError
        If a coordinate cannot be parsed as a float, is not finite, or the number of
        coordinates differs from ``count``.
    """
    values = tuple(_finite_values(name, values))
    if len(values) != count:
        raise ValueError(f"{name} must hold {count} coordinates, got {len(values)}.")
    return values
