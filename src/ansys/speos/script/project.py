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

from typing import Mapping, Optional, Union

import ansys.speos.core as core
import ansys.speos.script.opt_prop as opt_prop
import ansys.speos.script.sensor as sensor
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
            tmp_scene_link = speos.client.scenes().create()
            tmp_scene_link.load_file(path)
            self._fill_features(from_scene=tmp_scene_link)
        return

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

    def find(self, name: str, feature_type: Optional[type] = None) -> Optional[Union[opt_prop.OptProp, source.Source, sensor.Sensor]]:
        """Find a feature.

        Parameters
        ----------
        name : str
            Name of the feature.
        feature_type : type
            Type of the wanted feature.

        Returns
        -------
        Union[ansys.speos.script.opt_prop.OptProp, ansys.speos.script.source.Source, ansys.speos.script.sensor.Sensor], optional
            Found feature, or None.
        """
        if feature_type is None:
            found_feature = next((x for x in self._features if x._name == name), None)
        else:
            found_feature = next((x for x in self._features if type(x) == feature_type and x._name == name), None)
        if found_feature is not None:
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

    def __str__(self):
        """Return the string representation of the project's scene."""
        return str(self.scene_link)

    def _fill_features(self, from_scene: core.Scene):
        """Fill project features from a scene."""
        scene_data = from_scene.get()
        for mat_inst in scene_data.materials:
            op_feature = self.create_optical_property(name=mat_inst.name)
            op_feature._material_instance = mat_inst
            op_feature.vop_template_link = self.client.get_item(key=mat_inst.vop_guid)
            if len(mat_inst.sop_guids) > 0:
                op_feature.sop_template_link = self.client.get_item(key=mat_inst.sop_guids[0])
            op_feature.reset()
            op_feature.commit()

        for src_inst in scene_data.sources:
            src_feat = self.create_source(name=src_inst.name)
            src_feat._source_instance = src_inst
            src_feat.source_template_link = self.client.get_item(key=src_inst.source_guid)
            src_feat.reset()
            src_feat.commit()

        for ssr_inst in scene_data.sensors:
            ssr_feat = self.create_sensor(name=ssr_inst.name)
            ssr_feat._sensor_instance = ssr_inst
            ssr_feat.sensor_template_link = self.client.get_item(key=ssr_inst.sensor_guid)
            ssr_feat.reset()
            ssr_feat.commit()
