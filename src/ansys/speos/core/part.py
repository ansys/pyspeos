"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import Mapping

from ansys.api.speos.part.v1 import part_pb2 as messages
from ansys.api.speos.part.v1 import part_pb2_grpc as service

from ansys.speos.core.body import BodyLink
from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

Part = messages.Part


class PartLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> Part:
        return self._stub.read(self)

    def set(self, data: Part) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class PartStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.PartsManagerStub(channel=channel))

    def create(self, message: Part) -> PartLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(part=message))
        return PartLink(self, resp.guid)

    def read(self, ref: PartLink) -> Part:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("PartLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.part

    def update(self, ref: PartLink, data: Part):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("PartLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, part=data))

    def delete(self, ref: PartLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("PartLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> list[PartLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: PartLink(self, x), guids))


class PartFactory:
    def new(name: str, bodies: list[BodyLink], description: str = "", metadata: Mapping[str, str] = None) -> Part:
        part = Part(name=name, description=description)
        if metadata is not None:
            part.metadata.update(metadata)
        for body in bodies:
            part.body_guids.append(body.key)
        return part
