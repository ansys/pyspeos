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
"""Provides a way to interact with Speos feature: Optical Property."""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Mapping, Optional, Union
import uuid

import ansys.speos.core.body as body
import ansys.speos.core.face as face
from ansys.speos.core.generic.parameters import MaterialOpticParameters
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
import ansys.speos.core.part as part
from ansys.speos.core.project import Project
import ansys.speos.core.proto_message_utils as proto_message_utils


class BaseSop:
    """Base class for Surface Optical Property.

    Notes
    -----
    This is a Super class, **Do not instantiate this class yourself**
    """

    def __init__(self):
        self._sop_template = None
        # Create material instance
        self._material_instance = None

    @property
    def sop_type(self) -> str:
        """Surface Optical Property type.

        Returns
        -------
        str
            SOP type as string.
        """
        if self._material_instance.HasField("texture"):
            return "texture"
        if self._sop_template.HasField("mirror"):
            return "mirror"
        if self._sop_template.HasField("optical_polished"):
            return "optical_polished"
        if self._sop_template.HasField("library"):
            return "library"

    @property
    def sop_reflectance(self) -> float:
        """Perfect specular surface reflectance.

        Parameters
        ----------
        value : float
            Reflectance, expected from 0. to 100. in %.
            By default, ``100``.

        Returns
        -------
        float
            Reflectance value
        """
        if self._sop_template.HasField("mirror"):
            return self._sop_template.mirror.reflectance

    @sop_reflectance.setter
    def sop_reflectance(self, value: float):
        if self._sop_template.HasField("mirror"):
            self._sop_template.mirror.reflectance = value
        else:
            raise TypeError(
                "Surface Optical Property is not set to mirror Type, please use set_mirror_library"
                "before"
            )

    def set_surface_mirror(self) -> BaseSop:
        """
        Define SOP as perfect specular surface.

        Returns
        -------
        ansys.speos.core.opt_prop.BaseSop
            Optical property.
        """
        self._sop_template.mirror.SetInParent()
        self._sop_template.mirror.reflectance = 100
        return self

    def set_surface_opticalpolished(self) -> BaseSop:
        """
        Transparent or perfectly polished material (glass, plastic).

        Returns
        -------
        ansys.speos.core.opt_prop.BaseSop
            Optical property.
        """
        self._sop_template.optical_polished.SetInParent()
        return self

    @property
    def sop_library(self) -> str:
        r"""Based on surface optical properties file.

        Parameters
        ----------
        value : str
            Surface optical properties file, \*.scattering, \*.bsdf, \*.brdf, \*.coated, ...

        Returns
        -------
        str
            File path to file location
        """
        if self._sop_template.HasField("library"):
            return self._sop_template.library.sop_file_uri

    @sop_library.setter
    def sop_library(self, value: Union[Path, str]):
        if self._sop_template.HasField("library"):
            self._sop_template.library.sop_file_uri = str(value)
        else:
            raise TypeError(
                "Surface Optical Property is not set to library Type, please use"
                "set_surface_library before"
            )

    def set_surface_library(self) -> BaseSop:
        """Based on surface optical properties file.

        Returns
        -------
        ansys.speos.core.opt_prop.BaseSop
            Optical property.
        """
        self._sop_template.library.SetInParent()
        return self


class BaseVop:
    """Base class for Surface Optical Property.

    Notes
    -----
    This is a Super class, **Do not instantiate this class yourself**
    """

    def __init__(self):
        self._sop_template = None
        # Create VOP template
        self._vop_template = None
        # Create material instance
        self._material_instance = None

        self._vop_optic = None

    @property
    def vop_type(self):
        """Volume Optical Property Type.

        Returns
        -------
        str
            VOP type as string
        """
        if self._vop_template:
            if self._vop_template.HasField("opaque"):
                return "opaque"
            if self._vop_template.HasField("optic"):
                return "optic"
            if self._vop_template.HasField("library"):
                return "library"

    @property
    def vop_optic(self) -> MaterialOpticParameters:
        """Property of the clear transparent volume.

        Parameters
        ----------
        value : MaterialOpticParameters
            Optic material information

        Returns
        -------
        MaterialOpticParameters
            Dataclass containing optics information
        """
        if self._vop_template.HasField("optic"):
            self._vop_optic = MaterialOpticParameters(
                self._vop_template.optic.index,
                self._vop_template.optic.absorption,
                self._vop_template.optic.constringence,
            )
            return self._vop_optic

    @vop_optic.setter
    def vop_optic(self, value: MaterialOpticParameters):
        if self._vop_template.HasField("optic"):
            self._vop_template.optic.index = value.index
            self._vop_template.optic.absorption = value.absorption
            if value.constringence:
                self._vop_template.optic.constringence = value.constringence
            else:
                self._vop_template.optic.ClearField("constringence")
            self._vop_optic = value
        else:
            raise TypeError(
                "Volume Optical Property is not set to optic Type, please use set_volume_optic"
                "before"
            )

    @property
    def vop_library(self) -> str:
        r"""Volume property based on \*.material file.

        Parameters
        ----------
        value : Union[str, Path]
            location of the \*.material file

        Returns
        -------
        str
            location of the \*.material file
        """
        if self._vop_template.HasField("library"):
            return self._vop_template.library.material_file_uri

    @vop_library.setter
    def vop_library(self, value: Union[Path, str]):
        if self._vop_template.HasField("library"):
            self._vop_template.library.material_file_uri = str(value)
        else:
            raise TypeError(
                "Volume Optical Property is not set to library Type, please use"
                "set_volume_library before"
            )

    def set_volume_none(self) -> OptProp:
        """
        No volume optical property.

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            Optical property.
        """
        self._vop_template = None
        return self

    def set_volume_opaque(self) -> OptProp:
        """
        Non transparent material.

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            Optical property.
        """
        if self._vop_template is None:
            self._vop_template = ProtoVOPTemplate(
                name=self._name + ".VOP",
                description=self._sop_template.description,
                metadata=self._sop_template.metadata,
            )
        self._vop_template.opaque.SetInParent()
        return self

    def set_volume_optic(
        self,
    ) -> OptProp:
        """
        Transparent colorless material without bulk scattering.

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            Optical property.
        """
        if self._vop_template is None:
            self._vop_template = ProtoVOPTemplate(
                name=self._name + ".VOP",
                description=self._sop_template.description,
                metadata=self._sop_template.metadata,
            )
        self._vop_template.optic.SetInParent()
        self._vop_template.optic.index = 1.5
        self._vop_template.optic.absorption = 0
        self._vop_template.optic.ClearField("constringence")
        return self

    # Deactivated due to a bug on SpeosRPC server side
    # def set_volume_nonhomogeneous(
    #         self,
    #         path: str,
    #         axis_system: Optional[List[float]] = None
    # ) -> OptProp:
    #    """
    #    Material with non-homogeneous refractive index.
    #
    #    Parameters
    #    ----------
    #    path : str
    #        \*.gradedmaterial file that describes the spectral variations of
    #        refractive index and absorption with the respect to position in space.
    #    axis_system : Optional[List[float]]
    #        Orientation of the non-homogeneous material [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
    #        By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.
    #
    #    Returns
    #    -------
    #    ansys.speos.core.opt_prop.OptProp
    #        Optical property.
    #    """
    #    if not axis_system:
    #        axis_system = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    #    if self._vop_template is None:
    #        self._vop_template = VOPTemplate(
    #            name=self._name + ".VOP",
    #            description=self._sop_template.description,
    #            metadata=self._sop_template.metadata
    #        )
    #    self._vop_template.non_homogeneous.gradedmaterial_file_uri = path
    #    self._material_instance.non_homogeneous_properties.axis_system[:] = axis_system
    #    return self

    def set_volume_library(self) -> OptProp:
        r"""
        Based on \*.material file.

        Parameters
        ----------
        path : str
            \*.material file

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            Optical property.
        """
        if self._vop_template is None:
            self._vop_template = ProtoVOPTemplate(
                name=self._name + ".VOP",
                description=self._sop_template.description,
                metadata=self._sop_template.metadata,
            )
        self._vop_template.library.SetInParent()
        return self


class TextureLayer(BaseSop):
    """Describes the Optical and texture property of 1 Layer of a combined surface description."""

    def __init__(
        self,
        project: Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        mat_id: str = "",
    ):
        super().__init__()
        self._project = project
        self.sop_template_link = None
        if metadata is None:
            metadata = {}
        self._sop_template = ProtoSOPTemplate(
            name=name + ".SOP", description=description, metadata=metadata
        )
        self._texture_template = ProtoScene.MaterialInstance.Texture.Layer()
        self._normal_map_props = None
        self._image_props = None
        self._aniso_props = None
        self._unique_id = mat_id

    @property
    def sop_type(self) -> str:
        """Surface Optical Property type.

        Returns
        -------
        str
            SOP type as string.
        """
        if self._sop_template.HasField("texture"):
            return "texture"
        if self._sop_template.HasField("mirror"):
            return "mirror"
        if self._sop_template.HasField("optical_polished"):
            return "optical_polished"
        if self._sop_template.HasField("library"):
            return "library"

    @property
    def roughness(self):
        """Roughness parameter of the normal map.

        Parameters
        ----------
        value : float
            Roughness parameter

        Returns
        -------
        float
            Roughness Parameter.
        """
        if self._sop_template.HasField("texture"):
            if self._sop_template.texture.HasField("normal_map"):
                return self._sop_template.texture.normal_map.roughness

    @roughness.setter
    def roughness(self, value: float):
        if self._sop_template.HasField("texture"):
            if self._sop_template.texture.HasField("normal_map"):
                self._sop_template.texture.normal_map.roughness = value
            else:
                raise TypeError("No Normal map defined")
        else:
            raise TypeError("No texture and normal map defined")

    @property
    def image_texture_file_uri(self):
        """File path image texture.

        Parameters
        ----------
        value : Union[Path, str]
            File path image texture.

        Returns
        -------
        str
            File path image texture.
        """
        if self._sop_template.HasField("texture"):
            if self._sop_template.texture.HasField("image"):
                return self._sop_template.texture.image.bitmap_file_uri

    @image_texture_file_uri.setter
    def image_texture_file_uri(self, value: Union[Path, str]):
        self._sop_template.texture.SetInParent()
        self._sop_template.texture.image.SetInParent()
        self._sop_template.texture.image.bitmap_file_uri = str(value)

    @property
    def normal_map_file_uri(self):
        """File path normal map.

        Parameters
        ----------
        value : Union[Path, str]
            File path normal map.

        Returns
        -------
        str
            File path normal map.
        """
        if self._sop_template.HasField("texture"):
            if self._sop_template.texture.HasField("normal_map"):
                if self._sop_template.texture.normal_map.HasField("from_image"):
                    return self._sop_template.texture.normal_map.from_image.bitmap_file_uri
                if self._sop_template.texture.normal_map.HasField("from_normal_map"):
                    return self._sop_template.texture.normal_map.from_normal_map.normal_map_file_uri

    @normal_map_file_uri.setter
    def normal_map_file_uri(self, value: Union[Path, str]):
        if self._sop_template.texture.normal_map.HasField("from_image"):
            self._sop_template.texture.normal_map.from_image.bitmap_file_uri = str(value)
        if self._sop_template.texture.normal_map.HasField("from_normal_map"):
            self._sop_template.texture.normal_map.from_normal_map.normal_map_file_uri = str(value)
        else:
            raise TypeError("Please use set normal_myp type before")

    @property
    def normal_map_property(self) -> Union[TextureMapping, TextureMappingOperator]:
        """Contains all texture mapping properties of the normal Map.

        Parameters
        ----------
        value : Union[TextureMapping, TextureMappingOperator]
            Texture Mapping information

        Returns
        -------
        Union[TextureMapping, TextureMappingOperator]
            Texture mapping properties
        """
        if self._sop_template.texture.HasField("normal_map"):
            if self._texture_template.HasField("normal_map_properties"):
                if self._normal_map_props:
                    return self._normal_map_props
                elif self._texture_template.normal_map_properties.HasField("vertices_data_index"):
                    self._normal_map_props = TextureMapping(
                        self._sop_template, self._texture_template
                    )
                    return self._normal_map_props
                else:
                    self._normal_map_props = TextureMappingOperator(
                        self._sop_template, self._texture_template.normal_map_properties
                    )
                    return self._normal_map_props

    @normal_map_property.setter
    def normal_map_property(self, value: Union[TextureMapping, TextureMappingOperator]):
        if isinstance(value, (TextureMapping, TextureMappingOperator)):
            self._normal_map_props = value
        else:
            raise ValueError("please provide valid data")

    @property
    def image_property(self) -> Union[TextureMapping, TextureMappingOperator]:
        """Contains all texture mapping properties of the Image texture.

        Parameters
        ----------
        value : Union[TextureMapping, TextureMappingOperator]
            Texture Mapping information

        Returns
        -------
        Union[TextureMapping, TextureMappingOperator]
            Texture mapping properties
        """
        if self._sop_template.texture.HasField("image"):
            if self._texture_template.HasField("image_properties"):
                if self._image_props:
                    return self._image_props
                elif self._texture_template.image_properties.HasField("vertices_data_index"):
                    self._image_props = TextureMapping(self._sop_template, self._texture_template)
                    return self._image_props
                else:
                    self._image_props = TextureMappingOperator(
                        self._sop_template, self._texture_template.image_properties
                    )
                    return self._image_props

    @image_property.setter
    def image_property(self, value: Union[TextureMapping, TextureMappingOperator]):
        if isinstance(value, (TextureMapping, TextureMappingOperator)):
            self._image_props = value
        else:
            raise ValueError("please provide valid data")

    @property
    def anisotropic_property(self) -> Union[TextureMapping, TextureMappingOperator]:
        """Contains all texture mapping properties of the anisotorpic orientation.

        Parameters
        ----------
        value : Union[TextureMapping, TextureMappingOperator]
            Texture Mapping information

        Returns
        -------
        Union[TextureMapping, TextureMappingOperator]
            Texture mapping properties
        """
        if self._sop_template.texture.HasField("image"):
            if self._texture_template.HasField("anisotropy_map_properties"):
                if self._aniso_props:
                    return self._aniso_props
                elif self._texture_template.anisotropy_map_properties.HasField(
                    "vertices_data_index"
                ):
                    self._aniso_props = TextureMapping(self._sop_template, self._texture_template)
                    return self._aniso_props
                else:
                    self._aniso_props = TextureMappingOperator(
                        self._sop_template, self._texture_template.anisotropy_map_properties
                    )
                    return self._aniso_props

    @anisotropic_property.setter
    def anisotropic_property(self, value: Union[TextureMapping, TextureMappingOperator]):
        if isinstance(value, (TextureMapping, TextureMappingOperator)):
            self._aniso_props = value
        else:
            raise ValueError("please provide valid data")

    def set_normal_map_from_image(self):
        """Set normal map type to from image."""
        self._sop_template.texture.SetInParent()
        self._sop_template.texture.normal_map.SetInParent()
        self._sop_template.texture.normal_map.from_image.SetInParent()

    def set_normal_map_from_normal_map(self):
        """Set normal map type to from normal map image."""
        self._sop_template.texture.SetInParent()
        self._sop_template.texture.normal_map.SetInParent()
        self._sop_template.texture.normal_map.from_normal_map.SetInParent()

    def commit(self) -> TextureLayer:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            Optical Property feature.
        """
        # The _unique_id will help to find correct item in the scene.materials:
        # the list of MaterialInstance
        if not self._unique_id:
            self._unique_id = str(uuid.uuid4())
            self._material_instance.metadata["UniqueId"] = self._unique_id

        # Save or Update the sop template (depending on if it was already saved before)
        if self.sop_template_link is None:
            if self._sop_template is not None:
                self.sop_template_link = self._project.client.sop_templates().create(
                    message=self._sop_template
                )
                # Always clean sop_guids to be sure that we never use both sop_guids and sop_guid
                self._texture_template.sop_guid = self.sop_template_link.key

        elif self.sop_template_link.get() != self._sop_template:
            self.sop_template_link.set(
                data=self._sop_template
            )  # Only update if sop template has changed
            self._texture_template.sop_guid = self.sop_template_link.key
        return self

    def reset(self) -> TextureLayer:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            OptProp feature.
        """
        # Reset sop template
        if self.sop_template_link is not None:
            self._sop_template = self.sop_template_link.get()
        return self

    def delete(self) -> TextureLayer:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            OptProp feature.
        """
        # Delete the sop template
        if self.sop_template_link is not None:
            self.sop_template_link.delete()
            self.sop_template_link = None

        self._texture_template = None
        # Reset the _unique_id
        self._unique_id = None
        self._texture_template.sop_guid = None
        return self

    def _fill(self, sop_guid: str, texture: ProtoScene.MaterialInstance.Texture.Layer):
        self.sop_template_link = self._project.client[sop_guid]
        self._sop_template = self.sop_template_link.get()
        self._texture_template = texture


class TextureMappingOperator:
    """Mapping operator."""

    def __init__(
        self,
        sop_template,
        mapping_opp: Optional[ProtoScene.MaterialInstance.Texture.MappingOperator] = None,
    ):
        self._mapping = mapping_opp
        if self._mapping is None:
            self._mapping = ProtoScene.MaterialInstance.Texture.MappingOperator()
        self._sop_template = sop_template

    @property
    def repeat_u(self):
        """Repeat image along u axis.

        Parameters
        ----------
        value : bool
            Defines if image get repeated or not

        Returns
        -------
        bool
            true if image is repeated else False
        """
        if self._sop_template.texture.HasField("image"):
            return self._sop_template.texture.image.repeat_along_u
        if self._sop_template.texture.HasField("normal_map"):
            return self._sop_template.texture.normal_map.repeat_along_u

    @repeat_u.setter
    def repeat_u(self, value: bool):
        if self._sop_template.texture.HasField("image"):
            self._sop_template.texture.image.repeat_along_u = value
        if self._sop_template.texture.HasField("normal_map"):
            self._sop_template.texture.normal_map.repeat_along_u = value

    @property
    def repeat_v(self):
        """Repeat image along v axis.

        Parameters
        ----------
        value : bool
            Defines if image get repeated or not

        Returns
        -------
        bool
            true if image is repeate else False
        """
        if self._sop_template.texture.HasField("image"):
            return self._sop_template.texture.image.repeat_along_v
        if self._sop_template.texture.HasField("normal_map"):
            return self._sop_template.texture.normal_map.repeat_along_v

    @repeat_v.setter
    def repeat_v(self, value: bool):
        if self._sop_template.texture.HasField("image"):
            self._sop_template.texture.image.repeat_along_v = value
        if self._sop_template.texture.HasField("normal_map"):
            self._sop_template.texture.normal_map.repeat_along_v = value

    @property
    def type(self) -> str:
        """Mapping type used by this operator."""
        if self._mapping.HasField("planar"):
            return "planar"
        if self._mapping.HasField("cubic"):
            return "cubic"
        if self._mapping.HasField("spherical"):
            return "spherical"
        if self._mapping.HasField("cylindrical"):
            return "cylindrical"

    @property
    def axis_system(self) -> list[float]:
        """Axis system for Texture mapping operator.

        Parameters
        ----------
        axis_system : list[float]
            Position/orientation of the Mapping operator [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].

        Returns
        -------
        list[float]
            Position/orientation of the Mapping operator [Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz].
        """
        return self._mapping.axis_system

    @axis_system.setter
    def axis_system(self, axis_system):
        self._mapping.axis_system[:] = axis_system

    @property
    def u_offset(self) -> float:
        """Shift in u direction.

        Parameters
        ----------
        value : float
            Shift in u direction in mm.

        Returns
        -------
        float
            Shift in u direction in mm.
        """
        return self._mapping.u_offset

    @u_offset.setter
    def u_offset(self, value: float):
        self._mapping.u_offset = value

    @property
    def v_offset(self) -> float:
        """Shift in v direction.

        Parameters
        ----------
        value : float
            Shift in v direction in mm.

        Returns
        -------
        float
            Shift in v direction in mm.
        """
        return self._mapping.v_offset

    @v_offset.setter
    def v_offset(self, value: float):
        self._mapping.v_offset = value

    @property
    def u_scale(self) -> float:
        """Scaling Factor for U direction.

        Parameters
        ----------
        value : float
            Scaling Factor for U direction.

        Returns
        -------
        float
            Scaling Factor for U direction.
        """
        return self._mapping.u_scale_factor

    @u_scale.setter
    def u_scale(self, value: float):
        self._mapping.u_scale_factor = value

    @property
    def v_scale(self) -> float:
        """Scaling Factor for v direction.

        Parameters
        ----------
        value : float
            Scaling Factor for v direction.

        Returns
        -------
        float
            Scaling Factor for v direction.
        """
        return self._mapping.v_scale_factor

    @v_scale.setter
    def v_scale(self, value: float):
        self._mapping.v_scale_factor = value

    @property
    def u_length(self) -> float:
        """Image size in u direction.

        Parameters
        ----------
        value : float
            Image size in u direction in mm.

        Returns
        -------
        float
            Image size in u direction in mm.
        """
        return self._mapping.u_length

    @u_length.setter
    def u_length(self, value: float):
        self._mapping.u_length = value

    @property
    def v_length(self) -> float:
        """Image size in v direction.

        Parameters
        ----------
        value : float
            Image size in v direction in mm.

        Returns
        -------
        float
            Image size in v direction in mm.
        """
        if self._mapping.HasField("v_length"):
            return self._mapping.v_length

    @v_length.setter
    def v_length(self, value: float):
        self._mapping.v_length = value

    @property
    def rotation(self):
        """Define image rotation of uv.

        Parameters
        ----------
        value : float
            Rotation value between -360 and 360 in degree

        Returns
        -------
        float
            Image rotation of uv
        """
        return self._mapping.rotation

    @rotation.setter
    def rotation(self, value):
        self._mapping.rotation = value

    def set_type_planar(self):
        """Define Mapping operation with a planar projection."""
        self._mapping.planar.SetInParent()

    def set_type_cubic(self):
        """Define Mapping operation with a planar projection."""
        self._mapping.cubic.SetInParent()

    def set_type_spherical(self, sphere_perimeter: float):
        """Define Mapping operation with a planar projection."""
        self._mapping.spherical.SetInParent()
        self._mapping.spherical.sphere_perimeter = sphere_perimeter

    def set_type_cylindrical(self, base_perimeter: float):
        """Define Mapping operation with a planar projection."""
        self._mapping.cylindrical.SetInParent()
        self._mapping.cylindrical.base_perimeter = base_perimeter


class TextureMapping:
    """Mapping operator."""

    def __init__(self, sop_template, texture_template):
        self._sop_template = sop_template
        self._texture_template = texture_template

    @property
    def repeat_u(self):
        """Repeat image along u axis.

        Parameters
        ----------
        value : bool
            Defines if image get repeated or not

        Returns
        -------
        bool
            true if image is repeated else False
        """
        if self._sop_template.texture.HasField("image"):
            return self._sop_template.texture.image.repeat_along_u
        if self._sop_template.texture.HasField("normal_map"):
            return self._sop_template.texture.normal_map.repeat_along_u

    @repeat_u.setter
    def repeat_u(self, value: bool):
        if self._sop_template.texture.HasField("image"):
            self._sop_template.texture.image.repeat_along_u = value
        if self._sop_template.texture.HasField("normal_map"):
            self._sop_template.texture.normal_map.repeat_along_u = value

    @property
    def repeat_v(self):
        """Repeat image along v axis.

        Parameters
        ----------
        value : bool
            Defines if image get repeated or not

        Returns
        -------
        bool
            true if image is repeated else False
        """
        if self._sop_template.texture.HasField("image"):
            return self._sop_template.texture.image.repeat_along_v
        if self._sop_template.texture.HasField("normal_map"):
            return self._sop_template.texture.normal_map.repeat_along_v

    @repeat_v.setter
    def repeat_v(self, value: bool):
        if self._sop_template.texture.HasField("image"):
            self._sop_template.texture.image.repeat_along_v = value
        if self._sop_template.texture.HasField("normal_map"):
            self._sop_template.texture.normal_map.repeat_along_v = value

    @property
    def vertices_data_index(self):
        """Index in face's vertices_data where UV mapping is stored.

        Parameters
        ----------
        value : int
            Index in face's vertices_data where UV mapping is stored

        Returns
        -------
        int
            Index in face's vertices_data where UV mapping is stored
        """
        if self._texture_template.HasField("image_properties"):
            return self._texture_template.image_properties.vertices_data_index
        if self._texture_template.HasField("normal_map_properties"):
            return self._texture_template.normal_map_properties.vertices_data_index
        if self._texture_template.HasField("anisotropy_map_properties"):
            return self._texture_template.anisotropy_map_properties.vertices_data_index

    @vertices_data_index.setter
    def vertices_data_index(self, value: int):
        if self._texture_template.HasField("image_properties"):
            self._texture_template.image_properties.vertices_data_index = value
        if self._texture_template.HasField("normal_map_properties"):
            self._texture_template.normal_map_properties.vertices_data_index = value
        if self._texture_template.HasField("anisotropy_map_properties"):
            self._texture_template.anisotropy_map_properties.vertices_data_index = value


class OptProp(BaseSop, BaseVop):
    """Speos feature: optical property.

    By default, a mirror 100% is chosen as surface optical property,
    without any volume optical property.
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
    metadata : Optional[Mapping[str, str]], optional
        Metadata of the feature.
        By default, ``None``.
    """

    def __init__(
        self,
        project: Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
    ):
        super(BaseSop).__init__()
        super(BaseVop).__init__()
        self._name = name
        self._project = project
        self._unique_id = None
        self.sop_template_link = None
        """Link object for the sop template in database."""
        self.vop_template_link = None
        """Link object for the vop template in database."""

        # Create SOP template
        if metadata is None:
            metadata = {}
        self._sop_template = ProtoSOPTemplate(
            name=name + ".SOP", description=description, metadata=metadata
        )

        # Create VOP template
        self._vop_template = None

        # Create material instance
        self._material_instance = ProtoScene.MaterialInstance(
            name=name, description=description, metadata=metadata
        )
        self._texture = None
        # Default values
        self.set_surface_mirror()
        self.set_volume_none()
        self.geometries = None

    @property
    def texture(self) -> list[TextureLayer]:
        """All texture Layers used in this Material."""
        return self._texture

    @texture.setter
    def texture(self, value: list[TextureLayer]):
        for layer in value:
            if not isinstance(layer, TextureLayer):
                raise ValueError("not a texture")
        self._texture = value

    @property
    def geometries(
        self,
    ) -> List[str]:
        """Select geometries on which the optical properties will be applied.

        Parameters
        ----------
        geometries : List[str],
            List of geometries. Giving an empty list means "All geometries"
            ``None``, means "no geometry".

        Returns
        -------
        List[str]
            List of geometry references used by this material
        """
        return self._material_instance.geometries.geo_paths

    @geometries.setter
    def geometries(
        self,
        geometries: Optional[List[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]],
    ) -> None:
        if geometries is None:
            self._material_instance.ClearField("geometries")
        else:
            geo_paths = []
            for gr in geometries:
                if isinstance(gr, GeoRef):
                    geo_paths.append(gr)
                elif isinstance(gr, (face.Face, body.Body, part.Part.SubPart)):
                    geo_paths.append(gr.geo_path)
                else:
                    msg = f"Type {type(gr)} is not supported as Optical property geometry input."
                    raise TypeError(msg)
            self._material_instance.geometries.geo_paths[:] = [
                gp.to_native_link() for gp in geo_paths
            ]

    def _to_dict(self) -> dict:
        out_dict = {}

        # MaterialInstance (= vop guid + sop guids + geometries)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            mat_inst = next(
                (x for x in scene_data.materials if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if mat_inst is not None:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client, message=mat_inst
                )
            else:
                out_dict = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self._material_instance,
                )
        else:
            out_dict = proto_message_utils._replace_guids(
                speos_client=self._project.client,
                message=self._material_instance,
            )

        if "vop" not in out_dict.keys():
            # SensorTemplate
            if self.vop_template_link is None:
                if self._vop_template is not None:
                    out_dict["vop"] = proto_message_utils._replace_guids(
                        speos_client=self._project.client,
                        message=self._vop_template,
                    )
            else:
                out_dict["vop"] = proto_message_utils._replace_guids(
                    speos_client=self._project.client,
                    message=self.vop_template_link.get(),
                )

        if "sops" not in out_dict.keys():
            # SensorTemplate
            if self.sop_template_link is None:
                if self._sop_template is not None:
                    out_dict["sops"] = [
                        proto_message_utils._replace_guids(
                            speos_client=self._project.client,
                            message=self._sop_template,
                        )
                    ]
            else:
                out_dict["sops"] = [
                    proto_message_utils._replace_guids(
                        speos_client=self._project.client,
                        message=self.sop_template_link.get(),
                    )
                ]

        proto_message_utils._replace_properties(json_dict=out_dict)

        return out_dict

    def get(self, key: str = "") -> str | dict:
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

    def __str__(self):
        """Return the string representation of the optical property."""
        out_str = ""
        # MaterialInstance (= vop guid + sop guids + geometries)
        if self._project.scene_link and self._unique_id is not None:
            scene_data = self._project.scene_link.get()
            mat_inst = next(
                (x for x in scene_data.materials if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if mat_inst is None:
                out_str += "local: "
        else:
            out_str += "local: "

        out_str += proto_message_utils.dict_to_str(dict=self._to_dict())
        return out_str

    def commit(self) -> OptProp:
        """Save feature: send the local data to the speos server database.

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            Optical Property feature.
        """
        # The _unique_id will help to find correct item in the scene.materials:
        # the list of MaterialInstance
        if self._unique_id is None:
            self._unique_id = str(uuid.uuid4())
            self._material_instance.metadata["UniqueId"] = self._unique_id

        # Save or Update the vop template (depending on if it was already saved before)
        if self.vop_template_link is None:
            if self._vop_template is not None:
                self.vop_template_link = self._project.client.vop_templates().create(
                    message=self._vop_template
                )
                self._material_instance.vop_guid = self.vop_template_link.key
        elif self.vop_template_link.get() != self._vop_template:
            self.vop_template_link.set(
                data=self._vop_template
            )  # Only update if vop template has changed

        # Save or Update the sop template (depending on if it was already saved before)
        if self.sop_template_link is None:
            if self._sop_template is not None:
                self.sop_template_link = self._project.client.sop_templates().create(
                    message=self._sop_template
                )
                # Always clean sop_guids to be sure that we never use both sop_guids and sop_guid
                self._material_instance.ClearField("sop_guids")
                # Fill sop_guid(s) field according to the server capability regarding textures
                if self._project.client.scenes()._is_texture_available:
                    if self.texture:
                        self._material_instance.texture.ClearField("layers")
                        layers = []
                        for layer in self.texture:
                            layers.append(layer._texture_template)
                        self._material_instance.texture.layers[:] = layers
                    else:
                        self._material_instance.sop_guid = self.sop_template_link.key
                else:
                    self._material_instance.sop_guids.append(self.sop_template_link.key)
        elif self.sop_template_link.get() != self._sop_template:
            self.sop_template_link.set(
                data=self._sop_template
            )  # Only update if sop template has changed

        # Update the scene with the material instance
        if self._project.scene_link:
            update_scene = True
            scene_data = self._project.scene_link.get()  # retrieve scene data

            # Look if an element corresponds to the _unique_id
            mat_inst = next(
                (x for x in scene_data.materials if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if mat_inst is not None:
                if mat_inst != self._material_instance:
                    mat_inst.CopyFrom(self._material_instance)  # if yes, just replace
                else:
                    update_scene = False
            else:
                scene_data.materials.append(
                    self._material_instance
                )  # if no, just add it to the list of material instances

            if update_scene:  # Update scene only if instance has changed
                self._project.scene_link.set(data=scene_data)  # update scene data

        return self

    def reset(self) -> OptProp:
        """Reset feature: override local data by the one from the speos server database.

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
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
            mat_inst = next(
                (x for x in scene_data.materials if x.metadata["UniqueId"] == self._unique_id),
                None,
            )
            if mat_inst is not None:
                self._material_instance = mat_inst
        return self

    def delete(self) -> OptProp:
        """Delete feature: delete data from the speos server database.

        The local data are still available

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
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

        # Reset then the sop_guid/sop_guids fields (as the sop template was deleted just above)
        self._material_instance.ClearField("sop_guid")
        self._material_instance.ClearField("sop_guids")

        # Remove the material instance from the scene
        scene_data = self._project.scene_link.get()  # retrieve scene data
        mat_inst = next(
            (x for x in scene_data.materials if x.metadata["UniqueId"] == self._unique_id),
            None,
        )
        if mat_inst is not None:
            scene_data.materials.remove(mat_inst)
            self._project.scene_link.set(data=scene_data)  # update scene data

        # Reset the _unique_id
        self._unique_id = None
        self._material_instance.metadata.pop("UniqueId")
        return self

    def _fill(self, mat_inst: ProtoScene.MaterialInstance):
        self._unique_id = mat_inst.metadata["UniqueId"]
        self._material_instance = mat_inst
        self.vop_template_link = self._project.client[mat_inst.vop_guid]
        if mat_inst.HasField("sop_guid"):
            self.sop_template_link = self._project.client[mat_inst.sop_guid]
        elif mat_inst.HasField("texture"):
            texture = []
            for layer in mat_inst.texture.layers:
                cur_layer = TextureLayer(self._project, name="", mat_id=self._unique_id)
                cur_layer._fill(layer.sop_guid, layer)
                texture.append(cur_layer)
        elif len(mat_inst.sop_guids) > 0:
            self.sop_template_link = self._project.client[mat_inst.sop_guids[0]]
        else:  # Specific case for ambient material
            self._sop_template = None
        self.reset()
