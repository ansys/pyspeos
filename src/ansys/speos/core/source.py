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

"""Provides a way to interact with Speos feature: Source."""

from __future__ import annotations

import datetime
from difflib import SequenceMatcher
from typing import List, Mapping, Optional, Union
import uuid

import numpy as np

from ansys.api.speos.scene.v2 import scene_pb2
from ansys.speos.core import (
    project as project,
    proto_message_utils as proto_message_utils,
)
import ansys.speos.core.body as body
import ansys.speos.core.face as face
import ansys.speos.core.generic.general_methods as general_methods
from ansys.speos.core.generic.visualization_methods import _VisualArrow, _VisualData
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.intensity import Intensity
from ansys.speos.core.kernel.client import SpeosClient
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.source_template import ProtoSourceTemplate
from ansys.speos.core.spectrum import Spectrum


class BaseSource:
    """
    Super Class for all sources.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project in which source shall be created.
    name : str
        Name of the source.
    description : str
        Description of the source.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    source_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance, optional
        Source instance to provide if the feature does not have to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.

    Notes
    -----
    This is a Super class, **Do not instantiate this class yourself**
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
    ) -> None:
        self._project = project
        self._name = name
        self._unique_id = None
        self._visual_data = _VisualData(ray=True) if general_methods._GRAPHICS_AVAILABLE else None
        self.source_template_link = None
        """Link object for the source template in database."""

        if metadata is None:
            metadata = {}

        if source_instance is None:
            # Create local SourceTemplate
            self._source_template = ProtoSourceTemplate(
                name=name, description=description, metadata=metadata
            )

            # Create local SourceInstance
            self._source_instance = ProtoScene.SourceInstance(
                name=name, description=description, metadata=metadata
            )
        else:
            self._unique_id = source_instance.metadata["UniqueId"]
            self.source_template_link = self._project.client[source_instance.source_guid]
            self._reset()

    class _Spectrum:
        def __init__(
            self,
            speos_client: SpeosClient,
            name: str,
            message_to_complete: Union[
                ProtoSourceTemplate.RayFile,
                ProtoSourceTemplate.Surface,
                ProtoSourceTemplate.Luminaire,
            ],
            spectrum_guid: str = "",
        ) -> None:
            self._message_to_complete = message_to_complete
            if spectrum_guid != "":
                self._spectrum = Spectrum(
                    speos_client=speos_client,
                    name=name + ".Spectrum",
                    key=spectrum_guid,
                )
            else:
                self._spectrum = Spectrum(speos_client=speos_client, name=name + ".Spectrum")

            self._no_spectrum = None  # None means never committed, or deleted
            self._no_spectrum_local = False

        def __str__(self) -> str:
            if self._no_spectrum is None:
                if self._no_spectrum_local is False:
                    return str(self._spectrum)
            else:
                if self._no_spectrum is False:
                    return str(self._spectrum)
            return ""

        def _commit(self) -> BaseSource._Spectrum:
            if not self._no_spectrum_local:
                self._spectrum.commit()
                self._message_to_complete.spectrum_guid = self._spectrum.spectrum_link.key
                self._no_spectrum = self._no_spectrum_local
            return self

        def _reset(self) -> BaseSource._Spectrum:
            self._spectrum.reset()
            if self._no_spectrum is not None:
                self._no_spectrum_local = self._no_spectrum
            return self

        def _delete(self) -> BaseSource._Spectrum:
            self._no_spectrum = None
            return self

    def _to_dict(self) -> dict:
        out_dict = {}

        # SourceInstance (= source guid + source properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            src_inst = next(
                (x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if src_inst is not None:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=src_inst
                )
            else:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._source_instance,
                )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._project.client, message=self._source_instance
            )

        if "source" not in out_dict.keys():
            # SourceTemplate
            if self.source_template_link is None:
                out_dict["source"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._source_template,
                )
            else:
                out_dict["source"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self.source_template_link.get(),
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
                (x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if src_inst is None:
                out_str += "local: "
        else:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())
        return out_str

    def _commit(self) -> BaseSource:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        # The _unique_id will help to find correct item in the scene.sources:
        # the list of SourceInstance
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._source_instance.metadata["UniqueId"] = self._unique_id

        # Save or Update the source template (depending on if it was already saved before)
        if self.source_template_link is None:
            self.source_template_link = self._project.client.source_templates().create(
                message=self._source_template
            )
            self._source_instance.source_guid = self.source_template_link.key
        elif self.source_template_link.get() != self._source_template:
            self.source_template_link.set(
                data=self._source_template
            )  # Only update if template has changed

        # Update the scene with the source instance
        if self._project.scene_link:
            update_scene = True
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            src_inst = next(
                (x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if src_inst is not None:
                if src_inst != self._source_instance:
                    src_inst.CopyFrom(self._source_instance)  # if yes, just replace
                else:
                    update_scene = False
            else:
                scene_data.sources.append(
                    self._source_instance
                )  # if no, just add it to the list of sources

            if update_scene:  # Update scene only if instance has changed
                self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def _reset(self) -> BaseSource:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        # Reset source template
        if self.source_template_link is not None:
            self._source_template = self.source_template_link.get()

        # Reset source instance
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            # Look if an element corresponds to the _unique_id
            src_inst = next(
                (x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if src_inst is not None:
                self._source_instance = src_inst
        return self

    def _delete(self) -> BaseSource:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        # This allows to clean-managed object contained in _luminaire, _rayfile, etc..
        # Like Spectrum, IntensityTemplate

        # Delete the source template
        if self.source_template_link is not None:
            self.source_template_link.delete()
            self.source_template_link = None

        # Reset then the source_guid (as the source template was deleted just above)
        self._source_instance.source_guid = ""

        # Remove the source from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data
        src_inst = next(
            (x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id),
            None,
        )
        if src_inst is not None:
            scene_data.sources.remove(src_inst)
            self._project.scene_link.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        self._source_instance.metadata.pop("UniqueId")
        return self

    def _fill(self, src_inst):
        self._unique_id = src_inst.metadata["UniqueId"]
        self._source_instance = src_inst
        self.source_template_link = self._project.client[src_inst.source_guid]
        self._reset()

    def commit(self) -> BaseSource:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        if hasattr(self, "_spectrum"):
            self._spectrum._commit()
        self._commit()
        if general_methods._GRAPHICS_AVAILABLE:
            self._visual_data.updated = False
        return self

    def reset(self) -> BaseSource:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        if hasattr(self, "_spectrum"):
            self._spectrum._reset()
        self._reset()
        return self

    def delete(self) -> BaseSource:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.source.BaseSource
            Source feature.
        """
        if hasattr(self, "_spectrum"):
            self._spectrum._delete()
        self._delete()
        return self


class SourceLuminaire(BaseSource):
    """LuminaireSource.

    By default, a flux from intensity file is chosen, with an incandescent spectrum.

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
    default_values : bool
        Uses default values when True.
    """

    @general_methods.min_speos_version(25, 2, 0)
    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
        default_values: bool = True,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )

        self._spectrum = self._Spectrum(
            speos_client=self._project.client,
            name=name,
            message_to_complete=self._source_template.luminaire,
            spectrum_guid=self._source_template.luminaire.spectrum_guid,
        )

        if default_values:
            # Default values
            self.set_flux_from_intensity_file().set_spectrum().set_incandescent()
            self.set_axis_system()

    @property
    def visual_data(self) -> _VisualData:
        """Property containing Luminaire source visualization data.

        Returns
        -------
        _VisualData
            Instance of VisualData Class for pyvista.PolyData of feature rays, coordinate_systems.

        """
        if self._visual_data.updated:
            return self._visual_data
        else:
            self._visual_data = (
                _VisualData(ray=True) if general_methods._GRAPHICS_AVAILABLE else None
            )
            for ray_path in self._project.scene_link.get_source_ray_paths(
                self._name, rays_nb=100, raw_data=True, display_data=True
            ):
                self._visual_data.add_data_line(
                    _VisualArrow(
                        line_vertices=[ray_path.impacts_coordinates, ray_path.last_direction],
                        color=tuple(ray_path.colors.values),
                        arrow=False,
                    )
                )
            feature_pos_info = self.get(key="axis_system")
            feature_luminaire_pos = np.array(feature_pos_info[:3])
            feature_luminaire_x_dir = np.array(feature_pos_info[3:6])
            feature_luminaire_y_dir = np.array(feature_pos_info[6:9])
            feature_luminaire_z_dir = np.array(feature_pos_info[9:12])
            self._visual_data.coordinates.origin = feature_luminaire_pos
            self._visual_data.coordinates.x_axis = feature_luminaire_x_dir
            self._visual_data.coordinates.y_axis = feature_luminaire_y_dir
            self._visual_data.coordinates.z_axis = feature_luminaire_z_dir
            self._visual_data.updated = True
            return self._visual_data

    def set_flux_from_intensity_file(self) -> SourceLuminaire:
        """Take flux from intensity file provided.

        Returns
        -------
        ansys.speos.core.source.SourceLuminaire
            Luminaire source.
        """
        self._source_template.luminaire.flux_from_intensity_file.SetInParent()
        return self

    def set_flux_luminous(self, value: float = 683) -> SourceLuminaire:
        """Set luminous flux.

        Parameters
        ----------
        value : float
            Luminous flux in lumens.
            By default, ``683.0``.

        Returns
        -------
        ansys.speos.core.source.SourceLuminaire
            Luminaire source.
        """
        self._source_template.luminaire.luminous_flux.luminous_value = value
        return self

    def set_flux_radiant(self, value: float = 1) -> SourceLuminaire:
        """Set radiant flux.

        Parameters
        ----------
        value : float
            Radiant flux in watts.
            By default, ``1.0``.

        Returns
        -------
        ansys.speos.core.source.SourceLuminaire
            Luminaire source.
        """
        self._source_template.luminaire.radiant_flux.radiant_value = value
        return self

    def set_intensity_file_uri(self, uri: str) -> SourceLuminaire:
        """Set intensity file.

        Parameters
        ----------
        uri : str
            IES or EULUMDAT format file uri.

        Returns
        -------
        ansys.speos.core.source.SourceLuminaire
            Luminaire source.
        """
        self._source_template.luminaire.intensity_file_uri = uri
        return self

    def set_spectrum(self) -> Spectrum:
        """Set spectrum.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum.
        """
        if self._spectrum._message_to_complete is not self._source_template.luminaire:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._spectrum._message_to_complete = self._source_template.luminaire
        return self._spectrum._spectrum

    def set_axis_system(self, axis_system: Optional[List[float]] = None) -> SourceLuminaire:
        """Set the position of the source.

        Parameters
        ----------
        axis_system : Optional[List[float]]
            Position of the source [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

        Returns
        -------
        ansys.speos.core.source.SourceLuminaire
            Luminaire source.
        """
        if axis_system is None:
            axis_system = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
        self._source_instance.luminaire_properties.axis_system[:] = axis_system
        return self


class SourceRayFile(BaseSource):
    """RayFile Source.

    By default, flux and spectrum from ray file are selected.

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
    default_values : bool
        Uses default values when True.
    """

    @general_methods.min_speos_version(25, 2, 0)
    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
        default_values: bool = True,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )
        self._client = self._project.client

        spectrum_guid = ""
        if self._source_template.rayfile.HasField("spectrum_guid"):
            spectrum_guid = self._source_template.rayfile.spectrum_guid
        self._spectrum = self._Spectrum(
            speos_client=self._client,
            name=name,
            message_to_complete=self._source_template.rayfile,
            spectrum_guid=spectrum_guid,
        )
        if spectrum_guid == "":
            self.set_spectrum_from_ray_file()

        self._name = name

        if default_values:
            # Default values
            self.set_flux_from_ray_file().set_spectrum_from_ray_file()
            self.set_axis_system()

    @property
    def visual_data(self) -> _VisualData:
        """Property containing Rayfile source visualization data.

        Returns
        -------
        _VisualData
            Instance of VisualData Class for pyvista.PolyData of feature rays, coordinate_systems.

        """
        if self._visual_data.updated:
            return self._visual_data
        else:
            self._visual_data = (
                _VisualData(ray=True) if general_methods._GRAPHICS_AVAILABLE else None
            )
            for ray_path in self._project.scene_link.get_source_ray_paths(
                self._name, rays_nb=100, raw_data=True, display_data=True
            ):
                self._visual_data.add_data_line(
                    _VisualArrow(
                        line_vertices=[ray_path.impacts_coordinates, ray_path.last_direction],
                        color=tuple(ray_path.colors.values),
                        arrow=False,
                    )
                )
            feature_pos_info = self.get(key="axis_system")
            feature_rayfile_pos = np.array(feature_pos_info[:3])
            feature_rayfile_x_dir = np.array(feature_pos_info[3:6])
            feature_rayfile_y_dir = np.array(feature_pos_info[6:9])
            feature_rayfile_z_dir = np.array(feature_pos_info[9:12])
            self._visual_data.coordinates.origin = feature_rayfile_pos
            self._visual_data.coordinates.x_axis = feature_rayfile_x_dir
            self._visual_data.coordinates.y_axis = feature_rayfile_y_dir
            self._visual_data.coordinates.z_axis = feature_rayfile_z_dir
            self._visual_data.updated = True
            return self._visual_data

    def set_ray_file_uri(self, uri: str) -> SourceRayFile:
        """Set ray file.

        Parameters
        ----------
        uri : str
            Rayfile format file uri (.ray or .tm25ray files expected).

        Returns
        -------
        ansys.speos.core.source.SourceRayFile
            RayFile source.
        """
        self._source_template.rayfile.ray_file_uri = uri
        return self

    def set_flux_from_ray_file(self) -> SourceRayFile:
        """Take flux from ray file provided.

        Returns
        -------
        ansys.speos.core.source.SourceRayFile
            RayFile source.
        """
        self._source_template.rayfile.flux_from_ray_file.SetInParent()
        return self

    def set_flux_luminous(self, value: float = 683) -> SourceRayFile:
        """Set luminous flux.

        Parameters
        ----------
        value : float
            Luminous flux in lumens.
            By default, ``683.0``.

        Returns
        -------
        ansys.speos.core.source.SourceRayFile
            RayFile source.
        """
        self._source_template.rayfile.luminous_flux.luminous_value = value
        return self

    def set_flux_radiant(self, value: float = 1) -> SourceRayFile:
        """Set radiant flux.

        Parameters
        ----------
        value : float
            Radiant flux in watts.
            By default, ``1.0``.

        Returns
        -------
        ansys.speos.core.source.SourceRayFile
            RayFile source.
        """
        self._source_template.rayfile.radiant_flux.radiant_value = value
        return self

    def set_spectrum_from_ray_file(self) -> SourceRayFile:
        """Take spectrum from ray file provided.

        Returns
        -------
        ansys.speos.core.source.SourceRayFile
            RayFile source.
        """
        self._source_template.rayfile.spectrum_from_ray_file.SetInParent()
        self._spectrum._no_spectrum_local = True
        return self

    def set_spectrum(self) -> Spectrum:
        """Set spectrum of the Source.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum.
        """
        if self._source_template.rayfile.HasField("spectrum_from_ray_file"):
            guid = ""
            if self._spectrum._spectrum.spectrum_link is not None:
                guid = self._spectrum._spectrum.spectrum_link.key
            self._source_template.rayfile.spectrum_guid = guid

        if self._spectrum._message_to_complete is not self._source_template.rayfile:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._spectrum._message_to_complete = self._source_template.rayfile

        self._spectrum._no_spectrum_local = False
        return self._spectrum._spectrum

    def set_axis_system(self, axis_system: Optional[List[float]] = None) -> SourceRayFile:
        """Set position of the source.

        Parameters
        ----------
        axis_system : Optional[List[float]]
            Position of the source [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

        Returns
        -------
        ansys.speos.core.source.SourceRayFile
            RayFile Source.
        """
        if axis_system is None:
            axis_system = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
        self._source_instance.rayfile_properties.axis_system[:] = axis_system
        return self

    def set_exit_geometries(self, exit_geometries: Optional[List[GeoRef]] = None) -> SourceRayFile:
        """Set exit geometries.

        Parameters
        ----------
        exit_geometries : List[ansys.speos.core.geo_ref.GeoRef]
            Exit Geometries that will use this rayfile source.
            By default, ``[]``.

        Returns
        -------
        ansys.speos.core.source.SourceRayFile
            RayFile Source.
        """
        if not exit_geometries:
            self._source_instance.rayfile_properties.ClearField("exit_geometries")
        else:
            self._source_instance.rayfile_properties.exit_geometries.geo_paths[:] = [
                gr.to_native_link() for gr in exit_geometries
            ]

        return self


class SourceSurface(BaseSource):
    """Type of Source : Surface.

    By default, a luminous flux and existence constant are chosen. With a monochromatic spectrum,
    and lambertian intensity (cos with N = 1).

    Parameters
    ----------
    speos_client : ansys.speos.core.kernel.client.SpeosClient
        The Speos instance client.
    name : str
        Name of the source feature.
    surface : ansys.api.speos.source.v1.source_pb2.SourceTemplate.Surface
        Surface source to complete.
    surface_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.SurfaceProperties
        Surface source properties to complete.
    default_values : bool
        Uses default values when True.
    """

    class ExitanceVariable:
        """Type of surface source existence : existence variable.

        Parameters
        ----------
        exitance_variable : ansys.api.speos.source.v1.source_pb2.SourceTemplate.Surface.
        ExitanceVariable
            Existence variable to complete.
        exitance_variable_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.
        SurfaceProperties.ExitanceVariableProperties
            Existence variable properties to complete.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_exitance_variable method available in
        Source classes.
        """

        def __init__(
            self,
            exitance_variable,
            exitance_variable_props,
            default_values: bool = True,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                msg = "ExitanceVariable class instantiated outside of class scope"
                raise RuntimeError(msg)
            self._exitance_variable = exitance_variable
            self._exitance_variable_props = exitance_variable_props

            if default_values:
                # Default values
                self._exitance_variable.SetInParent()
                self.set_axis_plane()

        def set_xmp_file_uri(self, uri: str) -> SourceSurface.ExitanceVariable:
            """Set existence xmp file.

            Parameters
            ----------
            uri : str
                XMP file describing existence.

            Returns
            -------
            ansys.speos.core.source.SourceSurface.ExitanceVariable
                ExitanceVariable of surface source.
            """
            self._exitance_variable.exitance_xmp_file_uri = uri
            return self

        def set_axis_plane(
            self, axis_plane: Optional[List[float]] = None
        ) -> SourceSurface.ExitanceVariable:
            """Set position of the existence map.

            Parameters
            ----------
            axis_plane : Optional[List[float]]
                Position of the existence map [Ox Oy Oz Xx Xy Xz Yx Yy Yz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0]``.

            Returns
            -------
            ansys.speos.core.source.SourceSurface.ExitanceVariable
                ExitanceVariable of surface Source.
            """
            if axis_plane is None:
                axis_plane = [0, 0, 0, 1, 0, 0, 0, 1, 0]
            self._exitance_variable_props.axis_plane[:] = axis_plane
            return self

    @general_methods.min_speos_version(25, 2, 0)
    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
        default_values: bool = True,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )
        self._speos_client = self._project.client
        self._name = name

        spectrum_guid = ""
        if self._source_template.surface.HasField("spectrum_guid"):
            spectrum_guid = self._source_template.surface.spectrum_guid
        self._spectrum = self._Spectrum(
            speos_client=self._speos_client,
            name=name,
            message_to_complete=self._source_template.surface,
            spectrum_guid=spectrum_guid,
        )

        self._intensity = Intensity(
            speos_client=self._speos_client,
            name=name + ".Intensity",
            intensity_props_to_complete=self._source_instance.surface_properties.intensity_properties,
            key=self._source_template.surface.intensity_guid,
        )

        # Attribute gathering more complex existence type
        self._exitance_type = None

        if default_values:
            # Default values
            self.set_flux_luminous().set_exitance_constant(geometries=[]).set_intensity()
            self.set_spectrum()

    @property
    def visual_data(self) -> _VisualData:
        """Property containing Surface source visualization data.

        Returns
        -------
        _VisualData
            Instance of VisualData Class for pyvista.PolyData of feature rays, coordinate_systems.

        """
        if self._visual_data.updated:
            return self._visual_data
        else:
            self._visual_data = (
                _VisualData(
                    ray=True,
                    coordinate_system=True if self._exitance_type is not None else False,
                )
                if general_methods._GRAPHICS_AVAILABLE
                else None
            )
            for ray_path in self._project.scene_link.get_source_ray_paths(
                self._name, rays_nb=100, raw_data=True, display_data=True
            ):
                self._visual_data.add_data_line(
                    _VisualArrow(
                        line_vertices=[ray_path.impacts_coordinates, ray_path.last_direction],
                        color=tuple(ray_path.colors.values),
                        arrow=False,
                    )
                )
            if self._visual_data.coordinates is not None:
                feature_pos_info = self.get(key="axis_plane")
                feature_surface_pos = np.array(feature_pos_info[:3])
                feature_surface_x_dir = np.array(feature_pos_info[3:6])
                feature_surface_y_dir = np.array(feature_pos_info[6:9])
                self._visual_data.coordinates.origin = feature_surface_pos
                self._visual_data.coordinates.x_axis = feature_surface_x_dir
                self._visual_data.coordinates.y_axis = feature_surface_y_dir
            self._visual_data.updated = True
            return self._visual_data

    def set_flux_from_intensity_file(self) -> SourceSurface:
        """Take flux from intensity file provided.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Surface source.
        """
        self._source_template.surface.flux_from_intensity_file.SetInParent()
        return self

    def set_flux_luminous(self, value: float = 683) -> SourceSurface:
        """Set luminous flux.

        Parameters
        ----------
        value : float
            Luminous flux in lumens.
            By default, ``683.0``.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Surface source.
        """
        self._source_template.surface.luminous_flux.luminous_value = value
        return self

    def set_flux_radiant(self, value: float = 1) -> SourceSurface:
        """Set radiant flux.

        Parameters
        ----------
        value : float
            Radiant flux in watts.
            By default, ``1.0``.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Surface source.
        """
        self._source_template.surface.radiant_flux.radiant_value = value
        return self

    def set_flux_luminous_intensity(self, value: float = 5) -> SourceSurface:
        """Set luminous intensity flux.

        Parameters
        ----------
        value : float
            Luminous intensity in candelas.
            By default, ``5.0``.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Surface source.
        """
        self._source_template.surface.luminous_intensity_flux.luminous_intensity_value = value
        return self

    def set_intensity(self) -> Intensity:
        """Set intensity.

        Returns
        -------
        ansys.speos.core.intensity.Intensity
            Intensity.
        """
        if (
            self._intensity._intensity_properties
            is not self._source_instance.surface_properties.intensity_properties
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._intensity._intensity_properties = (
                self._source_instance.surface_properties.intensity_properties
            )

        return self._intensity

    def set_exitance_constant(
        self, geometries: List[tuple[Union[GeoRef, face.Face, body.Body], bool]]
    ) -> SourceSurface:
        """Set existence constant.

        Parameters
        ----------
        geometries : List[tuple[ansys.speos.core.geo_ref.GeoRef, bool]]
            List of (face, reverseNormal).

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Surface source.
        """
        self._exitance_type = None

        self._source_template.surface.exitance_constant.SetInParent()
        self._source_instance.surface_properties.exitance_constant_properties.ClearField(
            "geo_paths"
        )
        if geometries != []:
            geo_paths = []
            for gr, reverse_normal in geometries:
                if isinstance(gr, GeoRef):
                    geo_paths.append(
                        ProtoScene.GeoPath(
                            geo_path=gr.to_native_link(), reverse_normal=reverse_normal
                        )
                    )
                elif isinstance(gr, (face.Face, body.Body)):
                    geo_paths.append(
                        ProtoScene.GeoPath(
                            geo_path=gr.geo_path.to_native_link(), reverse_normal=reverse_normal
                        )
                    )
                else:
                    msg = f"Type {type(gr)} is not supported as Surface Source geometry input."
                    raise TypeError(msg)
            self._source_instance.surface_properties.exitance_constant_properties.geo_paths.extend(
                geo_paths
            )
        return self

    def set_exitance_variable(self) -> SourceSurface.ExitanceVariable:
        """Set existence variable, taken from XMP map.

        Returns
        -------
        ansys.speos.core.source.SourceSurface.ExitanceVariable
            ExitanceVariable of surface source.
        """
        if self._exitance_type is None and self._source_template.surface.HasField(
            "exitance_variable"
        ):
            # Happens in case of project created via load of speos file
            self._exitance_type = SourceSurface.ExitanceVariable(
                exitance_variable=self._source_template.surface.exitance_variable,
                exitance_variable_props=self._source_instance.surface_properties.exitance_variable_properties,
                default_values=False,
                stable_ctr=True,
            )
        elif not isinstance(self._exitance_type, SourceSurface.ExitanceVariable):
            # if the _exitance_type is not ExitanceVariable then we create a new type.
            self._exitance_type = SourceSurface.ExitanceVariable(
                exitance_variable=self._source_template.surface.exitance_variable,
                exitance_variable_props=self._source_instance.surface_properties.exitance_variable_properties,
                stable_ctr=True,
            )
        elif (
            self._exitance_type._exitance_variable
            is not self._source_template.surface.exitance_variable
        ):
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._exitance_type._exitance_variable = self._source_template.surface.exitance_variable
            self._exitance_type._exitance_variable_props = (
                self._source_instance.surface_properties.exitance_variable_properties
            )
        return self._exitance_type

    def set_spectrum_from_xmp_file(self) -> SourceSurface:
        """Take spectrum from xmp file provided.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Surface source.
        """
        self._source_template.surface.spectrum_from_xmp_file.SetInParent()
        self._spectrum._no_spectrum_local = True
        return self

    def set_spectrum(self) -> Spectrum:
        """Set spectrum of the Source.

        Returns
        -------
        ansys.speos.core.spectrum.Spectrum
            Spectrum.
        """
        if self._source_template.surface.HasField("spectrum_from_xmp_file"):
            guid = ""
            if self._spectrum._spectrum.spectrum_link is not None:
                guid = self._spectrum._spectrum.spectrum_link.key
            self._source_template.surface.spectrum_guid = guid

        if self._spectrum._message_to_complete is not self._source_template.surface:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._spectrum._message_to_complete = self._source_template.surface

        self._spectrum._no_spectrum_local = False
        return self._spectrum._spectrum

    def commit(self) -> SourceSurface:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Source feature.
        """
        # intensity
        self._intensity.commit()
        self._source_template.surface.intensity_guid = self._intensity.intensity_template_link.key

        # spectrum & source
        super().commit()
        return self

    def reset(self) -> SourceSurface:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Source feature.
        """
        self._intensity.reset()
        # spectrum & source
        super().reset()
        return self

    def delete(self) -> SourceSurface:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.source.SourceSurface
            Source feature.
        """
        # Currently we don't perform delete in cascade,
        # so deleting a surface source does not delete the intensity template used
        # self._intensity.delete()

        # spectrum & source
        super().delete()
        return self


class BaseSourceAmbient(BaseSource):
    """
    Super Class for ambient sources.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project in which source shall be created.
    name : str
        Name of the source.
    description : str
        Description of the source.
        By default, ``""``.
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.
    source_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance, optional
        Source instance to provide if the feature does not have to be created from scratch
        By default, ``None``, means that the feature is created from scratch by default.

    Notes
    -----
    This is a Super class, **Do not instantiate this class yourself**
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
    ) -> None:
        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )

    class AutomaticSun:
        """Sun type Automatic.

        By default, user's current time and Ansys France is used a time zone.

        Parameters
        ----------
        sun: ansys.api.speos.scene.v2.scene_pb2.AutomaticSun
            Wavelengths range protobuf object to modify.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_sun_automatic method available in
        source classes.
        """

        def __init__(
            self,
            sun: scene_pb2.AutomaticSun,
            default_values: bool = True,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                raise RuntimeError(
                    "BaseSourceAmbient.AutomaticSun class instantiated outside of class scope"
                )
            self._sun = sun

            if default_values:
                now = datetime.datetime.now()
                self.year = now.year
                self.month = now.month
                self.day = now.day
                self.hour = now.hour
                self.minute = now.minute
                self.time_zone = "CET"
                self.longitude = 0.0
                self.latitude = 0.0

        @property
        def year(self) -> int:
            """Get year info of the automatic sun.

            Returns
            -------
            int
                year info.
            """
            return self._sun.year

        @year.setter
        def year(self, year: int) -> None:
            """Set year info of the automatic sun.

            Parameters
            ----------
            year: int
                year information.

            Returns
            -------
            None
            """
            self._sun.year = year

        @property
        def month(self) -> int:
            """Get month info of the automatic sun.

            Returns
            -------
            int
                month information.

            """
            return self._sun.month

        @month.setter
        def month(self, month: int) -> None:
            """Set month info of the automatic sun.

            Parameters
            ----------
            month: int
                month information.

            Returns
            -------
            None

            """
            self._sun.month = month

        @property
        def day(self) -> int:
            """Get day info of the automatic sun.

            Returns
            -------
            int
                day information.
            """
            return self._sun.day

        @day.setter
        def day(self, day: int) -> None:
            """Set day info of the automatic sun.

            Parameters
            ----------
            day: int
                day information.

            Returns
            -------
            None
            """
            self._sun.day = day

        @property
        def hour(self) -> int:
            """Get hour info of the automatic sun.

            Returns
            -------
            int
                hour information.

            """
            return self._sun.hour

        @hour.setter
        def hour(self, hour: int) -> None:
            """Set hour info of the automatic sun.

            Parameters
            ----------
            hour: int
                hour information.

            Returns
            -------
            None

            """
            self._sun.hour = hour

        @property
        def minute(self) -> int:
            """Get minute info of the automatic sun.

            Returns
            -------
            int
                minute information.

            """
            return self._sun.minute

        @minute.setter
        def minute(self, minute: int) -> None:
            """Set minute info of the automatic sun.

            Parameters
            ----------
            minute: int
                minute information.

            Returns
            -------
            None

            """
            self._sun.minute = minute

        @property
        def longitude(self) -> float:
            """Get longitude info of the automatic sun.

            Returns
            -------
            float
                longitude information.
            """
            return self._sun.longitude

        @longitude.setter
        def longitude(self, longitude: float) -> None:
            """Get longitude info of the automatic sun.

            Parameters
            ----------
            longitude: float
                longitude information.

            Returns
            -------
            None
            """
            self._sun.longitude = longitude

        @property
        def latitude(self) -> float:
            """Get latitude info of the automatic sun.

            Returns
            -------
            float
                latitude information.
            """
            return self._sun.latitude

        @latitude.setter
        def latitude(self, latitude: float) -> None:
            """Set latitude info of the automatic sun.

            Parameters
            ----------
            latitude: float
                latitude information.

            Returns
            -------
            None
            """
            self._sun.latitude = latitude

        @property
        def time_zone(self) -> str:
            """Get time zone info of the automatic sun.

            Returns
            -------
            str
                time zone abbreviation.
            """
            return self._sun.time_zone_uri

        @time_zone.setter
        def time_zone(self, time_zone: str) -> None:
            """Set time zone info of the automatic sun.

                default value to be "CET".

            Parameters
            ----------
            timezone: str
                timezone abbreviation.

            Returns
            -------
            None
            """
            self._sun.time_zone_uri = time_zone

    class Manual:
        """Sun type Manual>.

        By default, z-axis [0, 0, 1] is used as sun direction.

        Parameters
        ----------
        sun: ansys.api.speos.scene.v2.scene_pb2.ManualSun
            Wavelengths range protobuf object to modify.
        default_values : bool
            Uses default values when True.
        stable_ctr : bool
            Variable to indicate if usage is inside class scope

        Notes
        -----
        **Do not instantiate this class yourself**, use set_sun_manual method available in
        source classes.
        """

        def __init__(
            self,
            sun: scene_pb2.ManualSun,
            default_values: bool = True,
            stable_ctr: bool = False,
        ) -> None:
            if not stable_ctr:
                raise RuntimeError(
                    "BaseSourceAmbient.Manual class instantiated outside of class scope"
                )
            self._sun = sun

            if default_values:
                self.direction = [0, 0, 1]
                self.reverse_sun = False

        @property
        def direction(self) -> List[float]:
            """Get direction of the manual sun.

            Returns
            -------
            list of float
                list describing the direction of the manual sun.

            """
            return self._sun.sun_direction

        @direction.setter
        def direction(self, direction: List[float]) -> None:
            """Set direction of the manual sun.

                default value to be [0, 0, 1].

            Parameters
            ----------
            direction: List[float]
                direction of the sun.

            Returns
            -------
            BaseSourceAmbient.Manual

            """
            self._sun.sun_direction[:] = direction

        @property
        def reverse_sun(self) -> bool:
            """Get whether reverse direction of the manual sun.

            Returns
            -------
            bool
                True to reverse direction, False to not reverse direction

            """
            return self._sun.reverse_sun

        @reverse_sun.setter
        def reverse_sun(self, value: bool) -> None:
            """Reverse direction of the manual sun.

                default value to be False.

            Parameters
            ----------
            value: bool
                True to reverse direction, False to not reverse direction

            Returns
            -------
            None

            """
            self._sun.reverse_sun = value


class SourceAmbientNaturalLight(BaseSourceAmbient):
    """Natural light ambient source.

    By default, turbidity is set to be 3 with Sky.
    [0, 0, 1] is used as zenith direction, [0, 1, 0] as north direction.
    Sun type is set to be automatic type.

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
    default_values : bool
        Uses default values when True.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        source_instance: Optional[ProtoScene.SourceInstance] = None,
        default_values: bool = True,
    ) -> None:
        if metadata is None:
            metadata = {}

        super().__init__(
            project=project,
            name=name,
            description=description,
            metadata=metadata,
            source_instance=source_instance,
        )
        self._speos_client = self._project.client
        self._name = name
        self._type = None

        if default_values:
            # Default values
            self.zenith_direction = [0, 0, 1]
            self.north_direction = [0, 1, 0]
            self.reverse_north_direction = False
            self.reverse_zenith_direction = False
            self.turbidity = 3
            self.with_sky = True
            self.set_sun_automatic()

    @property
    def turbidity(self) -> float:
        """Get turbidity of the natural light source.

        Returns
        -------
        float
            value of Turbidity the measure of the fraction of scattering.

        """
        return self._source_template.ambient.natural_light.turbidity

    @turbidity.setter
    def turbidity(self, value: float) -> None:
        """Set turbidity of the natural light source.

            default value to be 3.

        Parameters
        ----------
        value: float
            set value of Turbidity the measure of the fraction of scattering.

        Returns
        -------
        None

        """
        if not 1.9 <= value <= 9.9:
            raise ValueError("Varies needs to be between 1.9 and 9.9")
        self._source_template.ambient.natural_light.turbidity = value

    @property
    def with_sky(self) -> bool:
        """Bool of whether activated using sky in the natural light source.

        Returns
        -------
        bool
            True as using sky, while False as using natural light without the sky.

        """
        return self._source_template.ambient.natural_light.with_sky

    @with_sky.setter
    def with_sky(self, value: bool) -> None:
        """Activate using sky in the natural light source.

            default value to be True.

        Parameters
        ----------
        value: bool
            True as using sky, while False as using natural light without the sky.

        Returns
        -------
        SourceAmbientNaturalLight

        """
        self._source_template.ambient.natural_light.with_sky = value

    @property
    def zenith_direction(self) -> List[float]:
        """Get zenith direction of the natural light source.

        Returns
        -------
        List[float]
            direction defines the zenith direction of the natural light.

        """
        return self._source_instance.ambient_properties.zenith_direction

    @zenith_direction.setter
    def zenith_direction(self, direction: Optional[List[float]] = None) -> None:
        """Set zenith direction of the natural light source.

            default value to be [0, 0, 1]

        Parameters
        ----------
        direction: Optional[List[float]]
            direction defines the zenith direction of the natural light.

        Returns
        -------
        None

        """
        self._source_instance.ambient_properties.zenith_direction[:] = direction

    @property
    def reverse_zenith_direction(self) -> bool:
        """
        Get whether reverse zenith direction of the natural light source.

        Returns
        -------
        bool
            True to reverse zenith direction, False otherwise.

        """
        return self._source_instance.ambient_properties.reverse_zenith

    @reverse_zenith_direction.setter
    def reverse_zenith_direction(self, value: bool) -> None:
        """Set reverse zenith direction of the natural light source.

            default value to be False.

        Parameters
        ----------
        value: bool
            True to reverse zenith direction, False otherwise.

        Returns
        -------
        None

        """
        self._source_instance.ambient_properties.reverse_zenith = value

    @property
    def north_direction(self) -> List[float]:
        """Get north direction of the natural light source.

        Returns
        -------
        List[float]
            direction defines the north direction of the natural light.

        """
        return self._source_instance.ambient_properties.natural_light_properties.north_direction

    @north_direction.setter
    def north_direction(self, direction: List[float]) -> None:
        """Set north direction of the natural light source.

            default value to be [0, 1, 0].

        Parameters
        ----------
        direction: List[float]
            direction defines the north direction of the natural light.

        Returns
        -------
        None

        """
        self._source_instance.ambient_properties.natural_light_properties.north_direction[:] = (
            direction
        )

    @property
    def reverse_north_direction(self) -> bool:
        """Get whether reverse north direction of the natural light source.

        Returns
        -------
        bool
            True as reverse north direction, False otherwise.

        """
        return self._source_instance.ambient_properties.natural_light_properties.reverse_north

    @reverse_north_direction.setter
    def reverse_north_direction(self, value: bool) -> None:
        """Set reverse north direction of the natural light source.

            default value to be False.

        Parameters
        ----------
        value: bool
            True to reverse north direction, False otherwise.

        Returns
        -------
        None

        """
        self._source_instance.ambient_properties.natural_light_properties.reverse_north = value

    def set_sun_automatic(self) -> BaseSourceAmbient.AutomaticSun:
        """Set natural light sun type as automatic.

        Returns
        -------
        BaseSourceAmbient.AutomaticSun

        """
        natural_light_properties = self._source_instance.ambient_properties.natural_light_properties
        if self._type is None and natural_light_properties.sun_axis_system.HasField(
            "automatic_sun"
        ):
            self._type = BaseSourceAmbient.AutomaticSun(
                natural_light_properties.sun_axis_system.automatic_sun,
                default_values=False,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSourceAmbient.AutomaticSun):
            # if the _type is not Colorimetric then we create a new type.
            self._type = BaseSourceAmbient.AutomaticSun(
                natural_light_properties.sun_axis_system.automatic_sun,
                stable_ctr=True,
            )
        elif self._type._sun is not natural_light_properties.sun_axis_system.automatic_sun:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sun = natural_light_properties.sun_axis_system.automatic_sun
        return self._type

    def set_sun_manual(self) -> BaseSourceAmbient.Manual:
        """Set natural light sun type as manual.

        Returns
        -------
        BaseSourceAmbient.Manual
        """
        natural_light_properties = self._source_instance.ambient_properties.natural_light_properties
        if self._type is None and natural_light_properties.sun_axis_system.HasField("manual_sun"):
            self._type = BaseSourceAmbient.Manual(
                natural_light_properties.sun_axis_system.manual_sun,
                default_values=False,
                stable_ctr=True,
            )
        elif not isinstance(self._type, BaseSourceAmbient.Manual):
            # if the _type is not Colorimetric then we create a new type.
            self._type = BaseSourceAmbient.Manual(
                natural_light_properties.sun_axis_system.manual_sun,
                stable_ctr=True,
            )
        elif self._type._sun is not natural_light_properties.sun_axis_system.manual_sun:
            # Happens in case of feature reset (to be sure to always modify correct data)
            self._type._sun = natural_light_properties.sun_axis_system.manual_sun
        return self._type
