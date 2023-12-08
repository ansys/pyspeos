"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import List, Mapping

from ansys.api.speos.part.v1 import body_pb2 as messages
from ansys.api.speos.part.v1 import body_pb2_grpc as service
import numpy as np

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.face import FaceFactory, FaceLink, FaceStub
from ansys.speos.core.geometry_utils import AxisPlane, AxisSystem
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

Body = messages.Body


class BodyLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> Body:
        return self._stub.read(self)

    def set(self, data: Body) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class BodyStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.BodiesManagerStub(channel=channel))

    def create(self, message: Body) -> BodyLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(body=message))
        return BodyLink(self, resp.guid)

    def read(self, ref: BodyLink) -> Body:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("BodyLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.body

    def update(self, ref: BodyLink, data: Body):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("BodyLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, body=data))

    def delete(self, ref: BodyLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("BodyLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[BodyLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: BodyLink(self, x), guids))


class BodyFactory:
    """Class to help creating Body message"""

    def new(name: str, faces: List[FaceLink], description: str = "", metadata: Mapping[str, str] = None) -> Body:
        """
        Create a Body message.

        Parameters
        ----------
        name : str
            Name of the body.
        faces : List[FaceLink]
            List of faces composing the body.
        description : str
            Description of the body.
        metadata : Mapping[str, str]
            Metadata of the body.

        Returns
        -------
        Body
            Body message created.
        """
        body = Body(name=name, description=description)
        if metadata is not None:
            body.metadata.update(metadata)
        for face in faces:
            body.face_guids.append(face.key)
        return body

    def box(
        name: str,
        face_stub: FaceStub,
        description: str = "",
        base: AxisSystem = AxisSystem(),
        x_size: float = 200,
        y_size: float = 200,
        z_size: float = 100,
        idx_face: int = 0,
        metadata: Mapping[str, str] = None,
    ) -> Body:
        """
        Create a specific body: a box.

        Parameters
        ----------
        name : str
            Name of the box.
        face_stub : FaceStub
            face stub, example speos.client.faces()
        description : str
            Description of the box.
        base : ansys.speos.core.geometry_utils.AxisSystem
            Center and orientation of the box.
        x_size : float
            size regarding x axis.
        y_size : float
            size regarding y axis.
        z_size : float
            size regarding z axis.
        idx_face : int
            start index used to name the faces like Face:x, Face:x+1, ...
        metadata : Mapping[str, str]
            Metadata of the box.

        Returns
        -------
        Body
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
