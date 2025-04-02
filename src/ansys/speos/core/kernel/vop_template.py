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

from ansys.api.speos.vop.v1 import vop_pb2 as messages, vop_pb2_grpc as service
from ansys.speos.core.kernel.crud import CrudItem, CrudStub
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str

ProtoVOPTemplate = messages.VOPTemplate
"""VOPTemplate protobuf class : ansys.api.speos.vop.v1.vop_pb2.VOPTemplate"""
ProtoVOPTemplate.__str__ = lambda self: protobuf_message_to_str(self)


class VOPTemplateLink(CrudItem):
    """
    Link object for a Volume Optical Property (VOP) template in database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.vop_template.VOPTemplateStub
        Database to link to.
    key : str
        Key of the vop template in the database.

    Examples
    --------
    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
    >>> speos = Speos(host="localhost", port=50098)
    >>> vop_t_db = speos.client.vop_templates()
    >>> vop_t_message = ProtoVOPTemplate(name="Opaque")
    >>> vop_t_message.opaque.SetInParent()
    >>> vop_t_link = vop_t_db.create(message=vop_t_message)

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        """Return the string representation of the vop template."""
        return str(self.get())

    def get(self) -> ProtoVOPTemplate:
        """Get the datamodel from database.

        Returns
        -------
        vop_template.VOPTemplate
            VOPTemplate datamodel.
        """
        return self._stub.read(self)

    def set(self, data: ProtoVOPTemplate) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : vop_template.VOPTemplate
            New VOPTemplate datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class VOPTemplateStub(CrudStub):
    """
    Database interactions for Volume Optical Properties templates.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a VOPTemplateStub is to retrieve it from SpeosClient via vop_templates()
    method. Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50098)
    >>> vop_t_db = speos.client.vop_templates()

    """

    def __init__(self, channel):
        super().__init__(stub=service.VOPTemplatesManagerStub(channel=channel))

    def create(self, message: ProtoVOPTemplate) -> VOPTemplateLink:
        """Create a new entry.

        Parameters
        ----------
        message : vop_template.VOPTemplate
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.kernel.vop_template.VOPTemplateLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(vop_template=message))
        return VOPTemplateLink(self, resp.guid)

    def read(self, ref: VOPTemplateLink) -> ProtoVOPTemplate:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.vop_template.VOPTemplateLink
            Link object to read.

        Returns
        -------
        vop_template.VOPTemplate
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("VOPTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.vop_template

    def update(self, ref: VOPTemplateLink, data: ProtoVOPTemplate):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.vop_template.VOPTemplateLink
            Link object to update.
        data : vop_template.VOPTemplate
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("VOPTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, vop_template=data))

    def delete(self, ref: VOPTemplateLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.vop_template.VOPTemplateLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("VOPTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[VOPTemplateLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.kernel.vop_template.VOPTemplateLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: VOPTemplateLink(self, x), guids))
