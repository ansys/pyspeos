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

"""Shared numeric, collection, and path validation helpers."""

from __future__ import annotations

from collections.abc import Collection, Sequence
import math
from pathlib import Path
from typing import List, Union

import numpy as np


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


def _finite_float(value: float, name: str, *, include_value: bool = False) -> float:
    """Convert a value to a finite float with a caller-specific error message."""
    try:
        number = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} must be finite.") from error
    if not math.isfinite(number):
        suffix = f", got {number}" if include_value else ""
        raise ValueError(f"{name} must be finite{suffix}.")
    return number


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
    return _finite_float(value, name, include_value=True)


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


def _validate_numeric_sequence(
    value: Collection[float], expected_length: int, noun: str, article: str = "A"
) -> np.ndarray:
    """Validate and convert a finite numeric sequence."""
    length_words = {2: "two", 3: "three", 9: "nine", 12: "twelve"}
    expected_text = length_words.get(expected_length, str(expected_length))
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(
            f"{article} {noun} must be a list or tuple of {expected_text} finite numbers."
        )
    if len(value) != expected_length:
        raise ValueError(f"{article} {noun} must contain exactly {expected_text} values.")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise TypeError(f"{noun.capitalize()} values must be numeric.")
    return np.asarray(
        [_finite_float(item, f"{noun.capitalize()} values") for item in value],
        dtype=float,
    )


def _validate_vector3(value: Collection[float]) -> np.ndarray:
    """Validate and convert a three-dimensional vector."""
    return _validate_numeric_sequence(value, 3, "vector")


def _validate_axis_system12(value: Collection[float]) -> np.ndarray:
    """Validate and convert a twelve-value axis system."""
    return _validate_numeric_sequence(value, 12, "axis system", article="An")


def _validate_scalar(value: float) -> float:
    """Validate and convert a finite scalar."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("A scalar must be a finite number.")
    return _finite_float(value, "A scalar")


def _validate_positive_int(value: int) -> int:
    """Validate a positive integer value."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Value must be an integer.")
    if value <= 0:
        raise ValueError("Value must be greater than 0.")
    return value


def _validate_pathlike(value: Union[str, Path], name: str) -> str:
    """Validate and convert a string or path-like value to a string."""
    if not isinstance(value, (str, Path)):
        raise TypeError(f"{name} must be a string or Path.")
    return str(value)
