# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
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

from pathlib import Path
import re
from typing import TYPE_CHECKING, List, Mapping, Optional, Union
import uuid

from google.protobuf.internal.containers import RepeatedScalarFieldContainer
import numpy as np

import ansys.speos.core.body as body
import ansys.speos.core.face as face
from ansys.speos.core.generic.general_methods import graphics_required
from ansys.speos.core.generic.visualization_methods import local2absolute
from ansys.speos.core.kernel.body import BodyLink
from ansys.speos.core.kernel.face import FaceLink
from ansys.speos.core.kernel.part import ProtoPart
from ansys.speos.core.kernel.scene import ProtoScene
import ansys.speos.core.opt_prop as opt_prop
import ansys.speos.core.part as part
import ansys.speos.core.proto_message_utils as proto_message_utils
from ansys.speos.core.sensor import (
    Sensor3DIrradiance,
    SensorCamera,
    SensorIrradiance,
    SensorRadiance,
)
from ansys.speos.core.simulation import (
    SimulationDirect,
    SimulationInteractive,
    SimulationInverse,
)
from ansys.speos.core.source import (
    SourceAmbientNaturalLight,
    SourceLuminaire,
    SourceRayFile,
    SourceSurface,
)
from ansys.speos.core.speos import Speos

try:
    from ansys.speos.core.generic.general_methods import run_if_graphics_required

    run_if_graphics_required(warning=True)
except ImportError as err:  # pragma: no cover
    raise err

if TYPE_CHECKING:  # pragma: no cover
    import pyvista as pv

    from ansys.tools.visualization_interface import Plotter


class Project:
    """A project describes all Speos features.

    This includes optical properties, sources, sensors, simulations that user can fill in.
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
    scene_link : ansys.speos.core.kernel.scene.SceneLink
        Link object for the scene in database.
    """

    def __init__(self, speos: Speos, path: Optional[Union[str, Path]] = ""):
        self.client = speos.client
        """Speos instance client."""
        self.scene_link = speos.client.scenes().create()
        """Link object for the scene in database."""
        self._features = []
        path = str(path)
        if len(path):
            self.scene_link.load_file(path)
            self._fill_features()

    # def list(self):
    #    """Return all feature key as a tree.
    #
    #    Can be used to list all features- Not yet implemented.
    #    """
    #    pass

    def create_optical_property(
        self,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> opt_prop.OptProp:
        """Create a new Optical Property feature.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        metadata : Optional[Mapping[str, str]]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            OptProp feature.
        """
        existing_features = self.find(name=name)
        if len(existing_features) != 0:
            msg = "Feature {}: {} has a conflict name with an existing feature.".format(
                opt_prop.OptProp, name
            )
            raise ValueError(msg)

        if metadata is None:
            metadata = {}
        feature = opt_prop.OptProp(
            project=self, name=name, description=description, metadata=metadata
        )
        self._features.append(feature)
        return feature

    def create_source(
        self,
        name: str,
        description: str = "",
        feature_type: type = SourceSurface,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Union[SourceSurface, SourceRayFile, SourceLuminaire, SourceAmbientNaturalLight]:
        """Create a new Source feature.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        feature_type: type
            Source type to be created.
            By default, ``ansys.speos.core.source.SourceSurface``.
            Allowed types:
            Union[ansys.speos.core.source.SourceSurface, ansys.speos.core.source.SourceRayFile, \
            ansys.speos.core.source.SourceLuminaire, \
            ansys.speos.core.source.SourceAmbientNaturalLight].
        metadata : Optional[Mapping[str, str]]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        Union[ansys.speos.core.source.SourceSurface,ansys.speos.core.source.SourceRayFile,\
        ansys.speos.core.source.SourceLuminaire, ansys.speos.core.source.SourceAmbientNaturalLight]
            Source class instance.
        """
        if metadata is None:
            metadata = {}

        existing_features = self.find(name=name)
        if len(existing_features) != 0:
            msg = "Feature {}: {} has a conflict name with an existing feature.".format(
                feature_type, name
            )
            raise ValueError(msg)
        feature = None
        match feature_type.__name__:
            case "SourceSurface":
                feature = SourceSurface(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case "SourceRayFile":
                feature = SourceRayFile(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case "SourceLuminaire":
                feature = SourceLuminaire(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case "SourceAmbientNaturalLight":
                feature = SourceAmbientNaturalLight(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case _:
                msg = "Requested feature {} does not exist in supported list {}".format(
                    feature_type, [SourceSurface, SourceLuminaire, SourceRayFile]
                )
                raise TypeError(msg)
        self._features.append(feature)
        return feature

    def create_simulation(
        self,
        name: str,
        description: str = "",
        feature_type: type = SimulationDirect,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Union[SimulationDirect, SimulationInteractive, SimulationInverse]:
        """Create a new Simulation feature.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        feature_type: type
            Simulation type to be created.
            By default, ``ansys.speos.core.simulation.SimulationDirect``.
            Allowed types: Union[ansys.speos.core.simulation.SimulationDirect, \
            ansys.speos.core.simulation.SimulationInteractive, \
            ansys.speos.core.simulation.SimulationInverse].
        metadata : Optional[Mapping[str, str]]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        Union[ansys.speos.core.simulation.SimulationDirect,\
        ansys.speos.core.simulation.SimulationInteractive,\
        ansys.speos.core.simulation.SimulationInverse]
            Simulation class instance
        """
        if metadata is None:
            metadata = {}

        existing_features = self.find(name=name)
        if len(existing_features) != 0:
            msg = "Feature {}: {} has a conflict name with an existing feature.".format(
                feature_type, name
            )
            raise ValueError(msg)
        feature = None
        match feature_type.__name__:
            case "SimulationDirect":
                feature = SimulationDirect(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case "SimulationInverse":
                feature = SimulationInverse(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case "SimulationInteractive":
                feature = SimulationInteractive(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case _:
                msg = "Requested feature {} does not exist in supported list {}".format(
                    feature_type,
                    [
                        SimulationDirect,
                        SimulationInverse,
                        SimulationInteractive,
                    ],
                )
                raise TypeError(msg)
        self._features.append(feature)
        return feature

    def create_sensor(
        self,
        name: str,
        description: str = "",
        feature_type: type = SensorIrradiance,
        metadata: Optional[Mapping[str, str]] = None,
    ) -> Union[SensorCamera, SensorRadiance, SensorIrradiance, Sensor3DIrradiance]:
        """Create a new Sensor feature.

        Parameters
        ----------
        name : str
            Name of the feature.
        description : str
            Description of the feature.
            By default, ``""``.
        feature_type: type
            Sensor type to be created.
            By default, ``ansys.speos.core.sensor.SensorIrradiance``.
            Allowed types: Union[ansys.speos.core.sensor.SensorCamera,\
            ansys.speos.core.sensor.SensorRadiance, \
            ansys.speos.core.sensor.SensorIrradiance, \
            ansys.speos.core.sensor.Sensor3DIrradiance].
        metadata : Optional[Mapping[str, str]]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        Union[ansys.speos.core.sensor.SensorCamera,\
        ansys.speos.core.sensor.SensorRadiance, ansys.speos.core.sensor.SensorIrradiance, \
        ansys.speos.core.sensor.Sensor3DIrradiance]
            Sensor class instance.
        """
        if metadata is None:
            metadata = {}

        existing_features = self.find(name=name)
        if len(existing_features) != 0:
            msg = "Feature {}: {} has a conflict name with an existing feature.".format(
                feature_type, name
            )
            raise ValueError(msg)
        feature = None
        match feature_type.__name__:
            case "SensorIrradiance":
                feature = SensorIrradiance(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case "SensorRadiance":
                feature = SensorRadiance(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case "SensorCamera":
                feature = SensorCamera(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case "Sensor3DIrradiance":
                feature = Sensor3DIrradiance(
                    project=self,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            case _:
                msg = "Requested feature {} does not exist in supported list {}".format(
                    feature_type,
                    [SensorIrradiance, SensorRadiance, SensorCamera, Sensor3DIrradiance],
                )
                raise TypeError(msg)
        self._features.append(feature)
        return feature

    def create_root_part(
        self,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
    ) -> part.Part:
        """Create the project root part feature.

        If a root part is already created in the project, it is returned.

        Parameters
        ----------
        description : str
            Description of the feature.
            By default, ``""``.
        metadata : Optional[Mapping[str, str]]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        ansys.speos.core.part.Part
            Part feature.
        """
        if metadata is None:
            metadata = {}

        name = "RootPart"
        existing_rp = self.find(name="", feature_type=part.Part)
        if existing_rp:
            return existing_rp[0]

        feature = part.Part(project=self, name=name, description=description, metadata=metadata)
        self._features.append(feature)
        return feature

    def find(
        self,
        name: str,
        name_regex: bool = False,
        feature_type: Optional[type] = None,
    ) -> List[
        Union[
            opt_prop.OptProp,
            SourceSurface,
            SourceLuminaire,
            SourceRayFile,
            SensorIrradiance,
            SensorRadiance,
            SensorCamera,
            SimulationDirect,
            SimulationInverse,
            SimulationInteractive,
            part.Part,
            body.Body,
            face.Face,
            part.Part.SubPart,
        ]
    ]:
        """Find feature(s) by name (possibility to use regex) and by feature type.

        Parameters
        ----------
        name : str
            Name of the feature.
        name_regex : bool
            Allows to use regex for name parameter.
            By default, ``False``, means that regex is not used for name parameter.
        feature_type : type
            Type of the wanted features.
            Mandatory to fill for geometry features.
            By default, ``None``, means that all features will be considered
            (except geometry features).

        Returns
        -------
        List[Union[ansys.speos.core.opt_prop.OptProp, ansys.speos.core.source.Surface, \
        ansys.speos.core.source.RayFile, ansys.speos.core.source.Luminaire, \
        ansys.speos.core.sensor.Camera, \
        ansys.speos.core.sensor.Radiance, ansys.speos.core.sensor.Irradiance, \
        ansys.speos.core.simulation.Direct, ansys.speos.core.simulation.Interactive, \
        ansys.speos.core.simulation.Inverse, ansys.speos.core.part.Part, \
        ansys.speos.core.body.Body, \
        ansys.speos.core.face.Face, ansys.speos.core.part.Part.SubPart]]
            Found features.

        Examples
        --------
        >>> # From name only
        >>> find(name="Camera.1")
        >>> # Specify feature type
        >>> find(name="Camera.1", feature_type=ansys.speos.core.sensor.SensorCamera)
        >>> # Using regex
        >>> find(
        >>>     name="Camera.*",
        >>>     name_regex=True,
        >>>     feature_type=ansys.speos.core.sensor.SensorCamera,
        >>> )
        Here some examples when looking for a geometry feature:
        (always precise feature_type)

        >>> # Root part
        >>> find(name="", feature_type=ansys.speos.core.part.Part)
        >>> # Body in root part
        >>> find(name="BodyName", feature_type=ansys.speos.core.body.Body)
        >>> # Face from body in root part
        >>> find(name="BodyName/FaceName", feature_type=ansys.speos.core.face.Face)
        >>> # Sub part in root part
        >>> find(name="SubPartName", feature_type=ansys.speos.core.part.Part.SubPart)
        >>> # Face in a body from sub part in root part :
        >>> find(name="SubPartName/BodyName/FaceName", feature_type=ansys.speos.core.face.Face)
        >>> # Regex can be use at each level separated by "/"
        >>> find(name="Body.*/Face.*", name_regex=True, feature_type=ansys.speos.core.face.Face)
        >>> # All faces of a specific body
        >>> find(name="BodyName/.*", name_regex=True, feature_type=ansys.speos.core.face.Face)
        >>> # All geometry features at first level (whatever their type: body, face, sub part)
        >>> find(name=".*", name_regex=True, feature_type=ansys.speos.core.part.Part)
        """
        orig_feature_type = None
        if (
            feature_type == part.Part
            or feature_type == part.Part.SubPart
            or feature_type == body.Body
            or feature_type == face.Face
        ):
            if feature_type != part.Part:
                orig_feature_type = feature_type
                feature_type = part.Part
            if name == "":
                name = "RootPart"
            else:
                name = "RootPart/" + name

        orig_name = name
        idx = name.find("/")
        if idx != -1:
            name = name[0:idx]

        if name_regex:
            p = re.compile(name)

        found_features = []
        if feature_type is None:
            if name_regex:
                found_features.extend([x for x in self._features if p.match(x._name)])
            else:
                found_features.extend([x for x in self._features if x._name == name])
        else:
            if name_regex:
                found_features.extend(
                    [
                        x
                        for x in self._features
                        if (
                            isinstance(x, feature_type)
                            or (isinstance(x._type, feature_type) if hasattr(x, "_type") else False)
                        )
                        and p.match(x._name)
                    ]
                )
            else:
                found_features.extend(
                    [
                        x
                        for x in self._features
                        if (
                            isinstance(x, feature_type)
                            or (isinstance(x._type, feature_type) if hasattr(x, "_type") else False)
                        )
                        and x._name == name
                    ]
                )

        if found_features and idx != -1:
            tmp = [
                f.find(
                    name=orig_name[idx + 1 :],
                    name_regex=name_regex,
                    feature_type=orig_feature_type,
                )
                for f in found_features
            ]

            found_features.clear()
            for feats in tmp:
                found_features.extend(feats)

        return found_features

    # def action(self, name: str):
    #    """Act on feature: update, hide/show, copy, ... - Not yet implemented"""
    #    pass

    # def save(self):
    #     """Save class state in file given at construction - Not yet implemented"""
    #     pass

    def delete(self) -> Project:
        """Delete project: erase scene data.

        Delete all features contained in the project.

        Returns
        -------
        ansys.speos.core.project.Project
            Project feature.
        """
        # Erase the scene
        if self.scene_link is not None:
            self.scene_link.set(data=ProtoScene())

        # Delete each feature that was created
        for f in self._features:
            f.delete()
        self._features.clear()

        return self

    def _to_dict(self) -> dict:
        # Replace all guids by content of objects in the dict
        output_dict = proto_message_utils._replace_guids(
            speos_client=self.client,
            message=self.scene_link.get(),
            ignore_simple_key="part_guid",
        )

        # For each feature, replace properties by putting them at correct place
        for k, v in output_dict.items():
            if type(v) is list:
                for inside_dict in v:
                    if k == "simulations":
                        sim_feat = self.find(
                            name=inside_dict["name"],
                            feature_type=SimulationDirect,
                        )
                        if len(sim_feat) == 0:
                            sim_feat = self.find(
                                name=inside_dict["name"],
                                feature_type=SimulationInverse,
                            )
                        if len(sim_feat) == 0:
                            sim_feat = self.find(
                                name=inside_dict["name"],
                                feature_type=SimulationInteractive,
                            )
                        sim_feat = sim_feat[0]
                        if sim_feat.job_link is None:
                            inside_dict["simulation_properties"] = (
                                proto_message_utils._replace_guids(
                                    speos_client=self.client,
                                    message=sim_feat._job,
                                    ignore_simple_key="scene_guid",
                                )
                            )
                        else:
                            inside_dict["simulation_properties"] = (
                                proto_message_utils._replace_guids(
                                    speos_client=self.client,
                                    message=sim_feat.job_link.get(),
                                    ignore_simple_key="scene_guid",
                                )
                            )

                    proto_message_utils._replace_properties(inside_dict)
        return output_dict

    def get(self) -> dict:
        """Get dictionary corresponding to the project - read only."""
        return self._to_dict()

    def find_key(self, key: str) -> List[tuple[str, dict]]:
        """Get values corresponding to the key in project dictionary - read only.

        Parameters
        ----------
        key : str
            Key to search in the project dictionary.

        Returns
        -------
        List[tuple[str, dict]]
            List of matching objects containing for each its x_path and its value.
        """
        return proto_message_utils._finder_by_key(dict_var=self._to_dict(), key=key)

    def __str__(self):
        """Return the string representation of the project's scene."""
        return proto_message_utils.dict_to_str(dict=self._to_dict())

    def _fill_bodies(
        self,
        body_guids: List[str],
        feat_host: Union[part.Part, part.Part.SubPart],
    ):
        """Fill part of sub part features from a list of body guids."""
        for b_link in self.client.get_items(keys=body_guids, item_type=BodyLink):
            b_data = b_link.get()
            b_feat = feat_host.create_body(name=b_data.name)
            b_feat.body_link = b_link
            b_feat._body = b_data  # instead of b_feat.reset() - this avoid a useless read in server

            f_links = self.client.get_items(keys=b_data.face_guids, item_type=FaceLink)
            face_db = self.client.faces()
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
        scene_data = self.scene_link.get()

        root_part_link = self.client[scene_data.part_guid]
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

        for sim_inst in scene_data.simulations:
            if sim_inst.metadata["UniqueId"] == "":
                sim_inst.metadata["UniqueId"] = str(uuid.uuid4())

        self.scene_link.set(data=scene_data)

    def _fill_features(self):
        """Fill project features from a scene."""
        self._add_unique_ids()

        scene_data = self.scene_link.get()

        root_part_link = self.client[scene_data.part_guid]
        root_part_data = root_part_link.get()
        root_part_feats = self.find(name="", feature_type=part.Part)
        root_part_feat = None
        if not root_part_feats:
            root_part_feat = self.create_root_part()
            root_part_data.name = "RootPart"
            root_part_link.set(root_part_data)
            self._fill_bodies(body_guids=root_part_data.body_guids, feat_host=root_part_feat)
        else:
            root_part_feat = root_part_feats[0]

        root_part_feat.part_link = root_part_link
        root_part_feat._part = root_part_data
        # instead of root_part_feat.reset() - this avoid a useless read in server

        for sp in root_part_data.parts:
            sp_feat = root_part_feat.create_sub_part(name=sp.name, description=sp.description)
            if sp.description.startswith("UniqueId_"):
                idx = sp.description.find("_")
                sp_feat._unique_id = sp.description[idx + 1 :]
            sp_feat.part_link = self.client[sp.part_guid]
            part_data = sp_feat.part_link.get()
            sp_feat._part_instance = sp
            sp_feat._part = (
                part_data  # instead of sp_feat.reset() - this avoid a useless read in server
            )
            self._fill_bodies(body_guids=part_data.body_guids, feat_host=sp_feat)

        for mat_inst in scene_data.materials:
            if len(self.find(name=mat_inst.name)) == 0:
                op_feature = self.create_optical_property(name=mat_inst.name)
                op_feature._fill(mat_inst=mat_inst)

        for src_inst in scene_data.sources:
            if src_inst.name in [_._name for _ in self._features]:
                continue
            src_feat = None
            if src_inst.HasField("rayfile_properties"):
                src_feat = SourceRayFile(
                    project=self,
                    name=src_inst.name,
                    source_instance=src_inst,
                    default_values=False,
                )
            elif src_inst.HasField("luminaire_properties"):
                src_feat = SourceLuminaire(
                    project=self,
                    name=src_inst.name,
                    source_instance=src_inst,
                    default_values=False,
                )
            elif src_inst.HasField("surface_properties"):
                src_feat = SourceSurface(
                    project=self,
                    name=src_inst.name,
                    source_instance=src_inst,
                    default_values=False,
                )
            elif src_inst.HasField("ambient_properties"):
                if src_inst.ambient_properties.HasField("natural_light_properties"):
                    src_feat = SourceAmbientNaturalLight(
                        project=self,
                        name=src_inst.name,
                        source_instance=src_inst,
                        default_values=False,
                    )
            if src_feat is not None:
                self._features.append(src_feat)

        for ssr_inst in scene_data.sensors:
            if ssr_inst.name in [_._name for _ in self._features]:
                continue
            ssr_feat = None
            if ssr_inst.HasField("irradiance_properties"):
                ssr_feat = SensorIrradiance(
                    project=self,
                    name=ssr_inst.name,
                    sensor_instance=ssr_inst,
                    default_values=False,
                )
            elif ssr_inst.HasField("radiance_properties"):
                ssr_feat = SensorRadiance(
                    project=self,
                    name=ssr_inst.name,
                    sensor_instance=ssr_inst,
                    default_values=False,
                )
            elif ssr_inst.HasField("camera_properties"):
                ssr_feat = SensorCamera(
                    project=self,
                    name=ssr_inst.name,
                    sensor_instance=ssr_inst,
                    default_values=False,
                )
            elif ssr_inst.HasField("irradiance_3d_properties"):
                ssr_feat = Sensor3DIrradiance(
                    project=self,
                    name=ssr_inst.name,
                    sensor_instance=ssr_inst,
                    default_values=False,
                )
            self._features.append(ssr_feat)

        for sim_inst in scene_data.simulations:
            if sim_inst.name in [_._name for _ in self._features]:
                continue
            sim_feat = None
            simulation_template_link = self.client[sim_inst.simulation_guid].get()
            if simulation_template_link.HasField("direct_mc_simulation_template"):
                sim_feat = SimulationDirect(
                    project=self,
                    name=sim_inst.name,
                    simulation_instance=sim_inst,
                    default_values=False,
                )
            elif simulation_template_link.HasField("inverse_mc_simulation_template"):
                sim_feat = SimulationInverse(
                    project=self,
                    name=sim_inst.name,
                    simulation_instance=sim_inst,
                    default_values=False,
                )
            elif simulation_template_link.HasField("interactive_simulation_template"):
                sim_feat = SimulationInteractive(
                    project=self,
                    name=sim_inst.name,
                    simulation_instance=sim_inst,
                    default_values=False,
                )
            self._features.append(sim_feat)

    def __extract_part_mesh_info(
        self,
        part_data: ProtoPart,
        part_coordinate_info: RepeatedScalarFieldContainer = None,
    ) -> pv.PolyData:
        """Extract mesh data info from a part.

        Parameters
        ----------
        speos_client : ansys.speos.core.kernel.client.SpeosClient
            The Speos instance client.
        part_data: ansys.api.speos.part.v1.part_pb2.Part
            Part from scene.
        part_coordinate_info: RepeatedScalarFieldContainer
            message contains part coordinate info: origin, x_vector, y_vector, z_vector

        Returns
        -------
        pv.PolyData
            mesh data extracted.
        """
        part_coordinate = [
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ]
        if part_coordinate_info is not None:
            part_coordinate = part_coordinate_info
        part_mesh_info = None
        for feature in part_data._geom_features:
            if not isinstance(feature, body.Body):
                continue
            body_visual_data = feature.visual_data.data
            body_visual_data.points = np.array(
                [local2absolute(vertice, part_coordinate) for vertice in body_visual_data.points]
            )
            if part_mesh_info is None:
                part_mesh_info = body_visual_data
            else:
                part_mesh_info = part_mesh_info.append_polydata(body_visual_data)
        return part_mesh_info

    def _create_speos_feature_preview(
        self,
        plotter: Plotter,
        speos_feature: Union[
            SensorCamera,
            SensorRadiance,
            SensorIrradiance,
            Sensor3DIrradiance,
            SourceLuminaire,
            SourceRayFile,
            SourceLuminaire,
        ],
        scene_seize: float,
    ) -> Plotter:
        """Add speos feature visual preview to pyvista plotter object.

        Parameters
        ----------
        plotter: Plotter
            ansys.tools.visualization_interface.Plotter
        speos_feature: Union[SensorCamera, SensorRadiance, SensorIrradiance,
        Sensor3DIrradiance, SourceLuminaire, SourceRayFile, SourceLuminaire]
            speos feature whose visual data will be added.
        scene_seize: float
            seize of max scene bounds

        Returns
        -------
        Plotter
            ansys.tools.visualization_interface.Plotter
        """
        if not isinstance(
            speos_feature,
            (
                SensorIrradiance,
                SensorRadiance,
                SensorCamera,
                Sensor3DIrradiance,
                SourceLuminaire,
                SourceRayFile,
                SourceSurface,
            ),
        ):
            return plotter

        ray_path_scale_factor = 0.2

        match speos_feature:
            case SourceRayFile() | SourceLuminaire() | SourceSurface():
                for visual_ray in speos_feature.visual_data.data:
                    tmp = visual_ray._VisualArrow__data
                    visual_ray._VisualArrow__data.points[1] = (
                        ray_path_scale_factor * scene_seize * (tmp.points[1] - tmp.points[0])
                        + tmp.points[0]
                    )
                    plotter.plot(visual_ray.data, color=visual_ray.color)
            case _:
                plotter.plot(
                    speos_feature.visual_data.data,
                    show_edges=True,
                    line_width=2,
                    edge_color="red",
                    color="orange",
                    opacity=0.5,
                )

        if speos_feature.visual_data.coordinates is not None:
            tmp_origin = speos_feature.visual_data.coordinates.origin
            tmp = speos_feature.visual_data.coordinates
            speos_feature.visual_data.coordinates._VisualCoordinateSystem__x_axis.points[:] = (
                tmp.x_axis.points - tmp_origin
            ) * ray_path_scale_factor * scene_seize + tmp_origin
            speos_feature.visual_data.coordinates._VisualCoordinateSystem__y_axis.points[:] = (
                tmp.y_axis.points - tmp_origin
            ) * ray_path_scale_factor * scene_seize + tmp_origin
            speos_feature.visual_data.coordinates._VisualCoordinateSystem__z_axis.points[:] = (
                tmp.z_axis.points - tmp_origin
            ) * ray_path_scale_factor * scene_seize + tmp_origin

            match speos_feature:
                case SensorRadiance() | SourceSurface():
                    plotter.plot(speos_feature.visual_data.coordinates.x_axis, color="red")
                    plotter.plot(speos_feature.visual_data.coordinates.y_axis, color="green")
                case SensorIrradiance() | SensorCamera() | SourceLuminaire() | SourceRayFile():
                    plotter.plot(speos_feature.visual_data.coordinates.x_axis, color="red")
                    plotter.plot(speos_feature.visual_data.coordinates.y_axis, color="green")
                    plotter.plot(speos_feature.visual_data.coordinates.z_axis, color="blue")
        return plotter

    @graphics_required
    def _create_preview(self, viz_args=None) -> Plotter:
        """Create preview pyvista plotter object.

        Parameters
        ----------
        viz_args : dict
            contains arguments in dict format passed to add mesh function
            e.g.
            - {'style': 'wireframe'},
            - {'style': 'surface', 'color':'white'},
            - {'opacity': 0.7, 'color':'white', 'show_edges': False},
        """
        import pyvista as pv

        from ansys.tools.visualization_interface import Plotter

        def find_all_subparts(target_part):
            subparts = []
            current_subparts_found = target_part.find(
                name=".*", name_regex=True, feature_type=part.Part.SubPart
            )
            if not current_subparts_found:
                return subparts
            for subpart in current_subparts_found:
                subparts.append(subpart)
                subparts.extend(find_all_subparts(subpart))
            return subparts

        if viz_args is None:
            viz_args = {}
        viz_args["show_edges"] = True

        p = Plotter()
        # Add cad visual data at the root part
        if self.scene_link.get().part_guid != "":
            _preview_mesh = pv.PolyData()
            root_part = self.find(name="", feature_type=part.Part)[0]

            # Add mesh of bodies directly contained in root part
            part_mesh_data = self.__extract_part_mesh_info(part_data=root_part)
            if part_mesh_data is not None:
                _preview_mesh = _preview_mesh.append_polydata(part_mesh_data)

            # Add mesh of bodies contained in sub-part
            subparts = find_all_subparts(root_part)
            for subpart in subparts:
                subpart_axis = subpart._part_instance.axis_system
                part_mesh_data = self.__extract_part_mesh_info(
                    part_data=subpart,
                    part_coordinate_info=subpart_axis,
                )
                if part_mesh_data is not None:
                    _preview_mesh = _preview_mesh.append_polydata(part_mesh_data)

            if _preview_mesh.n_points != 0 and _preview_mesh.n_cells != 0:
                p.plot(_preview_mesh, **viz_args)

        # Add speos visual data at the root part
        scene_bounds = p.backend.scene.bounds
        scene_x_seize = scene_bounds[1] - scene_bounds[0]
        scene_y_seize = scene_bounds[3] - scene_bounds[2]
        scene_z_seize = scene_bounds[5] - scene_bounds[4]
        scene_max = max(scene_x_seize, scene_y_seize, scene_z_seize)
        for feature in self._features:
            p = self._create_speos_feature_preview(
                plotter=p, speos_feature=feature, scene_seize=scene_max
            )
        return p

    @graphics_required
    def preview(
        self,
        viz_args=None,
        screenshot: Optional[Union[str, Path]] = None,
    ) -> None:
        """Preview cad bodies inside the project's scene.

        Parameters
        ----------
        viz_args : dict
            contains arguments in dict format passed to add mesh function
            e.g.
            - {'style': 'wireframe'},
            - {'style': 'surface', 'color':'white'},
            - {'opacity': 0.7, 'color':'white', 'show_edges': False}.

        screenshot : str or Path or ``None``
            Path to save a screenshot of the plotter. If defined Plotter will only create the
            screenshot

        """
        if viz_args is None:
            viz_args = {"opacity": 1}
        if screenshot is not None:
            screenshot = Path(screenshot)

        p = self._create_preview(viz_args=viz_args)
        p.show(screenshot=screenshot)
