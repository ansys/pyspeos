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

import re
from typing import List, Mapping, Optional, Union
import uuid

from google.protobuf.internal.containers import RepeatedScalarFieldContainer
import numpy as np
import pyvista as pv

import ansys.speos.core as core
import ansys.speos.script.body as body
import ansys.speos.script.face as face
import ansys.speos.script.opt_prop as opt_prop
import ansys.speos.script.part as part
import ansys.speos.script.proto_message_utils as proto_message_utils
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

    def create_source(
        self,
        name: str,
        description: str = "",
        feature_type: type = source.Surface,
        metadata: Mapping[str, str] = {},
    ) -> Union[source.Surface, source.RayFile, source.Luminaire]:
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
            By default, ``ansys.speos.script.source.Surface``.
            Allowed types:
            Union[ansys.speos.script.source.Surface, ansys.speos.script.source.RayFile, \
            ansys.speos.script.source.Luminaire].
        metadata : Mapping[str, str]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        Union[ansys.speos.script.source.Surface, ansys.speos.script.source.RayFile, ansys.speos.script.source.Luminaire]
            Source class instance.
        """
        feature = None
        if feature_type == source.Surface:
            feature = source.Surface(project=self, name=name, description=description, metadata=metadata)
        elif feature_type == source.RayFile:
            feature = source.RayFile(project=self, name=name, description=description, metadata=metadata)
        elif feature_type == source.Luminaire:
            feature = source.Luminaire(project=self, name=name, description=description, metadata=metadata)
        else:
            msg = "Requested feature {} does not exist in supported list {}".format(
                feature_type, [source.Surface, source.Luminaire, source.RayFile]
            )
            raise TypeError(msg)
        self._features.append(feature)
        return feature

    def create_simulation(
        self, name: str, description: str = "", feature_type: type = simulation.Direct, metadata: Mapping[str, str] = {}
    ) -> Union[simulation.Direct, simulation.Interactive, simulation.Inverse]:
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
            By default, ``ansys.speos.script.simulation.Direct``.
            Allowed types: Union[ansys.speos.script.simulation.Direct, ansys.speos.script.simulation.Interactive, \
            ansys.speos.script.simulation.Inverse].
        metadata : Mapping[str, str]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        Union[ansys.speos.script.simulation.Direct, ansys.speos.script.simulation.Interactive, ansys.speos.script.simulation.Inverse]
            Simulation class instance
        """
        feature = None
        if feature_type == simulation.Direct:
            feature = simulation.Direct(project=self, name=name, description=description, metadata=metadata)
        elif feature_type == simulation.Inverse:
            feature = simulation.Inverse(project=self, name=name, description=description, metadata=metadata)
        elif feature_type == simulation.Interactive:
            feature = simulation.Interactive(project=self, name=name, description=description, metadata=metadata)
        else:
            msg = "Requested feature {} does not exist in supported list {}".format(
                feature_type, [simulation.Direct, simulation.Inverse, simulation.Interactive]
            )
            raise TypeError(msg)
        self._features.append(feature)
        return feature

    def create_sensor(
        self, name: str, description: str = "", feature_type: type = sensor.Irradiance, metadata: Mapping[str, str] = {}
    ) -> Union[sensor.Camera, sensor.Radiance, sensor.Irradiance]:
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
            By default, ``ansys.speos.script.sensor.Irradiance``.
            Allowed types: Union[ansys.speos.script.sensor.Camera, ansys.speos.script.sensor.Radiance, \
            ansys.speos.script.sensor.Irradiance]
        metadata : Mapping[str, str]
            Metadata of the feature.
            By default, ``{}``.

        Returns
        -------
        Union[ansys.speos.script.sensor.Camera, ansys.speos.script.sensor.Radiance, ansys.speos.script.sensor.Irradiance]
            Sensor class instance.
        """
        feature = None
        if feature_type == sensor.Irradiance:
            feature = sensor.Irradiance(project=self, name=name, description=description, metadata=metadata)
        elif feature_type == sensor.Radiance:
            feature = sensor.Radiance(project=self, name=name, description=description, metadata=metadata)
        elif feature_type == sensor.Camera:
            feature = sensor.Camera(project=self, name=name, description=description, metadata=metadata)
        else:
            msg = "Requested feature {} does not exist in supported list {}".format(
                feature_type, [sensor.Irradiance, sensor.Radiance, sensor.Camera]
            )
            raise TypeError(msg)
        self._features.append(feature)
        return feature

    def create_root_part(self, description: str = "", metadata: Mapping[str, str] = {}) -> part.Part:
        """Create the project root part feature. If a root part is already created in the project, it is returned.

        Parameters
        ----------
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
        name = "RootPart"
        existing_rp = self.find(name=name, feature_type=part.Part)
        if existing_rp != []:
            return existing_rp[0]

        feature = part.Part(project=self, name=name, description=description, metadata=metadata)
        self._features.append(feature)
        return feature

    def find(
        self, name: str, name_regex: bool = False, feature_type: Optional[type] = None
    ) -> List[
        Union[
            opt_prop.OptProp,
            source.Surface,
            source.Luminaire,
            source.RayFile,
            sensor.Irradiance,
            sensor.Radiance,
            sensor.Camera,
            simulation.Direct,
            simulation.Inverse,
            simulation.Interactive,
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
            By default, ``None``, means that all features will be considered (except geometry features).

        Returns
        -------
        List[Union[ansys.speos.script.opt_prop.OptProp, ansys.speos.script.source.Surface, \
        ansys.speos.script.source.RayFile, ansys.speos.script.source.Luminaireansys.speos.script.sensor.Camera, \
        ansys.speos.script.sensor.Radiance, ansys.speos.script.sensor.Irradiance, \
        ansys.speos.script.simulation.Direct, ansys.speos.script.simulation.Interactive, \
        ansys.speos.script.simulation.Inverse, ansys.speos.script.part.Part, ansys.speos.script.body.Body, \
        ansys.speos.script.face.Face, ansys.speos.script.part.Part.SubPart]]
            Found features.

        Examples
        --------

        >>> # From name only
        >>> find(name="Camera.1")
        >>> # Specify feature type
        >>> find(name="Camera.1", feature_type=ansys.speos.script.sensor.Sensor)
        >>> # Specify feature type more specific
        >>> find(name="Camera.1", feature_type=ansys.speos.script.sensor.Sensor.Camera)
        >>> # Using regex
        >>> find(name="Camera.*", name_regex=True, feature_type=ansys.speos.script.sensor.Sensor.Camera)

        Here some examples when looking for a geometry feature:
        (always precise feature_type)

        >>> # Root part
        >>> find(name="", feature_type=ansys.speos.script.part.Part)
        >>> # Body in root part
        >>> find(name="BodyName", feature_type=ansys.speos.script.body.Body)
        >>> # Face from body in root part
        >>> find(name="BodyName/FaceName", feature_type=ansys.speos.script.face.Face)
        >>> # Sub part in root part
        >>> find(name="SubPartName", feature_type=ansys.speos.script.part.Part.SubPart)
        >>> # Face in a body from sub part in root part :
        >>> find(name="SubPartName/BodyName/FaceName", feature_type=ansys.speos.script.face.Face)
        >>> # Regex can be use at each level separated by "/"
        >>> find(name="Body.*/Face.*", name_regex=True, feature_type=ansys.speos.script.face.Face)
        >>> # All faces of a specific body
        >>> find(name="BodyName/.*", name_regex=True, feature_type=ansys.speos.script.face.Face)
        >>> # All geometry features at first level (whatever their type: body, face, sub part)
        >>> find(name=".*", name_regex=True, feature_type=ansys.speos.script.part.Part)
        """
        orig_feature_type = None
        if feature_type == part.Part or feature_type == part.Part.SubPart or feature_type == body.Body or feature_type == face.Face:
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
                        if (type(x) == feature_type or (type(x._type) == feature_type if hasattr(x, "_type") else False))
                        and p.match(x._name)
                    ]
                )
            else:
                found_features.extend(
                    [
                        x
                        for x in self._features
                        if (type(x) == feature_type or (type(x._type) == feature_type if hasattr(x, "_type") else False))
                        and x._name == name
                    ]
                )

        if found_features != [] and idx != -1:
            tmp = [f.find(name=orig_name[idx + 1 :], name_regex=name_regex, feature_type=orig_feature_type) for f in found_features]

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

    def _to_dict(self) -> dict:
        # Replace all guids by content of objects in the dict
        output_dict = proto_message_utils._replace_guids(
            speos_client=self.client, message=self.scene_link.get(), ignore_simple_key="part_guid"
        )

        # For each feature, replace properties by putting them at correct place
        for k, v in output_dict.items():
            if type(v) is list:
                for inside_dict in v:
                    if k == "simulations":
                        sim_feat = self.find(name=inside_dict["name"], feature_type=simulation.Direct)
                        if len(sim_feat) == 0:
                            sim_feat = self.find(name=inside_dict["name"], feature_type=simulation.Inverse)
                        if len(sim_feat) == 0:
                            sim_feat = self.find(name=inside_dict["name"], feature_type=simulation.Interactive)
                        sim_feat = sim_feat[0]
                        if sim_feat.job_link is None:
                            inside_dict["simulation_properties"] = proto_message_utils._replace_guids(
                                speos_client=self.client, message=sim_feat._job, ignore_simple_key="scene_guid"
                            )
                        else:
                            inside_dict["simulation_properties"] = proto_message_utils._replace_guids(
                                speos_client=self.client, message=sim_feat.job_link.get(), ignore_simple_key="scene_guid"
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

    def _fill_bodies(self, body_guids: List[str], feat_host: Union[part.Part, part.Part.SubPart]):
        """Fill part of sub part features from a list of body guids."""
        for b_link in self.client.get_items(keys=body_guids, item_type=core.BodyLink):
            b_data = b_link.get()
            b_feat = feat_host.create_body(name=b_data.name)
            b_feat.body_link = b_link
            b_feat._body = b_data  # instead of b_feat.reset() - this avoid a useless read in server
            f_links = self.client.get_items(keys=b_data.face_guids, item_type=core.FaceLink)
            for f_link in f_links:
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

        root_part_link = self.client.get_item(key=scene_data.part_guid)
        root_part_data = root_part_link.get()
        root_part_feats = self.find(name="", feature_type=part.Part)
        root_part_feat = None
        if root_part_feats == []:
            root_part_feat = self.create_root_part()
            root_part_data.name = "RootPart"
            root_part_link.set(root_part_data)
            self._fill_bodies(body_guids=root_part_data.body_guids, feat_host=root_part_feat)
        else:
            root_part_feat = root_part_feats[0]

        root_part_feat.part_link = root_part_link
        root_part_feat._part = root_part_data  # instead of root_part_feat.reset() - this avoid a useless read in server

        for sp in root_part_data.parts:
            sp_feat = root_part_feat.create_sub_part(name=sp.name, description=sp.description)
            if sp.description.startswith("UniqueId_"):
                idx = sp.description.find("_")
                sp_feat._unique_id = sp.description[idx + 1 :]
            sp_feat.part_link = self.client.get_item(key=sp.part_guid)
            part_data = sp_feat.part_link.get()
            sp_feat._part_instance = sp
            sp_feat._part = part_data  # instead of sp_feat.reset() - this avoid a useless read in server
            self._fill_bodies(body_guids=part_data.body_guids, feat_host=sp_feat)

        for mat_inst in scene_data.materials:
            op_feature = self.create_optical_property(name=mat_inst.name)
            op_feature._fill(mat_inst=mat_inst)

        for src_inst in scene_data.sources:
            if src_inst.HasField("rayfile_properties"):
                src_feat = source.RayFile(project=self, name=src_inst.name, source_instance=src_inst, default_values=False)
            elif src_inst.HasField("luminaire_properties"):
                src_feat = source.Luminaire(project=self, name=src_inst.name, source_instance=src_inst, default_values=False)
            elif src_inst.HasField("surface_properties"):
                src_feat = source.Surface(project=self, name=src_inst.name, source_instance=src_inst, default_values=False)
            self._features.append(src_feat)

        for ssr_inst in scene_data.sensors:
            if ssr_inst.HasField("irradiance_properties"):
                ssr_feat = sensor.Irradiance(project=self, name=ssr_inst.name, sensor_instance=ssr_inst, default_values=False)
            elif ssr_inst.HasField("camera_properties"):
                ssr_feat = sensor.Radiance(project=self, name=ssr_inst.name, sensor_instance=ssr_inst, default_values=False)
            elif ssr_inst.HasField("radiance_properties"):
                ssr_feat = sensor.Camera(project=self, name=ssr_inst.name, sensor_instance=ssr_inst, default_values=False)
            self._features.append(ssr_feat)

        for sim_inst in scene_data.simulations:
            simulation_template_link = self.client.get_item(key=sim_inst.simulation_guid).get()
            if simulation_template_link.HasField("direct_mc_simulation_template"):
                sim_feat = simulation.Direct(project=self, name=sim_inst.name, simulation_instance=sim_inst, default_values=False)
            elif simulation_template_link.HasField("inverse_mc_simulation_template"):
                sim_feat = simulation.Inverse(project=self, name=sim_inst.name, simulation_instance=sim_inst, default_values=False)
            elif simulation_template_link.HasField("interactive_simulation_template"):
                sim_feat = simulation.Interactive(project=self, name=sim_inst.name, simulation_instance=sim_inst, default_values=False)
            self._features.append(sim_feat)

    def __extract_part_mesh_info(self, part_data: core.Part, part_coordinate_info: RepeatedScalarFieldContainer = None) -> pv.PolyData:
        """
        extract mesh data info from a part.

        Parameters
        ----------
        speos_client : ansys.speos.core.client.SpeosClient
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

        def local2absolute(local_vertice: np.ndarray, coordinates) -> np.ndarray:
            """
            convert local coordinate to global coordinate.

            Parameters
            ----------
            local_vertice: np.ndarray
                numpy array includes x, y, z info.

            Returns
            -------
            np.ndarray
                numpy array includes x, y, z info

            """
            global_origin = np.array(coordinates[:3])
            global_x = np.array(coordinates[3:6]) * local_vertice[0]
            global_y = np.array(coordinates[6:9]) * local_vertice[1]
            global_z = np.array(coordinates[9:]) * local_vertice[2]
            return global_origin + global_x + global_y + global_z

        part_coordinate = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        if part_coordinate_info is not None:
            part_coordinate = part_coordinate_info
        part_mesh_info = None
        for body_idx, body_guid in enumerate(part_data.body_guids):
            body_item_data = self.client.get_item(body_guid).get()
            for face_idx, face_guid in enumerate(body_item_data.face_guids):
                face_item_data = self.client.get_item(face_guid).get()
                vertices = np.array(face_item_data.vertices)
                facets = np.array(face_item_data.facets)
                vertices = vertices.reshape(-1, 3)
                vertices = np.array([local2absolute(vertice, part_coordinate) for vertice in vertices])
                facets = facets.reshape(-1, 3)
                temp = np.full(facets.shape[0], 3)
                temp = np.vstack(temp)
                facets = np.hstack((temp, facets))
                face_mesh_data = pv.PolyData(vertices, facets)
                if part_mesh_info is None:
                    part_mesh_info = face_mesh_data
                else:
                    part_mesh_info = part_mesh_info.append_polydata(face_mesh_data)
        return part_mesh_info

    def _create_preview(self, viz_args=None) -> pv.Plotter:
        """
        create preview pyvista plotter object

        Parameters
        ----------
        viz_args : dict
            contains arguments in dict format passed to add mesh function
            e.g.
            - {'style': 'wireframe'},
            - {'style': 'surface', 'color':'white'},
            - {'opacity': 0.7, 'color':'white', 'show_edges': False},


        """
        if viz_args is None:
            viz_args = {}
        _preview_mesh = pv.PolyData()
        # Retrieve root part
        root_part_data = self.client.get_item(self.scene_link.get().part_guid).get()

        # Loop on all sub parts to retrieve their mesh
        if len(root_part_data.parts) != 0:
            for part_idx, part_item in enumerate(root_part_data.parts):
                part_item_data = self.client.get_item(part_item.part_guid).get()
                poly_data = self.__extract_part_mesh_info(part_data=part_item_data, part_coordinate_info=part_item.axis_system)
                if poly_data is not None:
                    _preview_mesh = _preview_mesh.append_polydata(poly_data)

        # Add also the mesh of bodies directly contained in root part
        poly_data = self.__extract_part_mesh_info(part_data=root_part_data)
        if poly_data is not None:
            _preview_mesh = _preview_mesh.append_polydata(poly_data)

        p = pv.Plotter()
        p.add_mesh(_preview_mesh, show_edges=True, **viz_args)
        return p

    def preview(self, viz_args=None) -> None:
        """Preview cad bodies inside the project's scene.

        Parameters
        ----------
        viz_args : dict
            contains arguments in dict format passed to add mesh function
            e.g.
            - {'style': 'wireframe'},
            - {'style': 'surface', 'color':'white'},
            - {'opacity': 0.7, 'color':'white', 'show_edges': False},
        """
        if viz_args is None:
            viz_args = {"opacity": 1}
        p = self._create_preview(viz_args=viz_args)
        p.show()
