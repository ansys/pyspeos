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

"""Provides a way to interact with Speos feature: Source."""
from __future__ import annotations

from typing import List, Mapping, Optional
import uuid

import ansys.speos.core as core
from ansys.speos.script.geo_ref import GeoRef
from ansys.speos.script.intensity import Intensity
import ansys.speos.script.project as project
from ansys.speos.script.spectrum import Spectrum


class Source:
    """Speos feature : Source.

    Parameters
    ----------
    project : ansys.speos.script.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str
        Description of the feature.
        By default, ``""``.
    metadata : Mapping[str, str]
        Metadata of the feature.
        By default, ``{}``.

    Attributes
    ----------
    source_template_link : ansys.speos.core.source_template.SourceTemplateLink
        Link object for the source template in database.
    """

    class Luminaire:
        """Type of Source : Luminaire.

        Parameters
        ----------
        speos_client : ansys.speos.core.client.SpeosClient
            The Speos instance client.
        source_template : ansys.api.speos.source.v1.source_pb2.SourceTemplate
            Template of the source.
        name : str
            Name of the source feature.
        """

        def __init__(self, speos_client: core.SpeosClient, source_template: core.SourceTemplate, name: str) -> None:
            self._source_template = source_template
            self._spectrum = Spectrum(speos_client=speos_client, name=name + ".Spectrum")

            # Default values
            self.set_flux_from_intensity_file().set_spectrum().set_incandescent()

        def set_flux_from_intensity_file(self) -> Source.Luminaire:
            """Take flux from intensity file provided.

            Returns
            -------
            ansys.speos.script.source.Source.Luminaire
                Luminaire source.
            """
            self._source_template.luminaire.flux_from_intensity_file.SetInParent()
            return self

        def set_flux_luminous(self, value: float = 683) -> Source.Luminaire:
            """Set luminous flux.

            Parameters
            ----------
            value : float
                Luminous flux in lumens.
                By default, ``683.0``.

            Returns
            -------
            ansys.speos.script.source.Source.Luminaire
                Luminaire source.
            """
            self._source_template.luminaire.luminous_flux.luminous_value = value
            return self

        def set_flux_radiant(self, value: float = 1) -> Source.Luminaire:
            """Set radiant flux.

            Parameters
            ----------
            value : float
                Radiant flux in watts.
                By default, ``1.0``.

            Returns
            -------
            ansys.speos.script.source.Source.Luminaire
                Luminaire source.
            """
            self._source_template.luminaire.radiant_flux.radiant_value = value
            return self

        def set_intensity_file_uri(self, uri: str) -> Source.Luminaire:
            """Set intensity file.

            Parameters
            ----------
            uri : str
                IES or EULUMDAT format file uri.

            Returns
            -------
            ansys.speos.script.source.Source.Luminaire
                Luminaire source.
            """
            self._source_template.luminaire.intensity_file_uri = uri
            return self

        def set_spectrum(self) -> Spectrum:
            """Set spectrum.

            Returns
            -------
            ansys.speos.script.spectrum.Spectrum
                Spectrum.
            """
            return self._spectrum

        def __str__(self) -> str:
            return str(self._spectrum)

        def _commit(self) -> Source.Luminaire:
            self._spectrum.commit()
            self._source_template.luminaire.spectrum_guid = self._spectrum.spectrum_link.key
            return self

    class Surface:
        """Type of Source : Surface.

        Parameters
        ----------
        speos_client : ansys.speos.core.client.SpeosClient
            The Speos instance client.
        source_template : ansys.api.speos.source.v1.source_pb2.SourceTemplate
            Template of the source.
        name : str
            Name of the source feature.
        intensity_properties : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.IntensityProperties
            Intensity properties.
        """

        def __init__(
            self,
            speos_client: core.SpeosClient,
            source_template: core.SourceTemplate,
            name: str,
            intensity_properties: core.Scene.SourceInstance.IntensityProperties,
        ) -> None:
            self._speos_client = speos_client
            self._source_template = source_template
            self._spectrum = None
            self._intensity = Intensity(
                speos_client=speos_client, name=name + ".Intensity", intensity_props_to_complete=intensity_properties
            )

            # Default values
            self.set_flux_luminous().set_exitance_constant().set_intensity()
            self.set_spectrum()

        def set_flux_from_intensity_file(self) -> Source.Surface:
            """Take flux from intensity file provided.

            Returns
            -------
            ansys.speos.script.source.Source.Surface
                Surface source.
            """
            self._source_template.surface.flux_from_intensity_file.SetInParent()
            return self

        def set_flux_luminous(self, value: float = 683) -> Source.Surface:
            """Set luminous flux.

            Parameters
            ----------
            value : float
                Luminous flux in lumens.
                By default, ``683.0``.

            Returns
            -------
            ansys.speos.script.source.Source.Surface
                Surface source.
            """
            self._source_template.surface.luminous_flux.luminous_value = value
            return self

        def set_flux_radiant(self, value: float = 1) -> Source.Surface:
            """Set radiant flux.

            Parameters
            ----------
            value : float
                Radiant flux in watts.
                By default, ``1.0``.

            Returns
            -------
            ansys.speos.script.source.Source.Surface
                Surface source.
            """
            self._source_template.surface.radiant_flux.radiant_value = value
            return self

        def set_flux_luminous_intensity(self, value: float = 5) -> Source.Surface:
            """Set luminous intensity flux.

            Parameters
            ----------
            value : float
                Luminous intensity in candelas.
                By default, ``5.0``.

            Returns
            -------
            ansys.speos.script.source.Source.Surface
                Surface source.
            """
            self._source_template.surface.luminous_intensity_flux.luminous_intensity_value = value
            return self

        def set_intensity(self) -> Intensity:
            """Set intensity.

            Returns
            -------
            ansys.speos.script.intensity.Intensity
                Intensity.
            """
            return self._intensity

        def set_exitance_constant(self) -> Source.Surface:
            """Set exitance constant.

            Returns
            -------
            ansys.speos.script.source.Source.Surface
                Surface source.
            """
            self._source_template.surface.exitance_constant.SetInParent()
            return self

        def set_exitance_variable(self, uri: str) -> Source.Surface:
            """Set exitance variable, taken from XMP map.

            Parameters
            ----------
            uri : str
                XMP file describing exitance.

            Returns
            -------
            ansys.speos.script.source.Source.Surface
                Surface source.
            """
            self._source_template.surface.exitance_variable.exitance_xmp_file_uri = uri
            return self

        def set_spectrum_from_xmp_file(self) -> Source.Surface:
            """Take spectrum from xmp file provided.

            Returns
            -------
            ansys.speos.script.source.Source.Surface
                Surface source.
            """
            self._source_template.surface.spectrum_from_xmp_file.SetInParent()
            self._spectrum = None
            return self

        def set_spectrum(self) -> Spectrum:
            """Set spectrum

            Returns
            -------
            ansys.speos.script.spectrum.Spectrum
                Spectrum.
            """
            if self._spectrum is None:
                self._spectrum = Spectrum(speos_client=self._speos_client, name=self._source_template.name + ".Spectrum")
                self._source_template.surface.spectrum_guid = ""
            return self._spectrum

        def __str__(self) -> str:
            out_str = ""
            out_str += str(self._intensity)
            if self._spectrum is not None:
                out_str += str(self._spectrum)
            return out_str

        def _commit(self) -> Source.Surface:
            # intensity
            self._intensity.commit()
            self._source_template.surface.intensity_guid = self._intensity.intensity_template_link.key

            # spectrum
            if self._spectrum is not None:
                self._spectrum.commit()
                self._source_template.surface.spectrum_guid = self._spectrum.spectrum_link.key
            return self

    class RayFile:
        """Type of Source : RayFile.

        Parameters
        ----------
        speos_client : ansys.speos.core.client.SpeosClient
            The Speos instance client.
        source_template : ansys.api.speos.source.v1.source_pb2.SourceTemplate
            Template of the source.
        name : str
            Name of the source feature.
        """

        def __init__(self, speos_client: core.SpeosClient, source_template: core.SourceTemplate, name: str) -> None:
            self._client = speos_client
            self._source_template = source_template
            self._spectrum = None

            # Default values
            self.set_flux_from_ray_file().set_spectrum_from_ray_file()

        def set_ray_file_uri(self, uri: str) -> Source.RayFile:
            """Set ray file.

            Parameters
            ----------
            uri : str
                Rayfile format file uri (.ray or .tm25ray files expected).

            Returns
            -------
            ansys.speos.script.source.Source.RayFile
                RayFile source.
            """
            self._source_template.rayfile.ray_file_uri = uri
            return self

        def set_flux_from_ray_file(self) -> Source.RayFile:
            """Take flux from ray file provided.

            Returns
            -------
            ansys.speos.script.source.Source.RayFile
                RayFile source.
            """
            self._source_template.rayfile.flux_from_ray_file.SetInParent()
            return self

        def set_flux_luminous(self, value: float = 683) -> Source.RayFile:
            """Set luminous flux.

            Parameters
            ----------
            value : float
                Luminous flux in lumens.
                By default, ``683.0``.

            Returns
            -------
            ansys.speos.script.source.Source.RayFile
                RayFile source.
            """
            self._source_template.rayfile.luminous_flux.luminous_value = value
            return self

        def set_flux_radiant(self, value: float = 1) -> Source.RayFile:
            """Set radiant flux.

            Parameters
            ----------
            value : float
                Radiant flux in watts.
                By default, ``1.0``.

            Returns
            -------
            ansys.speos.script.source.Source.RayFile
                RayFile source.
            """
            self._source_template.rayfile.radiant_flux.radiant_value = value
            return self

        def set_spectrum_from_ray_file(self) -> Source.RayFile:
            """Take spectrum from ray file provided.

            Returns
            -------
            ansys.speos.script.source.Source.RayFile
                RayFile source.
            """
            self._source_template.rayfile.spectrum_from_ray_file.SetInParent()
            self._spectrum = None
            return self

        def set_spectrum(self) -> Spectrum:
            """Set spectrum

            Returns
            -------
            ansys.speos.script.spectrum.Spectrum
                Spectrum.
            """
            if self._spectrum is None:
                self._spectrum = Spectrum(speos_client=self._client, name=self._source_template.name + ".Spectrum")
                self._source_template.rayfile.spectrum_guid = ""
            return self._spectrum

        def __str__(self) -> str:
            out_str = ""
            if self._spectrum is not None:
                out_str += str(self._spectrum)
            return out_str

        def _commit(self) -> Source.RayFile:
            if self._spectrum is not None:
                self._spectrum.commit()
                self._source_template.rayfile.spectrum_guid = self._spectrum.spectrum_link.key

            return self

    class RayFileProperties:
        """Properties for source of type: RayFile.

        Parameters
        ----------
        source_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance
            Instance of the source.
        """

        def __init__(self, source_instance: core.Scene.SourceInstance) -> None:
            self._source_instance = source_instance

            # Default values
            self.set_axis_system()

        def set_axis_system(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Source.RayFileProperties:
            """Set position of the source.

            Parameters
            ----------
            axis_system : List[float]
                Position of the source [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

            Returns
            -------
            ansys.speos.script.source.Source.RayFileProperties
                RayFile Source properties.
            """
            self._source_instance.rayfile_properties.axis_system[:] = axis_system
            return self

        def set_exit_geometries(self, exit_geometries: Optional[List[GeoRef]] = None) -> Source.RayFileProperties:
            """Set exit geometries.

            Parameters
            ----------
            exit_geometries : List[ansys.speos.script.geo_ref.GeoRef], optional
                Exit Geometries that will use this rayfile source.
                By default, ``None``.

            Returns
            -------
            ansys.speos.script.source.Source.RayFileProperties
                RayFile Source properties.
            """
            if exit_geometries is not None:
                self._source_instance.rayfile_properties.exit_geometries.geo_paths[:] = [gr.to_native_link() for gr in exit_geometries]
            return self

    class SurfaceProperties:
        """Properties for source of type: Surface.

        Parameters
        ----------
        source_instance : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance
            Instance of the source.
        """

        def __init__(self, source_instance: core.Scene.SourceInstance) -> None:
            self._source_instance = source_instance

        def set_exitance_constant_properties(self, geometries: List[tuple[GeoRef, bool]]) -> Source.SurfaceProperties:
            """Set geometries in case the surface source has exitance constant.

            Parameters
            ----------
            geometries : List[tuple[ansys.speos.script.geo_ref.GeoRef, bool]]
                List of (face, reverseNormal).

            Returns
            -------
            ansys.speos.script.source.Source.SurfaceProperties
                Surface Source properties.
            """
            my_list = [
                core.Scene.GeoPath(geo_path=gr.to_native_link(), reverse_normal=reverse_normal) for (gr, reverse_normal) in geometries
            ]
            self._source_instance.surface_properties.exitance_constant_properties.ClearField("geo_paths")
            self._source_instance.surface_properties.exitance_constant_properties.geo_paths.extend(my_list)
            return self

        def set_exitance_variable_properties(self, axis_plane: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0]) -> Source.SurfaceProperties:
            """Set position of the exitance map in case the surface source has exitance variable.

            Parameters
            ----------
            axis_plane : List[float]
                Position of the exitance map [Ox Oy Oz Xx Xy Xz Yx Yy Yz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0]``.

            Returns
            -------
            ansys.speos.script.source.Source.SurfaceProperties
                Surface Source properties.
            """
            self._source_instance.surface_properties.exitance_variable_properties.axis_plane[:] = axis_plane
            return self

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._unique_id = None
        self.source_template_link = None
        """Link object for the source template in database."""

        # Attribute representing the kind of source. Can be on object of type script.Source.Luminaire, script.Source.RayFile, ...
        self._type = None
        # Attribute gathering more complex source properties
        self._props = None

        # Create local SourceTemplate
        self._source_template = core.SourceTemplate(name=name, description=description, metadata=metadata)

        # Create local SourceInstance
        self._source_instance = core.Scene.SourceInstance(name=name, description=description, metadata=metadata)

    def set_luminaire(self) -> Luminaire:
        """Set the source as luminaire.

        Returns
        -------
        ansys.speos.script.source.Source.Luminaire
            Luminaire source.
        """
        if type(self._type) != Source.Luminaire:
            self._type = Source.Luminaire(
                speos_client=self._project.client, source_template=self._source_template, name=self._source_template.name
            )
        return self._type

    def set_surface(self) -> Surface:
        """Set the source as surface.

        Returns
        -------
        ansys.speos.script.source.Source.Surface
            Surface source.
        """
        if type(self._props) != Source.SurfaceProperties:
            self._props = Source.SurfaceProperties(source_instance=self._source_instance)
        if type(self._type) != Source.Surface:
            self._type = Source.Surface(
                speos_client=self._project.client,
                source_template=self._source_template,
                name=self._source_template.name,
                intensity_properties=self._source_instance.surface_properties.intensity_properties,
            )
        return self._type

    def set_rayfile(self) -> RayFile:
        """Set the source as rayfile.

        Returns
        -------
        ansys.speos.script.source.Source.RayFile
            Surface source.
        """
        if type(self._type) != Source.RayFile:
            self._type = Source.RayFile(
                speos_client=self._project.client, source_template=self._source_template, name=self._source_template.name
            )
        return self._type

    def set_luminaire_properties(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Source:
        """Set the properties related to luminaire template.

        Parameters
        ----------
        axis_system : List[float]
            Position of the source [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
            By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

        Returns
        -------
        ansys.speos.script.source.Source
            Source feature.
        """
        self._source_instance.luminaire_properties.axis_system[:] = axis_system
        return self

    def set_surface_properties(self) -> Source.SurfaceProperties:
        """Set the properties related to surface template.

        Returns
        -------
        ansys.speos.script.source.Source.SurfaceProperties
            Surface source properties.
        """
        if type(self._props) != Source.SurfaceProperties:
            self._props = Source.SurfaceProperties(source_instance=self._source_instance)
        return self._props

    def set_rayfile_properties(self) -> Source.RayFileProperties:
        """Set the properties related to rayfile template.

        Returns
        -------
        ansys.speos.script.source.Source.RayFileProperties
            RayFile source properties.
        """
        if type(self._props) != Source.RayFileProperties:
            self._props = Source.RayFileProperties(source_instance=self._source_instance)
        return self

    def __str__(self) -> str:
        """Return the string representation of the source."""
        out_str = ""
        # SourceInstance (= source guid + source properties)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            src_inst = next((x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id), None)
            if src_inst is not None:
                out_str += core.protobuf_message_to_str(src_inst)
            else:
                out_str += f"local: " + core.protobuf_message_to_str(self._source_instance)
        else:
            out_str += f"local: " + core.protobuf_message_to_str(self._source_instance)

        # SourceTemplate
        if self.source_template_link is None:
            out_str += f"\nlocal: {self._source_template}"
        else:
            out_str += "\n" + str(self.source_template_link)

        # Contained objects like Spectrum, IntensityTemplate
        if self._type is not None:
            out_str += "\n"
            out_str += str(self._type)

        return out_str

    def commit(self) -> Source:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.script.source.Source
            Source feature.
        """
        # The _unique_id will help to find correct item in the scene.sources (the list of SourceInstance)
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._source_instance.metadata["UniqueId"] = self._unique_id

        # This allows to commit managed object contained in _luminaire, _rayfile, etc.. Like Spectrum, IntensityTemplate
        if self._type is not None:
            self._type._commit()

        # Save or Update the source template (depending on if it was already saved before)
        if self.source_template_link is None:
            self.source_template_link = self._project.client.source_templates().create(message=self._source_template)
            self._source_instance.source_guid = self.source_template_link.key
        else:
            self.source_template_link.set(data=self._source_template)

        # Update the scene with the source instance
        if self._project.scene_link:
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            src_inst = next((x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id), None)
            if src_inst is not None:
                src_inst.CopyFrom(self._source_instance)  # if yes, just replace
            else:
                scene_data.sources.append(self._source_instance)  # if no, just add it to the list of sources

            self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def reset(self) -> Source:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.script.source.Source
            Source feature.
        """
        # Reset source template
        if self.source_template_link is not None:
            self._source_template = self.source_template_link.get()

        # Reset source instance
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            # Look if an element corresponds to the _unique_id
            src_inst = next((x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id), None)
            if src_inst is not None:
                self._source_instance = src_inst
        return self

    def delete(self) -> Source:
        """Delete feature: delete data from the speos server database.
        The local data are still available

        Returns
        -------
        ansys.speos.script.source.Source
            Source feature.
        """
        # Delete the source template
        if self.source_template_link is not None:
            self.source_template_link.delete()
            self.source_template_link = None

        # Reset then the source_guid (as the source template was deleted just above)
        self._source_instance.source_guid = ""

        # Remove the source from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data
        src_inst = next((x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id), None)
        if src_inst is not None:
            scene_data.sources.remove(src_inst)
            self._project.scene_link.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        return self
