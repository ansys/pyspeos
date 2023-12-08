"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import List, Mapping

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
    def mirror(name: str, reflectance: float = 100, description: str = "", metadata: Mapping[str, str] = None) -> SOPTemplate:
        sop = SOPTemplate(name=name, description=description)
        if metadata is not None:
            sop.metadata.update(metadata)
        sop.mirror.reflectance = reflectance
        return sop

    def optical_polished(name: str, description: str = "", metadata: Mapping[str, str] = None) -> SOPTemplate:
        sop = SOPTemplate(name=name, description=description)
        if metadata is not None:
            sop.metadata.update(metadata)
        sop.optical_polished.SetInParent()
        return sop

    def library(name: str, sop_file_uri: str, description: str = "", metadata: Mapping[str, str] = None) -> SOPTemplate:
        sop = SOPTemplate(name=name, description=description)
        if metadata is not None:
            sop.metadata.update(metadata)
        sop.library.sop_file_uri = sop_file_uri
        return sop

    def plugin(
        name: str, plugin_sop_file_uri: str, parameters_file_uri: str, description: str = "", metadata: Mapping[str, str] = None
    ) -> SOPTemplate:
        sop = SOPTemplate(name=name, description=description)
        if metadata is not None:
            sop.metadata.update(metadata)
        sop.plugin.plugin_sop_file_uri = plugin_sop_file_uri
        sop.plugin.parameters_file_uri = parameters_file_uri
        return sop
