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

"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import List, Mapping, Optional

from ansys.api.speos.part.v1 import face_pb2 as messages
from ansys.api.speos.part.v1 import face_pb2_grpc as service
import numpy as np

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.geometry_utils import AxisPlane
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

Face = messages.Face
Face.__str__ = lambda self: protobuf_message_to_str(self)


class FaceLink(CrudItem):
    """Link object for job in database."""

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return str(self.get())

    def get(self) -> Face:
        """Get the datamodel from database."""
        return self._stub.read(self)

    def set(self, data: Face) -> None:
        """Change datamodel in database."""
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class FaceStub(CrudStub):
    """
    Database interactions for face.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> face_db = speos.client.faces()

    """

    def __init__(self, channel):
        super().__init__(stub=service.FacesManagerStub(channel=channel))

    def create(self, message: Face) -> FaceLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(face=message))
        return FaceLink(self, resp.guid)

    def read(self, ref: FaceLink) -> Face:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("FaceLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.face

    def update(self, ref: FaceLink, data: Face):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("FaceLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, face=data))

    def delete(self, ref: FaceLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("FaceLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[FaceLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: FaceLink(self, x), guids))


class FaceFactory:
    """Class to help creating Face message"""

    def new(
        name: str,
        vertices: List[float],
        facets: List[int],
        normals: List[float],
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Face:
        """
        Create a Face message.

        Parameters
        ----------
        name : str
            Name of the face.
        vertices : List[float]
            Coordinates of all points [p1x, p1y, p1z, p2x, p2y, p2z, ...].
        facets : List[int]
            Indexes of points for all triangles [t1_1, t1_2, t1_3, t2_1, t2_2, t2_3, ...].
        normals: List[float],
            Normal vector for all points [n1x, n1y, n1z, n2x, n2y, n2z, ...].
        description : str, optional
            Description of the face.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the face.
            By default, ``None``.

        Returns
        -------
        Face
            Face message created.
        """
        face = Face(name=name, description=description, vertices=vertices, facets=facets, normals=normals)
        if metadata is not None:
            face.metadata.update(metadata)
        return face

    def rectangle(
        name: str,
        description: Optional[str] = "",
        base: Optional[AxisPlane] = AxisPlane(),
        x_size: Optional[float] = 200,
        y_size: Optional[float] = 100,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Face:
        """
        Create a specific face: a rectangle.

        Parameters
        ----------
        name : str
            Name of the face.
        description : str, optional
            Description of the face.
            By default, ``""``.
        base : ansys.speos.core.geometry_utils.AxisPlane
            Center and orientation of the rectangle.
            By default, ``ansys.speos.core.geometry_utils.AxisPlane()``.
        x_size : float, optional
            size regarding x axis.
            By default, ``200``.
        y_size : float, optional
            size regarding y axis.
            By default, ``100``.
        metadata : Mapping[str, str], optional
            Metadata of the face.
            By default, ``None``.

        Returns
        -------
        Face
            Face message created.
        """
        face = Face(name=name, description=description)
        if metadata is not None:
            face.metadata.update(metadata)

        face.vertices.extend(base.origin - np.multiply(0.5 * x_size, base.x_vect) - np.multiply(0.5 * y_size, base.y_vect))
        face.vertices.extend(base.origin + np.multiply(0.5 * x_size, base.x_vect) - np.multiply(0.5 * y_size, base.y_vect))
        face.vertices.extend(base.origin + np.multiply(0.5 * x_size, base.x_vect) + np.multiply(0.5 * y_size, base.y_vect))
        face.vertices.extend(base.origin - np.multiply(0.5 * x_size, base.x_vect) + np.multiply(0.5 * y_size, base.y_vect))

        normal = np.cross(base.x_vect, base.y_vect)
        for i in range(4):
            face.normals.extend(normal)

        face.facets.extend([0, 1, 3, 1, 2, 3])

        return face
