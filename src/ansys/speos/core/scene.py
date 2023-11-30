"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""
from typing import Mapping

from ansys.api.speos.scene.v1 import scene_pb2 as messages
from ansys.api.speos.scene.v1 import scene_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.part import PartLink
from ansys.speos.core.proto_message import protobuf_message_to_str
from ansys.speos.core.vop_template import VOPTemplateLink

Scene = messages.Scene


class SceneLink(CrudItem):
    def __init__(self, db, key: str):
        super().__init__(db, key)

    def __str__(self) -> str:
        return protobuf_message_to_str(self.get())

    def get(self) -> Scene:
        return self._stub.read(self)

    def set(self, data: Scene) -> None:
        self._stub.update(self, data)

    def delete(self) -> None:
        self._stub.delete(self)


class SceneStub(CrudStub):
    def __init__(self, channel):
        super().__init__(stub=service.ScenesManagerStub(channel=channel))

    def create(self, message: Scene) -> SceneLink:
        """Create a new entry."""
        resp = CrudStub.create(self, messages.Create_Request(scene=message))
        return SceneLink(self, resp.guid)

    def read(self, ref: SceneLink) -> Scene:
        """Get an existing entry."""
        if not ref.stub == self:
            raise ValueError("SceneLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.scene

    def update(self, ref: SceneLink, data: Scene):
        """Change an existing entry."""
        if not ref.stub == self:
            raise ValueError("SceneLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, scene=data))

    def delete(self, ref: SceneLink) -> None:
        """Remove an existing entry."""
        if not ref.stub == self:
            raise ValueError("SceneLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> list[SceneLink]:
        """List existing entries."""
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SceneLink(self, x), guids))


class GeoPaths:
    def __init__(self, geo_paths: list[str]) -> None:
        self.geo_paths = geo_paths


class SceneFactory:
    class VOPInstance:
        def __init__(
            self,
            name: str,
            vop_template: VOPTemplateLink,
            geometries: GeoPaths,
            description: str = "",
            metadata: Mapping[str, str] = None,
        ) -> None:
            self.name = name
            self.description = description
            self.metadata = metadata
            self.vop_template = vop_template
            self.geometries = geometries

    def new(name: str, part: PartLink, vop_instances: list[VOPInstance], description: str = "") -> Scene:
        scene = Scene(name=name, description=description)
        scene.part_guid = part.key
        for vop_i in vop_instances:
            vop_i_dm = messages.Scene.VOPInstance(name=vop_i.name, description=vop_i.description)
            if vop_i.metadata is not None:
                vop_i_dm.metadata.update(vop_i.metadata)
            vop_i_dm.vop_guid = vop_i.vop_template.key
            vop_i_dm.geometries.geo_paths.extend(vop_i.geometries.geo_paths)
            scene.vops.append(vop_i_dm)
        return scene
