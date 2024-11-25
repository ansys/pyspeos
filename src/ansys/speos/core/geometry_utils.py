# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

"""Provides some classes needed for geometry."""
from typing import List, Optional


class AxisSystem:
    """
    Represents an axis system.

    Parameters
    ----------
    origin : List[float], optional
        Origin of the axis system.
        By default, ``[0, 0, 0]``.
    x_vect : List[float], optional
        X vector of the axis system.
        By default, ``[1, 0, 0]``.
    y_vect : List[float], optional
        Y vector of the axis system.
        By default, ``[0, 1, 0]``.
    z_vect : List[float], optional
        Z vector of the axis system.
        By default, ``[0, 0, 1]``.
    """

    def __init__(
        self,
        origin: Optional[List[float]] = [0, 0, 0],
        x_vect: Optional[List[float]] = [1, 0, 0],
        y_vect: Optional[List[float]] = [0, 1, 0],
        z_vect: Optional[List[float]] = [0, 0, 1],
    ) -> None:
        self.origin = origin
        """Origin of the axis system"""
        self.x_vect = x_vect
        """X vector of the axis system"""
        self.y_vect = y_vect
        """Y vector of the axis system"""
        self.z_vect = z_vect
        """Z vector of the axis system"""


class AxisPlane:
    """
    Represents an axis plane.

    Parameters
    ----------
    origin : List[float], optional
        Origin of the axis plane.
        By default, ``[0, 0, 0]``.
    x_vect : List[float], optional
        X vector of the axis plane.
        By default, ``[1, 0, 0]``.
    y_vect : List[float], optional
        Y vector of the axis plane.
        By default, ``[0, 1, 0]``.
    """

    def __init__(
        self,
        origin: Optional[List[float]] = [0, 0, 0],
        x_vect: Optional[List[float]] = [1, 0, 0],
        y_vect: Optional[List[float]] = [0, 1, 0],
    ) -> None:
        self.origin = origin
        """Origin of the axis plane"""
        self.x_vect = x_vect
        """X vector of the axis plane"""
        self.y_vect = y_vect
        """Y vector of the axis plane"""
