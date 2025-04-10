# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
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

"""General methods and helpers collection.

this includes decorator and methods
"""

from functools import lru_cache, wraps
import math
from typing import List, Union
import warnings

_GRAPHICS_AVAILABLE = None
GRAPHICS_ERROR = (
    "Preview unsupported without 'ansys-tools-visualization_interface' installed. "
    "You can install this using `pip install ansys-speos-core[graphics]`."
)


def deprecate_kwargs(old_arguments: dict, removed_version="0.3.0"):
    """Issues deprecation warnings for arguments.

    Parameters
    ----------
    old_arguments : dict
        key old argument value new argument name
    removed_version : str
        Release version with which argument support will be removed
        By Default, next major release

    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            func_name = function.__name__
            for alias, new in old_arguments.items():
                if alias in kwargs:
                    if new in kwargs:
                        msg = f"{func_name} received both {alias} and {new} as arguments!\n"
                        msg += f"{alias} is deprecated, use {new} instead."
                        raise TypeError(msg)
                    msg = f"Argument `{alias}` is deprecated for method `{func_name}`; it will be "
                    msg += f"removed with Release v{removed_version}. Please use `{new}` instead."
                    kwargs[new] = kwargs.pop(alias)
                    warnings.warn(msg, DeprecationWarning, stacklevel=2)
            retval = function(*args, **kwargs)
            return retval

        return wrapper

    return decorator


@lru_cache
def run_if_graphics_required(warning=False):
    """Check if graphics are available."""
    global _GRAPHICS_AVAILABLE
    if _GRAPHICS_AVAILABLE is None:
        try:
            import pyvista as pv  # noqa: F401

            from ansys.tools.visualization_interface import Plotter  # noqa: F401

            _GRAPHICS_AVAILABLE = True
        except ImportError:  # pragma: no cover
            _GRAPHICS_AVAILABLE = False

    if _GRAPHICS_AVAILABLE is False and warning is False:  # pragma: no cover
        raise ImportError(GRAPHICS_ERROR)
    elif _GRAPHICS_AVAILABLE is False:  # pragma: no cover
        warnings.warn(GRAPHICS_ERROR)


def graphics_required(method):
    """Decorate a method as requiring graphics.

    Parameters
    ----------
    method : callable
        Method to decorate.

    Returns
    -------
    callable
        Decorated method.
    """

    def wrapper(*args, **kwargs):
        run_if_graphics_required()
        return method(*args, **kwargs)

    return wrapper


def magnitude_vector(vector: List[float]) -> float:
    """
    Compute the magnitude (length) of a 3D vector.

    Parameters
    ----------
    vector: List
        A 2D or 3D vector as a list [x, y, z].

    Returns
    -------
    float
        The magnitude (length) of the vector.
    """
    if len(vector) == 2:
        # 2D vector magnitude
        magnitude = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
    elif len(vector) == 3:
        # 3D vector magnitude
        magnitude = math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)
    else:
        raise ValueError("Input vector must be either 2D or 3D")

    return magnitude


def normalize_vector(vector: List[float]) -> List[float]:
    """
    Normalize a 2D or 3D vector to have a length of 1.

    Parameters
    ----------
    vector: List
        A vector as a list [x, y] for 2D or [x, y, z] for 3D.

    Returns
    -------
    List
        The normalized vector.
    """
    # Check if the vector has 2 or 3 components
    magnitude = magnitude_vector(vector)
    if magnitude == 0:
        raise ValueError("Cannot normalize the zero vector")

    if len(vector) == 2:
        normalized_v = [vector[0] / magnitude, vector[1] / magnitude]
    elif len(vector) == 3:
        normalized_v = [vector[0] / magnitude, vector[1] / magnitude, vector[2] / magnitude]
    else:
        raise ValueError("Input vector must be either 2D or 3D")

    return normalized_v


class Vector:
    """A simple 2D or 3D vector class supporting basic vector operations."""

    def __init__(self, components: List[Union[int, float]]):
        """
        Initialize a Vector.

        Parameters
        ----------
        components : List[int or float]
            The components of the vector (must be 2D or 3D).

        Raises
        ------
        TypeError
            If the input is not a list.
        ValueError
            If the input list is not of length 2 or 3.
        """
        if not isinstance(components, list):
            raise TypeError("Vector components must be provided as a list.")
        if len(components) not in (2, 3):
            raise ValueError("Only 2D or 3D vectors are supported.")
        self.components = components

    def __add__(self, other: "Vector") -> "Vector":
        """
        Add two vectors.

        Parameters
        ----------
        other : Vector
            The vector to add.

        Returns
        -------
        Vector
            The result of vector addition.
        """
        if not isinstance(other, Vector):
            return NotImplemented
        if len(self.components) != len(other.components):
            raise ValueError("Vectors must have the same dimensions.")
        return Vector([a + b for a, b in zip(self.components, other.components)])

    def __sub__(self, other: "Vector") -> "Vector":
        """
        Subtract one vector from another.

        Parameters
        ----------
        other : Vector
            The vector to subtract.

        Returns
        -------
        Vector
            The result of vector subtraction.
        """
        if not isinstance(other, Vector):
            return NotImplemented
        if len(self.components) != len(other.components):
            raise ValueError("Vectors must have the same dimensions.")
        return Vector([a - b for a, b in zip(self.components, other.components)])

    def __mul__(self, other: Union[int, float, "Vector"]) -> Union["Vector", float]:
        """
        Multiply the vector by a scalar or compute the dot product with another vector.

        Parameters
        ----------
        other : int, float, or Vector
            A scalar for scalar multiplication, or another vector for dot product.

        Returns
        -------
        Vector or float
            A new scaled vector or the result of the dot product.
        """
        if isinstance(other, (int, float)):
            return Vector([a * other for a in self.components])
        elif isinstance(other, Vector):
            if len(self.components) != len(other.components):
                raise ValueError("Vectors must have the same dimensions.")
            return sum(a * b for a, b in zip(self.components, other.components))
        else:
            return NotImplemented

    def __eq__(self, other: object) -> bool:
        """
        Check if two vectors are equal.

        Parameters
        ----------
        other : object
            The vector to compare.

        Returns
        -------
        bool
            True if vectors have the same components, False otherwise.
        """
        if not isinstance(other, Vector):
            return NotImplemented
        return self.components == other.components

    def __len__(self) -> int:
        """
        Return the number of dimensions of the vector.

        Returns
        -------
        int
            The number of elements in the vector (2 or 3).
        """
        return len(self.components)

    def __repr__(self) -> str:
        """
        Return a string representation of the vector.

        Returns
        -------
        str
            The string representation.
        """
        return f"Vector({self.components})"
