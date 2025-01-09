# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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
from typing import Iterator, List

from ansys.api.speos.results.v1.ray_path_pb2 import RayPath
from ansys.api.speos.scene.v2 import scene_pb2 as messages
from ansys.api.speos.scene.v2 import scene_pb2_grpc as service

from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str

Scene = messages.Scene
"""Scene protobuf class : ansys.api.speos.scene.v2.scene_pb2.Scene"""
Scene.__str__ = lambda self: protobuf_message_to_str(self)
Scene.MaterialInstance.__str__ = lambda self: protobuf_message_to_str(self)
Scene.SceneInstance.__str__ = lambda self: protobuf_message_to_str(self)
Scene.SourceInstance.__str__ = lambda self: protobuf_message_to_str(self)
Scene.SensorInstance.__str__ = lambda self: protobuf_message_to_str(self)
Scene.SimulationInstance.__str__ = lambda self: protobuf_message_to_str(self)


class SceneLink(CrudItem):
    """
    Link object for a scene in database.

    Parameters
    ----------
    db : ansys.speos.core.scene.SceneStub
        Database to link to.
    key : str
        Key of the scene in the database.

    Examples
    --------

    >>> from ansys.speos.core.speos import Speos
    >>> from ansys.speos.core.scene import Scene
    >>> speos = Speos(host="localhost", port=50051)
    >>> sce_db = speos.client.scenes()
    >>> sce_link = sce_db.create(message=Scene(name="Empty_Scene"))

    """

    def __init__(self, db, key: str):
        super().__init__(db, key)
        self._actions_stub = db._actions_stub

    def __str__(self) -> str:
        """Return the string representation of the scene."""
        return str(self.get())

    def get(self) -> Scene:
        """Get the datamodel from database.

        Returns
        -------
        scene.Scene
            Scene datamodel.
        """
        return self._stub.read(self)

    def set(self, data: Scene) -> None:
        """Change datamodel in database.

        Parameters
        ----------
        data : scene.Scene
            New scene datamodel.
        """
        self._stub.update(self, data)

    def delete(self) -> None:
        """Remove datamodel from database."""
        self._stub.delete(self)

    # Actions
    def load_file(self, file_uri: str) -> None:
        """
        Load speos file to fill the scene.

        Parameters
        ----------
        file_uri : str
            File to be loaded.
        """
        self._actions_stub.LoadFile(messages.LoadFile_Request(guid=self.key, file_uri=file_uri))

    def get_source_ray_paths(self, source_path: str, rays_nb: int = 100) -> Iterator[RayPath]:
        """
        Retrieve source ray paths.

        Parameters
        ----------
        source_path : str
            Path to the source in the Scene : "<source name>" for a specific source in the current scene,
            or "<sub-scene name>/<source name>" for a specific source in a specific sub scene.
        rays_nb : int, optional
            Number of rays generated by the source.
            By default, ``100``.

        Returns
        -------
        Iterator[ansys.api.speos.results.v1.ray_path_pb2.RayPath]
            Ray paths generated by the source.
        """
        for rp in self._actions_stub.GetSourceRayPaths(
            messages.GetSourceRayPaths_Request(guid=self.key, source_path=source_path, rays_nb=rays_nb)
        ):
            yield rp


class SceneStub(CrudStub):
    """
    Database interactions for scenes.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a SceneStub is to retrieve it from SpeosClient via scenes() method.
    Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos(host="localhost", port=50051)
    >>> sce_db = speos.client.scenes()

    """

    def __init__(self, channel):
        super().__init__(stub=service.ScenesManagerStub(channel=channel))
        self._actions_stub = service.SceneActionsStub(channel=channel)

    def create(self, message: Scene = Scene()) -> SceneLink:
        """Create a new entry.

        Parameters
        ----------
        message : scene.Scene
            Datamodel for the new entry.

        Returns
        -------
        ansys.speos.core.scene.SceneLink
            Link object created.
        """
        resp = CrudStub.create(self, messages.Create_Request(scene=message))
        return SceneLink(self, resp.guid)

    def read(self, ref: SceneLink) -> Scene:
        """Get an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.scene.SceneLink
            Link object to read.

        Returns
        -------
        scene.Scene
            Datamodel of the entry.
        """
        if not ref.stub == self:
            raise ValueError("SceneLink is not on current database")
        resp = CrudStub.read(self, messages.Read_Request(guid=ref.key))
        return resp.scene

    def update(self, ref: SceneLink, data: Scene):
        """Change an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.scene.SceneLink
            Link object to update.
        data : scene.Scene
            New datamodel for the entry.
        """
        if not ref.stub == self:
            raise ValueError("SceneLink is not on current database")
        CrudStub.update(self, messages.Update_Request(guid=ref.key, scene=data))

    def delete(self, ref: SceneLink) -> None:
        """Remove an existing entry.

        Parameters
        ----------
        ref : ansys.speos.core.scene.SceneLink
            Link object to delete.
        """
        if not ref.stub == self:
            raise ValueError("SceneLink is not on current database")
        CrudStub.delete(self, messages.Delete_Request(guid=ref.key))

    def list(self) -> List[SceneLink]:
        """List existing entries.

        Returns
        -------
        List[ansys.speos.core.scene.SceneLink]
            Link objects.
        """
        guids = CrudStub.list(self, messages.List_Request()).guids
        return list(map(lambda x: SceneLink(self, x), guids))
