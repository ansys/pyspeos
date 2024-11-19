# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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
"""Provides a way to gather Speos features."""
from __future__ import annotations

from typing import List, Mapping, Optional, Union
import uuid

import ansys.speos.core as core
import ansys.speos.script.opt_prop as opt_prop
import ansys.speos.script.part as part
import ansys.speos.script.sensor as sensor
import ansys.speos.script.simulation as simulation
import ansys.speos.script.source as source


class Project:
    """A project describes all Speos features (optical properties, sources, sensors, simulations) that user can fill in.
    Project provides functions to create new feature, find a feature.

    It can be created from empty or loaded from a specific file.

    Parameters
    ----------
    speos : ansys.speos.core.speos.Speos
        Speos session (connected to gRPC server).
    path : str
        The project will be loaded from this speos file.
        By default, ``""``, means create from empty.

    Attributes
    ----------
    scene_link : ansys.speos.core.scene.SceneLink
        Link object for the scene in database.
    """

    def __init__(self, speos: core.Speos, path: str = ""):
        self.client = speos.client
        """Speos instance client."""
        self.scene_link = speos.client.scenes().create()
        """Link object for the scene in database."""
        self._features = []
        if len(path):
            self.scene_link.load_file(path)
            self._fill_features()

    # def list(self):
    #    """Return all feature key as a tree, can be used to list all features- Not yet implemented"""
    #    pass

    def create_optical_property(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> opt_prop.OptProp:
        """Create a new Optical Property feature.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        metadata : Mapping[str, str]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
            OptProp feature.
        """
        feature = opt_prop.OptProp(project=self, name=name, description=description, metadata=metadata)
        self._features.append(feature)
        return feature

    def create_source(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> source.Source:
        """Create a new Source feature.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        metadata : Mapping[str, str]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        ansys.speos.script.source.Source
            Source feature.
        """
        feature = source.Source(project=self, name=name, description=description, metadata=metadata)
        self._features.append(feature)
        return feature

    def create_simulation(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> simulation.Simulation:
        """Create a new Simulation feature.

        Parameters
        ----------

        """
        feature = simulation.Simulation(project=self, name=name, description=description, metadata=metadata)
        self._features.append(feature)
        return feature

    def create_sensor(self, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> sensor.Sensor:
        """Create a new Sensor feature.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        metadata : Mapping[str, str]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        ansys.speos.script.sensor.Sensor
            Sensor feature.
        """
        feature = sensor.Sensor(project=self, name=name, description=description, metadata=metadata)
        self._features.append(feature)
        return feature

    def create_root_part(self, name: str = "RootPart", description: str = "", metadata: Mapping[str, str] = {}) -> part.Part:
        """Create the project root part feature.

        Parameters
        ----------
        name : str
            Name of the feature.
            By default, ``"RootPart"``.
        description : str
            Description of the feature.
            By default, ``""``.
        metadata : Mapping[str, str]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        ansys.speos.script.part.Part
            Part feature.
        """
        feature = part.Part(project=self, name=name, description=description, metadata=metadata)
        if self.find(name=name, feature_type=part.Part) is not None:
            raise ValueError("A root part feature already exists with this name: " + name)
        self._features.append(feature)
        return feature

    def find(
        self, name: str, feature_type: Optional[type] = None
    ) -> Optional[Union[opt_prop.OptProp, source.Source, sensor.Sensor, part.Part]]:
        """Find a feature.

        Parameters
        ----------
        name : str
            Name of the feature.
            Possibility to look also for bodies, faces, subpart.
            Example "RootPart/BodyName/FaceName", "RootPart/SubPartName/BodyName/FaceName"
        feature_type : type
            Type of the wanted feature.
            If looking for geometry feature, only precise part.Part as feature_type, whatever looking for subpart, body or face.

        Returns
        -------
        Union[ansys.speos.script.opt_prop.OptProp, ansys.speos.script.source.Source, ansys.speos.script.sensor.Sensor, \
ansys.speos.script.part.Part], optional
            Found feature, or None.
        """
        orig_name = name
        idx = name.find("/")
        if idx != -1:
            name = name[0:idx]

        if feature_type is None:
            found_feature = next((x for x in self._features if x._name == name), None)
        else:
            found_feature = next((x for x in self._features if type(x) == feature_type and x._name == name), None)

        if found_feature is not None:
            if idx != -1:
                found_feature = found_feature.find(orig_name[idx + 1 :])
            return found_feature
        return None

    # def action(self, name: str):
    #    """Act on feature: update, hide/show, copy, ... - Not yet implemented"""
    #    pass

    # def save(self):
    #    """Save class state in file given at construction - Not yet implemented"""
    #    pass

    def delete(self) -> Project:
        """Delete project: erase scene data.
        Delete all features contained in the project.

        Returns
        -------
        ansys.speos.script.project.Project
            Source feature.
        """
        # Erase the scene
        if self.scene_link is not None:
            self.scene_link.set(data=core.Scene())

        # Delete each feature that was created
        for f in self._features:
            f.delete()
        self._features.clear()

        return self

    def __str__(self):
        """Return the string representation of the project's scene."""
        return str(self.scene_link)

    def _fill_bodies(self, body_guids: List[str], feat_host: Union[part.Part, part.Part.SubPart]):
        """Fill part of sub part features from a list of body guids."""
        for b_link in self.client.get_items(keys=body_guids, item_type=core.BodyLink):
            b_data = b_link.get()
            b_feat = feat_host.create_body(name=b_data.name)
            b_feat.body_link = b_link
            b_feat._body = b_data  # instead of b_feat.reset() - this avoid a useless read in server
            for f_link in self.client.get_items(keys=b_data.face_guids, item_type=core.FaceLink):
                f_data = f_link.get()
                f_feat = b_feat.create_face(name=f_data.name)
                f_feat.face_link = f_link
                f_feat._face = f_data  # instead of f_feat.reset() - this avoid a useless read in server

    def _add_unique_ids(self):
        scene_data = self.scene_link.get()

        root_part_link = self.client.get_item(key=scene_data.part_guid)
        root_part = root_part_link.get()
        update_rp = False
        for sub_part in root_part.parts:
            if sub_part.description.startswith("UniqueId_") == False:
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

        for sim_inst in scene_data.simulations:
            if sim_inst.metadata["UniqueId"] == "":
                sim_inst.metadata["UniqueId"] = str(uuid.uuid4())

        self.scene_link.set(data=scene_data)

    def _fill_features(self):
        """Fill project features from a scene."""
        self._add_unique_ids()

        scene_data = self.scene_link.get()

        part = self.client.get_item(key=scene_data.part_guid).get()
        part_feat = self.find(name="RootPart")
        if part_feat is None:
            part_feat = self.create_root_part()
            self._fill_bodies(body_guids=part.body_guids, feat_host=part_feat)

        for sp in part.parts:
            sp_feat = part_feat.create_sub_part(name=sp.name, description=sp.description)
            if sp.description.startswith("UniqueId_"):
                idx = sp.description.find("_")
                sp_feat._unique_id = sp.description[idx + 1 :]
            sp_feat.part_link = self.client.get_item(key=sp.part_guid)
            sp_feat._part_instance = sp
            self._fill_bodies(body_guids=sp_feat.part_link.get().body_guids, feat_host=sp_feat)
            sp_feat.reset()
        part_feat.reset()
        part_feat.commit()

        for mat_inst in scene_data.materials:
            op_feature = self.create_optical_property(name=mat_inst.name)
            op_feature._unique_id = mat_inst.metadata["UniqueId"]
            op_feature._material_instance = mat_inst
            op_feature.vop_template_link = self.client.get_item(key=mat_inst.vop_guid)
            if len(mat_inst.sop_guids) > 0:
                op_feature.sop_template_link = self.client.get_item(key=mat_inst.sop_guids[0])
            else:  # Specific case for ambient material
                op_feature._sop_template = None
            op_feature.reset()

        for src_inst in scene_data.sources:
            src_feat = self.create_source(name=src_inst.name)
            src_feat._unique_id = src_inst.metadata["UniqueId"]
            src_feat._source_instance = src_inst
            src_feat.source_template_link = self.client.get_item(key=src_inst.source_guid)
            src_feat.reset()

        for ssr_inst in scene_data.sensors:
            ssr_feat = self.create_sensor(name=ssr_inst.name)
            ssr_feat._unique_id = ssr_inst.metadata["UniqueId"]
            ssr_feat._sensor_instance = ssr_inst
            ssr_feat.sensor_template_link = self.client.get_item(key=ssr_inst.sensor_guid)
            ssr_feat.reset()

        for sim_inst in scene_data.simulations:
            sim_feat = self.create_simulation(name=sim_inst.name)
            sim_feat._unique_id = sim_inst.metadata["UniqueId"]
            sim_feat._simulation_instance = sim_inst
            sim_feat.simulation_template_link = self.client.get_item(key=sim_inst.simulation_guid)
            sim_feat.reset()
            # To get default values related to job -> simu properties
            if sim_feat._simulation_template.HasField("direct_mc_simulation_template"):
                sim_feat.set_direct()
            elif sim_feat._simulation_template.HasField("inverse_mc_simulation_template"):
                sim_feat.set_inverse()
            elif sim_feat._simulation_template.HasField("interactive_simulation_template"):
                sim_feat.set_interactive()
