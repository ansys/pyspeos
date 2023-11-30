"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import Mapping

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


class FaceFactory:
    def new(
        name: str,
        vertices: list[float],
        facets: list[int],
        normals: list[float],
        description: str = "",
        metadata: Mapping[str, str] = None,
    ) -> Face:
        face = Face(name=name, description=description, vertices=vertices, facets=facets, normals=normals)
        if metadata is not None:
            face.metadata.update(metadata)
        return face

    def rectangle(
        name: str,
        description: str = "",
        center: list[float] = [0, 0, 0],
        x_axis: list[float] = [1, 0, 0],
        y_axis: list[float] = [0, 1, 0],
        x_size: float = 200,
        y_size: float = 100,
        metadata: Mapping[str, str] = None,
    ) -> Face:
        face = Face(name=name, description=description)
        if metadata is not None:
            face.metadata.update(metadata)

        face.vertices.extend(center - np.multiply(0.5 * x_size, x_axis) - np.multiply(0.5 * y_size, y_axis))
        face.vertices.extend(center + np.multiply(0.5 * x_size, x_axis) - np.multiply(0.5 * y_size, y_axis))
        face.vertices.extend(center + np.multiply(0.5 * x_size, x_axis) + np.multiply(0.5 * y_size, y_axis))
        face.vertices.extend(center - np.multiply(0.5 * x_size, x_axis) + np.multiply(0.5 * y_size, y_axis))

        normal = np.cross(x_axis, y_axis)
        for i in range(4):
            face.normals.extend(normal)

        face.facets.extend([0, 1, 3, 1, 2, 3])

        return face
