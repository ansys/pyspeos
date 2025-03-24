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

"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""

from typing import Iterator, List

from ansys.api.speos.part.v1 import (
    face_pb2 as messages,
    face_pb2_grpc as service,
)
from ansys.speos.core.kernel.crud import CrudItem, CrudStub
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str

ProtoFace = messages.Face
"""Face protobuf class : ansys.api.speos.part.v1.face_pb2.Face"""
ProtoFace.__str__ = lambda self: protobuf_message_to_str(self)


class FaceLink(CrudItem):
    """Link object for job in database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.face.FaceStub
        Database to link to.
    key : str
        Key of the face in the database.
    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the face."""
        return str(self.get())

    def get(self) -> ProtoFace:
        """Get the datamodel from database.

        Returns
        -------
        face.Face
            Face datamodel.
        """
        return self._stub.read(self)

    def set(self, data: ProtoFace) -> None:
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
    >>> speos = Speos(host="localhost", port=50098)
    >>> face_db = speos.client.faces()

    """

    def __init__(self, channel):
        super().__init__(stub=service.FacesManagerStub(channel=channel))
        self._actions_stub = service.FaceActionsStub(channel=channel)

    def create(self, message: ProtoFace) -> FaceLink:
        """Create a new entry.

        Parameters
        ----------
        message : face.Face
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.kernel.face.FaceLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(face=ProtoFace(name="tmp")))

        chunk_iterator = FaceStub._face_to_chunks(
            guid=resp.guid, message=message, nb_items=128 * 1024
        )
        self._actions_stub.Upload(chunk_iterator)

        return FaceLink(self, resp.guid)

    def read(self, ref: FaceLink) -> ProtoFace:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.face.FaceLink
            Link object to read.

        Returns
        -------
        face.Face
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("FaceLink is not on current database")
        chunks = self._actions_stub.Download(request=messages.Download_Request(guid=ref.key))
        return FaceStub._chunks_to_face(chunks)

    def update(self, ref: FaceLink, data: ProtoFace) -> None:
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.face.FaceLink
            Link object to update.

        data : face.Face
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("FaceLink is not on current database")

        CrudStub.update(
            self,
            messages.Update_Request(guid=ref.key, face=ProtoFace(name="tmp")),
        )
        chunk_iterator = FaceStub._face_to_chunks(guid=ref.key, message=data, nb_items=128 * 1024)
        self._actions_stub.Upload(chunk_iterator)

    def delete(self, ref: FaceLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.face.FaceLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("FaceLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[FaceLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.kernel.face.FaceLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: FaceLink(self, x), guids))

    @staticmethod
    def _face_to_chunks(guid: str, message: ProtoFace, nb_items: int) -> Iterator[messages.Chunk]:
        for j in range(4):
            if j == 0:
                chunk_face_header = messages.Chunk(
                    face_header=messages.Chunk.FaceHeader(
                        guid=guid,
                        name=message.name,
                        description=message.description,
                        metadata=message.metadata,
                        sizes=[
                            len(message.vertices),
                            len(message.facets),
                            len(message.texture_coordinates_channels),
                        ],
                    )
                )
                yield chunk_face_header
            elif j == 1:
                for i in range(0, len(message.vertices), nb_items):
                    chunk_vertices = messages.Chunk(
                        vertices=messages.Chunk.Vertices(data=message.vertices[i : i + nb_items])
                    )
                    yield chunk_vertices
            elif j == 2:
                for i in range(0, len(message.facets), nb_items):
                    chunk_facets = messages.Chunk(
                        facets=messages.Chunk.Facets(data=message.facets[i : i + nb_items])
                    )
                    yield chunk_facets
            elif j == 3:
                for i in range(0, len(message.normals), nb_items):
                    chunk_normals = messages.Chunk(
                        normals=messages.Chunk.Normals(data=message.normals[i : i + nb_items])
                    )
                    yield chunk_normals

    @staticmethod
    def _chunks_to_face(chunks: messages.Chunk) -> ProtoFace:
        out_face = ProtoFace()
        for chunk in chunks:
            if chunk.HasField("face_header"):
                out_face.name = chunk.face_header.name
                out_face.description = chunk.face_header.description
                out_face.metadata.update(chunk.face_header.metadata)
            if chunk.HasField("vertices"):
                out_face.vertices.extend(chunk.vertices.data)
            if chunk.HasField("facets"):
                out_face.facets.extend(chunk.facets.data)
            if chunk.HasField("normals"):
                out_face.normals.extend(chunk.normals.data)

        return out_face
