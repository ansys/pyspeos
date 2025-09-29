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

from typing import TYPE_CHECKING, List, Tuple, Union

import numpy as np

from ansys.speos.core.generic.general_methods import (
    graphics_required,
    magnitude_vector,
    normalize_vector,
)

if TYPE_CHECKING:  # pragma: no cover
    import pyvista as pv


@graphics_required
class _VisualCoordinateSystem:
    """Visualization data for the coordinate system.

    By default, there is empty visualization data.

    Notes
    -----
    **Do not instantiate this class yourself**.
    """

    def __init__(self):
        import pyvista as pv

        self.__origin = [0.0, 0.0, 0.0]
        self.__x_axis = pv.Arrow(
            start=self.__origin,
            direction=[1.0, 0.0, 0.0],
            scale=1.0,
            tip_radius=0.05,
            shaft_radius=0.01,
        )
        self.__y_axis = pv.Arrow(
            start=self.__origin,
            direction=[0.0, 1.0, 0.0],
            scale=1.0,
            tip_radius=0.05,
            shaft_radius=0.01,
        )
        self.__z_axis = pv.Arrow(
            start=self.__origin,
            direction=[0.0, 0.0, 1.0],
            scale=1.0,
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
        return self.__origin

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
            raise ValueError("origin must be a List of three values.")
        self.__origin = value

    @property
    def x_axis(self) -> "pv.PolyData":
        """Returns the x-axis of the coordinate system.

        Returns
        -------
        pv.PolyData
            pyvista.PolyData the x-axis of the coordinate system.

        """
        return self.__x_axis

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
            raise ValueError("x_axis must be a List of three values.")
        self.__x_axis = pv.Arrow(
            start=self.__origin,
            direction=normalize_vector(vector=x_vector),
            scale=magnitude_vector(vector=x_vector),
            tip_radius=0.05,
            shaft_radius=0.01,
        )

    @property
    def y_axis(self) -> "pv.PolyData":
        """
        Returns the y-axis of the coordinate system.

        Returns
        -------
        pv.PolyData
            pyvista.PolyData the y-axis of the coordinate system.

        """
        return self.__y_axis

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
            raise ValueError("y_axis must be a List of three values.")
        self.__y_axis = pv.Arrow(
            start=self.__origin,
            direction=normalize_vector(vector=y_vector),
            scale=magnitude_vector(vector=y_vector),
            tip_radius=0.05,
            shaft_radius=0.01,
        )

    @property
    def z_axis(self) -> "pv.PolyData":
        """
        Returns the z-axis of the coordinate system.

        Returns
        -------
        pv.PolyData
            pyvista.PolyData the z-axis of the coordinate system.

        """
        return self.__z_axis

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
            raise ValueError("z_axis must be a List of three values.")
        self.__z_axis = pv.Arrow(
            start=self.__origin,
            direction=normalize_vector(vector=z_vector),
            scale=magnitude_vector(vector=z_vector),
            tip_radius=0.05,
            shaft_radius=0.01,
        )


@graphics_required
class _VisualArrow:
    """Visualization data for the line or arrow.

    By default, there is empty visualization data.

    Notes
    -----
    **Do not instantiate this class yourself**.
    """

    def __init__(
        self,
        line_vertices: List[List[float]],
        color: Tuple[float, float, float] = (0.643, 1.0, 0.0),
        arrow: bool = False,
    ) -> None:
        import pyvista as pv

        if len(line_vertices) != 2 or any(len(point) != 3 for point in line_vertices):
            raise ValueError(
                "line_vertices is expected to be composed of 2 vertices with 3 elements each."
            )
        line_vertices = np.array(line_vertices)
        if arrow:
            self.__data = pv.Arrow(
                start=line_vertices[0],
                direction=line_vertices[1],
                scale=1,
                tip_radius=0.05,
                shaft_radius=0.01,
            )
        else:
            self.__data = pv.Line(line_vertices[0], line_vertices[0] + line_vertices[1])
        if all(value < 1 for value in color):
            self.__color = color + (255,)
        else:
            self.__color = tuple(value / 255 for value in color) + (255,)

    @property
    def data(self) -> "pv.PolyData":
        """
        Returns the pyvista data of _VisualArrow.

        Returns
        -------
        pv.PolyData
            The pyvista data of _VisualArrow.

        """
        return self.__data

    @property
    def color(self) -> Tuple[float, float, float]:
        """
        Returns the color property of _VisualArrow.

        Returns
        -------
        Tuple[float, float, float]
            The color tuple of _VisualArrow.

        """
        return self.__color


@graphics_required
class _VisualData:
    """Visualization data for the sensor.

    By default, there is empty visualization data.

    Notes
    -----
    **Do not instantiate this class yourself**
    """

    def __init__(self, ray: bool = False, coordinate_system: bool = True):
        import pyvista as pv

        self._data = [] if ray else pv.PolyData()
        self.coordinates = _VisualCoordinateSystem() if coordinate_system else None
        self.updated = False

    @property
    def data(self) -> Union["pv.PolyData", List[_VisualArrow]]:
        """
        Returns the pyvista data of _VisualData.

        Returns
        -------
        Union["pv.PolyData", List[_VisualArrow]]
            The data of the surface visualization if surface data,
            else List[_VisualArrow] containing ray info.

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

        if len(triangle_vertices) != 3 or any(len(vertex) != 3 for vertex in triangle_vertices):
            raise ValueError(
                "triangle_vertices is expected to be composed of 3 vertices with 3 elements each."
            )
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

        if len(rectangle_vertices) != 3 or any(len(vertex) != 3 for vertex in rectangle_vertices):
            raise ValueError(
                "rectangle_vertices is expected to be composed of 3 vertices with 3 elements each."
            )
        self._data = self._data.append_polydata(pv.Rectangle(rectangle_vertices))

    def add_data_line(self, line: _VisualArrow) -> None:
        """
        Add line data to Visualization data.

        Parameters
        ----------
        line: _VisualArrow
            _VisualArrow presenting one line

        Returns
        -------
        None
        """
        self._data.append(line)

    def add_data_mesh(self, vertices: np.ndarray, facets: np.ndarray) -> None:
        """
        Add mesh data to Visualization data.

        Parameters
        ----------
        vertices: numpy.ndarray
            The vertices of the mesh.
        facets: numpy.ndarray
            The facets of the mesh.

        Returns
        -------
        None
        """
        import pyvista as pv

        if vertices.shape[1] != 3 or facets.shape[1] != 4:
            raise ValueError(
                "mesh vertices is expected to be composed of 3 elements each, and 4 for facets."
            )
        self._data = self._data.append_polydata(pv.PolyData(vertices, facets))


def local2absolute(local_vertice: np.ndarray, coordinates) -> np.ndarray:
    """Convert local coordinate to global coordinate.

    Parameters
    ----------
    coordinates: list
        local coordinate in shape [1, 9],
        coordinates[3:6] as x-axis,
        coordinates[3:6] as y-axis,
        coordinates[3:6] as z-axis.
    local_vertice: np.ndarray
        numpy array includes x, y, z info.

    Returns
    -------
    np.ndarray
        numpy array includes x, y, z info

    """
    global_origin = np.array(coordinates[:3])
    global_x = np.array(coordinates[3:6]) * local_vertice[0]
    global_y = np.array(coordinates[6:9]) * local_vertice[1]
    global_z = np.array(coordinates[9:]) * local_vertice[2]
    return global_origin + global_x + global_y + global_z
