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
from __future__ import annotations

from typing import List, Mapping, Optional
import uuid

import ansys.speos.core as core
from ansys.speos.script.geo_ref import GeoRef
import ansys.speos.script.project as project
from ansys.speos.script.spectrum import Spectrum


class Source:
    class Luminaire:
        def __init__(self, project: project.Project, source_template: core.SourceTemplate, name: str) -> None:
            self._project = project
            self._source_template = source_template
            self._spectrum = Spectrum(speos_client=self._project.client, name=name + ".Spectrum", source_template=self._source_template)

            # Default values
            self.set_flux_from_intensity_file().set_spectrum().set_incandescent()

        def set_flux_from_intensity_file(self) -> Source.Luminaire:
            self._source_template.luminaire.flux_from_intensity_file.SetInParent()
            return self

        def set_flux_luminous(self, value: float = 683) -> Source.Luminaire:
            self._source_template.luminaire.luminous_flux.luminous_value = value
            return self

        def set_flux_radiant(self, value: float = 1) -> Source.Luminaire:
            self._source_template.luminaire.radiant_flux.radiant_value = value
            return self

        def set_intensity_file_uri(self, uri: str) -> Source.Luminaire:
            self._source_template.luminaire.intensity_file_uri = uri
            return self

        def set_spectrum(self) -> Spectrum:
            return self._spectrum

        def __str__(self) -> str:
            return str(self._spectrum)

        def _commit(self) -> Source.Luminaire:
            self._spectrum.commit()
            return self

    class RayFile:
        def __init__(self, project: project.Project, source_template: core.SourceTemplate, name: str) -> None:
            self._project = project
            self._source_template = source_template
            self._spectrum = None

            # Default values
            self.set_flux_from_ray_file().set_spectrum_from_ray_file()

        def set_ray_file_uri(self, uri: str) -> Source.RayFile:
            self._source_template.rayfile.ray_file_uri = uri
            return self

        def set_flux_from_ray_file(self) -> Source.RayFile:
            self._source_template.rayfile.flux_from_ray_file.SetInParent()
            return self

        def set_flux_luminous(self, value: float = 683) -> Source.RayFile:
            self._source_template.rayfile.luminous_flux.luminous_value = value
            return self

        def set_flux_radiant(self, value: float = 1) -> Source.RayFile:
            self._source_template.rayfile.radiant_flux.radiant_value = value
            return self

        def set_spectrum_from_ray_file(self) -> Source.RayFile:
            self._source_template.rayfile.spectrum_from_ray_file.SetInParent()
            self._spectrum = None
            return self

        def set_spectrum(self) -> Spectrum:
            self._spectrum = Spectrum(
                speos_client=self._project.client, name=self._source_template.name + ".Spectrum", source_template=self._source_template
            )
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
            return self

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}) -> None:
        self._project = project
        self._unique_id = None
        self.source_template_link = None

        self._type = (
            None  # Attribute representing the kind of source. Can be on object of type script.Source.Luminaire, script.Source.RayFile, ...
        )

        # Create SourceTemplate
        self._source_template = core.SourceTemplate(name=name, description=description, metadata=metadata)

        # Create SourceInstance
        self._source_instance = core.Scene.SourceInstance(name=name, description=description, metadata=metadata)

    def set_luminaire(self) -> Luminaire:
        if type(self._type) != Source.Luminaire:
            self._type = Source.Luminaire(project=self._project, source_template=self._source_template, name=self._source_template.name)

        return self._type

    def set_rayfile(self) -> RayFile:
        if type(self._type) != Source.RayFile:
            self._type = Source.RayFile(project=self._project, source_template=self._source_template, name=self._source_template.name)

        return self._type

    def set_luminaire_properties(self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> Source:
        self._source_instance.luminaire_properties.axis_system[:] = axis_system
        return self

    def set_rayfile_properties(
        self, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1], exit_geometries: Optional[List[GeoRef]] = None
    ) -> Source:
        self._source_instance.rayfile_properties.axis_system[:] = axis_system
        if exit_geometries is not None:
            self._source_instance.rayfile_properties.exit_geometries.geo_paths[:] = [gr.to_native_link() for gr in exit_geometries]
        return self

    def __str__(self) -> str:
        out_str = ""
        # SourceInstance (= source guid + source properties)
        if self._project.scene and self._unique_id is not None:
            scene_data = self._project.scene.get()
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
        """Save feature"""
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
        if self._project.scene:
            scene_data = self._project.scene.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            src_inst = next((x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id), None)
            if src_inst is not None:
                src_inst.CopyFrom(self._source_instance)  # if yes, just replace
            else:
                scene_data.sources.append(self._source_instance)  # if no, just add it to the list of sources

            self._project.scene.set(data=scene_data)  # update scene data

        return self

    def delete(self) -> Source:
        # Delete the source template
        if self.source_template_link is not None:
            self.source_template_link.delete()
            self.source_template_link = None

        # Reset then the source_guid (as the source template was deleted just above)
        self._source_instance.source_guid = ""

        # Remove the source from the scene
        scene_data = self._project.scene.get()  # retrieve scene data
        src_inst = next((x for x in scene_data.sources if x.metadata["UniqueId"] == self._unique_id), None)
        if src_inst is not None:
            scene_data.sources.remove(src_inst)
            self._project.scene.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        return self
