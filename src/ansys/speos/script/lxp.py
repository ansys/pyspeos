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

import ansys.api.speos.lpf.v2.lpf_file_reader_pb2 as lpf_file_reader__v2__pb2
import ansys.api.speos.lpf.v2.lpf_file_reader_pb2_grpc as lpf_file_reader__v2__pb2_grpc
import pyvista as pv

import ansys.speos.core as core
from ansys.speos.script.project import Project

ERROR_IDS = [7, 8, 9, 10, 11, 12, 13, 14, 15]
NO_ERROR_IDS = [0, 1, 2, 3, 4, 5, 6, 16, -7, -6, -5, -5, -4, -3, -2, -1]


class RayPath:
    """
    Framework representing a singular raypath.
    """

    def __init__(self, raypath, sensor_contribution=False):
        self._nb_impacts = len(raypath.impacts)
        self._impacts = [[inter.x, inter.y, inter.z] for inter in raypath.impacts]
        self._wl = raypath.wavelengths[0]
        self._body_ids = raypath.body_context_ids
        self._face_ids = raypath.unique_face_ids
        self._last_direction = [raypath.lastDirection.x, raypath.lastDirection.y, raypath.lastDirection.z]
        self._intersection_type = raypath.interaction_statuses
        if sensor_contribution:
            self._sensor_contribution = [
                {"sensor_id": sc.sensor_id, "position": [sc.coordinates.x, sc.coordinates.y]} for sc in raypath.sensor_contributions
            ]
        else:
            self._sensor_contribution = None

    @property
    def nb_impacts(self):
        return self._nb_impacts

    @property
    def impacts(self):
        return self._impacts

    @property
    def wl(self):
        return self._wl

    @property
    def body_ids(self):
        return self._body_ids

    @property
    def face_ids(self):
        return self._face_ids

    @property
    def last_direction(self):
        return self._last_direction

    @property
    def intersection_type(self):
        return self._intersection_type

    @property
    def sensor_contribution(self):
        return self._sensor_contribution

    def get(self, key=""):
        data = {k: v.fget(self) for k, v in RayPath.__dict__.items() if isinstance(v, property)}
        if key == "":
            return data
        elif data.get(key):
            return data.get(key)
        else:
            print("Used key: {} not found in key list: {}.".format(key, data.keys()))

    def __str__(self):
        return str(self.get())


class LightPathFinder:
    """
    The Lightpathfinder defines n interface to reas lpf files. These files contain a set of simulated rays with all
    there intersections and properties.

    Parameters
    ----------
    speos : core.Speos
    path : str
        path to lpf file to be opened

    """

    def __init__(self, speos: core.Speos, path: str):
        self.client = speos.client
        self._stub = lpf_file_reader__v2__pb2_grpc.LpfFileReader_MonoStub(self.client.channel)
        self.__open(path)
        self._data = self._stub.GetInformation(lpf_file_reader__v2__pb2.GetInformation_Request_Mono())
        self._nb_traces = self._data.nb_of_traces
        self._nb_xmps = self._data.nb_of_xmps
        self._has_sensor_contributions = self._data.has_sensor_contributions
        self._sensor_names = self._data.sensor_names
        self._rays = self.__parse_traces()
        self._filtered_rays = []

    @property
    def nb_traces(self) -> int:
        """Number of light path's within LPF data set"""
        return self._nb_traces

    @property
    def nb_xmps(self) -> int:
        """Number of sensors involved within LPF data set"""
        return self._nb_xmps

    @property
    def has_sensor_contributions(self) -> bool:
        """Sensor contribution, including coordinates"""
        return self._has_sensor_contributions

    @property
    def sensor_names(self) -> list[str]:
        """list of involved sensor names"""
        return self._sensor_names

    @property
    def rays(self) -> list[RayPath]:
        """list raypath's within lpf file"""
        return self._rays

    @property
    def filtered_rays(self) -> list[RayPath]:
        """list of filtered ray path's"""
        return self._filtered_rays

    def __str__(self):
        return str({k: v.fget(self) for k, v in LightPathFinder.__dict__.items() if isinstance(v, property) and "rays" not in k})

    def __open(self, path: str):
        """
        method to open lpf file
        Parameters
        ----------
        path : str
            Path to file
        """
        self._stub.InitLpfFileName(lpf_file_reader__v2__pb2.InitLpfFileName_Request_Mono(lpf_file_uri=path))

    def __parse_traces(self) -> list[RayPath]:
        """
        Reads all raypathes from lpf dataset
        Returns
        -------
            list[script.RayPath]

        """
        raypaths = []
        for rp in self._stub.Read(lpf_file_reader__v2__pb2.Read_Request_Mono()):
            raypaths.append(RayPath(rp, self._has_sensor_contributions))
        return raypaths

    def __filter_by_last_intersection_types(self, options: list[int], new=True):
        """filters raypathes based on last intersection types and populates filtered_rays property"""
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

    def filter_by_face_ids(self, options: list[int], new=True):
        """filters raypathes based on face ids and populates filtered_rays property

        Parameters
        ----------
        options : list[int]
         list of face ids
        new : bool
            defines if new filter is created or existing filter is filtered


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

    def filter_by_body_ids(self, options: list[int], new=True):
        """filters raypathes based on body ids and populates filtered_rays property

        Parameters
        ----------
        options : list[int]
            list of body ids
        new : bool
            defines if new filter is created or existing filter is filtered
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

    def filter_error_rays(self):
        """filters rays and only shows rays in error"""
        self.__filter_by_last_intersection_types(options=ERROR_IDS)

    def remove_error_rays(self):
        """filters rays and only shows rays not in error"""
        self.__filter_by_last_intersection_types(options=NO_ERROR_IDS)

    @staticmethod
    def __add_ray_to_pv(plotter: pv.Plotter, ray: RayPath, max_ray_length: float):
        """
        add a ray to pyvista plotter
        Parameters
        ----------
        plotter : pv.Plotter
            pyvista plotter object to which rays should be added
        ray : script.RayPath
            RayPath object which contains rayinformation to be added
        max_ray_length : float
            length of the last ray
        """
        temp = ray.impacts
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
        plotter.add_mesh(mesh, color=wavelength_to_rgb(ray.wl), line_width=2)

    def preview(self, nb_ray: int = 100, max_ray_length: float = 50.0, ray_filter: bool = False, project: Project = None):
        """
        method to preview lpf file with pyvista

        Parameters
        ----------
        nb_ray : int
            number of rays to be visualized
        max_ray_length : float
            length of last ray
        ray_filter : bool
            boolean to decide if filtered rays or all rays should be shown
        project : script.Project
            Speos Project/Geometry to be added to pyvista visualisation
        """
        if ray_filter:
            if len(self._filtered_rays) > 0:
                temp_rays = self._filtered_rays
            else:
                temp_rays = self._rays
        else:
            temp_rays = self._rays
        if not project:
            plotter = pv.Plotter()
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
        plotter.show()


def wavelength_to_rgb(wavelength: float, gamma: float = 0.8) -> [int, int, int, int]:
    """This converts a given wavelength of light to an
    approximate RGB color value. The wavelength must be given
    in nanometers in the range from 380 nm through 750 nm
    (789 THz through 400 THz).
    Based on code by Dan Bruton
    http://www.physics.sfasu.edu/astro/color/spectra.html
    """

    wavelength = float(wavelength)
    if wavelength >= 380 and wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        G = 0.0
        B = (1.0 * attenuation) ** gamma
    elif wavelength >= 440 and wavelength <= 490:
        R = 0.0
        G = ((wavelength - 440) / (490 - 440)) ** gamma
        B = 1.0
    elif wavelength >= 490 and wavelength <= 510:
        R = 0.0
        G = 1.0
        B = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif wavelength >= 510 and wavelength <= 580:
        R = ((wavelength - 510) / (580 - 510)) ** gamma
        G = 1.0
        B = 0.0
    elif wavelength >= 580 and wavelength <= 645:
        R = 1.0
        G = (-(wavelength - 645) / (645 - 580)) ** gamma
        B = 0.0
    elif wavelength >= 645 and wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = (1.0 * attenuation) ** gamma
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0
    R *= 255
    G *= 255
    B *= 255
    return [int(R), int(G), int(B), 255]
