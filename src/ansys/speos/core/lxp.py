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

"""The lxp module contains classes and functions to simplify the interaction with ray data.

Ray data is provided as lpf file.
LPF files contain a set of simulated rays with all their intersections and properties.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

import ansys.api.speos.lpf.v2.lpf_file_reader_pb2 as lpf_file_reader__v2__pb2
import ansys.api.speos.lpf.v2.lpf_file_reader_pb2_grpc as lpf_file_reader__v2__pb2_grpc
from ansys.speos.core.generic.general_methods import graphics_required, wavelength_to_rgb
from ansys.speos.core.project import Project, Speos

if TYPE_CHECKING:  # pragma: no cover
    from ansys.tools.visualization_interface import Plotter
try:
    from ansys.speos.core.generic.general_methods import run_if_graphics_required

    run_if_graphics_required(warning=True)
except ImportError as err:  # pragma: no cover
    raise err

ERROR_IDS = [7, 8, 9, 10, 11, 12, 13, 14, 15]
"""Intersection types indicating an error state."""

NO_ERROR_IDS = [0, 1, 2, 3, 4, 5, 6, 16, -7, -6, -5, -5, -4, -3, -2, -1]
"""Intersection types indicating a correct ray state."""


class RayPath:
    """Framework representing a singular ray path.

    Parameters
    ----------
    raypath : ansys.api.speos.lpf.v2.lpf_file_reader__v2__pb2.RayPath
        RayPath object
    sensor_contribution : bool
        Defines if sensor contributions are stored within the data.
        By default ``False``.
    """

    def __init__(
        self,
        raypath: lpf_file_reader__v2__pb2.RayPath,
        sensor_contribution: bool = False,
    ):
        self._nb_impacts = len(raypath.impacts)
        self._impacts = [[inter.x, inter.y, inter.z] for inter in raypath.impacts]
        self._wl = raypath.wavelengths[0]
        self._body_ids = raypath.body_context_ids
        self._face_ids = raypath.unique_face_ids
        self._last_direction = [
            raypath.lastDirection.x,
            raypath.lastDirection.y,
            raypath.lastDirection.z,
        ]
        self._intersection_type = raypath.interaction_statuses
        if sensor_contribution:
            self._sensor_contribution = [
                {
                    "sensor_id": sc.sensor_id,
                    "position": [sc.coordinates.x, sc.coordinates.y],
                }
                for sc in raypath.sensor_contributions
            ]
        else:
            self._sensor_contribution = None

    @property
    def nb_impacts(self) -> int:
        """Number of impacts contained in ray path.

        Returns
        -------
        int
            Number of impacts
        """
        return self._nb_impacts

    @property
    def impacts(self) -> list[list[float]]:
        """XYZ coordinates for each impact.

        Returns
        -------
        list[list[float]]
            list containing the impact coordinates [[x0,y0,z0],[x1,y1,z1],...]
        """
        return self._impacts

    @property
    def wl(self) -> float:
        """Wavelength of the ray.

        Returns
        -------
        float
            Wavelength in nm
        """
        return self._wl

    @property
    def body_ids(self) -> list[int]:
        """Body ID of interacted body for each impact.

        Returns
        -------
        list[int]
            List of body IDs for each impact.
        """
        return self._body_ids

    @property
    def face_ids(self) -> list[int]:
        """Face ID of interacted body for each impact.

        Returns
        -------
        list[int]
            List of face IDs for each impact.
        """
        return self._face_ids

    @property
    def last_direction(self) -> list[float]:
        """Last direction of the ray.

        Returns
        -------
        list[float]
            Last direction of the rays as list[x,y,z].
        """
        return self._last_direction

    @property
    def intersection_type(self) -> list[int]:
        """Intersection type of the ray for each impact.

        Returns
        -------
        list[int]
            Intersection type at each impact.

        Notes
        -----
        Available intersection types:

        - StatusAbsorbed = 0
        - StatusSpecularTransmitted = 1
        - StatusGaussianTransmitted = 2
        - StatusLambertianTransmitted = 3
        - StatusVolumicDiffused = 4
        - StatusJustEmitted = 5
        - StatusDiracTransmitted = 6
        - StatusError = 7
        - StatusErrorVolumicBodyNotClosed = 8
        - StatusErrorVolumeConflict = 9
        - StatusError2DTangency = 10
        - StatusError2DIntersect3DWarning = 11
        - StatusErrorNonOpticalMaterial = 12
        - StatusErrorIntersection = 13
        - StatusErrorNonOpticalMaterialAtEmission = 14
        - StatusError3DTextureSupportTangency = 15
        - StatusLast = 16
        - StatusFirst = -7
        - StatusDiracReflected = -6
        - StatusReserved = -5
        - StatusGrinStep = -4
        - StatusLambertianReflected = -3
        - StatusGaussianReflected = -2
        - StatusSpecularReflected = -1
        """
        return self._intersection_type

    @property
    def sensor_contribution(self) -> Union[None, list[dict]]:
        """Provide the sensor contribution information for each sensor.

        Returns
        -------
        Union[None, list[dict]]
            If no sensor contribution, None will be returned. If there is sensor contribution, \
            a dictionary with the following information is returned:\
            {“sensor_id”: sc.sensor_id,
            “position”: [sc.coordinates.x, sc.coordinates.y]}
        """
        return self._sensor_contribution

    def get(self, key=""):
        """Retrieve any information from the RayPath object.

        Parameters
        ----------
        key : str
            Name of the property.

        Returns
        -------
        property
            Values/content of the associated property.
        """
        data = {k: v.fget(self) for k, v in RayPath.__dict__.items() if isinstance(v, property)}
        if key == "":
            return data
        elif data.get(key):
            return data.get(key)
        else:
            print("Used key: {} not found in key list: {}.".format(key, data.keys()))

    def __str__(self):
        """Create string representation of a RayPath."""
        return str(self.get())


class LightPathFinder:
    """Define an interface to read LPF files.

    LPF files contain a set of simulated rays including their intersections and properties.

    Parameters
    ----------
    speos : ansys.speos.core.speos.Speos
        Speos Session (connected to Speos gRPC server).
    path : str
        Path to the LPF file to be opened.

    """

    def __init__(self, speos: Speos, path: str):
        self.client = speos.client
        """Speos instance client"""
        self._stub = lpf_file_reader__v2__pb2_grpc.LpfFileReader_MonoStub(self.client.channel)
        self.__open(path)
        self._data = self._stub.GetInformation(
            lpf_file_reader__v2__pb2.GetInformation_Request_Mono()
        )
        self._nb_traces = self._data.nb_of_traces
        self._nb_xmps = self._data.nb_of_xmps
        self._has_sensor_contributions = self._data.has_sensor_contributions
        self._sensor_names = self._data.sensor_names
        self._rays = self.__parse_traces()
        self._filtered_rays = []

    @property
    def nb_traces(self) -> int:
        """Number of light paths within LPF data set."""
        return self._nb_traces

    @property
    def nb_xmps(self) -> int:
        """Number of sensors involved within LPF data set."""
        return self._nb_xmps

    @property
    def has_sensor_contributions(self) -> bool:
        """Define if a LPF file contains information regarding the sensor contribution."""
        return self._has_sensor_contributions

    @property
    def sensor_names(self) -> list[str]:
        """List of involved sensor names."""
        return self._sensor_names

    @property
    def rays(self) -> list[RayPath]:
        """List ray paths within LPF file."""
        return self._rays

    @property
    def filtered_rays(self) -> list[RayPath]:
        """List of filtered ray paths."""
        return self._filtered_rays

    def __str__(self):
        """Create string representation of LightPathFinder."""
        return str(
            {
                k: v.fget(self)
                for k, v in LightPathFinder.__dict__.items()
                if isinstance(v, property) and "rays" not in k
            }
        )

    def __open(self, path: str):
        """Open LPF file.

        Parameters
        ----------
        path : str
            Path to file
        """
        self._stub.InitLpfFileName(
            lpf_file_reader__v2__pb2.InitLpfFileName_Request_Mono(lpf_file_uri=path)
        )

    def __parse_traces(self) -> list[RayPath]:
        """Read all ray paths from lpf dataset.

        Returns
        -------
            list[script.RayPath]

        """
        raypaths = []
        for rp in self._stub.Read(lpf_file_reader__v2__pb2.Read_Request_Mono()):
            raypaths.append(RayPath(rp, self._has_sensor_contributions))
        return raypaths

    def __filter_by_last_intersection_types(self, options: list[int], new=True):
        """Filter ray paths based on last intersection types.

        Populate filtered_rays property.
        """
        if new:
            self._filtered_rays = []
            for ray in self._rays:
                if int(ray.intersection_type[-1]) in options:
                    self._filtered_rays.append(ray)
        else:
            temp_rays = self._filtered_rays
            self._filtered_rays = []
            for ray in temp_rays:
                if int(ray.intersection_type[-1]) in options:
                    self._filtered_rays.append(ray)

    def filter_by_face_ids(self, options: list[int], new=True) -> LightPathFinder:
        """Filter ray paths based on face IDs and populates filtered_rays property.

        Parameters
        ----------
        options : list[int]
            List of face IDs.
        new : bool
            Define if a new filter is created or an existing filter is filtered.

        Returns
        -------
        ansys.speos.core.lxp.LightPathFinder
            LightPathFinder Instance.
        """
        if new:
            self._filtered_rays = []
            for ray in self._rays:
                if any([faceid in options for faceid in ray.face_ids]):
                    self._filtered_rays.append(ray)
        else:
            temp_rays = self._filtered_rays
            self._filtered_rays = []
            for ray in temp_rays:
                if any([faceid in options for faceid in ray.face_ids]):
                    self._filtered_rays.append(ray)
        return self

    def filter_by_body_ids(self, options: list[int], new=True) -> LightPathFinder:
        """Filter ray paths based on body IDs and populates filtered_rays property.

        Parameters
        ----------
        options : list[int]
            List of body IDs.
        new : bool
            Define if a new filter is created or an existing filter is filtered.

        Returns
        -------
        ansys.speos.core.lxp.LightPathFinder
            LightPathFinder Instance.
        """
        if new:
            self._filtered_rays = []
            for ray in self._rays:
                if any([body_id in options for body_id in ray.body_ids]):
                    self._filtered_rays.append(ray)
        else:
            temp_rays = self._filtered_rays
            self._filtered_rays = []
            for ray in temp_rays:
                if any([body_id in options for body_id in ray.body_ids]):
                    self._filtered_rays.append(ray)
        return self

    def filter_error_rays(self) -> LightPathFinder:
        """Filter ray paths and only shows rays in error.

        Returns
        -------
        ansys.speos.core.lxp.LightPathFinder
            LightPathFinder Instance.
        """
        self.__filter_by_last_intersection_types(options=ERROR_IDS)
        return self

    def remove_error_rays(self) -> LightPathFinder:
        """Filter rays and only shows rays not in error.

        Returns
        -------
        ansys.speos.core.lxp.LightPathFinder
            LightPathFinder Instance.
        """
        self.__filter_by_last_intersection_types(options=NO_ERROR_IDS)
        return self

    @staticmethod
    @graphics_required
    def __add_ray_to_pv(plotter: Plotter, ray: RayPath, max_ray_length: float):
        """Add a ray to pyvista plotter.

        Parameters
        ----------
        plotter : Plotter
            Ansys plotter object to which rays should be added.
        ray : script.RayPath
            RayPath object which contains ray information to be added.
        max_ray_length : float
            Length of the last ray.
        """
        import pyvista as pv

        temp = ray.impacts.copy()
        if not 7 <= ray.intersection_type[-1] <= 15:
            temp.append(
                [
                    ray.impacts[-1][0] + max_ray_length * ray.last_direction[0],
                    ray.impacts[-1][1] + max_ray_length * ray.last_direction[1],
                    ray.impacts[-1][2] + max_ray_length * ray.last_direction[2],
                ]
            )
        if len(ray.impacts) > 2:
            mesh = pv.MultipleLines(temp)
        else:
            mesh = pv.Line(temp[0], temp[1])
        plotter.plot(mesh, color=wavelength_to_rgb(ray.wl), line_width=2)

    @graphics_required
    def preview(
        self,
        nb_ray: int = 100,
        max_ray_length: float = 50.0,
        ray_filter: bool = False,
        project: Project = None,
        screenshot: Optional[Union[str, Path]] = None,
    ) -> LightPathFinder:
        """Preview LPF file with pyvista.

        Parameters
        ----------
        nb_ray : int
            Number of rays to be visualized.
        max_ray_length : float
            Length of last ray.
        ray_filter : bool
            Boolean to decide if filtered rays or all rays should be shown.
        project : ansys.speos.core.project.Project
            Speos Project/Geometry to be added to pyvista visualisation.
        screenshot : str or Path or ``None``
            Path to save a screenshot of the plotter. If defined Plotter will only create the
            screenshot

        Returns
        -------
        ansys.speos.core.lxp.LightPathFinder
            LightPathFinder Instance.

        Notes
        -----
        Please use the ``q``-key to close the plotter as some
        operating systems (namely Windows) will experience issues
        saving a screenshot if the exit button in the GUI is pressed.
        """
        from ansys.tools.visualization_interface import Plotter

        if ray_filter:
            if len(self._filtered_rays) > 0:
                temp_rays = self._filtered_rays
            else:
                print("no filtered rays")
                temp_rays = self._rays
        else:
            temp_rays = self._rays
        if not project:
            plotter = Plotter()
            if nb_ray > len(temp_rays):
                for ray in temp_rays:
                    self.__add_ray_to_pv(plotter, ray, max_ray_length)
            else:
                for i in range(nb_ray):
                    self.__add_ray_to_pv(plotter, temp_rays[i], max_ray_length)
        else:
            plotter = project._create_preview(viz_args={"opacity": 0.5})
            if nb_ray > len(temp_rays):
                for ray in temp_rays:
                    self.__add_ray_to_pv(plotter, ray, max_ray_length)
            else:
                for i in range(nb_ray):
                    self.__add_ray_to_pv(plotter, temp_rays[i], max_ray_length)
        plotter.show(screenshot=screenshot)
        return self
