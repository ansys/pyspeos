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
import os
from pathlib import Path
from typing import List, Mapping, Optional, Tuple, Union
import uuid

import numpy as np

from ansys.speos.core import opt_prop, part
import ansys.speos.core.generic.general_methods as general_methods
from ansys.speos.core.generic.parameters import LightBoxParameters
from ansys.speos.core.generic.visualization_methods import _VisualArrow, _VisualData, local2absolute
from ansys.speos.core.ground_plane import GroundPlane
from ansys.speos.core.kernel import BodyLink, FaceLink, ProtoScene
import ansys.speos.core.project as project
import ansys.speos.core.proto_message_utils as proto_message_utils
from ansys.speos.core.simulation import BaseSimulation
from ansys.speos.core.source import (
    SourceAmbientEnvironment,
    SourceAmbientNaturalLight,
    SourceDisplay,
    SourceLuminaire,
    SourceRayFile,
    SourceSurface,
)


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
        password: str | None = None,
    ) -> None:
        self.file = str(file)
        """SPEOS file."""
        if password is None:
            password = os.getenv("PYSPEOS_ENCRYPTED_PASSWORD", "")
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
        self._features = []
        self._visual_data = [] if general_methods._GRAPHICS_AVAILABLE else None
        if scene_instance is None:
            self.scene_template_link = self._project.client.scenes().create()
            self._scene_instance = ProtoScene.SceneInstance(
                name=name, description=description, metadata=metadata
            )
        else:
            self._unique_id = scene_instance.metadata["UniqueId"]
            self.scene_template_link = self._project.client[scene_instance.scene_guid]
            # reset will fill _scene_instance from project (using _unique_id)
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
        self.scene_template_link.load_file(file_uri=lightbox.file, password=lightbox.password)
        self._scene_instance.scene_guid = self.scene_template_link.key
        self._fill_features()

        # the following part is to check if any simulation contains source paths from the
        # current lightbox whose light source has been modified via set_speos_light_box.
        # If there is such simulation,
        # 1. the source paths from the current lightbox will be removed from this simulation
        # if they are not included in the new lightbox file.
        # 2. kept if they are still included in the new lightbox file.
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

    def _fill_subparts(
        self, sub_parts: List[part.Part.SubPart], feat_host: Union[part.Part, part.Part.SubPart]
    ):
        for sp in sub_parts:
            sp_feat = feat_host.create_sub_part(name=sp.name, description=sp.description)
            if sp.description.startswith("UniqueId_"):
                idx = sp.description.find("_")
                sp_feat._unique_id = sp.description[idx + 1 :]
            sp_feat.part_link = self._project.client[sp.part_guid]
            part_data = sp_feat.part_link.get()
            sp_feat._part_instance = sp
            sp_feat._part = (
                part_data  # instead of sp_feat.reset() - this avoid a useless read in server
            )
            self._fill_bodies(body_guids=part_data.body_guids, feat_host=sp_feat)
            self._fill_subparts(sub_parts=part_data.parts, feat_host=sp_feat)

    def _fill_bodies(
        self,
        body_guids: List[str],
        feat_host: Union[part.Part, part.Part.SubPart],
    ):
        """Fill part of sub part features from a list of body guids."""
        for b_link in self._project.client.get_items(keys=body_guids, item_type=BodyLink):
            b_data = b_link.get()
            if not b_data.face_guids:
                continue
            b_feat = feat_host.create_body(name=b_data.name)
            b_feat.body_link = b_link
            b_feat._body = b_data  # instead of b_feat.reset() - this avoid a useless read in server

            f_links = self._project.client.get_items(keys=b_data.face_guids, item_type=FaceLink)
            face_db = self._project.client.faces()
            if face_db._is_batch_available:
                f_data_list = face_db.read_batch(refs=f_links)
                for f_data, f_link in zip(f_data_list, f_links):
                    f_feat = b_feat.create_face(name=f_data.name)
                    f_feat.face_link = f_link
                    f_feat._face = (
                        f_data  # instead of f_feat.reset() - this avoid a useless read in server
                    )
            else:
                for f_link in f_links:
                    f_data = f_link.get()
                    f_feat = b_feat.create_face(name=f_data.name)
                    f_feat.face_link = f_link
                    f_feat._face = (
                        f_data  # instead of f_feat.reset() - this avoid a useless read in server
                    )

    def _add_unique_ids(self):
        scene_data = self.scene_template_link.get()

        root_part_link = self._project.client[scene_data.part_guid]
        root_part = root_part_link.get()
        update_rp = False
        for sub_part in root_part.parts:
            if sub_part.description.startswith("UniqueId_") is False:
                sub_part.description = "UniqueId_" + str(uuid.uuid4())
                update_rp = True
        if update_rp:
            root_part_link.set(data=root_part)

        for mat_inst in scene_data.materials:
            if mat_inst.metadata["UniqueId"] == "":
                mat_inst.metadata["UniqueId"] = str(uuid.uuid4())

        for src_inst in scene_data.sources:
            if src_inst.metadata["UniqueId"] == "":
                src_inst.metadata["UniqueId"] = str(uuid.uuid4())

        for ssr_inst in scene_data.sensors:
            if ssr_inst.metadata["UniqueId"] == "":
                ssr_inst.metadata["UniqueId"] = str(uuid.uuid4())

        for scene_inst in scene_data.scenes:
            if scene_inst.metadata["UniqueId"] == "":
                scene_inst.metadata["UniqueId"] = str(uuid.uuid4())

        for sim_inst in scene_data.simulations:
            if sim_inst.metadata["UniqueId"] == "":
                sim_inst.metadata["UniqueId"] = str(uuid.uuid4())

        self.scene_template_link.set(data=scene_data)

    def _fill_features(self):
        """Fill project features from a scene."""
        # delete previously created features
        for feature in self._features:
            feature.delete()
        # load new features
        self._add_unique_ids()

        scene_data = self.scene_template_link.get()

        root_part_link = self._project.client[scene_data.part_guid]
        root_part_data = root_part_link.get()
        root_part_feats = [
            feature for feature in self._features if feature.name == f"{self.name}/RootPart"
        ]
        root_part_feat = None
        if len(root_part_feats) == 0:
            root_part_feat = part.Part(
                project=self._project, name=f"{self.name}/RootPart", description="", metadata=None
            )
            self._features.append(root_part_feat)
            root_part_data.name = f"{self.name}/RootPart"
            root_part_link.set(root_part_data)
            self._fill_bodies(body_guids=root_part_data.body_guids, feat_host=root_part_feat)
        else:
            root_part_feat = root_part_feats[0]

        root_part_feat.part_link = root_part_link
        root_part_feat._part = root_part_data
        # instead of root_part_feat.reset() - this avoid a useless read in server

        self._fill_subparts(sub_parts=root_part_data.parts, feat_host=root_part_feat)

        for mat_inst in scene_data.materials:
            op_feature = opt_prop.OptProp(
                project=self._project,
                name=f"{self.name}/{mat_inst.name}",
                description="",
                metadata=None,
                default_parameters=None,
            )
            op_feature._fill(mat_inst=mat_inst)
            self._features.append(op_feature)

        for src_inst in scene_data.sources:
            src_feat = None
            if src_inst.HasField("rayfile_properties"):
                src_feat = SourceRayFile(
                    project=self._project,
                    name=f"{self.name}/{src_inst.name}",
                    source_instance=src_inst,
                    default_parameters=None,
                )
            elif src_inst.HasField("luminaire_properties"):
                src_feat = SourceLuminaire(
                    project=self._project,
                    name=f"{self.name}/{src_inst.name}",
                    source_instance=src_inst,
                    default_parameters=None,
                )
            elif src_inst.HasField("surface_properties"):
                src_feat = SourceSurface(
                    project=self._project,
                    name=f"{self.name}/{src_inst.name}",
                    source_instance=src_inst,
                    default_parameters=None,
                )
            elif src_inst.HasField("display_properties"):
                src_feat = SourceDisplay(
                    project=self._project,
                    name=f"{self.name}/{src_inst.name}",
                    source_instance=src_inst,
                    default_parameters=None,
                )
            elif src_inst.HasField("ambient_properties"):
                if src_inst.ambient_properties.HasField("natural_light_properties"):
                    src_feat = SourceAmbientNaturalLight(
                        project=self._project,
                        name=f"{self.name}/{src_inst.name}",
                        source_instance=src_inst,
                        default_parameters=None,
                    )
                elif src_inst.ambient_properties.HasField("environment_map_properties"):
                    src_feat = SourceAmbientEnvironment(
                        project=self._project,
                        name=f"{self.name}/{src_inst.name}",
                        source_instance=src_inst,
                        default_parameters=None,
                    )
            if src_feat is not None:
                self._features.append(src_feat)

        # ground plane
        if scene_data.HasField("ground"):
            ground_feat = GroundPlane(project=self, ground=scene_data.ground)

            if ground_feat is not None:
                self._features.append(ground_feat)

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

                    # the following part is to update the simulation source paths of which
                    # the corresponding lightbox instance has been modified via set_speos_light_box
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

        # SceneInstance (= scene guid + scene properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            scene_inst = next(
                (x for x in scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if scene_inst is not None:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=scene_inst
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
            # SceneTemplate
            if self.scene_template_link is None:
                out_dict["scene"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._scene_template,
                )
            else:
                out_dict["scene"] = proto_message_utils._replace_guids(
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
            scene_inst = next(
                (x for x in scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if scene_inst is None:
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
        # Delete the scene template
        if self.scene_template_link is not None:
            self.scene_template_link.delete()
            self.scene_template_link = None

        # Reset then the scene_guid (as the scene template was deleted just above)
        self._scene_instance.scene_guid = ""

        # Remove the scene instance from the scene
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
