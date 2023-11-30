"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from ansys.api.speos.part.v1 import face_pb2 as messages
from ansys.api.speos.part.v1 import face_pb2_grpc as service
import numpy as np

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message import protobuf_message_to_str

Face = messages.Face


class FaceLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> Face:
        return self._stub.read(self)

    def set(self, data: Face) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class FaceStub(CrudStub):
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

    def list(self) -> list[FaceLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: FaceLink(self, x), guids))


class Point3f:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    def get(self) -> list[float]:
        return [self.x, self.y, self.z]


class Vector3f:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    def get(self) -> list[float]:
        return [self.x, self.y, self.z]


class FaceFactory:
    def rectangle(
        name: str,
        description: str,
        center: Point3f = Point3f(x=0, y=0, z=0),
        x_axis: Vector3f = Vector3f(x=1, y=0, z=0),
        y_axis: Vector3f = Vector3f(x=0, y=1, z=0),
        x_size: float = 200,
        y_size: float = 100,
    ) -> Face:
        face = Face(name=name, description=description)

        face.vertices.extend(center.get() - np.multiply(0.5 * x_size, x_axis.get()) - np.multiply(0.5 * y_size, y_axis.get()))
        face.vertices.extend(center.get() + np.multiply(0.5 * x_size, x_axis.get()) - np.multiply(0.5 * y_size, y_axis.get()))
        face.vertices.extend(center.get() + np.multiply(0.5 * x_size, x_axis.get()) + np.multiply(0.5 * y_size, y_axis.get()))
        face.vertices.extend(center.get() - np.multiply(0.5 * x_size, x_axis.get()) + np.multiply(0.5 * y_size, y_axis.get()))

        normal = np.cross(x_axis.get(), y_axis.get())
        for i in range(4):
            face.normals.extend(normal)

        face.facets.extend([0, 1, 3, 1, 2, 3])

        return face
