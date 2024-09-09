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


class OptProp:
    """
    Represent a Speos optical properties

    Parameters
    ----------
    project : project.Project
        Project that will own the optical property.
    name : str
        Name of the optical property.
    description : str, optional
        Description of the optical property.
        By default, ``""``.
    metadata : Mapping[str, str], optional
        Metadata of the sop template.
        By default, ``None``.
    """

    def __init__(self, project: project.Project, name: str, description: Optional[str] = "", metadata: Optional[Mapping[str, str]] = None):
        self._project = project
        self._unique_id = None
        # Create SOP template
        self._sop_template = core.SOPTemplate(
            name=name, description=description if description else "", metadata=metadata if metadata else {}
        )

        # Create VOP template
        self._vop_template = core.VOPTemplate(
            name=name, description=description if description else "", metadata=metadata if metadata else {}
        )

        # Create material instance
        self._material_instance = core.Scene.MaterialInstance(
            name=name, description=description if description else "", metadata=metadata if metadata else {}
        )

    def set_surface_mirror(self, reflectance: float) -> OptProp:
        """
        Perfect specular surface.

        Parameters
        ----------
        reflectance : float
            Reflectance, expected from 0. to 100. in %.

        Returns
        -------
        OptProp
            Optical property.
        """
        self._sop_template.mirror.reflectance = reflectance
        return self

    def set_surface_opticalpolished(self) -> OptProp:
        """
        Transparent or perfectly polished material (glass, plastic).

        Returns
        -------
        OptProp
            Optical property.
        """
        self._sop_template.optical_polished.SetInParent()
        return self

    def set_surface_library(self, path: str) -> OptProp:
        """
        Based on surface optical properties file.

        Parameters
        ----------
        path : str
            Surface optical properties file, \*.scattering, \*.bsdf, \*.brdf, \*.coated, ...

        Returns
        -------
        OptProp
            Optical property.
        """
        self._sop_template.library.sop_file_uri = path
        return self

    def set_volume_opaque(self) -> OptProp:
        """
        Non transparent material.

        Returns
        -------
        OptProp
            Optical property.
        """
        self._vop_template.opaque.SetInParent()
        return self

    def set_volume_optic(self, index: float, absorption: float, constringence: Optional[float]) -> OptProp:
        """
        Transparent colorless material without bulk scattering.

        Parameters
        ----------
        index : float
            Refractive index.
        absorption : float
            Absorption coefficient value. mm-1
        constringence : float, optional
            Abbe number.
            None means no constringence.

        Returns
        -------
        OptProp
            Optical property.
        """
        self._vop_template.optic.index = index
        self._vop_template.optic.absorption = absorption
        if constringence is not None:
            self._vop_template.optic.constringence = constringence
        else:
            del self._vop_template.optic.constringence
        return self

    def set_volume_nonhomogeneous(self, path: str, coordsys: GeoRef) -> OptProp:
        """
        Material with non-homogeneous refractive index.

        Parameters
        ----------
        path : str
            \*.gradedmaterial file that describes the spectral variations of
            refractive index and absorption with the respect to position in space.
        coordsys : GeoRef

        Returns
        -------
        OptProp
            Optical property.
        """
        self._vop_template.non_homogeneous.gradedmaterial_file_uri = path
        return self

    def set_volume_library(self, path: str) -> OptProp:
        """
        Based on \*.material file.

        Parameters
        ----------
        path : str
            \*.material file

        Returns
        -------
        OptProp
            Optical property.
        """
        self._vop_template.library.material_file_uri = path
        return self

    def set_geometries(self, geometries: List[GeoRef]) -> OptProp:
        """Takes all geometries if nothing provided"""
        self._material_instance.geometries.geo_paths[:] = [gr.to_native_link() for gr in geometries]
        return self

    def __str__(self):
        return (
            f"SOP template: {self._sop_template}\n"
            + f"VOP template: {self._vop_template}\n"
            + f"Material instance: {self._material_instance}"
        )

    def commit(self) -> OptProp:
        """Save feature"""
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._vop_template.metadata["UniqueId"] = self._unique_id
            self._vop_template_link = self._project.client.vop_templates().create(message=self._vop_template)
            self._sop_template.metadata["UniqueId"] = self._unique_id
            self._sop_template_link = self._project.client.sop_templates().create(message=self._sop_template)
            self._material_instance.metadata["UniqueId"] = self._unique_id
            self._material_instance.vop_guid = self._vop_template_link.key
            self._material_instance.sop_guids.append(self._sop_template_link.key)
            if self._project.scene:
                scene_data = self._project.scene.get()  # retrieve scene data
                scene_data.materials.append(self._material_instance)
                self._project.scene.set(data=scene_data)
        else:
            self._vop_template_link.set(data=self._vop_template)
            self._sop_template_link.set(data=self._sop_template)
            if self._project.scene:
                scene_data = self._project.scene.get()  # retrieve scene
                mat_inst = next((x for x in scene_data.materials if x.metadata["UniqueId"] == self._unique_id), None)
                if mat_inst:
                    mat_inst = self._material_instance
                self._project.scene.set(data=scene_data)
        return self
