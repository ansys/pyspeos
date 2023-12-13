"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import List, Mapping, Optional

from ansys.api.speos.sop.v1 import sop_pb2 as messages
from ansys.api.speos.sop.v1 import sop_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

SOPTemplate = messages.SOPTemplate


class SOPTemplateLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> SOPTemplate:
        return self._stub.read(self)

    def set(self, data: SOPTemplate) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class SOPTemplateStub(CrudStub):
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
        Create a SOPTemplate message, with mirror type.
        Perfect specular surface.

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
        Create a SOPTemplate message, with optical polished type.
        Transparent or perfectly polished material (glass, plastic)

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
        Create a SOPTemplate message, with library type.
        Based on surface optical properties file

        Parameters
        ----------
        name : str
            Name of the sop template.
        sop_file_uri : str
            Surface optical properties file, *.scattering, *.bsdf, *.brdf, *.coated, ...
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
        Create a SOPTemplate message, with plugin type.
        Custom made plug-in

        Parameters
        ----------
        name : str
            Name of the sop template.
        plugin_sop_file_uri : str
            *.sop plug-in
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
