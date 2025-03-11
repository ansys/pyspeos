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

from ansys.api.speos.intensity.v1 import (
    intensity_pb2 as messages,
    intensity_pb2_grpc as service,
)
from ansys.speos.core.kernel.crud import CrudItem, CrudStub
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_str

ProtoIntensityTemplate = messages.IntensityTemplate
"""IntensityTemplate protobuf class.

ansys.api.speos.intensity.v1.intensity_pb2.IntensityTemplate"""
ProtoIntensityTemplate.__str__ = lambda self: protobuf_message_to_str(self)


class IntensityTemplateLink(CrudItem):
    """
    Link object for intensity template in database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.intensity_template.IntensityTemplateStub
        Database to link to.
    key : str
        Key of the body in the database.

    Examples
    --------
    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.kernel.intensity_template import (
    ...     ProtoIntensityTemplate,
    ... )
    >>> speos = Speos(host="localhost", port=50098)
    >>> int_t_db = speos.client.intensity_templates()
    >>> int_t_message = ProtoIntensityTemplate(name="Cos_3_170")
    >>> int_t_message.cos.N = 3.0
    >>> int_t_message.cos.total_angle = 170
    >>> int_t_link = int_t_db.create(message=int_t_message)

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)
        self._actions_stub = db._actions_stub

    def __str__(self) -> str:
        """Return the string representation of the intensity_template."""
        return str(self.get())

    def get(self) -> ProtoIntensityTemplate:
        """Get the datamodel from database.

        Returns
        -------
        intensity_template.IntensityTemplate
            IntensityTemplate datamodel.
        """
        return self._stub.read(self)

    def set(self, data: ProtoIntensityTemplate) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : intensity_template.IntensityTemplate
            New IntensityTemplate datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)

    # Actions
    def get_library_type_info(self) -> messages.GetLibraryTypeInfo_Response:
        """
        Retrieve information about intensity template in case of library type.

        Returns
        -------
        ansys.api.speos.intensity.v1.intensity_pb2.GetLibraryTypeInfo_Response
            Information about intensity template, like flux value.
        """
        return self._actions_stub.GetLibraryTypeInfo(
            messages.GetLibraryTypeInfo_Request(guid=self.key)
        )


class IntensityTemplateStub(CrudStub):
    """
    Database interactions for intensity templates.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a IntensityTemplateStub is to retrieve it from SpeosClient via
    intensity_templates() method. Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50098)
    >>> int_t_db = speos.client.intensity_templates()

    """

    def __init__(self, channel):
        super().__init__(stub=service.IntensityTemplatesManagerStub(channel=channel))
        self._actions_stub = service.IntensityTemplateActionsStub(channel=channel)

    def create(self, message: ProtoIntensityTemplate) -> IntensityTemplateLink:
        """Create a new entry.

        Parameters
        ----------
        message : intensity_template.IntensityTemplate
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.kernel.intensity_template.IntensityTemplateLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(intensity_template=message))
        return IntensityTemplateLink(self, resp.guid)

    def read(self, ref: IntensityTemplateLink) -> ProtoIntensityTemplate:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.intensity_template.IntensityTemplateLink
            Link object to read.

        Returns
        -------
        intensity_template.IntensityTemplate
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("IntensityTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.intensity_template

    def update(self, ref: IntensityTemplateLink, data: ProtoIntensityTemplate):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.intensity_template.IntensityTemplateLink
            Link object to update.

        data : intensity_template.IntensityTemplate
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("IntensityTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, intensity_template=data))

    def delete(self, ref: IntensityTemplateLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.kernel.intensity_template.IntensityTemplateLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("IntensityTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[IntensityTemplateLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.kernel.intensity_template.IntensityTemplateLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: IntensityTemplateLink(self, x), guids))
