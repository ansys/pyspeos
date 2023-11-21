"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from ansys.api.speos.sensor.v1 import sensor_pb2 as messages
from ansys.api.speos.sensor.v1 import sensor_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub

SensorTemplate = messages.SensorTemplate


class SensorTemplateLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def get(self) -> SensorTemplate:
        return self._stub.Read(self)

    def set(self, data: SensorTemplate) -> None:
        self._stub.Update(self, data)

    def delete(self) -> None:
        self._stub.Delete(self)


class SensorTemplateStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.SensorTemplatesManagerStub(channel=channel))

    def Create(self, message: SensorTemplate) -> SensorTemplateLink:
        """Create a new entry."""
        resp = CrudStub.Create(self, messages.Create_Request(sensor_template=message))
        return SensorTemplateLink(self, resp.guid)

    def Read(self, ref: SensorTemplateLink) -> SensorTemplate:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("SensorTemplateLink is not on current database")
        resp = CrudStub.Read(self, messages.Read_Request(guid=ref.key))
        return resp.sensor_template

    def Update(self, ref: SensorTemplateLink, data: SensorTemplate):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("SensorTemplateLink is not on current database")
        CrudStub.Update(self, messages.Update_Request(guid=ref.key, sensor_template=data))

    def Delete(self, ref: SensorTemplateLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("SensorTemplateLink is not on current database")
        CrudStub.Delete(self, messages.Delete_Request(guid=ref.key))

    def List(self) -> list:
        """List existing entries."""
        guids = CrudStub.List(self, messages.List_Request()).guids
        return list(map(lambda x: SensorTemplateLink(self, x), guids))
