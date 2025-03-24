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

from ansys.api.speos.sop.v1 import sop_pb2 as messages, sop_pb2_grpc as service
from ansys.speos.core.kernel.crud import CrudItem, CrudStub
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str

ProtoSOPTemplate = messages.SOPTemplate
"""SOPTemplate protobuf class : ansys.api.speos.sop.v1.sop_pb2.SOPTemplate"""
ProtoSOPTemplate.__str__ = lambda self: protobuf_message_to_str(self)


class SOPTemplateLink(CrudItem):
    """
    Link object for Surface Optical Properties template in database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.sop_template.SOPTemplateStub
        Database to link to.
    key : str
        Key of the sop_template in the database.

    Examples
    --------
    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
    >>> speos = Speos(host="localhost", port=50098)
    >>> sop_t_db = speos.client.sop_templates()
    >>> sop_t_message = ProtoSOPTemplate(name="Mirror_50")
    >>> sop_t_message.mirror.reflectance = 50
    >>> sop_t_link = sop_t_db.create(message=sop_t_message)

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the sop_template."""
        return str(self.get())

    def get(self) -> ProtoSOPTemplate:
        """Get the datamodel from database.

        Returns
        -------
        sop_template.SOPTemplate
            SOPTemplate datamodel.
        """
        return self._stub.read(self)

    def set(self, data: ProtoSOPTemplate) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : sop_template.SOPTemplate
            New SOPTemplate datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class SOPTemplateStub(CrudStub):
    """
    Database interactions for Surface Optical Properties templates.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a SOPTemplateStub is to retrieve it from SpeosClient via sop_templates()
    method. Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50098)
    >>> sop_t_db = speos.client.sop_templates()

    """

    def __init__(self, channel):
        super().__init__(stub=service.SOPTemplatesManagerStub(channel=channel))

    def create(self, message: ProtoSOPTemplate) -> SOPTemplateLink:
        """Create a new entry.

        Parameters
        ----------
        message : sop_template.SOPTemplate
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.kernel.sop_template.SOPTemplateLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(sop_template=message))
        return SOPTemplateLink(self, resp.guid)

    def read(self, ref: SOPTemplateLink) -> ProtoSOPTemplate:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.sop_template.SOPTemplateLink
            Link object to read.

        Returns
        -------
        sop_template.SOPTemplate
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("SOPTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.sop_template

    def update(self, ref: SOPTemplateLink, data: ProtoSOPTemplate):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.sop_template.SOPTemplateLink
            Link object to update.
        data : sop_template.SOPTemplate
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("SOPTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, sop_template=data))

    def delete(self, ref: SOPTemplateLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.sop_template.SOPTemplateLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("SOPTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SOPTemplateLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.kernel.sop_template.SOPTemplateLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SOPTemplateLink(self, x), guids))
