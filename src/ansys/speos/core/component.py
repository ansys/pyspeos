# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
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

"""Provides a way to interact with Speos component feature: Lightbox."""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import Mapping, Optional
import uuid

from ansys.speos.core.generic.constants import ORIGIN
import ansys.speos.core.generic.general_methods as general_methods
from ansys.speos.core.generic.visualization_methods import _VisualData
from ansys.speos.core.kernel import ProtoScene
import ansys.speos.core.project as project
import ansys.speos.core.proto_message_utils as proto_message_utils


class SpeosFileInstance:
    """Represents a SPEOS file containing geometries and materials.

    Geometries are placed in the root part of a project, and oriented according to the axis_system
    argument.

    Parameters
    ----------
    file : str
        SPEOS or Lightbox file to be loaded.
    axis_system : Optional[List[float]]
        Location and orientation to define for the geometry of the SPEOS file,
        [Ox, Oy, Oz, Xx, Xy, Xz, Yx, Yy, Yz, Zx, Zy, Zz].
        By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.
    name : str
        Name chosen for the imported geometry. This name is used as subpart name under the root part
        of the project.
        By default, "" (meaning user has not defined a name), then the name of the SPEOS file
        without extension is taken.
        Note: Materials are named after the name. For instance name.material.1 representing the
        first material of the imported geometry.
    """

    def __init__(
        self,
        file: str,
        axis_system: Optional[list[float]] = None,
        password: str = "",
        name: str = "",
    ) -> None:
        self.file = file
        """SPEOS file."""
        self.axis_system = ORIGIN if axis_system is None else axis_system
        """Location and orientation to define for the geometry of the SPEOS file."""
        self.name = name
        """Name for the imported geometry, and used to name the materials."""
        self.password = password
        """Password for the imported lightbox."""

        if self.name == "":
            self.name = Path(file).stem


class LightBox:
    """Component feature: Lightbox.

    By default, regarding inherent characteristics, an irradiance sensor of type photometric and
    illuminance type planar is chosen. By default, regarding properties, an axis system is
    selected to position the sensor, no layer separation and no ray file generation are chosen.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    scene_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SceneInstance, optional
        Scene instance to provide if the feature does not has to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        scene_instance: Optional[ProtoScene.SceneInstance] = None,
        default_parameters: Optional = None,
    ):
        self._name = name
        self._unique_id = None
        self._project = project
        self.scene_template_link = None
        self._visual_data = _VisualData() if general_methods._GRAPHICS_AVAILABLE else None
        if scene_instance is None:
            self._scene_instance = ProtoScene.SceneInstance(
                name=name, description=description, metadata=metadata
            )
        else:
            self._unique_id = (
                scene_instance.metadata["UniqueId"]
                if scene_instance.metadata["UniqueId"] != ""
                else uuid.uuid4()
            )
            self.scene_template_link = self._project.client[scene_instance.scene_guid]
            self.reset()

    @property
    def visual_data(self):
        """Property containing Lightbox visualization data.

        Returns
        -------
        _VisualData
            Instance of VisualData Class for pyvista.PolyData of feature rays, coordinate_systems.

        """
        if self._visual_data.updated is True:
            return self._visual_data
        else:
            None

    @property
    def axis_system(self) -> list[float]:
        """Property of the lightbox coordinate system.

        Parameters
        ----------
        axis_system: list[float]
            coordinate information

        Returns
        -------
        list[float]
            coordinate information

        """
        return self._scene_instance.axis_system

    @axis_system.setter
    def axis_system(self, axis_system: list[float]) -> None:
        self._scene_instance.axis_system[:] = axis_system

    def set_speos_light_box(self, lightbox: SpeosFileInstance) -> LightBox:
        """Set lightbox file to be used for Lightbox feature.

        Parameters
        ----------
        lightbox: SpeosFileInstance
            lightbox information to be imported.

        Returns
        -------
        ansys.speos.core.component.LightBox
            Lightbox feature

        """
        tmp_lightbox_scene_link = self._project.client.scenes().create()
        tmp_lightbox_scene_link.load_file(file_uri=lightbox.file, password=lightbox.password)
        #### check if need to delete the guid
        self._scene_instance.scene_guid = tmp_lightbox_scene_link.key
        self._scene_instance.axis_system[:] = lightbox.axis_system
        self._scene_instance.name = lightbox.name
        return self

    def commit(self) -> LightBox:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.component.LightBox
            Lightbox feature.
        """
        if general_methods._GRAPHICS_AVAILABLE:
            self._visual_data.updated = False

        # The _unique_id will help to find the correct item in the scene.scenes:
        # the list of SceneInstance
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._scene_instance.metadata["UniqueId"] = self._unique_id

        # Update the scene with the lightbox instance
        if self._project.scene_link:
            update_scene = True
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            scene_inst = next(
                (x for x in scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if scene_inst is not None:
                if scene_inst != self._scene_instance:
                    scene_inst.CopyFrom(self._scene_instance)  # if yes, just replace

                    sim_insts = [
                        x
                        for x in scene_data.simulations
                        if any(self._name in path for path in x.source_paths)
                    ]
                    for sim_inst in sim_insts:
                        current_sources = sim_inst.source_paths
                        sim_inst.source_paths[:] = [
                            x for x in current_sources if self._name not in x
                        ]
                else:
                    update_scene = False
            else:
                scene_data.scenes.append(
                    self._scene_instance
                )  # if no, just add it to the list of lightbox instances

            if update_scene:  # Update scene only if instance has changed
                self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def _to_dict(self) -> dict:
        out_dict = {}

        # SourceInstance (= source guid + source properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            src_inst = next(
                (x for x in scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if src_inst is not None:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=src_inst
                )
            else:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._scene_instance,
                )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._project.client, message=self._scene_instance
            )

        if "scene" not in out_dict.keys():
            # SourceTemplate
            if self.scene_template_link is None:
                out_dict["source"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._scene_instance,
                )
            else:
                out_dict["source"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self.scene_template_link.get(),
                )

        # # handle spectrum & intensity
        # if self._type is not None:
        #     self._type._to_dict(dict_to_complete=out_dict)

        proto_message_utils._replace_properties(json_dict=out_dict)

        return out_dict

    def get(self, key: str = "") -> list[tuple[str, dict]]:
        """Get dictionary corresponding to the project - read only.

        Parameters
        ----------
        key: str

        Returns
        -------
        str | dict
        """
        if key == "":
            return self._to_dict()
        info = proto_message_utils._value_finder_key_startswith(dict_var=self._to_dict(), key=key)
        content = list(info)
        if len(content) != 0:
            content.sort(
                key=lambda x: SequenceMatcher(None, x[0], key).ratio(),
                reverse=True,
            )
            return content[0][1]
        info = proto_message_utils._flatten_dict(dict_var=self._to_dict())
        print("Used key: {} not found in key list: {}.".format(key, info.keys()))

    def __str__(self) -> str:
        """Return the string representation of the source."""
        out_str = ""
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            src_inst = next(
                (x for x in scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if src_inst is None:
                out_str += "local: "
        else:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())
        return out_str

    def reset(self) -> LightBox:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.component.LightBox
            Lightbox feature.
        """
        # Reset sensor template

        # Reset sensor instance
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            # Look if an element corresponds to the _unique_id
            scene_inst = next(
                (x for x in scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if scene_inst is not None:
                self._scene_instance = scene_inst
        return self

    def delete(self) -> LightBox:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.component.LightBox
            Lightbox feature.
        """
        # Delete the sensor template
        # Reset then the sensor_guid (as the sensor template was deleted just above)
        self._scene_instance.scene_guid = ""

        # Remove the sensor from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data
        scene_inst = next(
            (x for x in scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
            None,
        )
        if scene_inst is not None:
            scene_data.scenes.remove(scene_inst)
            self._project.scene_link.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        self._scene_instance.metadata.pop("UniqueId")
        return self
