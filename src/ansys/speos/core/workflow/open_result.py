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
from typing import Union

import ansys.api.speos.file.v1.file_transfer as file_transfer_helper__v1
import ansys.api.speos.file.v1.file_transfer_pb2_grpc as file_transfer__v1__pb2_grpc

if os.name == "nt":
    from comtypes.client import CreateObject

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from numpy import ndarray

from ansys.speos.core.simulation import (
    SimulationDirect,
    SimulationInteractive,
    SimulationInverse,
)


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


def _display_image(img: ndarray):
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
