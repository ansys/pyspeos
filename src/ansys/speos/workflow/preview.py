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
"""Provides a way to preview the geometry of a project feature (of script layer)."""
from google.protobuf.internal.containers import RepeatedScalarFieldContainer
import numpy as np
import pyvista as pv

import ansys.speos.core as core
from ansys.speos.script.project import Project


def __extract_part_mesh_info(
    speos_client: core.SpeosClient, part_data: core.Part, part_coordinate_info: RepeatedScalarFieldContainer = None
) -> pv.PolyData:
    """
    extract mesh data info from a part.

    Parameters
    ----------
    speos_client : ansys.speos.core.client.SpeosClient
        The Speos instance client.
    part_data: ansys.api.speos.part.v1.part_pb2.Part
        Part from scene.
    part_coordinate_info: RepeatedScalarFieldContainer
        message contains part coordinate info: origin, x_vector, y_vector, z_vector

    Returns
    -------
    pv.PolyData
        mesh data extracted.
    """

    def local2absolute(local_vertice: np.ndarray) -> np.ndarray:
        """
        convert local coordinate to global coordinate.

        Parameters
        ----------
        local_vertice: np.ndarray
            numpy array includes x, y, z info.

        Returns
        -------
        np.ndarray
            numpy array includes x, y, z info

        """
        global_origin = np.array(part_coordinate.origin)
        global_x = np.array(part_coordinate.x_vect) * local_vertice[0]
        global_y = np.array(part_coordinate.y_vect) * local_vertice[1]
        global_z = np.array(part_coordinate.z_vect) * local_vertice[2]
        return global_origin + global_x + global_y + global_z

    part_coordinate = core.AxisSystem()
    part_coordinate.origin = [0.0, 0.0, 0.0]
    part_coordinate.x_vect = [1.0, 0.0, 0.0]
    part_coordinate.y_vect = [0.0, 1.0, 0.0]
    part_coordinate.z_vect = [0.0, 0.0, 1.0]
    if part_coordinate_info is not None:
        part_coordinate.origin = part_coordinate_info[:3]
        part_coordinate.x_vect = part_coordinate_info[3:6]
        part_coordinate.y_vect = part_coordinate_info[6:9]
        part_coordinate.z_vect = part_coordinate_info[9:]
    part_mesh_info = None
    for body_idx, body_guid in enumerate(part_data.body_guids):
        body_item_data = speos_client.get_item(body_guid).get()
        for face_idx, face_guid in enumerate(body_item_data.face_guids):
            face_item_data = speos_client.get_item(face_guid).get()
            vertices = np.array(face_item_data.vertices)
            facets = np.array(face_item_data.facets)
            vertices = vertices.reshape(-1, 3)
            vertices = np.array([local2absolute(vertice) for vertice in vertices])
            facets = facets.reshape(-1, 3)
            temp = np.full(facets.shape[0], 3)
            temp = np.vstack(temp)
            facets = np.hstack((temp, facets))
            face_mesh_data = pv.PolyData(vertices, facets)
            if part_mesh_info is None:
                part_mesh_info = face_mesh_data
            else:
                part_mesh_info = part_mesh_info.append_polydata(face_mesh_data)
    return part_mesh_info


def preview(project: Project) -> None:
    """Preview cad bodies inside the project's scene.

    Parameters
    ----------
    project : ansys.speos.script.project.Project
        Project to preview.
    """
    _preview_mesh = pv.PolyData()

    # Retrieve root part
    root_part_data = project.client.get_item(project.scene_link.get().part_guid).get()

    # Loop on all sub parts to retrieve their mesh
    if len(root_part_data.parts) != 0:
        for part_idx, part_item in enumerate(root_part_data.parts):
            part_item_data = project.client.get_item(part_item.part_guid).get()
            poly_data = __extract_part_mesh_info(
                speos_client=project.client, part_data=part_item_data, part_coordinate_info=part_item.axis_system
            )
            if poly_data is not None:
                _preview_mesh = _preview_mesh.append_polydata(poly_data)

    # Add also the mesh of bodies directly contained in root part
    poly_data = __extract_part_mesh_info(speos_client=project.client, part_data=root_part_data)
    if poly_data is not None:
        _preview_mesh = _preview_mesh.append_polydata(poly_data)

    p = pv.Plotter()
    p.add_mesh(_preview_mesh, show_edges=True)
    p.show()
