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

from ansys.api.speos.part.v1 import body_pb2 as messages
from ansys.api.speos.part.v1 import body_pb2_grpc as service
import numpy as np

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.face import FaceFactory, FaceLink, FaceStub
from ansys.speos.core.geometry_utils import AxisPlane, AxisSystem
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

Body = messages.Body
"""Body protobuf class : ansys.api.speos.part.v1.body_pb2.Body"""
Body.__str__ = lambda self: protobuf_message_to_str(self)


class BodyLink(CrudItem):
    """Link object for a body in database.

    Parameters
    ----------
    db : ansys.speos.core.body.BodyStub
        Database to link to.
    key : str
        Key of the body in the database.
    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the body."""
        return str(self.get())

    def get(self) -> Body:
        """Get the datamodel from database.

        Returns
        -------
        body.Body
            Body datamodel.
        """
        return self._stub.read(self)

    def set(self, data: Body) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : body.Body
            New body datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class BodyStub(CrudStub):
    """
    Database interactions for body.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a BodyStub is to retrieve it from SpeosClient via bodies() method.
    Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> body_db = speos.client.bodies()

    """

    def __init__(self, channel):
        super().__init__(stub=service.BodiesManagerStub(channel=channel))

    def create(self, message: Body) -> BodyLink:
        """Create a new entry.

        Parameters
        ----------
        message : body.Body
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.body.BodyLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(body=message))
        return BodyLink(self, resp.guid)

    def read(self, ref: BodyLink) -> Body:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.body.BodyLink
            Link object to read.

        Returns
        -------
        body.Body
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("BodyLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.body

    def update(self, ref: BodyLink, data: Body) -> None:
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.body.BodyLink
            Link object to update.

        data : body.Body
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("BodyLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, body=data))

    def delete(self, ref: BodyLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.body.BodyLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("BodyLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[BodyLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.body.BodyLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: BodyLink(self, x), guids))


class BodyFactory:
    """Class to help creating Body message"""

    @staticmethod
    def new(name: str, faces: List[FaceLink], description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None) -> Body:
        """Create a Body message.

        Parameters
        ----------
        name : str
            Name of the body.
        faces : List[ansys.speos.core.face.FaceLink]
            List of faces composing the body.
        description : str, optional
            Description of the body.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the body.
            By default, ``None``.

        Returns
        -------
        body.Body
            Body message created.
        """
        body = Body(name=name, description=description)
        if metadata is not None:
            body.metadata.update(metadata)
        for face in faces:
            body.face_guids.append(face.key)
        return body

    @staticmethod
    def box(
        name: str,
        face_stub: FaceStub,
        description: Optional[str] = "",
        base: Optional[AxisSystem] = AxisSystem(),
        x_size: Optional[float] = 200,
        y_size: Optional[float] = 200,
        z_size: Optional[float] = 100,
        idx_face: Optional[int] = 0,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Body:
        """
        Create a specific body: a box.

        Parameters
        ----------
        name : str
            Name of the box.
        face_stub : ansys.speos.core.face.FaceStub
            Face stub, example speos.client.faces()
        description : str, optional
            Description of the box.
            By default, ``""``.
        base : ansys.speos.core.geometry_utils.AxisSystem, optional
            Center and orientation of the box.
            By default, ``AxisSystem()``.
        x_size : float, optional
            size regarding x axis.
            By default, ``200``.
        y_size : float, optional
            size regarding y axis.
            By default, ``200``.
        z_size : float, optional
            size regarding z axis.
            By default, ``100``.
        idx_face : int, optional
            start index used to name the faces like Face:x, Face:x+1, ...
            By default, ``0``.
        metadata : Mapping[str, str], optional
            Metadata of the box.
            By default, ``None``.

        Returns
        -------
        body.Body
            Body message created.
        """
        body = Body(name=name, description=description)
        if metadata is not None:
            body.metadata.update(metadata)
        face0 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face),
                base=AxisPlane(
                    origin=base.origin - np.multiply(0.5 * z_size, base.z_vect), x_vect=np.multiply(-1, base.x_vect), y_vect=base.y_vect
                ),
                x_size=x_size,
                y_size=y_size,
            )
        )
        face1 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face + 1),
                base=AxisPlane(origin=base.origin + np.multiply(0.5 * z_size, base.z_vect), x_vect=base.x_vect, y_vect=base.y_vect),
                x_size=x_size,
                y_size=y_size,
            )
        )
        face2 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face + 2),
                base=AxisPlane(base.origin - np.multiply(0.5 * x_size, base.x_vect), x_vect=base.z_vect, y_vect=base.y_vect),
                x_size=z_size,
                y_size=y_size,
            )
        )
        face3 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face + 3),
                base=AxisPlane(
                    base.origin + np.multiply(0.5 * x_size, base.x_vect), x_vect=np.multiply(-1, base.z_vect), y_vect=base.y_vect
                ),
                x_size=z_size,
                y_size=y_size,
            )
        )
        face4 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face + 4),
                base=AxisPlane(base.origin - np.multiply(0.5 * y_size, base.y_vect), x_vect=base.x_vect, y_vect=base.z_vect),
                x_size=x_size,
                y_size=z_size,
            )
        )
        face5 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face + 5),
                base=AxisPlane(
                    base.origin + np.multiply(0.5 * y_size, base.y_vect), x_vect=base.x_vect, y_vect=np.multiply(-1, base.z_vect)
                ),
                x_size=x_size,
                y_size=z_size,
            )
        )

        body.face_guids.extend([face0.key, face1.key, face2.key, face3.key, face4.key, face5.key])
        return body
