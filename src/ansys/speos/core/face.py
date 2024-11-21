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
from typing import Iterator, List, Mapping, Optional

from ansys.api.speos.part.v1 import face_pb2 as messages
from ansys.api.speos.part.v1 import face_pb2_grpc as service
import numpy as np

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.geometry_utils import AxisPlane
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

Face = messages.Face
"""Face protobuf class : ansys.api.speos.part.v1.face_pb2.Face"""
Face.__str__ = lambda self: protobuf_message_to_str(self)


class FaceLink(CrudItem):
    """Link object for job in database.

    Parameters
    ----------
    db : ansys.speos.core.face.FaceStub
        Database to link to.
    key : str
        Key of the face in the database.
    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the face."""
        return str(self.get())

    def get(self) -> Face:
        """Get the datamodel from database.

        Returns
        -------
        face.Face
            Face datamodel.
        """
        return self._stub.read(self)

    def set(self, data: Face) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : face.Face
            New Face datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class FaceStub(CrudStub):
    """
    Database interactions for face.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a FaceStub is to retrieve it from SpeosClient via faces() method.
    Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> face_db = speos.client.faces()

    """

    def __init__(self, channel):
        super().__init__(stub=service.FacesManagerStub(channel=channel))
        self._actions_stub = service.FaceActionsStub(channel=channel)

    def create_batch(self, message_list: List[Face]) -> List[FaceLink]:
        """Create new entries.

        Parameters
        ----------
        message_list : List[face.Face]
            List of datamodels for the new entries.

        Returns
        -------
        List[ansys.speos.core.face.FaceLink]
            List pf link objects created.
        """
        guids = [CrudStub.create(self, messages.Create_Request(face=Face(name="tmp"))).guid for m in message_list]

        chunk_iterator = FaceStub._faces_to_chunks(guids=guids, message_list=message_list, nb_items=128 * 1024)
        self._actions_stub.Upload(chunk_iterator)

        return [FaceLink(self, guid) for guid in guids]

    def create(self, message: Face) -> FaceLink:
        """Create a new entry.

        Parameters
        ----------
        message : face.Face
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.face.FaceLink
            Link object created.
        """
        return self.create_batch(message_list=[message])[0]

    def read_batch(self, refs: List[FaceLink]) -> List[Face]:
        """Get existing entries.

        Parameters
        ----------
        refs : List[ansys.speos.core.face.FaceLink]
            List of link objects to read.

        Returns
        -------
        List[face.Face]
            Datamodels of the entries.
        """
        for ref in refs:
            if not ref.stub == self:
                raise ValueError("FaceLink is not on current database. Key=" + ref.key)
        chunks = self._actions_stub.Download(request=messages.Download_Request(guids=[ref.key for ref in refs]))
        return FaceStub._chunks_to_faces(chunks)

    def read(self, ref: FaceLink) -> Face:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.face.FaceLink
            Link object to read.

        Returns
        -------
        face.Face
            Datamodel of the entry.
        """
        return self.read_batch(refs=[ref])[0]

    def update(self, ref: FaceLink, data: Face) -> None:
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.face.FaceLink
            Link object to update.

        data : face.Face
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("FaceLink is not on current database")

        CrudStub.update(self, messages.Update_Request(guid=ref.key, face=Face(name="tmp")))
        chunk_iterator = FaceStub._face_to_chunks(guid=ref.key, message=data, nb_items=128 * 1024)
        self._actions_stub.Upload(chunk_iterator)

    def delete(self, ref: FaceLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.face.FaceLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("FaceLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[FaceLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.face.FaceLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: FaceLink(self, x), guids))

    @staticmethod
    def _faces_to_chunks(guids: List[str], message_list: List[Face], nb_items: int) -> Iterator[messages.Chunk]:
        for guid, message in zip(guids, message_list):
            for j in range(4):
                if j == 0:
                    chunk_face_header = messages.Chunk(
                        face_header=messages.Chunk.FaceHeader(
                            guid=guid,
                            name=message.name,
                            description=message.description,
                            metadata=message.metadata,
                            sizes=[len(message.vertices), len(message.facets), len(message.texture_coordinates_channels)],
                        )
                    )
                    yield chunk_face_header
                elif j == 1:
                    for i in range(0, len(message.vertices), nb_items):
                        chunk_vertices = messages.Chunk(vertices=messages.Chunk.Vertices(data=message.vertices[i : i + nb_items]))
                        yield chunk_vertices
                elif j == 2:
                    for i in range(0, len(message.facets), nb_items):
                        chunk_facets = messages.Chunk(facets=messages.Chunk.Facets(data=message.facets[i : i + nb_items]))
                        yield chunk_facets
                elif j == 3:
                    for i in range(0, len(message.normals), nb_items):
                        chunk_normals = messages.Chunk(normals=messages.Chunk.Normals(data=message.normals[i : i + nb_items]))
                        yield chunk_normals

    @staticmethod
    def _chunks_to_faces(chunks: messages.Chunk) -> List[Face]:
        out_faces = []
        out_face = Face()
        for chunk in chunks:
            if chunk.HasField("face_header"):
                if out_face != Face():  # Add face each time a new one starts
                    out_faces.append(out_face)
                    out_face = Face()
                out_face.name = chunk.face_header.name
                out_face.description = chunk.face_header.description
                out_face.metadata.update(chunk.face_header.metadata)
            if chunk.HasField("vertices"):
                out_face.vertices.extend(chunk.vertices.data)
            if chunk.HasField("facets"):
                out_face.facets.extend(chunk.facets.data)
            if chunk.HasField("normals"):
                out_face.normals.extend(chunk.normals.data)

        out_faces.append(out_face)  # Don't forget to add last face
        return out_faces


class FaceFactory:
    """Class to help creating Face message"""

    @staticmethod
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
        face.Face
            Face message created.
        """
        face = Face(name=name, description=description, vertices=vertices, facets=facets, normals=normals)
        if metadata is not None:
            face.metadata.update(metadata)
        return face

    @staticmethod
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
        face.Face
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
