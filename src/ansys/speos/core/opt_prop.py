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
"""Utilities to interact with Speos optical property features.

This module exposes classes to create and manage Surface Optical Properties (SOP)
and Volume Optical Properties (VOP) and to compose material instances that can
be committed to a Speos project scene.

The public classes are:
- `BaseSop` for inheritance of SOP helpers,
- `BaseVop` for inheritance of VOP helpers,
- `TextureLayer` for a single texture layer,
- `OptProp` to represent a full material instance (SOP + VOP + geometries).
"""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Mapping, Optional, Union
import uuid

import ansys.speos.core.body as body
import ansys.speos.core.face as face
from ansys.speos.core.generic.general_methods import min_speos_version
from ansys.speos.core.generic.parameters import (
    MappingByData,
    MappingOperator,
    MappingTypes,
    MaterialOpticParameters,
    OptPropParameters,
    SopParameters,
    SopTypes,
    TextureLayerParameters,
    VopParameters,
    VopTypes,
)
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
import ansys.speos.core.part as part
import ansys.speos.core.project as p
import ansys.speos.core.proto_message_utils as proto_message_utils


class BaseSop:
    """Base class for Surface Optical Property helpers.

    Parameters
    ----------
    sop_parameters : Optional[SopParameters], optional
        Default SOP parameters to initialize the surface optical property. Default is ``None``.

    Notes
    -----
    This is a superclass and is not intended to be instantiated directly.
    """

    def __init__(self, sop_template, mat_inst, sop_parameters: Optional[SopParameters] = None):

        self._sop_template = sop_template
        # Create material instance
        self._material_instance = mat_inst

        if sop_parameters:
            self._apply_sop_parameters(sop_parameters)

    def _apply_sop_parameters(self, sop_parameters: SopParameters):
        """Apply SOP parameters to initialize the surface optical property.

        Parameters
        ----------
        sop_parameters : SopParameters
            SOP parameters to apply.
        """
        if sop_parameters.sop_type == SopTypes.mirror:
            self.set_surface_mirror()
            if sop_parameters.sop_reflectance is not None:
                self.sop_reflectance = sop_parameters.sop_reflectance
        elif sop_parameters.sop_type == SopTypes.optical_polished:
            self.set_surface_opticalpolished()
        elif sop_parameters.sop_type == SopTypes.library:
            self.set_surface_library()
            if sop_parameters.sop_library_file_uri:
                self.sop_library = sop_parameters.sop_library_file_uri

    @property
    def sop_type(self) -> str:
        """Surface optical property type.

        Returns
        -------
        str
            SOP type as string. Possible values include ``'texture'``,
            ``'mirror'``, ``'optical_polished'``, and ``'library'``.
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

        Returns
        -------
        float
            Reflectance value (0.0 to 100.0). Only valid when SOP is a mirror.
        """
        if self._sop_template.HasField("mirror"):
            return self._sop_template.mirror.reflectance

    @sop_reflectance.setter
    def sop_reflectance(self, value: float):
        """Set the mirror reflectance.

        Parameters
        ----------
        value : float
            Reflectance value to set (0.0 to 100.0).

        Raises
        ------
        TypeError
            If the current SOP is not of mirror type.
        """
        if self._sop_template.HasField("mirror"):
            self._sop_template.mirror.reflectance = value
        else:
            raise TypeError(
                "Surface Optical Property is not set to mirror Type, please use set_mirror_library"
                "before"
            )

    def set_surface_mirror(self) -> BaseSop:
        """Define SOP as a perfect specular surface.

        Returns
        -------
        ansys.speos.core.opt_prop.BaseSop
            Returns self for chaining.
        """
        self._sop_template.mirror.SetInParent()
        self._sop_template.mirror.reflectance = 100
        return self

    def set_surface_opticalpolished(self) -> BaseSop:
        """Set SOP to transparent or perfectly polished surface (e.g. glass).

        Returns
        -------
        ansys.speos.core.opt_prop.BaseSop
            Returns self for chaining.
        """
        self._sop_template.optical_polished.SetInParent()
        return self

    @property
    def sop_library(self) -> str:
        """Surface property file URI when SOP is a library entry.

        Returns
        -------
        str
            File path or URI of the SOP file (e.g. ``*.scattering``, ``*.bsdf``).
        """
        if self._sop_template.HasField("library"):
            return self._sop_template.library.sop_file_uri

    @sop_library.setter
    def sop_library(self, value: Union[Path, str]):
        """Set the SOP library file URI.

        Parameters
        ----------
        value : Union[str, Path]
            File path or URI to the surface optical properties file.

        Raises
        ------
        TypeError
            If the current SOP is not of library type.
        """
        if self._sop_template.HasField("library"):
            self._sop_template.library.sop_file_uri = str(value)
        else:
            raise TypeError(
                "Surface Optical Property is not set to library Type, please use"
                "set_surface_library before"
            )

    def set_surface_library(self) -> BaseSop:
        """Configure SOP to use a library file.

        Returns
        -------
        ansys.speos.core.opt_prop.BaseSop
            Returns self for chaining.
        """
        self._sop_template.library.SetInParent()
        return self


class BaseVop:
    """Base class for Volume Optical Property helpers.

    Parameters
    ----------
    vop_parameters : Optional[VopParameters], optional
        Default VOP parameters to initialize the volume optical property. Default is ``None``.

    Notes
    -----
    This is a superclass and is not intended to be instantiated directly.
    """

    class VopOptic:
        """Optic parameters for a clear transparent volume."""

        def __init__(self, parent, default_parameters: MaterialOpticParameters):
            self._parent = parent
            if default_parameters:
                self.index = default_parameters.index
                self.absorption = default_parameters.absorption
                self.constringence = default_parameters.constringence

        @property
        def index(self) -> float:
            """Real part of refractive index."""
            if self._parent._vop_template and self._parent._vop_template.HasField("optic"):
                return self._parent._vop_template.optic.index
            raise AttributeError("VOP is not of optic type")

        @index.setter
        def index(self, value: float):
            self._parent._vop_template.optic.index = value

        @property
        def absorption(self) -> float:
            """Absorption coefficient."""
            if self._parent._vop_template and self._parent._vop_template.HasField("optic"):
                return self._parent._vop_template.optic.absorption
            raise AttributeError("VOP is not of optic type")

        @absorption.setter
        def absorption(self, value: float):
            self._parent._vop_template.optic.absorption = value

        @property
        def constringence(self) -> Optional[float]:
            """Abbe Number."""
            if self._parent._vop_template and self._parent._vop_template.HasField("optic"):
                if self._parent._vop_template.optic.HasField("constringence"):
                    return self._parent._vop_template.optic.constringence
                return None
            raise AttributeError("VOP is not of optic type")

        @constringence.setter
        def constringence(self, value: Optional[float]):
            if value is not None:
                self._parent._vop_template.optic.constringence = value
            else:
                self._parent._vop_template.optic.ClearField("constringence")

    def __init__(self, vop_template, mat_inst, vop_parameters: Optional[VopParameters] = None):
        # Create VOP template
        self._vop_template = vop_template
        # Create material instance
        self._material_instance = mat_inst

        self._vop_optic = None

        if vop_parameters:
            self._apply_vop_parameters(vop_parameters)

    def _apply_vop_parameters(self, vop_parameters: VopParameters):
        """Apply VOP parameters to initialize the volume optical property.

        Parameters
        ----------
        vop_parameters : VopParameters
            VOP parameters to apply.
        """
        if vop_parameters.vop_type == VopTypes.optic:
            self.set_volume_optic()
        elif vop_parameters.vop_type == VopTypes.opaque:
            self.set_volume_opaque()
        elif vop_parameters.vop_type == VopTypes.library:
            self.set_volume_library()
            if vop_parameters.vop_library_file_uri:
                self.vop_library = vop_parameters.vop_library_file_uri

    @property
    def vop_type(self) -> Optional[str]:
        """Volume optical property type.

        Returns
        -------
        Optional[str]
            VOP type as a string. Possible values include ``'opaque'``,
            ``'optic'``, and ``'library'``. Returns ``None`` if no VOP template
            is present.
        """
        if self._vop_template:
            if self._vop_template.HasField("opaque"):
                return "opaque"
            if self._vop_template.HasField("optic"):
                return "optic"
            if self._vop_template.HasField("library"):
                return "library"

    @property
    def vop_optic(self) -> Optional[BaseVop.VopOptic]:
        """Optic parameters for a clear transparent volume.

        Returns
        -------
        Optional[VopOptic]
            VopOptic instance containing optics information (index, absorption,
            constringence) when VOP is of optic type, otherwise ``None``.
        """
        if self._vop_template.HasField("optic"):
            return self._vop_optic

    @property
    def vop_library(self) -> str:
        """Volume library file URI for VOP when using a material library.

        Returns
        -------
        str
            File path or URI of the volume material file (``*.material``).
        """
        if self._vop_template.HasField("library"):
            return self._vop_template.library.material_file_uri

    @vop_library.setter
    def vop_library(self, value: Union[Path, str]):
        """Set the VOP library material file URI.

        Parameters
        ----------
        value : Union[str, Path]
            File path or URI to the volume material file.

        Raises
        ------
        TypeError
            If the current VOP is not of library type.
        """
        if self._vop_template.HasField("library"):
            self._vop_template.library.material_file_uri = str(value)
        else:
            raise TypeError(
                "Volume Optical Property is not set to library Type, please use"
                "set_volume_library before"
            )

    def set_volume_none(self) -> "OptProp":
        """Remove any VOP template (no volume optical property).

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            Returns self (as the OptProp that owns this VOP helper).
        """
        self._vop_template = None
        return self

    def set_volume_opaque(self) -> "OptProp":
        """Set VOP to non-transparent (opaque) material.

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            Returns self (as the OptProp that owns this VOP helper).
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
    ) -> BaseVop.VopOptic:
        """Set VOP to a transparent, non-scattering optic.

        Returns
        -------
        ansys.speos.core.opt_prop.BaseVop.VopOptic
            Returns VOP Helper.
        """
        if self._vop_template is None:
            self._vop_template = ProtoVOPTemplate(
                name=self._name + ".VOP",
                description=self._sop_template.description,
                metadata=self._sop_template.metadata,
            )
            self._vop_optic = self.VopOptic(self, MaterialOpticParameters())
        elif self._vop_template.HasField("optic"):
            self._vop_optic = self.VopOptic(self, None)
        else:
            self._vop_template.optic.SetInParent()
            self._vop_optic = self.VopOptic(self, MaterialOpticParameters())
        return self._vop_optic

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
            Returns self (as the OptProp that owns this VOP helper).
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
    """Describes the optical and texture properties of a single texture layer.

    Parameters
    ----------
    opt_prop : ansys.speos.core.opt_prop.OptProp
        Optical Property which will hold this Layer
    name : str
        Name of the feature.
    description : str, optional
        Description of the feature. Default is an empty string.
    metadata : Optional[Mapping[str, str]], optional
        Metadata of the feature. Default is ``None``.
    texture_layer_parameters : Optional[TextureLayerParameters], optional
        Default texture layer parameters to initialize the texture layer. Default is ``None``.
    """

    @min_speos_version(25, 2, 0)
    def __init__(
        self,
        opt_prop: "OptProp",
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        default_parameters: Optional[TextureLayerParameters] = None,
    ):

        self._project = opt_prop._project
        self._opt_prop = opt_prop
        self.sop_template_link = None
        if metadata is None:
            metadata = {}
        self._sop_template = ProtoSOPTemplate(
            name=name + ".SOP", description=description, metadata=metadata
        )
        self._material_instance = opt_prop._material_instance
        self._material_instance.texture.SetInParent()
        self._texture_template = ProtoScene.MaterialInstance.Texture.Layer()
        self._normal_map_props = None
        self._image_props = None
        self._aniso_props = None

        self._index = None

        if default_parameters:
            super().__init__(
                self._sop_template, self._material_instance, default_parameters.sop_parameters
            )
            self._apply_texture_layer_parameters(default_parameters)
        else:
            super().__init__(self._sop_template, self._material_instance, SopParameters())

    def _apply_texture_layer_parameters(self, texture_layer_parameters: TextureLayerParameters):
        """Apply texture layer parameters to initialize the texture layer.

        Parameters
        ----------
        texture_layer_parameters : TextureLayerParameters
            Texture layer parameters to apply.
        """
        if texture_layer_parameters.image_texture:
            if texture_layer_parameters.image_texture_file_uri:
                self.image_texture_file_uri = texture_layer_parameters.image_texture_file_uri
            if texture_layer_parameters.image_texture_mapping:
                self.image_property = texture_layer_parameters.image_texture_mapping
        if texture_layer_parameters.normal_map:
            if texture_layer_parameters.normal_map_type == "from_image":
                self.set_normal_map_from_image()
            elif texture_layer_parameters.normal_map_type == "from_normal_map":
                self.set_normal_map_from_normal_map()
            if texture_layer_parameters.normal_map_file_uri:
                self.normal_map_file_uri = texture_layer_parameters.normal_map_file_uri
            if texture_layer_parameters.normal_map_mapping:
                self.normal_map_property = texture_layer_parameters.normal_map_mapping
        if texture_layer_parameters.anisotropy_map:
            if texture_layer_parameters.anisotropy_map_mapping:
                self.normal_map_property = texture_layer_parameters.normal_map_mapping

    @property
    def sop_type(self) -> str:
        """Surface optical property type for this texture layer.

        Returns
        -------
        str
            SOP type as string. Possible values: ``'mirror'``, ``'optical_polished'``,
            ``'library'``.
        """
        if self._sop_template.HasField("mirror"):
            return "mirror"
        if self._sop_template.HasField("optical_polished"):
            return "optical_polished"
        if self._sop_template.HasField("library"):
            return "library"

    @property
    def roughness(self) -> Optional[float]:
        """Roughness parameter of the normal map.

        Returns
        -------
        Optional[float]
            Roughness value when a normal map exists, otherwise ``None``.
        """
        if self._sop_template.HasField("texture"):
            if self._sop_template.texture.HasField("normal_map"):
                return self._sop_template.texture.normal_map.roughness

    @roughness.setter
    def roughness(self, value: float):
        """Set the roughness for the normal map.

        Parameters
        ----------
        value : float
            Roughness parameter to set.

        Raises
        ------
        TypeError
            If no normal map is defined.
        """
        if self._sop_template.HasField("texture"):
            if self._sop_template.texture.HasField("normal_map"):
                self._sop_template.texture.normal_map.roughness = value
            else:
                raise TypeError("No Normal map defined")
        else:
            raise TypeError("No texture and normal map defined")

    @property
    def image_texture_file_uri(self) -> Optional[str]:
        """URI of the image texture bitmap.

        Returns
        -------
        Optional[str]
            File path or URI of the image texture bitmap when defined, otherwise
            ``None``.
        """
        if self._sop_template.HasField("texture"):
            if self._sop_template.texture.HasField("image"):
                return self._sop_template.texture.image.bitmap_file_uri

    @image_texture_file_uri.setter
    def image_texture_file_uri(self, value: Union[Path, str]):
        """Set the image texture file URI.

        Parameters
        ----------
        value : Union[str, Path]
            File path or URI to the image texture bitmap.
        """
        if self._sop_template.HasField("texture"):
            if self._sop_template.texture.HasField("image"):
                self._sop_template.texture.image.bitmap_file_uri = str(value)
            else:
                self._sop_template.texture.image.SetInParent()
                self._sop_template.texture.image.bitmap_file_uri = str(value)
        else:
            self._sop_template.texture.SetInParent()
            self._sop_template.texture.image.SetInParent()
            self._sop_template.texture.image.bitmap_file_uri = str(value)

    @property
    def normal_map_file_uri(self) -> Optional[str]:
        """URI for the normal map source.

        Returns
        -------
        Optional[str]
            File path or URI of the normal map source (image or normal_map),
            or ``None`` when not defined.
        """
        if self._sop_template.HasField("texture"):
            if self._sop_template.texture.HasField("normal_map"):
                if self._sop_template.texture.normal_map.HasField("from_image"):
                    return self._sop_template.texture.normal_map.from_image.bitmap_file_uri
                if self._sop_template.texture.normal_map.HasField("from_normal_map"):
                    return self._sop_template.texture.normal_map.from_normal_map.normal_map_file_uri

    @normal_map_file_uri.setter
    def normal_map_file_uri(self, value: Union[Path, str]):
        """Set the normal map file URI.

        Parameters
        ----------
        value : Union[str, Path]
            File path or URI of the normal map.

        Raises
        ------
        TypeError
            If the normal map source type has not been set.
        """
        if self._sop_template.texture.normal_map.HasField("from_image"):
            self._sop_template.texture.normal_map.from_image.bitmap_file_uri = str(value)
        elif self._sop_template.texture.normal_map.HasField("from_normal_map"):
            self._sop_template.texture.normal_map.from_normal_map.normal_map_file_uri = str(value)
        else:
            raise TypeError("Please use set normal_map type before")

    @property
    def normal_map_property(self) -> Optional[Union[MappingByData, MappingOperator]]:
        """Texture mapping properties for the normal map.

        Returns
        -------
        Optional[Union[MappingByData, MappingOperator]]
            Mapping properties (either ``MappingByData`` or ``MappingOperator``)
            when defined, otherwise ``None``.
        """
        if self._sop_template.texture.HasField("normal_map"):
            if self._texture_template.HasField("normal_map_properties"):
                if self._normal_map_props:
                    return self._normal_map_props
                elif self._texture_template.normal_map_properties.HasField("vertices_data_index"):
                    self._normal_map_props = MappingByData(
                        repeat_u=self._sop_template.texture.image.repeat_along_u,
                        repeat_v=self._sop_template.texture.image.repeat_along_v,
                        vertices_data_index=self._texture_template.normal_map_properties.vertices_data_index,
                    )
                    return self._normal_map_props
                else:
                    cur_mapping_opp = self._texture_template.normal_map_properties.mapping_operator
                    perimeter = 1
                    for mapping_type in MappingTypes:
                        if cur_mapping_opp.HasField(mapping_type):
                            cur_type = mapping_type
                            if cur_type == MappingTypes.cylindrical:
                                perimeter = cur_mapping_opp.cylindrical.base_perimeter
                            elif cur_type == MappingTypes.spherical:
                                perimeter = cur_mapping_opp.spherical.sphere_perimeter
                    self._normal_map_props = MappingOperator(
                        mapping_type=cur_type,
                        repeat_u=self._sop_template.texture.normal_map.repeat_along_u,
                        repeat_v=self._sop_template.texture.normal_map.repeat_along_v,
                        u_length=cur_mapping_opp.u_length,
                        v_length=cur_mapping_opp.v_length
                        if cur_mapping_opp.HasField("v_length")
                        else None,
                        axis_system=cur_mapping_opp.axis_system,
                        u_scale=cur_mapping_opp.u_scale_factor,
                        v_scale=cur_mapping_opp.v_scale_factor,
                        rotation=cur_mapping_opp.rotation,
                        perimeter=perimeter,
                    )
                    return self._normal_map_props

    @normal_map_property.setter
    def normal_map_property(self, value: Union[MappingByData, MappingOperator]):
        """Set normal map mapping properties.

        Parameters
        ----------
        value : Union[MappingByData, MappingOperator]
            Mapping information to apply.

        Raises
        ------
        ValueError
            If the provided value is not a valid mapping object.
        """
        if isinstance(value, MappingOperator):
            self._normal_map_props = value
            mapping_op = self._texture_template.normal_map_properties.mapping_operator
            self._sop_template.texture.image.repeat_along_u = value.repeat_u
            self._sop_template.texture.image.repeat_along_v = value.repeat_v
            match value.mapping_type:
                case MappingTypes.planar:
                    mapping_op.planar.SetInParent()
                case MappingTypes.cubic:
                    mapping_op.cubic.SetInParent()
                case MappingTypes.spherical:
                    mapping_op.spherical.SetInParent()
                    mapping_op.spherical.sphere_perimeter = value.perimeter
                case MappingTypes.cylindrical:
                    mapping_op.cylindrical.SetInParent()
                    mapping_op.cylindrical.base_perimeter = value.perimeter
            mapping_op.u_length = value.u_length
            if value.v_length:
                mapping_op.v_length = value.v_length
            mapping_op.ClearField("axis_system")
            mapping_op.axis_system[:] = value.axis_system
            mapping_op.rotation = value.rotation
            mapping_op.u_scale_factor = value.u_scale
            mapping_op.v_scale_factor = value.v_scale
        elif isinstance(value, MappingByData):
            self._normal_map_props = value
            self._sop_template.texture.image.repeat_along_u = value.repeat_u
            self._sop_template.texture.image.repeat_along_v = value.repeat_v
            self._texture_template.normal_map_properties.vertices_data_index = (
                value.vertices_data_index
            )
        else:
            raise ValueError("please provide valid data")

    @property
    def image_property(self) -> Optional[Union[MappingByData, MappingOperator]]:
        """Texture mapping properties for the image texture.

        Returns
        -------
        Optional[Union[MappingByData, MappingOperator]]
            Mapping properties when defined, otherwise ``None``.
        """
        if self._sop_template.texture.HasField("image"):
            if self._texture_template.HasField("image_properties"):
                if self._image_props:
                    return self._image_props
                elif self._texture_template.image_properties.HasField("vertices_data_index"):
                    self._image_props = MappingByData(
                        repeat_u=self._sop_template.texture.image.repeat_along_u,
                        repeat_v=self._sop_template.texture.image.repeat_along_v,
                        vertices_data_index=self._texture_template.image_properties.vertices_data_index,
                    )
                    return self._image_props
                else:
                    cur_mapping_opp = self._texture_template.image_properties.mapping_operator
                    perimeter = 1
                    for mapping_type in MappingTypes:
                        if cur_mapping_opp.HasField(mapping_type):
                            cur_type = mapping_type
                            if cur_type == MappingTypes.cylindrical:
                                perimeter = cur_mapping_opp.cylindrical.base_perimeter
                            elif cur_type == MappingTypes.spherical:
                                perimeter = cur_mapping_opp.spherical.sphere_perimeter
                    self._image_props = MappingOperator(
                        mapping_type=cur_type,
                        repeat_u=self._sop_template.texture.image.repeat_along_u,
                        repeat_v=self._sop_template.texture.image.repeat_along_v,
                        u_length=cur_mapping_opp.u_length,
                        v_length=cur_mapping_opp.v_length
                        if cur_mapping_opp.HasField("v_length")
                        else None,
                        axis_system=cur_mapping_opp.axis_system,
                        u_scale=cur_mapping_opp.u_scale_factor,
                        v_scale=cur_mapping_opp.v_scale_factor,
                        rotation=cur_mapping_opp.rotation,
                        perimeter=perimeter,
                    )
                    return self._image_props

    @image_property.setter
    def image_property(self, value: Union[MappingByData, MappingOperator]):
        """Set image texture mapping properties.

        Parameters
        ----------
        value : Union[MappingByData, MappingOperator]
            Mapping information to apply.

        Raises
        ------
        ValueError
            If the provided value is not a valid mapping object.
        """
        if isinstance(value, MappingOperator):
            self._image_props = value
            mapping_op = self._texture_template.image_properties.mapping_operator
            self._sop_template.texture.image.repeat_along_u = value.repeat_u
            self._sop_template.texture.image.repeat_along_v = value.repeat_v
            match value.mapping_type:
                case MappingTypes.planar:
                    mapping_op.planar.SetInParent()
                case MappingTypes.cubic:
                    mapping_op.cubic.SetInParent()
                case MappingTypes.spherical:
                    mapping_op.spherical.SetInParent()
                    mapping_op.spherical.sphere_perimeter = value.perimeter
                case MappingTypes.cylindrical:
                    mapping_op.cylindrical.SetInParent()
                    mapping_op.cylindrical.base_perimeter = value.perimeter
            mapping_op.u_length = value.u_length
            if value.v_length:
                mapping_op.v_length = value.v_length
            mapping_op.ClearField("axis_system")
            mapping_op.axis_system[:] = value.axis_system
            mapping_op.rotation = value.rotation
            mapping_op.u_scale_factor = value.u_scale
            mapping_op.v_scale_factor = value.v_scale
        elif isinstance(value, MappingByData):
            self._image_props = value
            self._sop_template.texture.image.repeat_along_u = value.repeat_u
            self._sop_template.texture.image.repeat_along_v = value.repeat_v
            self._texture_template.image_properties.vertices_data_index = value.vertices_data_index
        else:
            raise ValueError("please provide valid data")

    @property
    def anisotropic_property(self) -> Optional[Union[MappingByData, MappingOperator]]:
        """Anisotropy map mapping properties.

        Returns
        -------
        Optional[Union[MappingByData, MappingOperator]]
            Mapping properties when defined, otherwise ``None``.
        """
        if self._texture_template.HasField("anisotropy_map_properties"):
            if self._aniso_props:
                return self._aniso_props
            elif self._texture_template.anisotropy_map_properties.HasField("vertices_data_index"):
                self._aniso_props = MappingByData(
                    vertices_data_index=self._texture_template.anisotropy_map_properties.vertices_data_index,
                )
                return self._aniso_props
            else:
                cur_mapping_opp = self._texture_template.anisotropy_map_properties.mapping_operator
                perimeter = 1
                for mapping_type in MappingTypes:
                    if cur_mapping_opp.HasField(mapping_type):
                        cur_type = mapping_type
                        if cur_type == MappingTypes.cylindrical:
                            perimeter = cur_mapping_opp.cylindrical.base_perimeter
                        elif cur_type == MappingTypes.spherical:
                            perimeter = cur_mapping_opp.spherical.sphere_perimeter
                self._aniso_props = MappingOperator(
                    mapping_type=cur_type,
                    u_length=1,
                    axis_system=cur_mapping_opp.axis_system,
                    rotation=cur_mapping_opp.rotation,
                    perimeter=perimeter,
                )
                return self._aniso_props

    @anisotropic_property.setter
    def anisotropic_property(self, value: Union[MappingByData, MappingOperator]):
        """Set anisotropy map mapping properties.

        Parameters
        ----------
        value : Union[MappingByData, MappingOperator]
            Mapping information to apply.

        Raises
        ------
        ValueError
            If the provided value is not a valid mapping object.
        """
        if isinstance(value, MappingOperator):
            self._aniso_props = value
            mapping_op = self._texture_template.anisotropy_map_properties.mapping_operator
            match value.mapping_type:
                case MappingTypes.planar:
                    mapping_op.planar.SetInParent()
                case MappingTypes.cubic:
                    mapping_op.cubic.SetInParent()
                case MappingTypes.spherical:
                    mapping_op.spherical.SetInParent()
                    mapping_op.spherical.sphere_perimeter = value.perimeter
                case MappingTypes.cylindrical:
                    mapping_op.cylindrical.SetInParent()
                    mapping_op.cylindrical.base_perimeter = value.perimeter
            mapping_op.ClearField("axis_system")
            mapping_op.axis_system[:] = value.axis_system
            mapping_op.rotation = value.rotation
        elif isinstance(value, MappingByData):
            self._aniso_props = value
            self._texture_template.image_properties.vertices_data_index = value.vertices_data_index
        else:
            raise ValueError("please provide valid data")

    def set_normal_map_from_image(self):
        """Configure the normal map to be sourced from an image."""
        self._sop_template.texture.SetInParent()
        self._sop_template.texture.normal_map.SetInParent()
        self._sop_template.texture.normal_map.from_image.SetInParent()

    def set_normal_map_from_normal_map(self):
        """Configure the normal map to be sourced from a normal map file."""
        self._sop_template.texture.SetInParent()
        self._sop_template.texture.normal_map.SetInParent()
        self._sop_template.texture.normal_map.from_normal_map.SetInParent()

    def commit(self) -> "TextureLayer":
        """Save or update the SOP template on the Speos server.

        Returns
        -------
        ansys.speos.core.opt_prop.TextureLayer
            Returns self after committing.
        """
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
        return self

    def reset(self) -> "TextureLayer":
        """Reset local texture layer data from server-side data.

        Returns
        -------
        ansys.speos.core.opt_prop.TextureLayer
            Returns self after resetting.
        """
        # Reset sop template
        if self.sop_template_link is not None:
            self._sop_template = self.sop_template_link.get()
            self._normal_map_props = None
            self._aniso_props = None
            self._image_props = None
        if self._project.scene_link is not None:
            scene_data = self._project.scene_link.get()
            mat_inst = next(
                (
                    x
                    for x in scene_data.materials
                    if x.metadata["UniqueId"] == self._material_instance.metadata["UniqueId"]
                ),
                None,
            )
            if mat_inst is not None:
                self._material_instance = mat_inst
                self._texture_template = mat_inst.texture.layers[self._index]

    def delete(self) -> "TextureLayer":
        """Delete the SOP template layer from the server and update local state.

        Returns
        -------
        ansys.speos.core.opt_prop.TextureLayer
            Returns self after deletion.
        """
        # Delete the sop template
        if self.sop_template_link is not None:
            self.sop_template_link.delete()
            self.sop_template_link = None
        self._texture_template.ClearField("sop_guid")
        layers = self._material_instance.texture.layers
        layers.pop(self._index)
        self._opt_prop.texture.pop(self._index)
        self._opt_prop.commit()
        self._material_instance.texture.ClearField("layers")
        self._material_instance.texture.layers.extend(layers)
        self._texture_template = None
        # Reset the _unique_id
        self._unique_id = None
        return self

    def _fill(self, sop_guid: str, texture: ProtoScene.MaterialInstance.Texture.Layer):
        """Populate OptProp from a server-side with server-side data.

        Parameters
        ----------
        sop_guid : str
            SOP template GUID.
        texture : ProtoScene.MaterialInstance.Texture.Layer
            The texture layer protobuf message.
        """
        self.sop_template_link = self._project.client[sop_guid]
        self._sop_template = self.sop_template_link.get()
        self._texture_template = texture


class OptProp(BaseVop, BaseSop):
    """Speos feature wrapper for an optical property (SOP + VOP + geometries).

    By default, an OptProp is a 100% mirror surface with no volume optical
    property and no geometries assigned.

    Parameters
    ----------
    project : ansys.speos.core.project.Project
        Project that will own the feature.
    name : str
        Name of the feature.
    description : str, optional
        Description of the feature. Default is an empty string.
    metadata : Optional[Mapping[str, str]], optional
        Metadata of the feature. Default is ``None``.
    default_parameters : Optional[OptPropParameters], optional
        Default optical property parameters to initialize the OptProp. Default is ``None``.
    """

    def __init__(
        self,
        project: p.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        default_parameters: Optional[OptPropParameters] = None,
    ):
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

        BaseVop.__init__(
            self,
            self._vop_template,
            self._material_instance,
            vop_parameters=default_parameters.vop_parameters if default_parameters else None,
        )
        BaseSop.__init__(
            self,
            self._sop_template,
            self._material_instance,
            sop_parameters=default_parameters.sop_parameters if default_parameters else None,
        )

        # Default values
        self.geometries = None

        if default_parameters and default_parameters.texture_parameters:
            self.texture = [
                TextureLayer(self, f"Layer{i}", texture_layer_parameters=layer)
                for i, layer in enumerate(default_parameters.texture_parameters)
            ]

    @property
    def texture(self) -> Optional[list["TextureLayer"]]:
        """List of texture layers used in this material.

        Returns
        -------
        Optional[list[TextureLayer]]
            Texture layers or ``None`` when not set.
        """
        return self._texture

    @texture.setter
    def texture(self, value: list["TextureLayer"]):
        """Set the texture layers.

        Parameters
        ----------
        value : list[TextureLayer]
            List of TextureLayer objects to assign.

        Raises
        ------
        ValueError
            If any element in ``value`` is not a TextureLayer instance.
        """
        for layer in value:
            if not isinstance(layer, TextureLayer):
                raise ValueError("not a texture")
        self._texture = value

    @property
    def geometries(
        self,
    ) -> List[str]:
        """Geometries to which this material is applied.

        An empty list means "all geometries"; ``None`` means "no geometry".

        Returns
        -------
        List[str]
            List of geometry references used by this material.
        """
        return self._material_instance.geometries.geo_paths

    @geometries.setter
    def geometries(
        self,
        geometries: Optional[List[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]],
    ) -> None:
        """Assign geometries to the material instance.

        Parameters
        ----------
        geometries : Optional[list[Union[GeoRef, body.Body, face.Face, part.Part.SubPart]]]
            Geometry references, GeoRef instances, Body instances, Face instances,
            or SubPart instances. Pass ``None`` to clear geometries.
        """
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
        """Return a JSON-serializable dict representing the material instance.

        Returns
        -------
        dict
            Dictionary representation of the material instance and templates,
            with GUIDs replaced for client use.
        """
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
        """Get a value or the whole dictionary representation.

        Parameters
        ----------
        key : str, optional
            If provided, tries to find a JSON key that starts with ``key`` and
            returns the best match. Default is empty string.

        Returns
        -------
        str or dict
            If ``key`` is empty, returns the full dict representation. If a match
            for ``key`` is found, returns the corresponding value. Otherwise,
            prints available keys and returns ``None`` implicitly.
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
        """Return the string representation of the optical property.

        Returns
        -------
        str
            Readable string representation of the material instance.
        """
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

    def commit(self) -> "OptProp":
        """Commit the material instance and templates to the server scene.

        Returns
        -------
        OptProp
            Returns self after committing.
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
        if self.texture:
            self._material_instance.texture.ClearField("layers")
            layers = []
            for i, layer in enumerate(self.texture):
                layers.append(layer._texture_template)
                layer._index = i
            self._material_instance.texture.layers.extend(layers)
        else:
            if self.sop_template_link is None:
                if self._sop_template is not None:
                    # Always clean sop_guids to be sure that we never use both sop_guids and
                    # sop_guid
                    self._material_instance.ClearField("sop_guids")
                    # Fill sop_guid(s) field according to the server capability regarding textures
                    if self._project.client.scenes()._is_texture_available:
                        self.sop_template_link = self._project.client.sop_templates().create(
                            message=self._sop_template
                        )
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

    def reset(self) -> "OptProp":
        """Reset local templates and material instance from the server.

        Returns
        -------
        OptProp
            Returns self after resetting.
        """
        # Reset vop template
        if self.vop_template_link is not None:
            self._vop_template = self.vop_template_link.get()
            if self._vop_template.HasField("optic"):
                self.set_volume_optic()

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

    def delete(self) -> "OptProp":
        """Delete templates and remove the material instance from the scene.

        Returns
        -------
        ansys.speos.core.opt_prop.OptProp
            Returns self after deletion and cleanup.
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
        """Populate OptProp from a server-side material instance.

        Parameters
        ----------
        mat_inst : ProtoScene.MaterialInstance
            MaterialInstance protobuf message retrieved from the server.
        """
        self._unique_id = mat_inst.metadata["UniqueId"]
        self._material_instance = mat_inst
        self.vop_template_link = self._project.client[mat_inst.vop_guid]
        if mat_inst.HasField("sop_guid"):
            self.sop_template_link = self._project.client[mat_inst.sop_guid]
        elif mat_inst.HasField("texture"):
            texture = []
            for i, layer in enumerate(mat_inst.texture.layers):
                cur_layer = TextureLayer(self, name=f"{self._name}.Layer.{i}")
                cur_layer._fill(layer.sop_guid, layer)
                cur_layer._index = i
                texture.append(cur_layer)
            self.texture = texture
        elif len(mat_inst.sop_guids) > 0:
            self.sop_template_link = self._project.client[mat_inst.sop_guids[0]]
        else:  # Specific case for ambient material
            self._sop_template = None
        self.reset()
