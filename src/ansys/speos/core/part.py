"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import List, Mapping, Optional

from ansys.api.speos.part.v1 import part_pb2 as messages
from ansys.api.speos.part.v1 import part_pb2_grpc as service

from ansys.speos.core.body import BodyLink
from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

Part = messages.Part
Part.__str__ = lambda self: protobuf_message_to_str(self)


class PartLink(CrudItem):
    """Link object for body in database."""

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return str(self.get())

    def get(self) -> Part:
        """Get the datamodel from database."""
        return self._stub.read(self)

    def set(self, data: Part) -> None:
        """Change datamodel in database."""
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class PartStub(CrudStub):
    """
    Database interactions for part.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> part_db = speos.client.parts()

    """

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

    def list(self) -> List[PartLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: PartLink(self, x), guids))


class PartFactory:
    """Class to help creating Part message"""

    def new(name: str, bodies: List[BodyLink], description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None) -> Part:
        """
        Create a Part message.

        Parameters
        ----------
        name : str
            Name of the part.
        bodies : List[BodyLink]
            List of all bodies contained in this part.
        description : str, optional
            Description of the part.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the part.
            By default, ``None``.

        Returns
        -------
        Part
            Part message created.
        """
        part = Part(name=name, description=description)
        if metadata is not None:
            part.metadata.update(metadata)
        for body in bodies:
            part.body_guids.append(body.key)
        return part
