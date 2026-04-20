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
"""Provide API helpers for the Speos LightBox component feature."""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Mapping, Optional, Tuple, Union
import uuid

import numpy as np

import ansys.speos.core.generic.general_methods as general_methods
from ansys.speos.core.generic.parameters import LightBoxParameters
from ansys.speos.core.generic.visualization_methods import _VisualArrow, _VisualData, local2absolute
from ansys.speos.core.kernel import ProtoScene
import ansys.speos.core.project as project
import ansys.speos.core.proto_message_utils as proto_message_utils
from ansys.speos.core.simulation import BaseSimulation


class LightBoxFile:
    """Represent a LightBox file containing geometries and sources.

    The LightBox content is imported as a scene inside a project scene.

    Parameters
    ----------
    file : pathlib.Path | str
        LightBox file to load.
    password : str, default: ""
        Password for the imported LightBox file.
    """

    def __init__(
        self,
        file: Union[Path, str],
        password: str = "",
    ) -> None:
        self.file = str(file)
        """SPEOS file."""
        self.password = password
        """Password for the imported lightbox."""


class LightBox:
    """Represent the Speos LightBox component feature.

    By default, the global origin axis system is used to position the LightBox.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str, default: ""
        Description of the feature.
    metadata : typing.Optional[typing.Mapping[str, str]], optional
        Metadata of the feature.
    scene_instance : ansys.speos.core.kernel.ProtoScene.SceneInstance, optional
        Existing scene instance to reuse. If ``None``, a new scene instance is created.
    default_parameters : ansys.speos.core.generic.parameters.LightBoxParameters, optional
        Initial parameter values applied to the feature after initialization.
    """

    def __init__(
        self,
        name: str,
        project: project.Project,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        scene_instance: Optional[ProtoScene.SceneInstance] = None,
        default_parameters: Optional[LightBoxParameters] = None,
    ):
        self._name = name
        self._unique_id = None
        self._project = project
        self.scene_template_link = None
        self._visual_data = [] if general_methods._GRAPHICS_AVAILABLE else None
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

        if default_parameters is not None:
            self.axis_system = default_parameters.axis_system

    @property
    def visual_data(self) -> List[_VisualData]:
        """Get LightBox visualization data.

        Returns
        -------
        list[ansys.speos.core.generic.visualization_methods._VisualData]
            Visualization payload containing mesh and ray data in absolute coordinates.

        """
        if len(self._visual_data) != 0 and all(data.updated is True for data in self._visual_data):
            return self._visual_data
        else:
            self._visual_data = [] if general_methods._GRAPHICS_AVAILABLE else None
            feature_pos_info = self.get(key="axis_system")
            for visual_body in self.get(key="bodys"):
                self._visual_data.append(_VisualData())
                for visual_face in visual_body["faces"]:
                    vertices = np.array(visual_face["vertices"]).reshape(-1, 3)
                    vertices = np.array(
                        [local2absolute(vertice, feature_pos_info) for vertice in vertices]
                    )
                    facets = np.array(visual_face["facets"]).reshape(-1, 3)
                    temp = np.full(facets.shape[0], 3)
                    temp = np.vstack(temp)
                    facets = np.hstack((temp, facets))
                    self._visual_data[-1].add_data_mesh(
                        vertices=vertices,
                        facets=facets,
                    )
                self._visual_data[-1].coordinates.origin = np.array(feature_pos_info[:3])
                self._visual_data[-1].coordinates.x_axis = np.array(feature_pos_info[3:6])
                self._visual_data[-1].coordinates.y_axis = np.array(feature_pos_info[6:9])
                self._visual_data[-1].coordinates.z_axis = np.array(feature_pos_info[9:12])
                self._visual_data[-1].updated = True

            for visual_source in self.get(key="sources"):
                source_name = visual_source["name"]
                self._visual_data.append(_VisualData(ray=True))

                for ray_path in self._project.client[
                    self.get(key="scene_guid")
                ].get_source_ray_paths(
                    source_path=source_name, rays_nb=100, raw_data=True, display_data=True
                ):
                    self._visual_data[-1].add_data_line(
                        _VisualArrow(
                            line_vertices=[
                                local2absolute(ray_path.impacts_coordinates, feature_pos_info),
                                ray_path.last_direction,
                            ],
                            color=tuple(ray_path.colors.values),
                            arrow=False,
                        )
                    )
                self._visual_data[-1].coordinates.origin = np.array(feature_pos_info[:3])
                self._visual_data[-1].coordinates.x_axis = np.array(feature_pos_info[3:6])
                self._visual_data[-1].coordinates.y_axis = np.array(feature_pos_info[6:9])
                self._visual_data[-1].coordinates.z_axis = np.array(feature_pos_info[9:12])
                self._visual_data[-1].updated = True
            return self._visual_data

    @property
    def source_paths(self) -> List[str]:
        """Get source paths for sources included in the LightBox.

        Returns
        -------
        list[str]
            Source paths in the form ``<lightbox_name>/<source_name>``.

        """
        sources_data = self._project.client[self._scene_instance.scene_guid].get().sources
        return [f"{self.name}/{data.name}" for data in sources_data]

    @property
    def name(self) -> str:
        """Get the LightBox name.

        Returns
        -------
        str
            Name of the lightbox feature.
        """
        return self._scene_instance.name

    @property
    def axis_system(self) -> List[float]:
        """Property of the lightbox coordinate system.

        Parameters
        ----------
        axis_system : List[float]
            Coordinate system values.

        Returns
        -------
        list[float]
            Coordinate system values.

        """
        return self._scene_instance.axis_system

    @axis_system.setter
    def axis_system(self, axis_system: List[float]) -> None:
        self._scene_instance.axis_system[:] = axis_system

    def set_speos_light_box(self, lightbox: LightBoxFile) -> LightBox:
        """Set the LightBox file used by this feature.

        Parameters
        ----------
        lightbox : ansys.speos.core.component.LightBoxFile
            LightBox file information to import.

        Returns
        -------
        ansys.speos.core.component.LightBox
            Updated LightBox feature.

        """
        tmp_lightbox_scene_link = self._project.client.scenes().create()
        tmp_lightbox_scene_link.load_file(file_uri=lightbox.file, password=lightbox.password)
        #### check if need to delete the guid
        self._scene_instance.scene_guid = tmp_lightbox_scene_link.key
        self._scene_instance.axis_system[:] = self.axis_system
        self._scene_instance.name = self.name

        for simulation in self._project.find(
            name=".*", name_regex=True, feature_type=BaseSimulation
        ):
            if any(self.name in path for path in simulation._simulation_instance.source_paths):
                current_sources = simulation._simulation_instance.source_paths
                new_sources = []
                for source in current_sources:
                    if (self.name not in source) or (source in self.source_paths):
                        new_sources.append(source)
                simulation.source_paths = new_sources
        return self

    def commit(self) -> LightBox:
        """Save the local feature data to the Speos server database.

        Returns
        -------
        ansys.speos.core.component.LightBox
            Updated LightBox feature.
        """
        if general_methods._GRAPHICS_AVAILABLE:
            for item in self._visual_data:
                item.updated = False

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
                        if any(self.name in path for path in x.source_paths)
                    ]
                    for sim_inst in sim_insts:
                        # modify the server
                        sim_inst.CopyFrom(
                            self._project.find(name=sim_inst.name)[0]._simulation_instance
                        )
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
        """Convert the LightBox data to a dictionary representation.

        Returns
        -------
        dict
            Flattened dictionary with resolved GUID references and properties.
        """
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
        proto_message_utils._replace_properties(json_dict=out_dict)

        return out_dict

    def get(self, key: str = "") -> List[Tuple[str, dict]]:
        """Get LightBox information from its dictionary representation - read only.

        Parameters
        ----------
        key : str, default: ""
            Key prefix used to look up a value.

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
        """Return the string representation of the LightBox."""
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
        """Reset local data from the Speos server database.

        Returns
        -------
        ansys.speos.core.component.LightBox
            Updated LightBox feature.
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
        """Delete feature data from the Speos server database.

        Local object data remain available after deletion.

        Returns
        -------
        ansys.speos.core.component.LightBox
            Updated LightBox feature.
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
