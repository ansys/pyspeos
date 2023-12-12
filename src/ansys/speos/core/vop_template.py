"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import List, Mapping, Optional

from ansys.api.speos.vop.v1 import vop_pb2 as messages
from ansys.api.speos.vop.v1 import vop_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

VOPTemplate = messages.VOPTemplate


class VOPTemplateLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> VOPTemplate:
        return self._stub.read(self)

    def set(self, data: VOPTemplate) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class VOPTemplateStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.VOPTemplatesManagerStub(channel=channel))

    def create(self, message: VOPTemplate) -> VOPTemplateLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(vop_template=message))
        return VOPTemplateLink(self, resp.guid)

    def read(self, ref: VOPTemplateLink) -> VOPTemplate:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("VOPTemplateLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.vop_template

    def update(self, ref: VOPTemplateLink, data: VOPTemplate):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("VOPTemplateLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, vop_template=data))

    def delete(self, ref: VOPTemplateLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("VOPTemplateLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[VOPTemplateLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: VOPTemplateLink(self, x), guids))


class VOPTemplateFactory:
    """Class to help creating VOPTemplate message. Volume Optical Property template."""

    def opaque(name: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None) -> VOPTemplate:
        """
        Create a VOPTemplate message, with opaque type.
        Non transparent material.

        Parameters
        ----------
        name : str
            Name of the vop template.
        description : str, optional
            Description of the vop template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the vop template.
            By default, ``None``.

        Returns
        -------
        VOPTemplate
            VOPTemplate message created.
        """
        vop = VOPTemplate(name=name, description=description)
        if metadata is not None:
            vop.metadata.update(metadata)
        vop.opaque.SetInParent()
        return vop

    def optic(
        name: str,
        index: Optional[float] = 1.5,
        absorption: Optional[float] = 0.0,
        constringence: Optional[float] = None,
        description: Optional[str] = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> VOPTemplate:
        """
        Create a VOPTemplate message, with optic type.
        Transparent colorless material without bulk scattering.

        Parameters
        ----------
        name : str
            Name of the vop template.
        index : float, optional
            Refractive index.
            By default, ``1.5``.
        absorption : float, optional
            Absorption coefficient value. mm-1
            By default, ``0.0``.
        constringence : float, optional
            Abbe number.
            By default, ``None``, ie no constringence.
        description : str, optional
            Description of the vop template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the vop template.
            By default, ``None``.

        Returns
        -------
        VOPTemplate
            VOPTemplate message created.
        """
        vop = VOPTemplate(name=name, description=description)
        if metadata is not None:
            vop.metadata.update(metadata)
        vop.optic.index = index
        vop.optic.absorption = absorption
        if constringence is not None:
            vop.optic.constringence = constringence
        return vop

    def library(
        name: str, material_file_uri: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None
    ) -> VOPTemplate:
        """
        Create a VOPTemplate message, with library type.
        Based on *.material file

        Parameters
        ----------
        name : str
            Name of the vop template.
        material_file_uri : str
            *.material file
        description : str, optional
            Description of the vop template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the vop template.
            By default, ``None``.

        Returns
        -------
        VOPTemplate
            VOPTemplate message created.
        """
        vop = VOPTemplate(name=name, description=description)
        if metadata is not None:
            vop.metadata.update(metadata)
        vop.library.material_file_uri = material_file_uri
        return vop

    def non_homogeneous(
        name: str, gradedmaterial_file_uri: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None
    ) -> VOPTemplate:
        """
        Create a VOPTemplate message, with non homogeneous type.
        Material with non-homogeneous refractive index.

        Parameters
        ----------
        name : str
            Name of the vop template.
        gradedmaterial_file_uri : str
            *.gradedmaterial file that describes the spectral variations of
            refractive index and absorption with the respect to position in space.
        description : str, optional
            Description of the vop template.
            By default, ``""``.
        metadata : Mapping[str, str], optional
            Metadata of the vop template.
            By default, ``None``.

        Returns
        -------
        VOPTemplate
            VOPTemplate message created.
        """
        vop = VOPTemplate(name=name, description=description)
        if metadata is not None:
            vop.metadata.update(metadata)
        vop.non_homogeneous.gradedmaterial_file_uri = gradedmaterial_file_uri
        return vop
