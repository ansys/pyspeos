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
    body_pb2 as messages,
    body_pb2_grpc as service,
)
from ansys.speos.core.kernel.crud import CrudItem, CrudStub
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str

ProtoBody = messages.Body
"""Body protobuf class : ansys.api.speos.part.v1.body_pb2.Body"""
ProtoBody.__str__ = lambda self: protobuf_message_to_str(self)


class BodyLink(CrudItem):
    """Link object for a body in database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.body.BodyStub
        Database to link to.
    key : str
        Key of the body in the database.
    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the body."""
        return str(self.get())

    def get(self) -> ProtoBody:
        """Get the datamodel from database.

        Returns
        -------
        body.Body
            Body datamodel.
        """
        return self._stub.read(self)

    def set(self, data: ProtoBody) -> None:
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
    >>> speos = Speos(host="localhost", port=50098)
    >>> body_db = speos.client.bodies()

    """

    def __init__(self, channel):
        super().__init__(stub=service.BodiesManagerStub(channel=channel))

    def create(self, message: ProtoBody) -> BodyLink:
        """Create a new entry.

        Parameters
        ----------
        message : body.Body
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.kernel.body.BodyLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(body=message))
        return BodyLink(self, resp.guid)

    def read(self, ref: BodyLink) -> ProtoBody:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.body.BodyLink
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

    def update(self, ref: BodyLink, data: ProtoBody) -> None:
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.body.BodyLink
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
        ref : ansys.speos.core.kernel.body.BodyLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("BodyLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[BodyLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.kernel.body.BodyLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: BodyLink(self, x), guids))
