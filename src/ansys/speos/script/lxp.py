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


class LightPathFinder:
    def __init__(self, speos: core.Speos, path: str):
        self.client = speos.client
        self._stub = lpf_file_reader__v2__pb2_grpc.LpfFileReader_MonoStub(self.client.channel)
        self.open(path)
        self._data = self._stub.GetInformation(lpf_file_reader__v2__pb2.GetInformation_Request_Mono())
        self.nb_traces = self._data.nb_of_traces
        self.nb_xmps = self._data.nb_of_xmps
        self.contributions = self._data.has_sensor_contributions
        self.sensor_names = self._data.sensor_names
        self.rays = self.__parse_traces()
        self.filtered_rays = None

    def open(self, path: str):
        self._stub.InitLpfFileName(lpf_file_reader__v2__pb2.InitLpfFileName_Request_Mono(lpf_file_uri=path))

    def __parse_traces(self):
        raypaths = []
        for rp in self._stub.Read(lpf_file_reader__v2__pb2.Read_Request_Mono()):
            raypaths.append(RayPath(rp))
        return raypaths

    def preview(self, nb_ray=100, max_ray_length=50, filter: bool = False, project: Project = None):
        if not project:
            plotter = pv.Plotter()
            if nb_ray > len(self.rays):
                for ray in self.rays:
                    temp = ray.impacts
                    if not 7 <= ray.intersectiontype[-1] <= 15:
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
            else:
                for i in range(nb_ray):
                    ray = self.rays[i]
                    temp = ray.impacts
                    if not 7 <= ray.intersectiontype[-1] <= 15:
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
        else:
            plotter = project._create_preview(viz_args={"opacity": 0.5})
            if nb_ray > len(self.rays):
                for ray in self.rays:
                    temp = ray.impacts
                    if not 7 <= ray.intersectiontype[-1] <= 15:
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
            else:
                for i in range(nb_ray):
                    ray = self.rays[i]
                    temp = ray.impacts
                    if not 7 <= ray.intersectiontype[-1] <= 15:
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
        plotter.show()

    def show_error_rays(self, nb_ray=100, project: Project = None):
        n, i = 0, 0
        if not project:
            plotter = pv.Plotter()
            while i < nb_ray:
                n += 1
                if n > len(self.rays):
                    break
                ray = self.rays[n]
                temp = ray.impacts
                if 7 <= ray.intersectiontype[-1] <= 15:
                    if len(ray.impacts) > 2:
                        mesh = pv.MultipleLines(temp)
                    else:
                        mesh = pv.Line(temp[0], temp[1])
                    plotter.add_mesh(mesh, color=wavelength_to_rgb(ray.wl), line_width=2)
                    i += 1
        else:
            plotter = project._create_preview(viz_args={"opacity": 0.5})
            while i < nb_ray:
                n += 1
                if (n + 1) > len(self.rays):
                    break
                ray = self.rays[n]
                temp = ray.impacts
                if 7 <= ray.intersectiontype[-1] <= 15:
                    if len(ray.impacts) > 2:
                        mesh = pv.MultipleLines(temp)
                    else:
                        mesh = pv.Line(temp[0], temp[1])
                    plotter.add_mesh(mesh, color=wavelength_to_rgb(ray.wl), line_width=2)
                    i += 1

        plotter.show()


class RayPath:
    def __init__(self, raypath):
        self.nb_impacts = len(raypath.impacts)
        self.impacts = [[inter.x, inter.y, inter.z] for inter in raypath.impacts]
        self.wl = raypath.wavelengths[0]
        self.body_ids = raypath.body_context_ids
        self.face_ids = raypath.unique_face_ids
        self.last_direction = [raypath.lastDirection.x, raypath.lastDirection.y, raypath.lastDirection.z]
        self.intersectiontype = raypath.interaction_statuses


def wavelength_to_rgb(wavelength, gamma=0.8):
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
