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

from typing import TYPE_CHECKING

from ansys.speos.core.generic.general_methods import graphics_required

if TYPE_CHECKING:  # pragma: no cover
    import pyvista as pv


@graphics_required
class VisualData:
    """Visualization data for the sensor.

    By default, there is empty visualization data.

    Notes
    -----
    **Do not instantiate this class yourself**, use set_dimensions method available in sensor
    classes.
    """

    def __init__(self) -> None:
        self.data = pv.PolyData()
        self.x_axis = pv.PolyData()
        self.y_axis = pv.PolyData()
        self.z_axis = pv.PolyData()

    @property
    def data(self) -> pv.PolyData:
        """
        Get visualization mesh data.

        Returns
        -------
        pv.PolyData
            mesh data.

        """
        return self.data

    @property
    def x_axis(self) -> pv.PolyData:
        """
        Get x-axis arrow data.

        Returns
        -------
        pv.PolyData
            x-axis arrow data.

        """
        return self.x_axis

    @property
    def y_axis(self) -> pv.PolyData:
        """
        Get y-axis arrow data.

        Returns
        -------
        pv.PolyData
            y-axis arrow data.

        """
        return self.y_axis

    @property
    def z_axis(self) -> pv.PolyData:
        """
        Get z-axis arrow data.

        Returns
        -------
        pv.PolyData
            z-axis arrow data.

        """
        return self.z_axis

    @data.setter
    def data(self, value) -> None:
        """
        Set visualization data.

        Parameters
        ----------
        value: pv.PolyData
            visualization data.

        Returns
        -------
        None

        """
        self._data = value

    @x_axis.setter
    def x_axis(self, value) -> None:
        """
        Set x-axis arrow data.

        Parameters
        ----------
        value: pv.PolyData
            x-axis arrow data.

        Returns
        -------
        None

        """
        self._x_axis = value

    @y_axis.setter
    def y_axis(self, value) -> None:
        """
        Set y-axis arrow data.

        Parameters
        ----------
        value: pv.PolyData
            y-axis arrow data.

        Returns
        -------
        None

        """
        self._y_axis = value

    @z_axis.setter
    def z_axis(self, value) -> None:
        """
        Set z-axis arrow data.

        Parameters
        ----------
        value: pv.PolyData
            z-axis arrow data.

        Returns
        -------
        None

        """
        self._z_axis = value
