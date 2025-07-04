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
"""Open one of the possible results generated out of the simulation."""

import os
from pathlib import Path
import tempfile
from typing import List, Union

import ansys.api.speos.file.v1.file_transfer as file_transfer_helper__v1
import ansys.api.speos.file.v1.file_transfer_pb2_grpc as file_transfer__v1__pb2_grpc
from ansys.api.speos.part.v1 import face_pb2

if os.name == "nt":
    from comtypes.client import CreateObject


import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy

from ansys.speos.core.simulation import (
    SimulationDirect,
    SimulationInteractive,
    SimulationInverse,
)


class _Speos3dData:
    def __init__(
        self,
        x,
        y,
        z,
        illuminance=0.0,
        irradiance=0.0,
        reflection=0.0,
        transmission=0.0,
        absorption=0.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.illuminance = float(illuminance)
        self.irradiance = float(irradiance)
        self.reflection = float(reflection)
        self.transmission = float(transmission)
        self.absorption = float(absorption)


def _find_correct_result(
    simulation_feature: Union[SimulationDirect, SimulationInverse, SimulationInteractive],
    result_name: str,
    download_if_distant: bool = True,
) -> str:
    if len(simulation_feature.result_list) == 0:
        raise ValueError("Please compute the simulation feature to generate results.")

    file_path = ""

    for res in simulation_feature.result_list:
        if res.HasField("path"):
            if res.path.endswith(result_name):
                file_path = res.path
                break
        elif res.HasField("upload_response"):
            if res.upload_response.info.file_name == result_name:
                if download_if_distant:
                    file_transfer_helper__v1.download_file(
                        file_transfer_service_stub=file_transfer__v1__pb2_grpc.FileTransferServiceStub(
                            simulation_feature._project.client.channel
                        ),
                        file_uri=res.upload_response.info.uri,
                        download_location=tempfile.gettempdir(),
                    )
                    file_path = str(
                        Path(tempfile.gettempdir()) / res.upload_response.info.file_name
                    )
                else:
                    file_path = res.upload_response.info.uri
                break
    return file_path


def _display_image(img: numpy.ndarray):
    if img is not None:
        plt.imshow(img)
        plt.axis("off")  # turns off axes
        plt.axis("tight")  # gets rid of white border
        plt.axis("image")  # square up the image instead of filling the "figure" space
        plt.show()


if os.name == "nt":

    def open_result_image(
        simulation_feature: Union[SimulationDirect, SimulationInverse, SimulationInteractive],
        result_name: str,
    ) -> None:
        """Retrieve an image from a specific simulation result.

        Parameters
        ----------
        simulation_feature : ansys.speos.core.simulation.Simulation
            The simulation feature.
        result_name : str
            The result name to open as an image.
        """
        file_path = _find_correct_result(simulation_feature, result_name)
        if file_path == "":
            raise ValueError(
                "No result corresponding to "
                + result_name
                + " is found in "
                + simulation_feature._name
            )

        if file_path.endswith("xmp") or file_path.endswith("XMP"):
            dpf_instance = CreateObject("XMPViewer.Application")
            dpf_instance.OpenFile(file_path)
            res = dpf_instance.ExportXMPImage(file_path + ".png", 1)
            if res:
                _display_image(mpimg.imread(file_path + ".png"))
        elif file_path.endswith("png") or file_path.endswith("PNG"):
            _display_image(mpimg.imread(file_path))

    def open_result_in_viewer(
        simulation_feature: Union[SimulationDirect, SimulationInverse],
        result_name: str,
    ) -> None:
        """Open a specific simulation result in the suitable viewer.

        Parameters
        ----------
        simulation_feature : ansys.speos.core.simulation.Simulation
            The simulation feature.
        result_name : str
            The result name to open in a viewer.
        """
        file_path = _find_correct_result(simulation_feature, result_name)

        if file_path.endswith("xmp") or file_path.endswith("XMP"):
            dpf_instance = CreateObject("XMPViewer.Application")
            dpf_instance.OpenFile(file_path)
            dpf_instance.Show(1)
        elif file_path.endswith("hdr") or file_path.endswith("HDR"):
            dpf_instance = CreateObject("HDRIViewer.Application")
            dpf_instance.OpenFile(file_path)
            dpf_instance.Show(1)

    def export_xmp_vtp(
        simulation_feature: Union[SimulationDirect, SimulationInverse],
        result_name: Union[str, Path],
    ) -> Path:
        """Export an XMP result into vtp file.

        Parameters
        ----------
        simulation_feature : ansys.speos.core.simulation.Simulation
            The simulation feature.
        result_name: Union[str, Path]
            file path of an XMP result.

        Returns
        -------
        Path
            file path of exported vtp file.

        """
        import pyvista as pv

        result_name = Path(result_name)
        if not str(result_name).lower().endswith(".xmp"):
            result_name = result_name.with_name(result_name.name + ".xmp")
        file_path = _find_correct_result(simulation_feature, str(result_name))

        if file_path == "":
            raise ValueError(
                "No result corresponding to "
                + str(result_name)
                + " is found in "
                + simulation_feature._name
            )

        file_path = Path(file_path)
        dpf_instance = CreateObject("XMPViewer.Application")
        dpf_instance.OpenFile(str(file_path))
        dimension_x = dpf_instance.XWidth
        dimension_y = dpf_instance.YHeight
        resolution_x = dpf_instance.XNb
        resolution_y = dpf_instance.YNb
        tmp_txt = file_path.with_suffix(".txt")
        dpf_instance.ExportTXT(str(tmp_txt))

        file = tmp_txt.open("r")
        content = file.readlines()
        file.close()
        skip_lines = 9 if "SeparatedByLayer" in content[7] else 8
        xmp_data = []
        if dpf_instance.Maptype == 2 and len(content[6].strip().split()) == 3:
            # spectral data within number of data tables
            spectral_tables = int(content[6].strip().split()[2])
            xmp_data = [
                [0 for _ in range(len(content[skip_lines].strip().split()))]
                for _ in range(resolution_y)
            ]
            for _ in range(spectral_tables):
                for i in range(resolution_y):
                    row = list(map(float, content[skip_lines].strip().split()))
                    for j in range(resolution_x):
                        xmp_data[i][j] += row[j]
                    skip_lines += 1
                # Skip one line between tables
                skip_lines += 1
        else:
            # not spectral data
            for line in content[skip_lines : skip_lines + resolution_y]:
                line_content = line.strip().split()
                xmp_data.append(list(map(float, line_content)))

        # Create VTK ImageData structure
        step_x = float(dimension_x) / resolution_x
        step_y = float(dimension_y) / resolution_y
        origin_x = -(resolution_x * step_x) / 2
        origin_y = -(resolution_y * step_y) / 2
        grid = pv.ImageData(
            dimensions=(resolution_x, resolution_y, 1),
            spacing=(step_x, step_y, 1),
            origin=(origin_x, origin_y, 0),
        )
        xmp_data = numpy.array(xmp_data)
        if xmp_data.shape[1] == resolution_x:
            if dpf_instance.UnitType == 0:
                grid["Radiometric"] = numpy.ravel(xmp_data)
            if dpf_instance.UnitType == 1:
                grid["Photometric"] = numpy.ravel(xmp_data)
        else:
            grid["X"] = numpy.ravel(xmp_data[:, 0::4])
            grid["Photometric"] = numpy.ravel(xmp_data[:, 1::4])
            grid["Radiometric"] = numpy.ravel(xmp_data[:, 2::4])
            grid["Z"] = numpy.ravel(xmp_data[:, 3::4])
        vtp_meshes = grid.extract_surface()
        # Export file to VTP
        vtp_meshes.save(str(file_path.with_suffix(".vtp")))
        return file_path.with_suffix(".vtp")

    def export_xm3_vtp(
        simulation_feature: Union[SimulationDirect, SimulationInverse],
        geo_faces: List[face_pb2.Face],
        result_name: Union[str, Path],
    ) -> Path:
        """Export an XMP result into vtp file.

        Parameters
        ----------
        simulation_feature : ansys.speos.core.simulation.Simulation
            The simulation feature.
        geo_faces: List[face_pb2.Face]
            list of face geometries.
        result_name: Union[str, Path]
            file path of an XMP result.

        Returns
        -------
        Path
            file path of exported vtp file.

        """
        import pyvista as pv

        result_name = Path(result_name)
        if not str(result_name).lower().endswith(".xm3"):
            result_name = result_name.with_name(result_name.name + ".xm3")
        file_path = _find_correct_result(simulation_feature, str(result_name))

        if file_path == "":
            raise ValueError(
                "No result corresponding to "
                + str(result_name)
                + " is found in "
                + simulation_feature._name
            )

        file_path = Path(file_path)
        dpf_instance = CreateObject("Xm3Viewer.Application")
        dpf_instance.OpenFile(str(file_path))
        tmp_txt = file_path.with_suffix(".txt")
        dpf_instance.Export(str(tmp_txt))

        file = tmp_txt.open("r")
        xm3_data = []
        content = file.readlines()
        header = content[0].strip().split("\t")
        illuminance_indices = [
            i for i, header_item in enumerate(header) if header_item == "Illuminance"
        ]
        irradiance_indices = [
            i for i, header_item in enumerate(header) if header_item == "Irradiance"
        ]
        reflection_indices = [
            i for i, header_item in enumerate(header) if "Reflection" in header_item
        ]
        transmission_indices = [
            i for i, header_item in enumerate(header) if "Transmission" in header_item
        ]
        absorption_indices = [
            i for i, header_item in enumerate(header) if "Absorption" in header_item
        ]

        skip_line = 1
        try:
            float(float(content[1].strip().split()[0]))
            skip_line = 1  # only single layer
        except ValueError:
            skip_line = 2  # separated layer
        for line in content[skip_line:]:
            line_content = line.strip().split("\t")
            xm3_data.append(
                _Speos3dData(
                    x=float(line_content[0]),
                    y=float(line_content[1]),
                    z=float(line_content[2]),
                    illuminance=sum(
                        [
                            float(item)
                            for i, item in enumerate(line_content)
                            if i in illuminance_indices
                        ],
                        0.0,
                    ),
                    irradiance=sum(
                        [
                            float(item)
                            for i, item in enumerate(line_content)
                            if i in irradiance_indices
                        ],
                        0.0,
                    ),
                    reflection=sum(
                        [
                            float(item)
                            for i, item in enumerate(line_content)
                            if i in reflection_indices
                        ],
                        0.0,
                    ),
                    transmission=sum(
                        [
                            float(item)
                            for i, item in enumerate(line_content)
                            if i in transmission_indices
                        ],
                        0.0,
                    ),
                    absorption=sum(
                        [
                            float(item)
                            for i, item in enumerate(line_content)
                            if i in absorption_indices
                        ],
                        0.0,
                    ),
                )
            )

        vtp_meshes = None
        for geo in geo_faces:
            vertices = numpy.array(geo.vertices).reshape(-1, 3)
            facets = numpy.array(geo.facets).reshape(-1, 3)
            temp = numpy.full(facets.shape[0], 3)
            temp = numpy.vstack(temp)
            facets = numpy.hstack((temp, facets))
            if vtp_meshes is None:
                vtp_meshes = pv.PolyData(vertices, facets)
            else:
                vtp_meshes = vtp_meshes.append_polydata(pv.PolyData(vertices, facets))

        vtp_meshes["Illuminance [lx]"] = [item.illuminance for item in xm3_data]
        vtp_meshes["Irradiance [W/m2]"] = [item.irradiance for item in xm3_data]
        vtp_meshes["Reflection"] = [item.reflection for item in xm3_data]
        vtp_meshes["Transmission"] = [item.transmission for item in xm3_data]
        vtp_meshes["Absorption"] = [item.absorption for item in xm3_data]
        # vtp_meshes = vtp_meshes.point_data_to_cell_data()
        vtp_meshes.save(str(file_path.with_suffix(".vtp")))
        return file_path.with_suffix(".vtp")
