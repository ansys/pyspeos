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

from ansys.api.speos.source.v1 import (
    source_pb2 as messages,
    source_pb2_grpc as service,
)
from ansys.speos.core.kernel.crud import CrudItem, CrudStub
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str

ProtoSourceTemplate = messages.SourceTemplate
"""SourceTemplate protobuf class : ansys.api.speos.source.v1.source_pb2.SourceTemplate"""
ProtoSourceTemplate.__str__ = lambda self: protobuf_message_to_str(self)


class SourceTemplateLink(CrudItem):
    """Link object for a source template in database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.source_template.SourceTemplateStub
        Database to link to.
    key : str
        Key of the source template in the database.
    """

    def __init__(self, db, key: str):
        super().__init__(db, key)
        self._actions_stub = db._actions_stub

    def __str__(self) -> str:
        """Return the string representation of the source template."""
        return str(self.get())

    def get(self) -> ProtoSourceTemplate:
        """Get the datamodel from database.

        Returns
        -------
        source_template.SourceTemplate
            Source template datamodel.
        """
        return self._stub.read(self)

    def set(self, data: ProtoSourceTemplate) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : source_template.SourceTemplate
            New source template datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)

    # Actions
    def get_ray_file_info(self) -> messages.GetRayFileInfo_Response:
        """
        Retrieve information about ray file source.

        Returns
        -------
        ansys.api.speos.source.v1.source_pb2.GetRayFileInfo_Response
            Information about ray file source, like flux value.
        """
        return self._actions_stub.GetRayFileInfo(messages.GetRayFileInfo_Request(guid=self.key))


class SourceTemplateStub(CrudStub):
    """
    Database interactions for source templates.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a SourceTemplateStub is to retrieve it from SpeosClient via
    source_templates() method. Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50098)
    >>> src_t_db = speos.client.source_templates()

    """

    def __init__(self, channel):
        super().__init__(stub=service.SourceTemplatesManagerStub(channel=channel))
        self._actions_stub = service.SourceTemplateActionsStub(channel=channel)

    def create(self, message: ProtoSourceTemplate) -> SourceTemplateLink:
        """Create a new entry.

        Parameters
        ----------
        message : source_template.SourceTemplate
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.kernel.source_template.SourceTemplateLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(source_template=message))
        return SourceTemplateLink(self, resp.guid)

    def read(self, ref: SourceTemplateLink) -> ProtoSourceTemplate:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.source_template.SourceTemplateLink
            Link object to read.

        Returns
        -------
        source_template.SourceTemplate
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("SourceTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.source_template

    def update(self, ref: SourceTemplateLink, data: ProtoSourceTemplate):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.source_template.SourceTemplateLink
            Link object to update.
        data : source_template.SourceTemplate
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("SourceTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, source_template=data))

    def delete(self, ref: SourceTemplateLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.source_template.SourceTemplateLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("SourceTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SourceTemplateLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.kernel.source_template.SourceTemplateLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SourceTemplateLink(self, x), guids))
