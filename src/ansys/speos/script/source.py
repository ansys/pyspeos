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

from typing import List, Mapping, Union
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

    class Spectrum:
        def __init__(
            self,
            speos_client: core.SpeosClient,
            name: str,
            message_to_complete: Union[core.SourceTemplate.RayFile, core.SourceTemplate.Surface, core.SourceTemplate.Luminaire],
            spectrum_guid: str = "",
        ) -> None:
            self._message_to_complete = message_to_complete
            if spectrum_guid != "":
                self._spectrum = Spectrum(speos_client=speos_client, name=name + ".Spectrum", key=spectrum_guid)
            else:
                self._spectrum = Spectrum(speos_client=speos_client, name=name + ".Spectrum")

            self._no_spectrum = None  # None means never committed, or deleted
            self._no_spectrum_local = False

        def __str__(self) -> str:
            if self._no_spectrum is None:
                if self._no_spectrum_local == False:
                    return str(self._spectrum)
            else:
                if self._no_spectrum == False:
                    return str(self._spectrum)
            return ""

        def _commit(self) -> Source.RayFile:
            if not self._no_spectrum_local:
                self._spectrum.commit()
                self._message_to_complete.spectrum_guid = self._spectrum.spectrum_link.key
                self._no_spectrum = self._no_spectrum_local
            return self

        def _reset(self) -> Source.RayFile:
            self._spectrum.reset()
            if self._no_spectrum is not None:
                self._no_spectrum_local = self._no_spectrum
            return self

        def _delete(self) -> Source.RayFile:
            self._no_spectrum = None
            return self

    class Luminaire:
        """Type of Source : Luminaire.
        By default, a flux from intensity file is chosen, with an incandescent spectrum.

        Parameters
        ----------
        speos_client : ansys.speos.core.client.SpeosClient
            The Speos instance client.
        name : str
            Name of the source feature.
        luminaire : ansys.api.speos.source.v1.source_pb2.SourceTemplate
            Luminaire source to complete.
        luminaire_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.LuminaireProperties
            Luminaire source properties to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            speos_client: core.SpeosClient,
            name: str,
            luminaire: core.SourceTemplate.luminaire,
            luminaire_props: core.Scene.SourceInstance.LuminaireProperties,
            default_values: bool = True,
        ) -> None:
            self._luminaire = luminaire
            self._luminaire_props = luminaire_props

            if self._luminaire.spectrum_guid != "":
                self._spectrum = Spectrum(speos_client=speos_client, name=name + ".Spectrum", key=self._luminaire.spectrum_guid)
            else:
                self._spectrum = Spectrum(speos_client=speos_client, name=name + ".Spectrum")

            if default_values:
                # Default values
                self.set_flux_from_intensity_file().set_spectrum().set_incandescent()
                self.set_axis_system()

        def set_flux_from_intensity_file(self) -> Source.Luminaire:
            """Take flux from intensity file provided.

            Returns
            -------
            ansys.speos.script.source.Source.Luminaire
                Luminaire source.
            """
            self._luminaire.flux_from_intensity_file.SetInParent()
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
            self._luminaire.luminous_flux.luminous_value = value
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
            self._luminaire.radiant_flux.radiant_value = value
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
            self._luminaire.intensity_file_uri = uri
            return self

        def set_spectrum(self) -> Spectrum:
            """Set spectrum.

            Returns
            -------
            ansys.speos.script.spectrum.Spectrum
                Spectrum.
            """
            return self._spectrum

        def set_axis_system(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Source.Luminaire:
            """Set position of the source.

            Parameters
            ----------
            axis_system : List[float]
                Position of the source [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

            Returns
            -------
            ansys.speos.script.source.Source.Luminaire
                Luminaire source.
            """
            self._luminaire_props.axis_system[:] = axis_system
            return self

        def __str__(self) -> str:
            return str(self._spectrum)

        def _commit(self) -> Source.Luminaire:
            self._spectrum.commit()
            self._luminaire.spectrum_guid = self._spectrum.spectrum_link.key
            return self

        def _reset(self) -> Source.Luminaire:
            return self

        def _delete(self) -> Source.Luminaire:
            return self

    class Surface:
        """Type of Source : Surface.
        By default, a luminous flux and exitance constant are chosen. With a monochromatic spectrum,
        and lambertian intensity (cos with N = 1).

        Parameters
        ----------
        speos_client : ansys.speos.core.client.SpeosClient
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
            """Type of surface source exitance : exitance variable.

            Parameters
            ----------
            exitance_variable : ansys.api.speos.source.v1.source_pb2.SourceTemplate.Surface.ExitanceVariable
                Exitance variable to complete.
            exitance_variable_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.SurfaceProperties.ExitanceVariableProperties
                Exitance variable properties to complete.
            default_values : bool
                Uses default values when True.
            """

            def __init__(
                self,
                exitance_variable: core.SourceTemplate.Surface.ExitanceVariable,
                exitance_variable_props: core.Scene.SourceInstance.SurfaceProperties.ExitanceVariableProperties,
                default_values: bool = True,
            ) -> None:
                self._exitance_variable = exitance_variable
                self._exitance_variable_props = exitance_variable_props

                if default_values:
                    # Default values
                    self.set_axis_plane()

            def set_xmp_file_uri(self, uri: str) -> Source.Surface.ExitanceVariable:
                """Set exitance xmp file.

                Parameters
                ----------
                uri : str
                    XMP file describing exitance.

                Returns
                -------
                ansys.speos.script.source.Source.Surface.ExitanceVariable
                    ExitanceVariable of surface source.
                """
                self._exitance_variable.exitance_xmp_file_uri = uri
                return self

            def set_axis_plane(self, axis_plane: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0]) -> Source.Surface.ExitanceVariable:
                """Set position of the exitance map.

                Parameters
                ----------
                axis_plane : List[float]
                    Position of the exitance map [Ox Oy Oz Xx Xy Xz Yx Yy Yz].
                    By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0]``.

                Returns
                -------
                ansys.speos.script.source.Source.Surface.ExitanceVariable
                    ExitanceVariable of surface Source.
                """
                self._exitance_variable_props.axis_plane[:] = axis_plane
                return self

        def __init__(
            self,
            speos_client: core.SpeosClient,
            name: str,
            surface: core.SourceTemplate.Surface,
            surface_props: core.Scene.SourceInstance.SurfaceProperties,
            default_values: bool = True,
        ) -> None:
            self._speos_client = speos_client
            self._surface = surface
            self._name = name
            self._surface_props = surface_props

            spectrum_guid = ""
            if self._surface.HasField("spectrum_guid"):
                spectrum_guid = self._surface.spectrum_guid
            self._spectrum = Source.Spectrum(
                speos_client=speos_client, name=name + ".Spectrum", message_to_complete=self._surface, spectrum_guid=spectrum_guid
            )

            self._intensity = Intensity(
                speos_client=speos_client,
                name=name + ".Intensity",
                intensity_props_to_complete=surface_props.intensity_properties,
                key=self._surface.intensity_guid,
            )

            # Attribute gathering more complex exitance type
            self._exitance_type = None

            if default_values:
                # Default values
                self.set_flux_luminous().set_exitance_constant(geometries=[]).set_intensity()
                self.set_spectrum()

        def set_flux_from_intensity_file(self) -> Source.Surface:
            """Take flux from intensity file provided.

            Returns
            -------
            ansys.speos.script.source.Source.Surface
                Surface source.
            """
            self._surface.flux_from_intensity_file.SetInParent()
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
            self._surface.luminous_flux.luminous_value = value
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
            self._surface.radiant_flux.radiant_value = value
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
            self._surface.luminous_intensity_flux.luminous_intensity_value = value
            return self

        def set_intensity(self) -> Intensity:
            """Set intensity.

            Returns
            -------
            ansys.speos.script.intensity.Intensity
                Intensity.
            """
            return self._intensity

        def set_exitance_constant(self, geometries: List[tuple[GeoRef, bool]]) -> Source.Surface:
            """Set exitance constant.

            Parameters
            ----------
            geometries : List[tuple[ansys.speos.script.geo_ref.GeoRef, bool]]
                List of (face, reverseNormal).

            Returns
            -------
            ansys.speos.script.source.Source.Surface
                Surface source.
            """
            self._exitance_type = None

            self._surface.exitance_constant.SetInParent()
            self._surface_props.exitance_constant_properties.ClearField("geo_paths")
            if geometries != []:
                my_list = [
                    core.Scene.GeoPath(geo_path=gr.to_native_link(), reverse_normal=reverse_normal) for (gr, reverse_normal) in geometries
                ]
                self._surface_props.exitance_constant_properties.geo_paths.extend(my_list)
            return self

        def set_exitance_variable(self) -> Source.Surface.ExitanceVariable:
            """Set exitance variable, taken from XMP map.

            Returns
            -------
            ansys.speos.script.source.Source.Surface.ExitanceVariable
                ExitanceVariable of surface source.
            """
            if self._exitance_type is None and self._surface.HasField("exitance_variable"):
                self._exitance_type = Source.Surface.ExitanceVariable(
                    exitance_variable=self._surface.exitance_variable,
                    exitance_variable_props=self._surface_props.exitance_variable_properties,
                    default_values=False,
                )
            elif type(self._exitance_type) != Source.Surface.ExitanceVariable:
                self._exitance_type = Source.Surface.ExitanceVariable(
                    exitance_variable=self._surface.exitance_variable,
                    exitance_variable_props=self._surface_props.exitance_variable_properties,
                )
            return self._exitance_type

        def set_spectrum_from_xmp_file(self) -> Source.Surface:
            """Take spectrum from xmp file provided.

            Returns
            -------
            ansys.speos.script.source.Source.Surface
                Surface source.
            """
            self._surface.spectrum_from_xmp_file.SetInParent()
            self._spectrum._no_spectrum_local = True
            return self

        def set_spectrum(self) -> Spectrum:
            """Set spectrum

            Returns
            -------
            ansys.speos.script.spectrum.Spectrum
                Spectrum.
            """
            if self._surface.HasField("spectrum_from_xmp_file"):
                guid = ""
                if self._spectrum._spectrum.spectrum_link is not None:
                    guid = self._spectrum._spectrum.spectrum_link.key
                self._surface.spectrum_guid = guid
            self._spectrum._no_spectrum_local = False
            return self._spectrum._spectrum

        def __str__(self) -> str:
            out_str = ""
            out_str += str(self._intensity)
            out_str += "\n" + str(self._spectrum)
            return out_str

        def _commit(self) -> Source.Surface:
            # intensity
            self._intensity.commit()
            self._surface.intensity_guid = self._intensity.intensity_template_link.key

            # spectrum
            self._spectrum._commit()
            return self

        def _reset(self) -> Source.Surface:
            self._spectrum._reset()
            return self

        def _delete(self) -> Source.Surface:
            self._spectrum._delete()
            return self

    class RayFile:
        """Type of Source : RayFile.
        By default, flux and spectrum from ray file are selected.

        Parameters
        ----------
        speos_client : ansys.speos.core.client.SpeosClient
            The Speos instance client.
        name : str
            Name of the source feature.
        ray_file : ansys.api.speos.source.v1.source_pb2.SourceTemplate.RayFile
            Ray file source to complete.
        ray_file_props : ansys.api.speos.scene.v2.scene_pb2.Scene.SourceInstance.RayFileProperties
            Ray file source properties to complete.
        default_values : bool
            Uses default values when True.
        """

        def __init__(
            self,
            speos_client: core.SpeosClient,
            name: str,
            ray_file: core.SourceTemplate.RayFile,
            ray_file_props: core.Scene.SourceInstance.RayFileProperties,
            default_values: bool = True,
        ) -> None:
            self._client = speos_client
            self._ray_file = ray_file
            self._ray_file_props = ray_file_props

            spectrum_guid = ""
            if self._ray_file.HasField("spectrum_guid"):
                spectrum_guid = self._ray_file.spectrum_guid
            self._spectrum = Source.Spectrum(
                speos_client=speos_client, name=name, message_to_complete=self._ray_file, spectrum_guid=spectrum_guid
            )
            self._name = name

            if default_values:
                # Default values
                self.set_flux_from_ray_file().set_spectrum_from_ray_file()
                self.set_axis_system()

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
            self._ray_file.ray_file_uri = uri
            return self

        def set_flux_from_ray_file(self) -> Source.RayFile:
            """Take flux from ray file provided.

            Returns
            -------
            ansys.speos.script.source.Source.RayFile
                RayFile source.
            """
            self._ray_file.flux_from_ray_file.SetInParent()
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
            self._ray_file.luminous_flux.luminous_value = value
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
            self._ray_file.radiant_flux.radiant_value = value
            return self

        def set_spectrum_from_ray_file(self) -> Source.RayFile:
            """Take spectrum from ray file provided.

            Returns
            -------
            ansys.speos.script.source.Source.RayFile
                RayFile source.
            """
            self._ray_file.spectrum_from_ray_file.SetInParent()
            self._spectrum._no_spectrum_local = True
            return self

        def set_spectrum(self) -> Spectrum:
            """Set spectrum

            Returns
            -------
            ansys.speos.script.spectrum.Spectrum
                Spectrum.
            """
            if self._ray_file.HasField("spectrum_from_ray_file"):
                guid = ""
                if self._spectrum._spectrum.spectrum_link is not None:
                    guid = self._spectrum._spectrum.spectrum_link.key
                self._ray_file.spectrum_guid = guid
            self._spectrum._no_spectrum_local = False
            return self._spectrum._spectrum

        def set_axis_system(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Source.RayFile:
            """Set position of the source.

            Parameters
            ----------
            axis_system : List[float]
                Position of the source [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
                By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.

            Returns
            -------
            ansys.speos.script.source.Source.RayFile
                RayFile Source.
            """
            self._ray_file_props.axis_system[:] = axis_system
            return self

        def set_exit_geometries(self, exit_geometries: List[GeoRef] = []) -> Source.RayFile:
            """Set exit geometries.

            Parameters
            ----------
            exit_geometries : List[ansys.speos.script.geo_ref.GeoRef]
                Exit Geometries that will use this rayfile source.
                By default, ``[]``.

            Returns
            -------
            ansys.speos.script.source.Source.RayFile
                RayFile Source.
            """
            if exit_geometries == []:
                self._ray_file_props.ClearField("exit_geometries")
            else:
                self._ray_file_props.exit_geometries.geo_paths[:] = [gr.to_native_link() for gr in exit_geometries]

            return self

        def __str__(self) -> str:
            return str(self._spectrum)

        def _commit(self) -> Source.RayFile:
            self._spectrum._commit()
            return self

        def _reset(self) -> Source.RayFile:
            self._spectrum._reset()
            return self

        def _delete(self) -> Source.RayFile:
            self._spectrum._delete()
            return self

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._name = name
        self._unique_id = None
        self.source_template_link = None
        """Link object for the source template in database."""

        # Attribute representing the kind of source. Can be on object of type script.Source.Luminaire, script.Source.RayFile, ...
        self._type = None

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
        if self._type is None and self._source_template.HasField("luminaire"):
            self._type = Source.Luminaire(
                speos_client=self._project.client,
                luminaire=self._source_template.luminaire,
                name=self._source_template.name,
                luminaire_props=self._source_instance.luminaire_properties,
                default_values=False,
            )
        elif type(self._type) != Source.Luminaire:
            self._type = Source.Luminaire(
                speos_client=self._project.client,
                luminaire=self._source_template.luminaire,
                name=self._source_template.name,
                luminaire_props=self._source_instance.luminaire_properties,
            )
        return self._type

    def set_surface(self) -> Surface:
        """Set the source as surface.

        Returns
        -------
        ansys.speos.script.source.Source.Surface
            Surface source.
        """
        if self._type is None and self._source_template.HasField("surface"):
            self._type = Source.Surface(
                speos_client=self._project.client,
                surface=self._source_template.surface,
                name=self._source_template.name,
                surface_props=self._source_instance.surface_properties,
                default_values=False,
            )
        elif type(self._type) != Source.Surface:
            self._type = Source.Surface(
                speos_client=self._project.client,
                surface=self._source_template.surface,
                name=self._source_template.name,
                surface_props=self._source_instance.surface_properties,
            )
        return self._type

    def set_rayfile(self) -> RayFile:
        """Set the source as rayfile.

        Returns
        -------
        ansys.speos.script.source.Source.RayFile
            RayFile source.
        """
        if self._type is None and self._source_template.HasField("rayfile"):
            self._type = Source.RayFile(
                speos_client=self._project.client,
                ray_file=self._source_template.rayfile,
                ray_file_props=self._source_instance.rayfile_properties,
                name=self._source_template.name,
                default_values=False,
            )
        elif type(self._type) != Source.RayFile:
            self._type = Source.RayFile(
                speos_client=self._project.client,
                ray_file=self._source_template.rayfile,
                ray_file_props=self._source_instance.rayfile_properties,
                name=self._source_template.name,
            )
        return self._type

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
            out_str += f"\nlocal: " + core.protobuf_message_to_str(self._source_template)
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
        # This allows to reset managed object contained in _luminaire, _rayfile, etc.. Like Spectrum, IntensityTemplate
        if self._type is not None:
            self._type._reset()

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
        # This allows to clean managed object contained in _luminaire, _rayfile, etc.. Like Spectrum, IntensityTemplate
        if self._type is not None:
            self._type._delete()

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
        self._source_instance.metadata.pop("UniqueId")
        return self
