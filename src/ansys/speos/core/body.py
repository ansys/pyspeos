"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import Mapping

from ansys.api.speos.part.v1 import body_pb2 as messages
from ansys.api.speos.part.v1 import body_pb2_grpc as service
import numpy as np

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.face import FaceFactory, FaceLink, FaceStub
from ansys.speos.core.geometry import CoordSys
from ansys.speos.core.proto_message import protobuf_message_to_str

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

    def list(self) -> list[BodyLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: BodyLink(self, x), guids))


class BodyFactory:
    def new(name: str, faces: list[FaceLink], description: str = "", metadata: Mapping[str, str] = None) -> Body:
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
        base: CoordSys = CoordSys(),
        x_size: float = 200,
        y_size: float = 200,
        z_size: float = 100,
        idx_face: int = 0,
        metadata: Mapping[str, str] = None,
    ) -> Body:
        body = Body(name=name, description=description)
        if metadata is not None:
            body.metadata.update(metadata)
        face0 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face),
                center=base.origin - np.multiply(0.5 * z_size, base.z_vect),
                x_axis=np.multiply(-1, base.x_vect),
                y_axis=base.y_vect,
                x_size=x_size,
                y_size=y_size,
            )
        )
        face1 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face + 1),
                center=base.origin + np.multiply(0.5 * z_size, base.z_vect),
                x_axis=base.x_vect,
                y_axis=base.y_vect,
                x_size=x_size,
                y_size=y_size,
            )
        )
        face2 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face + 2),
                center=base.origin - np.multiply(0.5 * x_size, base.x_vect),
                x_axis=base.z_vect,
                y_axis=base.y_vect,
                x_size=z_size,
                y_size=y_size,
            )
        )
        face3 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face + 3),
                center=base.origin + np.multiply(0.5 * x_size, base.x_vect),
                x_axis=np.multiply(-1, base.z_vect),
                y_axis=base.y_vect,
                x_size=z_size,
                y_size=y_size,
            )
        )
        face4 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face + 4),
                center=base.origin - np.multiply(0.5 * y_size, base.y_vect),
                x_axis=base.x_vect,
                y_axis=base.z_vect,
                x_size=x_size,
                y_size=z_size,
            )
        )
        face5 = face_stub.create(
            message=FaceFactory.rectangle(
                name="Face:" + str(idx_face + 5),
                center=base.origin + np.multiply(0.5 * y_size, base.y_vect),
                x_axis=base.x_vect,
                y_axis=np.multiply(-1, base.z_vect),
                x_size=x_size,
                y_size=z_size,
            )
        )

        body.face_guids.extend([face0.key, face1.key, face2.key, face3.key, face4.key, face5.key])
        return body
