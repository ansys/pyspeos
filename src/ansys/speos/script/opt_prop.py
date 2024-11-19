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
"""Provides a way to interact with Speos feature: Optical Property."""
from __future__ import annotations

from typing import List, Mapping, Optional
import uuid

import ansys.speos.core as core
from ansys.speos.script.geo_ref import GeoRef
import ansys.speos.script.project as project


class OptProp:
    """Speos feature: optical property
    By default, a mirror 100% is chosen as surface optical property, without any volume optical property.
    By default, the optical property is applied to no geometry.

    Parameters
    ----------
    project : project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str, optional
        Description of the feature.
        By default, ``""``.
    metadata : Mapping[str, str], optional
        Metadata of the feature.
        By default, ``None``.
    """

    def __init__(self, project: project.Project, name: str, description: str = "", metadata: Mapping[str, str] = {}):
        self._name = name
        self._project = project
        self._unique_id = None
        self.sop_template_link = None
        """Link object for the sop template in database."""
        self.vop_template_link = None
        """Link object for the vop template in database."""
        # Create SOP template
        self._sop_template = core.SOPTemplate(name=name + ".SOP", description=description, metadata=metadata)

        # Create VOP template
        self._vop_template = None

        # Create material instance
        self._material_instance = core.Scene.MaterialInstance(name=name, description=description, metadata=metadata)

        # Default values
        self.set_surface_mirror().set_volume_none().set_geometries()

    def set_surface_mirror(self, reflectance: float = 100) -> OptProp:
        """
        Perfect specular surface.

        Parameters
        ----------
        reflectance : float
            Reflectance, expected from 0. to 100. in %.
            By default, ``100``.

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
            Optical property.
        """
        self._sop_template.mirror.reflectance = reflectance
        return self

    def set_surface_opticalpolished(self) -> OptProp:
        """
        Transparent or perfectly polished material (glass, plastic).

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
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
        ansys.speos.script.opt_prop.OptProp
            Optical property.
        """
        self._sop_template.library.sop_file_uri = path
        return self

    def set_volume_none(self) -> OptProp:
        """
        No volume optical property.

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
            Optical property.
        """
        self._vop_template = None
        return self

    def set_volume_opaque(self) -> OptProp:
        """
        Non transparent material.

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
            Optical property.
        """
        if self._vop_template is None:
            self._vop_template = core.VOPTemplate(
                name=self._name + ".VOP", description=self._sop_template.description, metadata=self._sop_template.metadata
            )
        self._vop_template.opaque.SetInParent()
        return self

    def set_volume_optic(self, index: float = 1.5, absorption: float = 0, constringence: Optional[float] = None) -> OptProp:
        """
        Transparent colorless material without bulk scattering.

        Parameters
        ----------
        index : float
            Refractive index.
            By default, ``1.5``.
        absorption : float
            Absorption coefficient value. mm-1.
            By default, ``0``.
        constringence : float, optional
            Abbe number.
            By default, ``None``, means no constringence.

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
            Optical property.
        """
        if self._vop_template is None:
            self._vop_template = core.VOPTemplate(
                name=self._name + ".VOP", description=self._sop_template.description, metadata=self._sop_template.metadata
            )
        self._vop_template.optic.index = index
        self._vop_template.optic.absorption = absorption
        if constringence is not None:
            self._vop_template.optic.constringence = constringence
        else:
            self._vop_template.optic.ClearField("constringence")
        return self

    # Deactivated due to a bug on SpeosRPC server side
    # def set_volume_nonhomogeneous(self, path: str, axis_system: List[float] = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]) -> OptProp:
    #    """
    #    Material with non-homogeneous refractive index.
    #
    #    Parameters
    #    ----------
    #    path : str
    #        \*.gradedmaterial file that describes the spectral variations of
    #        refractive index and absorption with the respect to position in space.
    #    axis_system : List[float]
    #        Orientation of the non-homogeneous material [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
    #        By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.
    #
    #    Returns
    #    -------
    #    ansys.speos.script.opt_prop.OptProp
    #        Optical property.
    #    """
    #    if self._vop_template is None:
    #        self._vop_template = core.VOPTemplate(name=self._name + ".VOP", description=self._sop_template.description,
    #                                              metadata=self._sop_template.metadata)
    #    self._vop_template.non_homogeneous.gradedmaterial_file_uri = path
    #    self._material_instance.non_homogeneous_properties.axis_system[:] = axis_system
    #    return self

    def set_volume_library(self, path: str) -> OptProp:
        """
        Based on \*.material file.

        Parameters
        ----------
        path : str
            \*.material file

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
            Optical property.
        """
        if self._vop_template is None:
            self._vop_template = core.VOPTemplate(
                name=self._name + ".VOP", description=self._sop_template.description, metadata=self._sop_template.metadata
            )
        self._vop_template.library.material_file_uri = path
        return self

    def set_geometries(self, geometries: Optional[List[GeoRef]] = None) -> OptProp:
        """Select geometries on which the optical properties will be applied.

        Parameters
        ----------
        geometries : List[ansys.speos.script.geo_ref.GeoRef], optional
            List of geometries. Giving an empty list means "All geometries"
            By default, ``None``, means "no geometry".

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
            Optical property.
        """
        if geometries == None:
            self._material_instance.ClearField("geometries")
        else:
            self._material_instance.geometries.geo_paths[:] = [gr.to_native_link() for gr in geometries]
        return self

    def __str__(self):
        """Return the string representation of the optical property."""
        out_str = ""
        # MaterialInstance (= vop guid + sop guids + geometries)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            mat_inst = next((x for x in scene_data.materials if x.metadata["UniqueId"] == self._unique_id), None)
            if mat_inst is not None:
                out_str += core.protobuf_message_to_str(mat_inst)
            else:
                out_str += f"local: " + core.protobuf_message_to_str(self._material_instance)
        else:
            out_str += f"local: " + core.protobuf_message_to_str(self._material_instance)

        # VOPTemplate
        if self.vop_template_link is None:
            if self._vop_template is not None:
                out_str += f"\nlocal: " + core.protobuf_message_to_str(self._vop_template)
        else:
            out_str += "\n" + str(self.vop_template_link)

        # SOPTemplate
        if self.sop_template_link is None:
            out_str += f"\nlocal: " + core.protobuf_message_to_str(self._sop_template)
        else:
            out_str += "\n" + str(self.sop_template_link)

        return out_str

    def commit(self) -> OptProp:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
            Optical Property feature.
        """
        # The _unique_id will help to find correct item in the scene.materials (the list of MaterialInstance)
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._material_instance.metadata["UniqueId"] = self._unique_id

        # Save or Update the vop template (depending on if it was already saved before)
        if self.vop_template_link is None:
            if self._vop_template is not None:
                self.vop_template_link = self._project.client.vop_templates().create(message=self._vop_template)
                self._material_instance.vop_guid = self.vop_template_link.key
        elif self.vop_template_link.get() != self._vop_template:
            self.vop_template_link.set(data=self._vop_template)  # Only update if vop template has changed

        # Save or Update the sop template (depending on if it was already saved before)
        if self.sop_template_link is None:
            if self._sop_template is not None:
                self.sop_template_link = self._project.client.sop_templates().create(message=self._sop_template)
                self._material_instance.ClearField("sop_guids")
                self._material_instance.sop_guids.append(self.sop_template_link.key)
        elif self.sop_template_link.get() != self._sop_template:
            self.sop_template_link.set(data=self._sop_template)  # Only update if sop template has changed

        # Update the scene with the material instance
        if self._project.scene_link:
            update_scene = True
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            mat_inst = next((x for x in scene_data.materials if x.metadata["UniqueId"] == self._unique_id), None)
            if mat_inst is not None:
                if mat_inst != self._material_instance:
                    mat_inst.CopyFrom(self._material_instance)  # if yes, just replace
                else:
                    update_scene = False
            else:
                scene_data.materials.append(self._material_instance)  # if no, just add it to the list of material instances

            if update_scene:  # Update scene only if instance has changed
                self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def reset(self) -> OptProp:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
            OptProp feature.
        """
        # Reset vop template
        if self.vop_template_link is not None:
            self._vop_template = self.vop_template_link.get()

        # Reset sop template
        if self.sop_template_link is not None:
            self._sop_template = self.sop_template_link.get()

        # Reset material instance
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()  # retrieve scene data
            # Look if an element corresponds to the _unique_id
            mat_inst = next((x for x in scene_data.materials if x.metadata["UniqueId"] == self._unique_id), None)
            if mat_inst is not None:
                self._material_instance = mat_inst
        return self

    def delete(self) -> OptProp:
        """Delete feature: delete data from the speos server database.
        The local data are still available

        Returns
        -------
        ansys.speos.script.opt_prop.OptProp
            OptProp feature.
        """
        # Delete the vop template
        if self.vop_template_link is not None:
            self.vop_template_link.delete()
            self.vop_template_link = None

        # Reset then the vop_guid (as the vop template was deleted just above)
        self._material_instance.vop_guid = ""

        # Delete the sop template
        if self.sop_template_link is not None:
            self.sop_template_link.delete()
            self.sop_template_link = None

        # Reset then the sop_guids (as the sop template was deleted just above)
        self._material_instance.ClearField("sop_guids")

        # Remove the material instance from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data
        mat_inst = next((x for x in scene_data.materials if x.metadata["UniqueId"] == self._unique_id), None)
        if mat_inst is not None:
            scene_data.materials.remove(mat_inst)
            self._project.scene_link.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        self._material_instance.metadata.pop("UniqueId")
        return self
