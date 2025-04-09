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

"""Provides the ``VisualData`` class."""

from typing import TYPE_CHECKING, List

from ansys.speos.core.generic.general_methods import (
    graphics_required,
    magnitude_vector,
    normalize_vector,
)

if TYPE_CHECKING:  # pragma: no cover
    import pyvista as pv


@graphics_required
class VisualCoordinateSystem:
    """Visualization data for the coordinate system..

    By default, there is empty visualization data.

    Notes
    -----
    **Do not instantiate this class yourself**.
    classes.
    """

    def __init__(self):
        import pyvista as pv

        self._origin = [0.0, 0.0, 0.0]
        self._x_axis = pv.Arrow(
            start=self._origin,
            direction=[1.0, 0.0, 0.0],
            scale=10.0,
            tip_radius=0.05,
            shaft_radius=0.01,
        )
        self._y_axis = pv.Arrow(
            start=self._origin,
            direction=[0.0, 1.0, 0.0],
            scale=10.0,
            tip_radius=0.05,
            shaft_radius=0.01,
        )
        self._z_axis = pv.Arrow(
            start=self._origin,
            direction=[0.0, 0.0, 1.0],
            scale=10.0,
            tip_radius=0.05,
            shaft_radius=0.01,
        )

    @property
    def origin(self) -> List[float]:
        """Returns the origin of the coordinate system.

        Returns
        -------
        List[float]
            The origin of the coordinate system.

        """
        return self._origin

    @origin.setter
    def origin(self, value: List[float]) -> None:
        """Set the origin of the coordinate system.

        Parameters
        ----------
        value: List[float]
            The origin of the coordinate system.

        Returns
        -------
        None
        """
        if len(value) != 3:
            msg = "origin must be a list with three elements."
            raise ValueError(msg)
        self._origin = value

    @property
    def x_axis(self) -> "pv.Arrow":
        """Returns the x-axis of the coordinate system.

        Returns
        -------
        pv.Arrow
            pyvista.Arrow the x-axis of the coordinate system.

        """
        return self._x_axis

    @x_axis.setter
    def x_axis(self, x_vector: List[float]) -> None:
        """Set the x-axis of the coordinate system.

        Parameters
        ----------
        x_vector: List[float]
            The x-axis of the coordinate system.

        Returns
        -------
        None
        """
        import pyvista as pv

        if len(x_vector) != 3:
            msg = "x_axis must be a list with three elements."
            raise ValueError(msg)
        self._x_axis = pv.Arrow(
            start=self._origin,
            direction=normalize_vector(vector=x_vector),
            scale=magnitude_vector(vector=x_vector),
            tip_radius=0.05,
            shaft_radius=0.01,
        )

    @property
    def y_axis(self) -> "pv.Arrow":
        """
        Returns the y-axis of the coordinate system.

        Returns
        -------
        pv.Arrow
            pyvista.Arrow the y-axis of the coordinate system.

        """
        return self._y_axis

    @y_axis.setter
    def y_axis(self, y_vector: List[float]) -> None:
        """Set the y-axis of the coordinate system.

        Parameters
        ----------
        y_vector: List[float]
            The y-axis of the coordinate system.

        Returns
        -------
        None
        """
        import pyvista as pv

        if len(y_vector) != 3:
            msg = "y_axis must be a list with three elements."
            raise ValueError(msg)
        self._y_axis = pv.Arrow(
            start=self._origin,
            direction=normalize_vector(vector=y_vector),
            scale=magnitude_vector(vector=y_vector),
            tip_radius=0.05,
            shaft_radius=0.01,
        )

    @property
    def z_axis(self) -> "pv.Arrow":
        """
        Returns the z-axis of the coordinate system.

        Returns
        -------
        pv.Arrow
            pyvista.Arrow the z-axis of the coordinate system.

        """
        return self._z_axis

    @z_axis.setter
    def z_axis(self, z_vector: List[float]) -> None:
        """Set the z-axis of the coordinate system.

        Parameters
        ----------
        z_vector: List[float]
            The z-axis of the coordinate system.

        Returns
        -------
        None
        """
        import pyvista as pv

        if len(z_vector) != 3:
            msg = "z_axis must be a list with three elements."
            raise ValueError(msg)
        self._z_axis = pv.Arrow(
            start=self._origin,
            direction=normalize_vector(vector=z_vector),
            scale=magnitude_vector(vector=z_vector),
            tip_radius=0.05,
            shaft_radius=0.01,
        )


@graphics_required
class VisualData:
    """Visualization data for the sensor.

    By default, there is empty visualization data.

    Notes
    -----
    **Do not instantiate this class yourself**
    classes.
    """

    def __init__(self, coordinate_system=True):
        import pyvista as pv

        self._data = pv.PolyData()
        self.coordinates = VisualCoordinateSystem() if coordinate_system else None
        self.updated = False

    @property
    def data(self) -> "pv.PolyData":
        """
        Returns the data of the sensor.

        Returns
        -------
        pv.PolyData
            The data of the surface visualization.

        """
        return self._data

    def add_data_triangle(self, triangle_vertices: List[List[float]]) -> None:
        """
        Add surface data triangle to Visualization data.

        Parameters
        ----------
        triangle_vertices: List[List[float]]
            The vertices of the triangle.

        Returns
        -------
        None
        """
        import pyvista as pv

        if len(triangle_vertices) != 3 or any(len(vertice) != 3 for vertice in triangle_vertices):
            msg = "provided triangle vertices must have 3 elements"
            raise ValueError(msg)
        faces = [[3, 0, 1, 2]]
        self._data = self._data.append_polydata(pv.PolyData(triangle_vertices, faces))

    def add_data_rectangle(self, rectangle_vertices: List[List[float]]) -> None:
        """
        Add surface data rectangle to Visualization data.

        Parameters
        ----------
        rectangle_vertices: List[List[float]]
            The vertices of the rectangle.

        Returns
        -------
        None
        """
        import pyvista as pv

        if len(rectangle_vertices) != 3 or any(len(vertice) != 3 for vertice in rectangle_vertices):
            msg = "provided rectangle vertices must have 3 elements"
            raise ValueError(msg)
        self._data = self._data.append_polydata(pv.Rectangle(rectangle_vertices))
