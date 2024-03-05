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

from ansys.api.speos.sop.v1 import sop_pb2 as messages
from ansys.api.speos.sop.v1 import sop_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

SOPTemplate = messages.SOPTemplate
SOPTemplate.__str__ = lambda self: protobuf_message_to_str(self)


class SOPTemplateLink(CrudItem):
    """
    Link object for Surface Optical Properties template in database.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.sop_template import SOPTemplateFactory
    >>> speos = Speos(host="localhost", port=50051)
    >>> sop_t_db = speos.client.sop_templates()
    >>> sop_t_link = sop_t_db.create(message=SOPTemplateFactory.mirror(name="Mirror_50", reflectance=50))

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return str(self.get())

    def get(self) -> SOPTemplate:
        """Get the datamodel from database."""
        return self._stub.read(self)

    def set(self, data: SOPTemplate) -> None:
        """Change datamodel in database."""
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)


class SOPTemplateStub(CrudStub):
    """
    Database interactions for Surface Optical Properties templates.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> sop_t_db = speos.client.sop_templates()

    """

    def __init__(self, channel):
        super().__init__(stub=service.SOPTemplatesManagerStub(channel=channel))

    def create(self, message: SOPTemplate) -> SOPTemplateLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(sop_template=message))
        return SOPTemplateLink(self, resp.guid)

    def read(self, ref: SOPTemplateLink) -> SOPTemplate:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("SOPTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.sop_template

    def update(self, ref: SOPTemplateLink, data: SOPTemplate):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("SOPTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, sop_template=data))

    def delete(self, ref: SOPTemplateLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("SOPTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SOPTemplateLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SOPTemplateLink(self, x), guids))


class SOPTemplateFactory:
    """Class to help creating SOPTemplate message. Surface Optical Property template."""

    def mirror(
        name: str, reflectance: Optional[float] = 100, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None
    ) -> SOPTemplate:
        """
        Perfect specular surface.
        Create a SOPTemplate message, with mirror type.

        Parameters
        ----------
        name : str
            Name of the sop template.
        reflectance : float, optional
            Reflectance, expected from 0. to 100. in %
            By default, ``100``.
        description : str, optional
            Description of the sop template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the sop template.
            By default, ``None``.

        Returns
        -------
        SOPTemplate
            SOPTemplate message created.
        """
        sop = SOPTemplate(name=name, description=description)
        if metadata is not None:
            sop.metadata.update(metadata)
        sop.mirror.reflectance = reflectance
        return sop

    def optical_polished(name: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None) -> SOPTemplate:
        """
        Transparent or perfectly polished material (glass, plastic).
        Create a SOPTemplate message, with optical polished type.

        Parameters
        ----------
        name : str
            Name of the sop template.
        description : str, optional
            Description of the sop template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the sop template.
            By default, ``None``.

        Returns
        -------
        SOPTemplate
            SOPTemplate message created.
        """
        sop = SOPTemplate(name=name, description=description)
        if metadata is not None:
            sop.metadata.update(metadata)
        sop.optical_polished.SetInParent()
        return sop

    def library(name: str, sop_file_uri: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None) -> SOPTemplate:
        """
        Based on surface optical properties file.
        Create a SOPTemplate message, with library type.

        Parameters
        ----------
        name : str
            Name of the sop template.
        sop_file_uri : str
            Surface optical properties file, \*.scattering, \*.bsdf, \*.brdf, \*.coated, ...
        description : str, optional
            Description of the sop template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the sop template.
            By default, ``None``.

        Returns
        -------
        SOPTemplate
            SOPTemplate message created.
        """
        sop = SOPTemplate(name=name, description=description)
        if metadata is not None:
            sop.metadata.update(metadata)
        sop.library.sop_file_uri = sop_file_uri
        return sop

    def plugin(
        name: str,
        plugin_sop_file_uri: str,
        parameters_file_uri: str,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> SOPTemplate:
        """
        Custom made plug-in.
        Create a SOPTemplate message, with plugin type.

        Parameters
        ----------
        name : str
            Name of the sop template.
        plugin_sop_file_uri : str
            \*.sop plug-in
        parameters_file_uri : str
            Parameters file needed for the plug-in
        description : str, optional
            Description of the sop template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the sop template.
            By default, ``None``.

        Returns
        -------
        SOPTemplate
            SOPTemplate message created.
        """
        sop = SOPTemplate(name=name, description=description)
        if metadata is not None:
            sop.metadata.update(metadata)
        sop.plugin.plugin_sop_file_uri = plugin_sop_file_uri
        sop.plugin.parameters_file_uri = parameters_file_uri
        return sop
