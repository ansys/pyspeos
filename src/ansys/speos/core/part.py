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

from ansys.api.speos.part.v1 import part_pb2 as messages
from ansys.api.speos.part.v1 import part_pb2_grpc as service

from ansys.speos.core.body import BodyLink
from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.geometry_utils import AxisSystem
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


class PartInstanceFactory:
    """Class to help creating PartInstance message"""

    def new(
        name: str,
        part: PartLink,
        axis_system: Optional[AxisSystem] = AxisSystem(),
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Part.PartInstance:
        """
        Create a PartInstance message.

        Parameters
        ----------
        name : str
            Name of the part instance.
        part : PartLink
            Part to be instantiated.
        axis_system : ansys.speos.core.geometry_utils.AxisSystem, optional
            Position of the part instance.
            By default, ``ansys.speos.core.geometry_utils.AxisSystem()``.
        description : str, optional
            Description of the part instance.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the part.
            By default, ``None``.

        Returns
        -------
        Part.PartInstance
            PartInstance message created.
        """
        part_instance = Part.PartInstance(name=name, description=description)
        if metadata is not None:
            part_instance.metadata.update(metadata)

        part_instance.part_guid = part.key
        part_instance.axis_system.extend(axis_system.origin + axis_system.x_vect + axis_system.y_vect + axis_system.z_vect)

        return part_instance


class PartFactory:
    """Class to help creating Part message"""

    def new(
        name: str,
        bodies: List[BodyLink],
        parts: List[Part.PartInstance] = [],
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Part:
        """
        Create a Part message.

        Parameters
        ----------
        name : str
            Name of the part.
        bodies : List[BodyLink]
            List of all bodies contained in this part.
        parts : List[Part.PartInstance]
            List of all parts instantiated in this part.
            By default, ``[]``.
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
        for part_instance in parts:
            part.parts.append(part_instance)
        return part
