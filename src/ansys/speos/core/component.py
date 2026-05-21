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

from ansys.speos.core import body, face, opt_prop, part
from ansys.speos.core.generic.constants import ORIGIN
import ansys.speos.core.generic.general_methods as general_methods
from ansys.speos.core.generic.parameters import (
    DisplayParameters,
    LuminaireSourceParameters,
    OptPropParameters,
    RayFileSourceParameters,
    SurfaceSourceParameters,
)
from ansys.speos.core.generic.visualization_methods import _VisualArrow, _VisualData, local2absolute
from ansys.speos.core.ground_plane import GroundPlane
from ansys.speos.core.kernel import ProtoScene
import ansys.speos.core.project as project
import ansys.speos.core.proto_message_utils as proto_message_utils
from ansys.speos.core.source import (
    SourceDisplay,
    SourceLuminaire,
    SourceRayFile,
    SourceSurface,
)


class LightBoxFileInstance:
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
        axis_system: Optional[List[float]] = None,
    ) -> None:
        self.file = str(file)
        """SPEOS file."""
        if password is None:
            password = os.getenv("PYSPEOS_ENCRYPTED_PASSWORD", "")
        self.password = password
        """Password for the imported lightbox."""
        self.axis_system = ORIGIN if axis_system is None else axis_system


class LightBox:
    """Represent the Speos LightBox component feature.

    By default, the global origin axis system is used to position the LightBox.

    Parameters
    ----------
    parent_project : ansys.speos.core.project.Project
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
        parent_project: project.Project,
        instance: Optional[Union[LightBoxFileInstance, ProtoScene.SceneInstance]] = None,
    ):
        self._name = name
        self._unique_id = None
        self._parent_project = parent_project
        self._scene_instance = ProtoScene.SceneInstance(name=self._name)
        self._is_black = False
        self._visual_data = [] if general_methods._GRAPHICS_AVAILABLE else None

        match instance:
            case None:
                self.project = project.Project(speos=self._parent_project.client)
                self._scene_instance.axis_system[:] = ORIGIN
            case LightBoxFileInstance():
                self.project = project.Project(
                    speos=self._parent_project.client,
                    path=instance,
                    context=self._scene_instance.name + "/",
                )
                self._scene_instance.axis_system[:] = instance.axis_system
                scene_data = self.project.scene_link.get()
                if (
                    len(scene_data.sources) == 0
                    and scene_data.part_guid == ""
                    and len(scene_data.materials) == 0
                ):
                    self._is_black = True
            case ProtoScene.SceneInstance():
                self._unique_id = instance.metadata["UniqueId"]
                self.project = project.Project(speos=self._parent_project.client)
                self.project.scene_link = self.project.client[instance.scene_guid]
                self._scene_instance = instance
                scene_data = self.project.scene_link.get()
                # in case of black box don't fill features
                if scene_data.sources or scene_data.part_guid != "" or scene_data.materials:
                    self.project._fill_features(context=self._scene_instance.name + "/")
                else:
                    self._is_black = True
            case _:
                raise TypeError(
                    f"Incorrect parameter dataclass provided "
                    f"{str(type(instance))} instead of LightBoxFileInstance or SceneInstance"
                )

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

                for ray_path in self._parent_project.client[
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
        sources_data = self.project.scene_link.get().sources
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
            LightBox,
            part.Part,
            body.Body,
            face.Face,
            part.Part.SubPart,
            GroundPlane,
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
        List[Union[ansys.speos.core.opt_prop.OptProp, ansys.speos.core.source.SourceSurface, \
        ansys.speos.core.source.SourceRayFile, ansys.speos.core.source.SourceLuminaire, \
        ansys.speos.core.source.SourceAmbientEnvironment, \
        ansys.speos.core.source.SourceAmbientNaturalLight, \
        ansys.speos.core.sensor.SensorCamera, \
        ansys.speos.core.sensor.SensorRadiance, ansys.speos.core.sensor.SensorIrradiance, \
        ansys.speos.core.sensor.Sensor3DIrradiance, ansys.speos.core.sensor.SensorXMPIntensity, \
        ansys.speos.core.simulation.SimulationVirtualBSDF, \
        ansys.speos.core.simulation.SimulationDirect, \
        ansys.speos.core.simulation.SimulationInteractive, \
        ansys.speos.core.simulation.SimulationInverse, \
        ansys.speos.core.part.Part, \
        ansys.speos.core.body.Body, \
        ansys.speos.core.face.Face, ansys.speos.core.part.Part.SubPart, \
        ansys.speos.core.ground_plane.GroundPlane]]
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
        return self.project.find(name=name, name_regex=name_regex, feature_type=feature_type)

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
        if self._is_black:
            raise ValueError("A black lightbox does not allow creating features.")
        return self.project.create_root_part(description=description, metadata=metadata)

    def create_source(
        self,
        name: str,
        description: str = "",
        feature_type: type = SourceSurface,
        metadata: Optional[Mapping[str, str]] = None,
        parameters: Optional[
            Union[
                LuminaireSourceParameters,
                SurfaceSourceParameters,
                RayFileSourceParameters,
                DisplayParameters,
            ]
        ] = None,
    ) -> Union[
        SourceSurface,
        SourceRayFile,
        SourceLuminaire,
        SourceDisplay,
    ]:
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
            ansys.speos.core.source.SourceDisplay].
        metadata : Optional[Mapping[str, str]]
            Metadata of the feature.
            By default, ``{}``.
        parameters : Optional[Union[\
        ansys.speos.core.generic.parameters.LuminaireSourceParameters,\
        ansys.speos.core.generic.parameters.SurfaceSourceParameters,\
        ansys.speos.core.generic.parameters.RayFileSourceParameters,\
        ansys.speos.core.generic.parameters.DisplayParamaters]]
            Allows to provide parameters to overwrite default parameters.

        Returns
        -------
        Union[ansys.speos.core.source.SourceSurface, ansys.speos.core.source.SourceRayFile,\
        ansys.speos.core.source.SourceLuminaire, ansys.speos.core.source.SourceDisplay]
            Source class instance.
        """
        if self._is_black:
            raise ValueError("A black lightbox does not allow creating features.")
        source_feat = self.project.create_source(
            name=name,
            description=description,
            feature_type=feature_type,
            metadata=metadata,
            parameters=parameters,
        )
        source_feat._source_path = self._scene_instance.name + "/" + name
        return source_feat

    def create_optical_property(
        self,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        parameters: Optional[OptPropParameters] = None,
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
        parameters : Optional[ansys.speos.core.generic.parameters.OptPropParameters]
             Allows to provide parameters to overwrite default parameters.


        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            OptProp feature.
        """
        if self._is_black:
            raise ValueError("A black lightbox does not allow creating features.")
        return self.project.create_optical_property(
            name=name, description=description, metadata=metadata, parameters=parameters
        )

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

        for feature in self.project._features:
            feature.commit()
        self._scene_instance.scene_guid = self.project.scene_link.key

        # The _unique_id will help to find the correct item in the scene.scenes:
        # the list of SceneInstance
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._scene_instance.metadata["UniqueId"] = self._unique_id

        # Update the parent scene with the lightbox instance
        if self._parent_project.scene_link:
            update_parent_scene = True
            parent_scene_data = self._parent_project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            scene_inst = next(
                (x for x in parent_scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if scene_inst is not None:
                if scene_inst != self._scene_instance:
                    scene_inst.CopyFrom(self._scene_instance)  # if yes, just replace
                else:
                    update_parent_scene = False
            else:
                parent_scene_data.scenes.append(
                    self._scene_instance
                )  # if no, just add it to the list of lightbox instances

            if update_parent_scene:  # Update scene only if instance has changed
                self._parent_project.scene_link.set(data=parent_scene_data)  # update scene data

        return self

    def export(
        self, export_path: Path | str, password: str | None = None, black_boxed: bool = False
    ) -> Path:
        """Save the LightBox feature as a LightBox file.

        Parameters
        ----------
        black_boxed

        export_path : Path | str
            Path of the LightBox file to be saved.
        password: str | None
            Password to protect the LightBox file.
            By default, ``None``, means that the LightBox file will not be password protected
        black_boxed: bool
            Whether to save the LightBox file as black-boxed.
            By default, ``False``, means that the LightBox file will not be black-boxed.

        Returns
        -------
        ansys.speos.core.component.LightBox
            Updated LightBox feature.
        """
        if len(self.project._features) == 0:
            raise ValueError(
                "LightBox file cannot be saved due to is a black lightbox or no features inside."
            )
        if password is None:
            password = os.getenv("PYSPEOS_ENCRYPTED_PASSWORD", "")
        self.project.scene_link.save_file(
            file_uri=str(export_path), password=password, black_boxed=black_boxed
        )
        return Path(export_path) / Path(export_path).name

    def _to_dict(self) -> dict:
        """Convert the LightBox data to a dictionary representation.

        Returns
        -------
        dict
            Flattened dictionary with resolved GUID references and properties.
        """
        out_dict = {}

        # SceneInstance (= scene guid + scene properties)
        if self._parent_project.scene_link and self._unique_id is not None:
            parent_scene_data = self._parent_project.scene_link.get()
            scene_inst = next(
                (x for x in parent_scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if scene_inst is not None:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._parent_project.client, message=scene_inst
                )
            else:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._parent_project.client,
                    message=self._scene_instance,
                )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._parent_project.client, message=self._scene_instance
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
        if self._parent_project.scene_link and self._unique_id is not None:
            parent_scene_data = self._parent_project.scene_link.get()
            scene_inst = next(
                (x for x in parent_scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
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
        # Reset all features of the lightbox
        for feature in self.project._features:
            feature.reset()

        # Reset scene instance in parent project
        if self._parent_project.scene_link is not None:
            parent_scene_data = self._parent_project.scene_link.get()  # retrieve scene data
            # Look if an element corresponds to the _unique_id
            scene_inst = next(
                (x for x in parent_scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
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
        feature_part = None  # make sure the RootPart is deleted in the very end
        for feature in self.project._features:
            if not isinstance(feature, part.Part):
                feature.delete()
                feature = None
            else:
                feature_part = feature
        if feature_part is not None:
            feature_part.delete()
            feature_part = None
        self.project._features.clear()

        # Delete the lightbox scene
        if self.project.scene_link is not None:
            self.project.scene_link.delete()
            self.project.scene_link = None

        # Reset then the scene_guid (as the lightbox scene was deleted just above)
        self._scene_instance.scene_guid = ""
        # Reset axis system to origin as the lightbox scene is deleted
        self._scene_instance.axis_system[:] = ORIGIN

        # Remove the scene instance from the scene
        parent_scene_data = self._parent_project.scene_link.get()  # retrieve scene data
        scene_inst = next(
            (x for x in parent_scene_data.scenes if x.metadata["UniqueId"] == self._unique_id),
            None,
        )
        if scene_inst is not None:
            parent_scene_data.scenes.remove(scene_inst)
            self._parent_project.scene_link.set(data=parent_scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        self._scene_instance.metadata.pop("UniqueId")
        self._parent_project._features.remove(self)
        return self
