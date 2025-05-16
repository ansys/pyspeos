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

from typing import List

from ansys.api.speos.part.v1 import (
    part_pb2 as messages,
    part_pb2_grpc as service,
)
from ansys.speos.core.kernel.crud import CrudItem, CrudStub
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str

ProtoPart = messages.Part
"""Part protobuf class : ansys.api.speos.part.v1.part_pb2.Part"""
ProtoPart.__str__ = lambda self: protobuf_message_to_str(self)


class PartLink(CrudItem):
    """Link object for a part in database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.part.PartStub
        Database to link to.
    key : str
        Key of the part in the database.
    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the part."""
        return str(self.get())

    def get(self) -> ProtoPart:
        """Get the datamodel from database.

        Returns
        -------
        part.Part
            Part datamodel.
        """
        return self._stub.read(self)

    def set(self, data: ProtoPart) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : part.Part
            New part datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class PartStub(CrudStub):
    """
    Database interactions for part.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a PartStub is to retrieve it from SpeosClient via parts() method.
    Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50098)
    >>> part_db = speos.client.parts()

    """

    def __init__(self, channel):
        super().__init__(stub=service.PartsManagerStub(channel=channel))

    def create(self, message: ProtoPart) -> PartLink:
        """Create a new entry.

        Parameters
        ----------
        message : part.Part
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.kernel.part.PartLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(part=message))
        return PartLink(self, resp.guid)

    def read(self, ref: PartLink) -> ProtoPart:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.part.PartLink
            Link object to read.

        Returns
        -------
        part.Part
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("PartLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.part

    def update(self, ref: PartLink, data: ProtoPart):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.part.PartLink
            Link object to update.

        data : part.Part
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("PartLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, part=data))

    def delete(self, ref: PartLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.part.PartLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("PartLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[PartLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.kernel.part.PartLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: PartLink(self, x), guids))
