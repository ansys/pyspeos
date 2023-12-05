"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
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

    def list(self) -> list[VOPTemplateLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: VOPTemplateLink(self, x), guids))


class VOPTemplateFactory:
    def opaque(name: str, description: str) -> VOPTemplate:
        vop = VOPTemplate(name=name, description=description)
        vop.opaque.SetInParent()
        return vop

    def optic(name: str, description: str, index: float, absorption: float, constringence: float = None) -> VOPTemplate:
        vop = VOPTemplate(name=name, description=description)
        vop.optic.index = index
        vop.optic.absorption = absorption
        if constringence is not None:
            vop.optic.constringence = constringence
        return vop

    def library(name: str, description: str, material_file_uri: str) -> VOPTemplate:
        vop = VOPTemplate(name=name, description=description)
        vop.library.material_file_uri = material_file_uri
        return vop

    def non_homogeneous(name: str, description: str, gradedmaterial_file_uri: str) -> VOPTemplate:
        vop = VOPTemplate(name=name, description=description)
        vop.non_homogeneous.gradedmaterial_file_uri = gradedmaterial_file_uri
        return vop
