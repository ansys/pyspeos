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
    ImageTextureParameter,
    MappingByData,
    MappingCylindricalParameters,
    MappingOperator,
    MappingSphericalParameters,
    MappingTypes,
    NormalMapParameter,
    NormalMapTypes,
    OptPropParameters,
    SopLibraryParameters,
    SopMirrorParameters,
    SopTypes,
    TextureLayerParameters,
    TextureTypes,
    VopLibraryParameters,
    VopOpticParameters,
    VopTypes,
)
from ansys.speos.core.geo_ref import GeoRef
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
import ansys.speos.core.part as part
import ansys.speos.core.project as project
import ansys.speos.core.proto_message_utils as proto_message_utils


class BaseSop:
    """Base class for Surface Optical Property helpers.

    Notes
    -----
    This is a superclass and is not intended to be instantiated directly.
    """

    def __init__(
        self,
        sop_template: ProtoSOPTemplate,
        mat_inst: ProtoScene.MaterialInstance,
        sop_parameters: Optional[
            Union[SopMirrorParameters, SopLibraryParameters, SopTypes.optical_polished],
        ] = None,
        stable_ctr=False,
    ):
        """Initialize the SOP helper state.

        Parameters
        ----------
        sop_template : ansys.speos.core.kernel.sop_template.ProtoSOPTemplate
            Surface optical property template to wrap.
        mat_inst : ansys.speos.core.kernel.scene.ProtoScene.MaterialInstance
            Material instance that owns the SOP settings.
        sop_parameters : Optional[Union[\
        ansys.speos.core.generic.parameters.SopLibraryParameters, \
        ansys.speos.core.generic.parameters.SopMirrorParameters, \
        ansys.speos.core.generic.parameters.SopTypes.optical_polished, \
        ]], optional
            Default SOP parameters to apply at initialization.
        """
        if not stable_ctr:
            raise RuntimeError(
                "BaseSop is not intended to be instantiated directly."
                "Please use a subclass or set stable_ctr=True if you know what you're doing."
            )
        self._sop_template = sop_template
        # Create material instance
        self._material_instance = mat_inst
        self._mirror = None
        self._library = None

        if sop_parameters:
            self._fill_parameters_sop(sop_parameters)

    def _sync_sop_properties(self):
        """Synchronize cached SOP helper objects with the current SOP template."""
        if self._sop_template is None:
            self._mirror = None
            self._library = None
            return

        self._mirror = (
            self.SopMirror(self, stable_ctr=True) if self._sop_template.HasField("mirror") else None
        )
        self._library = (
            self.SopLibrary(self, stable_ctr=True)
            if self._sop_template.HasField("library")
            else None
        )

    def _fill_parameters_sop(
        self, sop_parameters: Optional[Union[SopMirrorParameters, SopLibraryParameters, SopTypes]]
    ):
        """Apply SOP parameters to initialize the surface optical property.

        Parameters
        ----------
        sop_parameters : ansys.speos.core.generic.parameters.SopParameters
            SOP parameters to apply.
        """
        if isinstance(sop_parameters, SopMirrorParameters):
            self.set_surface_mirror()
            self.sop_mirror.reflectance = sop_parameters.reflectance
        elif sop_parameters == SopTypes.optical_polished:
            self.set_surface_opticalpolished()
        elif isinstance(sop_parameters, SopLibraryParameters):
            self.set_surface_library()
            if sop_parameters.file_uri:
                self.sop_library.file_uri = sop_parameters.file_uri

    class SopMirror:
        """Mirror SOP parameters."""

        def __init__(self, parent: BaseSop, stable_ctr=False):
            """Create a mirror helper bound to a parent SOP.

            Parameters
            ----------
            parent : ansys.speos.core.opt_prop.BaseSop
                Base SOP wrapper that owns the mirror protobuf field.
            stable_ctr : bool, optional
                Internal guard to prevent unintended direct instantiation.
            """
            if not stable_ctr:
                raise RuntimeError(
                    "SopMirror is not intended to be instantiated directly."
                    "Please use BaseSop.set_surface_mirror() or set stable_ctr=True if you know "
                    "what you're doing."
                )
            self._parent = parent
            self._parent._sop_template.mirror.SetInParent()

        @property
        def reflectance(self) -> float:
            """Reflectance of the mirror surface in percentage.

            Returns
            -------
            float
                Reflectance value between 0 and 100.
            """
            return self._parent._sop_template.mirror.reflectance

        @reflectance.setter
        def reflectance(self, value: float):
            """Set the reflectance of the mirror surface.

            Parameters
            ----------
            value : float
                Reflectance value between 0 and 100.

            Raises
            ------
            ValueError
                If the reflectance value is not between 0 and 100.
            AttributeError
                If the SOP is not of mirror type.
            """
            if not (0 <= value <= 100):
                raise ValueError("Reflectance must be between 0 and 100.")
            self._parent._sop_template.mirror.reflectance = value

    @property
    def sop_mirror(self) -> Optional[BaseSop.SopMirror]:
        """Mirror helper for the current SOP template.

        Returns
        -------
        Optional[ansys.speos.core.opt_prop.BaseSop.SopMirror]
            Mirror helper when the active SOP field is ``mirror``, otherwise ``None``.
        """
        return self._mirror

    def set_surface_mirror(self) -> BaseSop.SopMirror:
        """Define SOP as a perfect specular surface.

        Returns
        -------
        ansys.speos.core.opt_prop.BaseSop.SopMirror
            Returns mirror helper for chaining.
        """
        self._library = None
        if self._sop_template.HasField("mirror"):
            self._library = None
            self._mirror = self.SopMirror(self, stable_ctr=True)
        else:
            self._mirror = self.SopMirror(self, stable_ctr=True)
            self._mirror.reflectance = SopMirrorParameters().reflectance
        return self._mirror

    def set_surface_opticalpolished(self) -> BaseSop:
        """Set SOP to transparent or perfectly polished surface (e.g. glass).

        Returns
        -------
        ansys.speos.core.opt_prop.BaseSop
            Returns self for chaining.
        """
        self._mirror = None
        self._library = None
        self._sop_template.optical_polished.SetInParent()
        return self

    class SopLibrary:
        """Library SOP parameters."""

        def __init__(self, parent: BaseSop, stable_ctr=False):
            """Create a library helper bound to a parent SOP.

            Parameters
            ----------
            parent : ansys.speos.core.opt_prop.BaseSop
                Base SOP wrapper that owns the library protobuf field.
            stable_ctr : bool, optional
                Internal guard to prevent unintended direct instantiation.
            """
            if not stable_ctr:
                raise RuntimeError(
                    "SopLibrary is not intended to be instantiated directly."
                    "Please use BaseSop.set_surface_library() or set stable_ctr=True if you know "
                    "what you're doing."
                )
            self._parent = parent
            self._parent._sop_template.library.SetInParent()

        @property
        def file_uri(self) -> str:
            """Surface property file URI when SOP is a library entry.

            Returns
            -------
            str
                File path or URI of the SOP file (e.g. ``*.scattering``, ``*.bsdf``).
            """
            return self._parent._sop_template.library.sop_file_uri

        @file_uri.setter
        def file_uri(self, value: Union[Path, str]):
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
            self._parent._sop_template.library.sop_file_uri = str(value)

    def set_surface_library(self) -> BaseSop.SopLibrary:
        """Configure SOP to use a library file.

        Returns
        -------
        ansys.speos.core.opt_prop.BaseSop.SopLibrary
            Returns library helper for chaining.
        """
        self._mirror = None
        self._sop_template.library.SetInParent()
        self._library = self.SopLibrary(self, stable_ctr=True)
        return self._library

    @property
    def sop_library(self) -> Optional[BaseSop.SopLibrary]:
        """SOP library parameters when SOP is of library type.

        Returns
        -------
        Optional[ansys.speos.core.opt_prop.BaseSop.SopLibrary]
            Library helper containing ``sop_file_uri`` when SOP is of library
            type, otherwise ``None``.
        """
        if self._sop_template.HasField("library"):
            return self._library


class BaseVop:
    """Base class for Volume Optical Property helpers.

    Notes
    -----
    This is a superclass and is not intended to be instantiated directly.
    """

    class VopOptic:
        """Optic parameters for a clear transparent volume."""

        def __init__(
            self,
            parent,
            default_parameters: Optional[VopOpticParameters] = None,
            stable_ctr=False,
        ):
            """Create an optic helper bound to a parent VOP.

            Parameters
            ----------
            parent : ansys.speos.core.opt_prop.BaseVop
                Base VOP wrapper that owns the optic protobuf field.
            default_parameters : Optional[ansys.speos.core.generic.parameters.VopOpticParameters]
                Default optic parameters to apply during initialization.
            stable_ctr : bool, optional
                Internal guard to prevent unintended direct instantiation.
            """
            if not stable_ctr:
                raise RuntimeError(
                    "VopOptic is not intended to be instantiated directly."
                    "Please use BaseVop.set_volume_optic() or set stable_ctr=True if you know "
                    "what you're doing."
                )
            self._parent = parent
            if default_parameters:
                self._fill_parameters(default_parameters)

        def _fill_parameters(self, default_parameters: VopOpticParameters):
            """Fill optic parameters from default parameters.

            Parameters
            ----------
            default_parameters : ansys.speos.core.generic.parameters.VopOpticParameters
                Default optic parameters to apply.
            """
            self.index = default_parameters.index
            self.absorption = default_parameters.absorption
            self.constringence = default_parameters.constringence

        @property
        def index(self) -> float:
            """Real part of refractive index."""
            return self._parent._vop_template.optic.index

        @index.setter
        def index(self, value: float):
            """Set the refractive index.

            Parameters
            ----------
            value : float
                Real refractive index value to store on the optic field.
            """
            self._parent._vop_template.optic.index = value

        @property
        def absorption(self) -> float:
            """Absorption coefficient."""
            return self._parent._vop_template.optic.absorption

        @absorption.setter
        def absorption(self, value: float):
            """Set the absorption coefficient.

            Parameters
            ----------
            value : float
                Absorption coefficient to store on the optic field.
            """
            self._parent._vop_template.optic.absorption = value

        @property
        def constringence(self) -> Optional[float]:
            """Abbe Number."""
            if self._parent._vop_template.optic.HasField("constringence"):
                return self._parent._vop_template.optic.constringence
            return None

        @constringence.setter
        def constringence(self, value: Optional[float]):
            """Set or clear the Abbe number.

            Parameters
            ----------
            value : Optional[float]
                Abbe number value, or ``None`` to clear the field.
            """
            if value is not None:
                self._parent._vop_template.optic.constringence = value
            else:
                self._parent._vop_template.optic.ClearField("constringence")

    class VopLibrary:
        """Helper class for library VOP parameters."""

        def __init__(self, parent: BaseVop, stable_ctr=False):
            """Create a library helper bound to a parent VOP.

            Parameters
            ----------
            parent : ansys.speos.core.opt_prop.BaseVop
                Base VOP wrapper that owns the library protobuf field.
            stable_ctr : bool, optional
                Internal guard to prevent unintended direct instantiation.
            """
            if not stable_ctr:
                raise RuntimeError(
                    "VopLibrary is not intended to be instantiated directly."
                    "Please use BaseVop.set_volume_library() or set stable_ctr=True if you know "
                    "what you're doing."
                )
            self._parent = parent
            self._parent._vop_template.library.SetInParent()

        @property
        def material_file_uri(self) -> str:
            """Volume material file URI when VOP is a library entry.

            Returns
            -------
            str
                File path or URI of the volume material file (``*.material``).
            """
            return self._parent._vop_template.library.material_file_uri

        @material_file_uri.setter
        def material_file_uri(self, value: Union[Path, str]):
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
            self._parent._vop_template.library.material_file_uri = str(value)

    def __init__(
        self,
        vop_template: Union[None, ProtoVOPTemplate],
        mat_inst: ProtoScene.MaterialInstance,
        vop_parameters: Optional[
            Union[VopTypes.none, VopTypes.opaque, VopLibraryParameters, VopOpticParameters]
        ] = None,
        stable_ctr=False,
    ):
        """Initialize the VOP helper state.

        Parameters
        ----------
        vop_template : Union[None, ansys.speos.core.kernel.vop_template.ProtoVOPTemplate]
            Volume optical property template to wrap.
        mat_inst : ansys.speos.core.kernel.scene.ProtoScene.MaterialInstance
            Material instance that owns the VOP settings.
        vop_parameters : Optional[Union[\
        ansys.speos.core.generic.parameters.VopTypes.none,\
        ansys.speos.core.generic.parameters.VopTypes.opaque, \
        ansys.speos.core.generic.parameters.VopLibraryParameters, \
        ansys.speos.core.generic.parameters.VopOpticParameters. \
        ]], optional
            Default VOP parameters to apply at initialization.
        """
        if not stable_ctr:
            raise RuntimeError(
                "BaseVop is not intended to be instantiated directly."
                "Please use a subclass or set stable_ctr=True if you know what you're doing."
            )
        # Create VOP template
        self._vop_template = vop_template
        # Create material instance
        self._material_instance = mat_inst

        self._vop_optic = None
        self._vop_library = None

        if vop_parameters:
            self._fill_parameters_vop(vop_parameters)

    def _fill_parameters_vop(
        self,
        vop_parameters: Union[
            VopTypes.none, VopTypes.opaque, VopLibraryParameters, VopOpticParameters
        ],
    ):
        """Apply VOP parameters to initialize the volume optical property.

        Parameters
        ----------
        vop_parameters : Union[\
        ansys.speos.core.generic.parameters.VopTypes.none,\
        ansys.speos.core.generic.parameters.VopTypes.opaque, \
        ansys.speos.core.generic.parameters.VopLibraryParameters, \
        ansys.speos.core.generic.parameters.VopOpticParameters. \
        ]VOP parameters to apply.
        """
        if vop_parameters == VopTypes.none:
            self.set_volume_none()
        elif isinstance(vop_parameters, VopOpticParameters):
            self.set_volume_optic()
            self.vop_optic._fill_parameters(vop_parameters)
        elif vop_parameters == VopTypes.opaque:
            self.set_volume_opaque()
        elif isinstance(vop_parameters, VopLibraryParameters):
            self.set_volume_library()
            self.vop_library.material_file_uri = vop_parameters.material_file_uri

    @property
    def vop_optic(self) -> Optional[BaseVop.VopOptic]:
        """Optic parameters for a clear transparent volume.

        Returns
        -------
        Optional[ansys.speos.core.opt_prop.BaseVop.VopOptic]
            Optic helper containing index, absorption, and constringence when
            VOP is of optic type, otherwise ``None``.
        """
        if self._vop_template.HasField("optic"):
            return self._vop_optic

    @property
    def vop_library(self) -> Optional[BaseVop.VopLibrary]:
        """Library parameters when VOP is of library type.

        Returns
        -------
        Optional[ansys.speos.core.opt_prop.BaseVop.VopLibrary]
            Library helper containing ``material_file_uri`` when VOP is of
            library type, otherwise ``None``.
        """
        if self._vop_template.HasField("library"):
            return self._vop_library

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
                name=self._material_instance.name + ".VOP",
                description=self._material_instance.description,
                metadata=self._material_instance.metadata,
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
                name=self._material_instance.name + ".VOP",
                description=self._material_instance.description,
                metadata=self._material_instance.metadata,
            )
            self._vop_optic = self.VopOptic(self, VopOpticParameters(), stable_ctr=True)
        elif self._vop_template.HasField("optic"):
            self._vop_optic = self.VopOptic(self, None, stable_ctr=True)
        else:
            self._vop_template.optic.SetInParent()
            self._vop_optic = self.VopOptic(self, VopOpticParameters(), stable_ctr=True)
        return self._vop_optic

    def set_volume_library(self) -> BaseVop.VopLibrary:
        """Set VOP to use a library file.

        Returns
        -------
        ansys.speos.core.opt_prop.BaseVop.VopLibrary
            Returns VOP Library helper.
        """
        if self._vop_template is None:
            self._vop_template = ProtoVOPTemplate(
                name=self._material_instance.name + ".VOP",
                description=self._material_instance.description,
                metadata=self._material_instance.metadata,
            )
        self._vop_template.library.SetInParent()
        self._vop_library = self.VopLibrary(self, stable_ctr=True)
        return self._vop_library

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


class TextureLayer(BaseSop):
    """Describes the optical and texture properties of a single texture layer."""

    class TextureMappingOperator:
        """Texture mapping operator for a texture layer."""

        def __init__(self, mapping, default_parameters: Optional[MappingOperator] = None):
            """Initialize a texture mapping operator wrapper.

            Parameters
            ----------
            mapping : protobuf message
                Message containing the ``mapping_operator`` field to manipulate.
            default_parameters : Optional[\
                ansys.speos.core.generic.parameters.MappingOperator\
            ], optional
                Default mapping parameters to apply to the operator.
            """
            self._mapping = mapping.mapping_operator
            self._fill_parameters(default_parameters)

        def _fill_parameters(self, default_parameters: Optional[MappingOperator] = None):
            """Fill mapping operator parameters from default parameters.

            Parameters
            ----------
            default_parameters : Optional[\
                ansys.speos.core.generic.parameters.MappingOperator\
            ], optional
                Default mapping parameters to apply.
            """
            if default_parameters and default_parameters:
                match default_parameters.mapping_type:
                    case MappingTypes.planar:
                        self._mapping.planar.SetInParent()
                    case MappingTypes.cubic:
                        self._mapping.cubic.SetInParent()
                    case _:
                        if isinstance(default_parameters.mapping_type, MappingSphericalParameters):
                            self._mapping.spherical.SetInParent()
                            self._mapping.spherical.sphere_perimeter = (
                                default_parameters.mapping_type.perimeter
                            )
                        elif isinstance(
                            default_parameters.mapping_type, MappingCylindricalParameters
                        ):
                            self._mapping.cylindrical.SetInParent()
                            self._mapping.cylindrical.base_perimeter = (
                                default_parameters.mapping_type.perimeter
                            )
                self._mapping.u_offset = default_parameters.u_offset
                self._mapping.v_offset = default_parameters.v_offset
                self._mapping.u_length = default_parameters.u_length
                if default_parameters.v_length:
                    self._mapping.v_length = default_parameters.v_length
                self._mapping.ClearField("axis_system")
                self._mapping.axis_system[:] = default_parameters.axis_system
                self._mapping.u_scale_factor = default_parameters.u_scale
                self._mapping.v_scale_factor = default_parameters.v_scale
                self._mapping.rotation = default_parameters.rotation

        @property
        def mapping_type(self) -> Optional[str]:
            """Mapping projection type.

            Returns
            -------
            Optional[str]
                One of ``'planar'``, ``'cubic'``, ``'spherical'``, ``'cylindrical'``,
                or ``None`` when no type is set.
            """
            for t in MappingTypes:
                if self._mapping.HasField(t):
                    return t
            return None

        @property
        def axis_system(self) -> list:
            """Reference axis system for the mapping operator.

            Returns
            -------
            list[float]
                Twelve floats ``[Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz]``.
            """
            return list(self._mapping.axis_system)

        @axis_system.setter
        def axis_system(self, value: list):
            """Set the reference axis system.

            Parameters
            ----------
            value : list[float]
                Twelve floats ``[Ox Oy Oz Xx Xy Xz Yx Yy Yz Zx Zy Zz]``.
            """
            self._mapping.ClearField("axis_system")
            self._mapping.axis_system[:] = value

        @property
        def u_offset(self) -> float:
            """Shift on U direction (mm).

            Returns
            -------
            float
                U offset value.
            """
            return self._mapping.u_offset

        @u_offset.setter
        def u_offset(self, value: float):
            """Set the U direction offset.

            Parameters
            ----------
            value : float
                U offset in mm.
            """
            self._mapping.u_offset = value

        @property
        def v_offset(self) -> float:
            """Shift on V direction (mm).

            Returns
            -------
            float
                V offset value.
            """
            return self._mapping.v_offset

        @v_offset.setter
        def v_offset(self, value: float):
            """Set the V direction offset.

            Parameters
            ----------
            value : float
                V offset in mm.
            """
            self._mapping.v_offset = value

        @property
        def u_scale(self) -> float:
            """Scale factor on U dimension.

            Returns
            -------
            float
                U scale factor.
            """
            return self._mapping.u_scale_factor

        @u_scale.setter
        def u_scale(self, value: float):
            """Set the U dimension scale factor.

            Parameters
            ----------
            value : float
                U scale factor.
            """
            self._mapping.u_scale_factor = value

        @property
        def v_scale(self) -> float:
            """Scale factor on V dimension.

            Returns
            -------
            float
                V scale factor.
            """
            return self._mapping.v_scale_factor

        @v_scale.setter
        def v_scale(self, value: float):
            """Set the V dimension scale factor.

            Parameters
            ----------
            value : float
                V scale factor.
            """
            self._mapping.v_scale_factor = value

        @property
        def u_length(self) -> float:
            """Dimension on U direction (mm).

            Returns
            -------
            float
                U length value.
            """
            return self._mapping.u_length

        @u_length.setter
        def u_length(self, value: float):
            """Set the U direction dimension.

            Parameters
            ----------
            value : float
                U length in mm.
            """
            self._mapping.u_length = value

        @property
        def v_length(self) -> Optional[float]:
            """Dimension on V direction (mm).

            Returns
            -------
            Optional[float]
                V length value, or ``None`` when not set (image ratio is used instead).
            """
            if self._mapping.HasField("v_length"):
                return self._mapping.v_length
            return None

        @v_length.setter
        def v_length(self, value: Optional[float]):
            """Set the V direction dimension.

            Parameters
            ----------
            value : Optional[float]
                V length in mm, or ``None`` to clear and use the image ratio.
            """
            if value is None:
                self._mapping.ClearField("v_length")
            else:
                self._mapping.v_length = value

        @property
        def rotation(self) -> float:
            """Rotation of UVs in degrees, in range ]-360, 360[.

            Returns
            -------
            float
                Rotation angle in degrees.
            """
            return self._mapping.rotation

        @rotation.setter
        def rotation(self, value: float):
            """Set the UV rotation angle.

            Parameters
            ----------
            value : float
                Rotation in degrees, must be in range ]-360, 360[.
            """
            self._mapping.rotation = value

        @property
        def perimeter(self) -> Optional[float]:
            """Sphere perimeter for spherical mapping (mm).

            Returns
            -------
            Optional[float]
                Sphere perimeter when mapping type is ``'spherical'``, otherwise ``None``.
            """
            if self._mapping.HasField("spherical"):
                return self._mapping.spherical.sphere_perimeter
            if self._mapping.HasField("cylindrical"):
                return self._mapping.cylindrical.base_perimeter
            return None

        @perimeter.setter
        def perimeter(self, value: float):
            """Set the sphere perimeter for spherical mapping.

            Parameters
            ----------
            value : float
                Sphere perimeter in mm.

            Raises
            ------
            TypeError
                If mapping type is not ``'spherical'``.
            """
            if self._mapping.HasField("spherical"):
                self._mapping.spherical.sphere_perimeter = value
            elif self._mapping.HasField("cylindrical"):
                self._mapping.cylindrical.base_perimeter = value
            else:
                raise TypeError(
                    f"Mapping type is not '{MappingTypes._spherical}' or "
                    f"'{MappingTypes._cylindrical}. Set mapping_type to "
                    f"'{MappingTypes._spherical}' or '{MappingTypes._cylindrical} first."
                )

        def __todict__(self):
            """Convert the mapping operator properties to a dictionary for comparison."""
            return {
                "mapping_type": self.mapping_type,
                "u_offset": self.u_offset,
                "v_offset": self.v_offset,
                "u_length": self.u_length,
                "v_length": self.v_length,
                "axis_system": self.axis_system,
                "u_scale": self.u_scale,
                "v_scale": self.v_scale,
                "rotation": self.rotation,
                "perimeter": self.perimeter,
            }

        def __eq__(self, other):
            """Override equality to compare mapping operator properties."""
            if isinstance(other, dict):
                return self.__todict__() == other
            elif isinstance(other, TextureLayer.TextureMappingOperator):
                return self.__todict__() == other.__todict__()
            else:
                return NotImplemented

        def __str__(self):
            """Represent the mapping operator as string."""
            return (
                f"TextureMappingOperator(mapping_type={self.mapping_type},"
                f"u_offset={self.u_offset}, "
                f"v_offset={self.v_offset}, "
                f"u_length={self.u_length}, "
                f"v_length={self.v_length}, "
                f"axis_system={self.axis_system}, "
                f"u_scale={self.u_scale}, "
                f"v_scale={self.v_scale}, "
                f"rotation={self.rotation}), "
                f"perimeter={self.perimeter},"
            )

    class TextureMappingByData:
        """Texture mapping by data for a texture layer."""

        def __init__(self, parent, default_parameters: Optional[MappingByData] = None):
            """Initialize a mapping-by-data helper.

            Parameters
            ----------
            parent : protobuf message
                Message containing a ``vertices_data_index`` field.
            default_parameters : Optional[\
                ansys.speos.core.generic.parameters.MappingByData\
            ], optional
                Default data-mapping parameters to apply.
            """
            self._parent = parent
            self._fill_parameters(default_parameters)

        def _fill_parameters(self, default_parameters: Optional[MappingByData] = None):
            """Fill mapping-by-data parameters from default parameters.

            Parameters
            ----------
            default_parameters : Optional[\
                ansys.speos.core.generic.parameters.MappingByData\
            ], optional
                Default data-mapping parameters to apply.
            """
            if default_parameters and default_parameters.vertices_data_index is not None:
                self.vertices_data_index = default_parameters.vertices_data_index

        @property
        def vertices_data_index(self) -> int:
            """Index of the vertices data to use for texture mapping.

            Returns
            -------
            int
                Index of the vertices data.
            """
            return self._parent.vertices_data_index

        @vertices_data_index.setter
        def vertices_data_index(self, value: int):
            """Set the index of the vertices data to use for texture mapping.

            Parameters
            ----------
            value : int
                Index of the vertices data.
            """
            self._parent.vertices_data_index = value

    class BaseTextureMap:
        """Base class for texture mapping properties."""

        def __init__(self, parent: TextureLayer, texture_type: TextureTypes, stable_ctr=False):
            """Initialize a base texture map helper.

            Parameters
            ----------
            parent : ansys.speos.core.opt_prop.TextureLayer
                Texture layer that owns the map data.
            texture_type : ansys.speos.core.generic.parameters.TextureTypes
                Texture map kind handled by the helper.
            """
            if not stable_ctr:
                raise RuntimeError(
                    "BaseTextureMap is not intended to be instantiated directly."
                    "Please use a subclass or set stable_ctr=True if you know what you're doing."
                )
            self._parent = parent
            self._mapping = None
            self._type = texture_type

        def _get_map_property(self):
            """Return the protobuf map property matching the current texture type."""
            if self._type == TextureTypes.image:
                return self._parent._texture_template.image_properties
            if self._type == TextureTypes.normal_map:
                return self._parent._texture_template.normal_map_properties
            if self._type == TextureTypes.anisotropy_map:
                return self._parent._texture_template.anisotropy_map_properties
            raise TypeError(f"Unsupported texture type for mapping: {self._type}")

        @staticmethod
        def _mapping_type_name(mapping_type: Union[MappingTypes, str]) -> str:
            """Normalize mapping type input to the protobuf oneof field name."""
            if isinstance(mapping_type, MappingTypes):
                return mapping_type.value
            elif isinstance(mapping_type, MappingCylindricalParameters):
                return MappingTypes._cylindrical.value
            elif isinstance(mapping_type, MappingSphericalParameters):
                return MappingTypes._spherical.value
            return str(mapping_type)

        def _set_mapping_operator(self, mapping_type: Union[MappingTypes, str]):
            """Switch to operator-based mapping and set its projection type."""
            mapping_type_name = self._mapping_type_name(mapping_type)
            map_property = self._get_map_property()
            if map_property.HasField("vertices_data_index"):
                map_property.ClearField("vertices_data_index")
                map_property.mapping_operator.SetInParent()
            if not map_property.mapping_operator.HasField(mapping_type_name):
                map_property.ClearField("mapping_operator")
                map_property.mapping_operator.SetInParent()
                if mapping_type_name not in {"planar", "cubic", "spherical", "cylindrical"}:
                    raise ValueError(
                        "Invalid mapping type. Must be one of 'planar', 'cubic', 'spherical', "
                        "'cylindrical'."
                    )
                getattr(map_property.mapping_operator, mapping_type_name).SetInParent()
                self._mapping = TextureLayer.TextureMappingOperator(
                    map_property, MappingOperator(mapping_type=mapping_type)
                )
            else:
                self._mapping = TextureLayer.TextureMappingOperator(map_property, None)
            return self._mapping

        @property
        def uv_mapping(
            self,
        ) -> Optional[
            Union[TextureLayer.TextureMappingByData, TextureLayer.TextureMappingOperator]
        ]:
            """Texture mapping properties for the texture layer."""
            if self._mapping:
                return self._mapping
            if self._type == TextureTypes.image:
                if self._parent._texture_template.image_properties.HasField("vertices_data_index"):
                    self._mapping = self._parent.TextureMappingByData(
                        self._parent._texture_template.image_properties, None
                    )
                else:
                    self._mapping = self._parent.TextureMappingOperator(
                        self._parent._texture_template.image_properties, None
                    )
            elif self._type == TextureTypes.normal_map:
                if self._parent._texture_template.normal_map_properties.HasField(
                    "vertices_data_index"
                ):
                    self._mapping = self._parent.TextureMappingByData(
                        self._parent._texture_template.normal_map_properties, None
                    )
                else:
                    self._mapping = self._parent.TextureMappingOperator(
                        self._parent._texture_template.normal_map_properties, None
                    )
            elif self._type == TextureTypes.anisotropy_map:
                if self._parent._texture_template.anisotropy_map_properties.HasField(
                    "vertices_data_index"
                ):
                    self._mapping = self._parent.TextureMappingByData(
                        self._parent._texture_template.anisotropy_map_properties, None
                    )
                else:
                    self._mapping = self._parent.TextureMappingOperator(
                        self._parent._texture_template.anisotropy_map_properties, None
                    )
            return self._mapping

        def set_uv_mapping_cylindrical(self):
            """Set cylindrical mapping for the texture layer.

            Returns
            -------
            ansys.speos.core.opt_prop.TextureLayer.TextureMappingOperator
                The mapping operator for the cylindrical mapping.
            """
            self._set_mapping_operator(MappingTypes._cylindrical)
            self._mapping.perimeter = 1  # Default perimeter value for cylindrical mapping
            return self._mapping

        def set_uv_mapping_planar(self):
            """Set planar mapping for the texture layer."""
            return self._set_mapping_operator(MappingTypes.planar)

        def set_uv_mapping_cubic(self):
            """Set cubic mapping for the texture layer."""
            return self._set_mapping_operator(MappingTypes.cubic)

        def set_uv_mapping_spherical(self):
            """Set spherical mapping for the texture layer.

            Returns
            -------
            ansys.speos.core.opt_prop.TextureLayer.TextureMappingOperator
                The mapping operator for the spherical mapping.
            """
            self._set_mapping_operator(MappingTypes._spherical)
            self._mapping.perimeter = 1  # Default perimeter value for spherical mapping
            return self._mapping

        def set_uv_mapping_by_data(self):
            """Set mapping by vertices data index for the texture layer."""
            map_property = self._get_map_property()
            if map_property.HasField("mapping_operator"):
                map_property.ClearField("mapping_operator")
            if not map_property.HasField("vertices_data_index"):
                map_property.vertices_data_index = 0
            self._mapping = TextureLayer.TextureMappingByData(map_property, None)
            return self._mapping

    class ImageTexture(BaseTextureMap):
        """Image texture mapping properties."""

        def __init__(
            self,
            parent: TextureLayer,
            default_parameters: Optional[ImageTextureParameter] = None,
            stable_ctr=False,
        ):
            """Initialize an image texture helper.

            Parameters
            ----------
            parent : ansys.speos.core.opt_prop.TextureLayer
                Texture layer that owns the image texture data.
            default_parameters : Optional[\
                ansys.speos.core.generic.parameters.ImageTextureParameter\
            ], optional
                Default image texture settings to apply.
            """
            if not stable_ctr:
                raise RuntimeError(
                    "ImageTexture is not intended to be instantiated directly."
                    "Please use TextureLayer.set_image_texture() or set stable_ctr=True if you "
                    "know what you're doing."
                )
            super().__init__(parent, TextureTypes.image, stable_ctr=True)
            self._fill_parameters(default_parameters)

        def _fill_parameters(self, default_parameters: Optional[ImageTextureParameter] = None):
            """Fill image texture parameters from default parameters.

            Parameters
            ----------
            default_parameters : Optional[\
                ansys.speos.core.generic.parameters.ImageTextureParameter\
            ], optional
                Default image texture settings to apply.
            stable_ctr : bool, optional
                Internal guard to prevent unintended direct instantiation.
            """
            if default_parameters:
                if default_parameters.file_path:
                    self.image_file_uri = default_parameters.file_path
                self.repeat_u = default_parameters.repeat_u
                self.repeat_v = default_parameters.repeat_v
                if isinstance(default_parameters.mapping, MappingOperator):
                    self._mapping = self._set_mapping_operator(
                        default_parameters.mapping.mapping_type
                    )
                    # Set mapping properties based on the provided MappingOperator
                    self._mapping.u_offset = default_parameters.mapping.u_offset
                    self._mapping.v_offset = default_parameters.mapping.v_offset
                    self._mapping.u_length = default_parameters.mapping.u_length
                    if default_parameters.mapping.v_length:
                        self._mapping.v_length = default_parameters.mapping.v_length
                    self._mapping.axis_system = default_parameters.mapping.axis_system
                    self._mapping.u_scale = default_parameters.mapping.u_scale
                    self._mapping.v_scale = default_parameters.mapping.v_scale
                    self._mapping.rotation = default_parameters.mapping.rotation
                elif (
                    default_parameters.mapping
                    and default_parameters.mapping.vertices_data_index is not None
                ):
                    self._mapping = self.set_uv_mapping_by_data()
                    self._mapping.vertices_data_index = (
                        default_parameters.mapping.vertices_data_index
                    )

        @property
        def repeat_u(self) -> bool:
            """Whether the texture repeats along the U direction."""
            return self._parent._sop_template.texture.image.repeat_along_u

        @repeat_u.setter
        def repeat_u(self, value: bool):
            """Set whether the image texture repeats along the U direction.

            Parameters
            ----------
            value : bool
                ``True`` to repeat along U, ``False`` otherwise.
            """
            self._parent._sop_template.texture.image.repeat_along_u = value

        @property
        def repeat_v(self) -> bool:
            """Whether the texture repeats along the V direction."""
            return self._parent._sop_template.texture.image.repeat_along_v

        @repeat_v.setter
        def repeat_v(self, value: bool):
            """Set whether the image texture repeats along the V direction.

            Parameters
            ----------
            value : bool
                ``True`` to repeat along V, ``False`` otherwise.
            """
            self._parent._sop_template.texture.image.repeat_along_v = value

        @property
        def image_file_uri(self) -> Optional[str]:
            """URI of the texture bitmap file."""
            return self._parent._sop_template.texture.image.bitmap_file_uri

        @image_file_uri.setter
        def image_file_uri(self, value: Union[Path, str]):
            """Set the texture bitmap file URI."""
            if self._type == TextureTypes.image:
                self._parent._sop_template.texture.image.bitmap_file_uri = str(value)

    class NormalMap(BaseTextureMap):
        """Normal map texture mapping properties."""

        def __init__(
            self,
            parent: TextureLayer,
            default_parameters: Optional[NormalMapParameter] = None,
            stable_ctr=False,
        ):
            """Initialize a normal map helper.

            Parameters
            ----------
            parent : ansys.speos.core.opt_prop.TextureLayer
                Texture layer that owns the normal map data.
            default_parameters : Optional[\
                ansys.speos.core.generic.parameters.NormalMapParameter\
            ], optional
                Default normal map settings to apply.
            """
            if not stable_ctr:
                raise RuntimeError(
                    "NormalMap is not intended to be instantiated directly."
                    "Please use TextureLayer.set_normal_map() or set stable_ctr=True if you know "
                    "what you're doing."
                )
            super().__init__(parent, TextureTypes.normal_map, stable_ctr=True)
            self._fill_parameters(default_parameters)

        def _fill_parameters(self, default_parameters: Optional[NormalMapParameter] = None):
            """Fill normal map parameters from default parameters.

            Parameters
            ----------
            default_parameters : Optional[\
                ansys.speos.core.generic.parameters.NormalMapParameter\
            ], optional
                Default normal map settings to apply.
            stable_ctr : bool, optional
                Internal guard to prevent unintended direct instantiation.
            """
            if default_parameters:
                match default_parameters.normal_map_type:
                    case NormalMapTypes.from_image:
                        self._set_normal_map_from_image()
                    case NormalMapTypes.from_normal_map:
                        self._set_normal_map_from_normal_map()
                if default_parameters.file_path:
                    self.normal_map_file_uri = default_parameters.file_path
                self.repeat_u = default_parameters.repeat_u
                self.repeat_v = default_parameters.repeat_v
                if isinstance(default_parameters.mapping, MappingOperator):
                    self._mapping = self._set_mapping_operator(
                        default_parameters.mapping.mapping_type
                    )
                    # Set mapping properties based on the provided MappingOperator
                    self._mapping.u_offset = default_parameters.mapping.u_offset
                    self._mapping.v_offset = default_parameters.mapping.v_offset
                    self._mapping.u_length = default_parameters.mapping.u_length
                    if default_parameters.mapping.v_length:
                        self._mapping.v_length = default_parameters.mapping.v_length
                    self._mapping.axis_system = default_parameters.mapping.axis_system
                    self._mapping.u_scale = default_parameters.mapping.u_scale
                    self._mapping.v_scale = default_parameters.mapping.v_scale
                    self._mapping.rotation = default_parameters.mapping.rotation
                elif (
                    default_parameters.mapping
                    and default_parameters.mapping.vertices_data_index is not None
                ):
                    self._mapping = self.set_uv_mapping_by_data()
                    self._mapping.vertices_data_index = (
                        default_parameters.mapping.vertices_data_index
                    )

        @property
        def repeat_u(self) -> bool:
            """Whether the normal map repeats along the U direction."""
            return self._parent._sop_template.texture.normal_map.repeat_along_u

        @repeat_u.setter
        def repeat_u(self, value: bool):
            """Set whether the normal map repeats along the U direction.

            Parameters
            ----------
            value : bool
                ``True`` to repeat along U, ``False`` otherwise.
            """
            self._parent._sop_template.texture.normal_map.repeat_along_u = value

        @property
        def repeat_v(self) -> bool:
            """Whether the normal map repeats along the V direction."""
            return self._parent._sop_template.texture.normal_map.repeat_along_v

        @repeat_v.setter
        def repeat_v(self, value: bool):
            """Set whether the normal map repeats along the V direction.

            Parameters
            ----------
            value : bool
                ``True`` to repeat along V, ``False`` otherwise.
            """
            self._parent._sop_template.texture.normal_map.repeat_along_v = value

        @property
        def normal_map_file_uri(self) -> Optional[str]:
            """URI of the normal map source file."""
            normal_map = self._parent._sop_template.texture.normal_map
            if normal_map.HasField("from_image"):
                return normal_map.from_image.bitmap_file_uri
            if normal_map.HasField("from_normal_map"):
                return normal_map.from_normal_map.normal_map_file_uri
            return None

        @normal_map_file_uri.setter
        def normal_map_file_uri(self, value: Union[Path, str]):
            """Set the normal map source file URI."""
            normal_map = self._parent._sop_template.texture.normal_map
            if normal_map.HasField("from_image"):
                normal_map.from_image.bitmap_file_uri = str(value)
            elif normal_map.HasField("from_normal_map"):
                normal_map.from_normal_map.normal_map_file_uri = str(value)

        @property
        def roughness(self) -> Optional[float]:
            """Roughness parameter of the normal map.

            Returns
            -------
            Optional[float]
                Roughness value when a normal map exists, otherwise ``None``.
            """
            if self._parent._sop_template.texture.HasField("normal_map"):
                return self._parent._sop_template.texture.normal_map.roughness

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
            if self._parent._sop_template.texture.HasField("normal_map"):
                self._parent._sop_template.texture.normal_map.roughness = value
            else:
                raise TypeError("No Normal map defined")

        def _set_normal_map_from_image(self):
            """Configure the normal map to be sourced from an image."""
            temp = ""
            if self.normal_map_file_uri:
                temp = self.normal_map_file_uri
            self._parent._sop_template.texture.normal_map.from_image.SetInParent()
            if temp:
                self.normal_map_file_uri = temp

        def _set_normal_map_from_normal_map(self):
            """Configure the normal map to be sourced from a normal map file."""
            temp = ""
            if self.normal_map_file_uri:
                temp = self.normal_map_file_uri
            self._parent._sop_template.texture.normal_map.from_normal_map.SetInParent()
            if temp:
                self.normal_map_file_uri = temp

    class AnisotropicMap(BaseTextureMap):
        """Anisotropy map texture mapping properties."""

        def __init__(
            self,
            parent: TextureLayer,
            default_parameters: Optional[MappingOperator] = None,
            stable_ctr=False,
        ):
            """Initialize an anisotropy map helper.

            Parameters
            ----------
            parent : ansys.speos.core.opt_prop.TextureLayer
                Texture layer that owns the anisotropy map data.
            default_parameters : Optional[\
                ansys.speos.core.generic.parameters.MappingOperator\
            ], optional
                Default anisotropy map settings to apply.
            """
            if not stable_ctr:
                raise RuntimeError(
                    "AnisotropicMap is not intended to be instantiated directly."
                    "Please use TextureLayer.set_anisotropy_map() or set stable_ctr=True if you "
                    "know what you're doing."
                )
            super().__init__(parent, TextureTypes.anisotropy_map, stable_ctr=True)
            self._fill_parameters(default_parameters)

        def _fill_parameters(self, default_parameters: Optional[MappingOperator] = None):
            """Fill anisotropy map parameters from default parameters.

            Parameters
            ----------
            default_parameters : Optional[\
                ansys.speos.core.generic.parameters.MappingOperator\
            ], optional
                Default anisotropy map settings to apply.
            stable_ctr : bool, optional
                Internal guard to prevent unintended direct instantiation.
            """
            if default_parameters:
                if isinstance(default_parameters, MappingOperator):
                    self._mapping = self._set_mapping_operator(default_parameters.mapping_type)
                    # Set mapping properties based on the provided MappingOperator
                    self._mapping.u_offset = default_parameters.u_offset
                    self._mapping.v_offset = default_parameters.v_offset
                    self._mapping.u_length = default_parameters.u_length
                    if default_parameters.v_length:
                        self._mapping.v_length = default_parameters.v_length
                    self._mapping.axis_system = default_parameters.axis_system
                    self._mapping.u_scale = default_parameters.u_scale
                    self._mapping.v_scale = default_parameters.v_scale
                    self._mapping.rotation = default_parameters.rotation

    @min_speos_version(25, 2, 0)
    def __init__(
        self,
        opt_prop: "OptProp",
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        default_parameters: Optional[TextureLayerParameters] = None,
    ):
        """Initialize a texture layer.

        Parameters
        ----------
        opt_prop : ansys.speos.core.opt_prop.OptProp
            Optical property that will own this texture layer.
        name : str
            Name of the texture layer feature.
        description : str, optional
            Description of the texture layer.
        metadata : Optional[Mapping[str, str]], optional
            Metadata to attach to the SOP template.
        default_parameters : Optional[\
            ansys.speos.core.generic.parameters.TextureLayerParameters\
        ], optional
            Default texture layer parameters to apply at initialization.
        """
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
        self._normal_map = None
        self._image_map = None
        self._aniso_map = None

        self._index = None

        if default_parameters:
            super().__init__(
                self._sop_template,
                self._material_instance,
                default_parameters.sop_parameters,
                stable_ctr=True,
            )
            self._fill_parameters(default_parameters)
        else:
            super().__init__(
                self._sop_template, self._material_instance, SopMirrorParameters(), stable_ctr=True
            )

    def _fill_parameters(self, default_parameters: Optional[TextureLayerParameters] = None):
        """Fill texture layer parameters from default parameters.

        Parameters
        ----------
        default_parameters : Optional[\
            ansys.speos.core.generic.parameters.TextureLayerParameters\
        ], optional
            Default texture layer parameters to apply.
        """
        if default_parameters.image_texture_parameters:
            self._image_map = TextureLayer.ImageTexture(
                self._texture_template,
                default_parameters.image_texture_parameters,
                stable_ctr=True,
            )
        if default_parameters.normal_map_parameters:
            self._normal_map = TextureLayer.NormalMap(
                self._texture_template,
                default_parameters.normal_map_parameters,
                stable_ctr=True,
            )
        if default_parameters.anisotropy_map_parameters:
            if default_parameters.anisotropy_map_parameters:
                self.normal_map_property = default_parameters.anisotropy_map_parameters

    @property
    def image_texture(self) -> ImageTexture:
        """Texture Properties of the Image Texture."""
        return self._image_map

    @property
    def normal_map(self) -> NormalMap:
        """Texture properties of the normal map."""
        return self._normal_map

    @property
    def anisotropic_map(self) -> AnisotropicMap:
        """Anisotropy map mapping properties."""
        return self._aniso_map

    def set_image_texture(self):
        """Activate Image texture in this texture layer."""
        if self._image_map:
            return self._image_map
        if self._texture_template.HasField("image_properties"):
            self._image_map = TextureLayer.ImageTexture(
                self, default_parameters=None, stable_ctr=True
            )
        else:
            self._image_map = TextureLayer.ImageTexture(
                self,
                default_parameters=ImageTextureParameter(),
                stable_ctr=True,
            )
        return self._image_map

    def set_image_texture_to_none(self):
        """Deactivate image texture in this texture layer."""
        if self._image_map:
            self._image_map = None
            self._texture_template.ClearField("image_properties")
        return self

    def set_normal_map_from_image(self):
        """Activate normal map in this texture layer."""
        if self._normal_map:
            self._normal_map._set_normal_map_from_image()
            return self._normal_map
        if self._texture_template.HasField("normal_map_properties"):
            self._normal_map = TextureLayer.NormalMap(
                self, default_parameters=None, stable_ctr=True
            )
            self._normal_map._set_normal_map_from_image()
        else:
            self._normal_map = TextureLayer.NormalMap(
                self,
                default_parameters=NormalMapParameter(),
                stable_ctr=True,
            )
        return self._normal_map

    def set_normal_map_from_normal_map(self):
        """Activate normal map in this texture layer."""
        if self._normal_map:
            self._normal_map._set_normal_map_from_normal_map()
            return self._normal_map
        if self._texture_template.HasField("normal_map_properties"):
            self._normal_map = TextureLayer.NormalMap(
                self, default_parameters=None, stable_ctr=True
            )
            self._normal_map._set_normal_map_from_normal_map()
        else:
            self._normal_map = TextureLayer.NormalMap(
                self,
                default_parameters=NormalMapParameter(
                    normal_map_type=NormalMapTypes.from_normal_map
                ),
                stable_ctr=True,
            )
        return self._normal_map

    def set_normal_map_to_none(self):
        """Deactivate normal map in this texture layer."""
        if self._normal_map:
            self._normal_map = None
            self._texture_template.ClearField("normal_map_properties")
        return self

    def set_anisotropy_map(self):
        """Activate anisotropy map in this texture layer."""
        if self._aniso_map:
            return self._aniso_map
        if self._texture_template.HasField("anisotropy_map_properties"):
            self._aniso_map = TextureLayer.AnisotropicMap(
                self, default_parameters=None, stable_ctr=True
            )
        else:
            self._aniso_map = TextureLayer.AnisotropicMap(
                self,
                default_parameters=MappingOperator(),
                stable_ctr=True,
            )
        return self._aniso_map

    def set_anisotropy_map_to_none(self):
        """Deactivate anisotropy map in this texture layer."""
        if self._aniso_map:
            self._aniso_map = None
            self._texture_template.ClearField("anisotropy_map_properties")
        return self

    def _commit(self) -> "TextureLayer":
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

    def _reset(self) -> "TextureLayer":
        """Reset local texture layer data from server-side data.

        Returns
        -------
        ansys.speos.core.opt_prop.TextureLayer
            Returns self after resetting.
        """
        # Reset sop template
        if self.sop_template_link is not None:
            self._sop_template = self.sop_template_link.get()
            self._sync_sop_properties()
            self._normal_map = None
            self._aniso_map = None
            self._image_map = None
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
                if self._texture_template.HasField("anisotropy_map_properties"):
                    self.set_anisotropy_map()
                if self._texture_template.HasField("normal_map_properties"):
                    if self._sop_template.texture.normal_map.HasField("from_image"):
                        self.set_normal_map_from_image()
                    elif self._sop_template.texture.normal_map.HasField("from_normal_map"):
                        self.set_normal_map_from_normal_map()
                if self._texture_template.HasField("image_properties"):
                    self.set_image_texture()
        return self

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
        texture : ansys.speos.core.kernel.scene.ProtoScene.MaterialInstance.Texture.Layer
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
    default_parameters : Optional[ansys.speos.core.generic.parameters.OptPropParameters], optional
        Default optical property parameters to initialize the OptProp. Default is ``None``.
    """

    def __init__(
        self,
        project: project.Project,
        name: str,
        description: str = "",
        metadata: Optional[Mapping[str, str]] = None,
        default_parameters: Optional[OptPropParameters] = None,
    ):
        """Initialize an optical property wrapper.

        Parameters
        ----------
        project : ansys.speos.core.project.Project
            Project that will own the optical property.
        name : str
            Name of the optical property.
        description : str, optional
            Human-readable description of the optical property.
        metadata : Optional[Mapping[str, str]], optional
            Metadata to attach to the created templates and material instance.
        default_parameters : Optional[\
            ansys.speos.core.generic.parameters.OptPropParameters\
        ], optional
            Default optical property parameters to apply at initialization.
        """
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
        self.geometries = None

        if default_parameters:
            self._fill_parameters(default_parameters)
        else:
            BaseSop.__init__(
                self,
                self._sop_template,
                self._material_instance,
                sop_parameters=None,
                stable_ctr=True,
            )
            BaseVop.__init__(
                self,
                self._vop_template,
                self._material_instance,
                vop_parameters=None,
                stable_ctr=True,
            )

    def _fill_parameters(self, default_parameters: OptPropParameters):
        """Fill optical property parameters from default parameters.

        Parameters
        ----------
        default_parameters : Optional[\
            ansys.speos.core.generic.parameters.OptPropParameters\
        ], optional
            Default optical property parameters to apply.
        """
        BaseVop.__init__(
            self,
            self._vop_template,
            self._material_instance,
            vop_parameters=default_parameters.vop_parameters,
            stable_ctr=True,
        )
        if isinstance(
            default_parameters.sop_parameters, (SopTypes, SopMirrorParameters, SopLibraryParameters)
        ):
            BaseSop.__init__(
                self,
                self._sop_template,
                self._material_instance,
                sop_parameters=default_parameters.sop_parameters,
                stable_ctr=True,
            )
        elif isinstance(default_parameters.sop_parameters, list):
            self._sop_template = None
            self.texture = [
                TextureLayer(self, f"Layer{i}", texture_layer_parameters=layer)
                for i, layer in enumerate(default_parameters.sop_parameters)
            ]

    @property
    def texture(self) -> Optional[list["TextureLayer"]]:
        """List of texture layers used in this material.

        Returns
        -------
        Optional[list[ansys.speos.core.opt_prop.TextureLayer]]
            Texture layers or ``None`` when not set.
        """
        return self._texture

    @texture.setter
    def texture(self, value: list["TextureLayer"]):
        """Set the texture layers.

        Parameters
        ----------
        value : list[ansys.speos.core.opt_prop.TextureLayer]
            List of texture layer objects to assign.

        Raises
        ------
        ValueError
            If any element in ``value`` is not a TextureLayer instance.
        """
        for layer in value:
            if not isinstance(layer, TextureLayer):
                raise ValueError("not a texture")
        self._sop_template = None
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
        geometries : Optional[list[Union[\
                ansys.speos.core.geo_ref.GeoRef, \
                ansys.speos.core.body.Body, \
                ansys.speos.core.face.Face, \
                ansys.speos.core.part.Part.SubPart, \
            ]]]
            Geometry references, ansys.speos.core.geo_ref.GeoRef instances,
            Body instances, Face instances,
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

    def _create_texture_layer_by_parameters(
        self,
        name: str,
        description: str = "",
        default_parameters: Optional[TextureLayerParameters] = TextureLayerParameters(),
    ) -> "TextureLayer":
        """Create a new texture layer with the provided parameters.

        Parameters
        ----------
        name : str
            Name of the texture layer.
        description : str, optional
            Description of the texture layer. Default is an empty string.
        default_parameters : Optional[\
            ansys.speos.core.generic.parameters.TextureLayerParameters\
        ], optional
            Default parameters for the texture layer. Default is an empty TextureLayerParameters.
        """
        if self._texture is None:
            self._texture = []
            if self._sop_template is not None:
                self.sop_template = None
        new_layer = TextureLayer(
            opt_prop=self,
            name=name,
            description=description,
            default_parameters=default_parameters,
        )
        new_layer._index = len(self._texture)
        self._texture.append(new_layer)
        return new_layer

    def create_texture_layer(self) -> "TextureLayer":
        """Create a new texture layer with default parameters and a default name.

        The default name is generated as "LayerX" where X is the index of the
        layer in the texture list.

        Returns
        -------
        ansys.speos.core.opt_prop.TextureLayer
            The newly created texture layer.
        """
        layer_name = f"Layer{len(self._texture) if self._texture else 0}"
        return self._create_texture_layer_by_parameters(name=layer_name)

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
            if self._sop_template is not None:
                self._sop_template = None
            self._material_instance.texture.ClearField("layers")
            layers = []
            for i, layer in enumerate(self.texture):
                layers.append(layer._texture_template)
                layer._index = i
                # Commit each layer to ensure sop templates are created/updated on the server
                layer._commit()
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
            if self._vop_template.HasField("library"):
                self.set_volume_library()

        # Reset sop template
        if self.sop_template_link is not None:
            self._sop_template = self.sop_template_link.get()
            self._sync_sop_properties()
        else:
            self._sync_sop_properties()

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
                if self._material_instance.HasField("texture"):
                    layers = []
                    for i, layer in enumerate(self._material_instance.texture.layers):
                        temp_layer = TextureLayer(self, name="")
                        temp_layer._fill(layer.sop_guid, layer)
                        temp_layer._index = i
                        temp_layer._reset()
                        layers.append(temp_layer)
                    self.texture = layers
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
        mat_inst : ansys.speos.core.kernel.scene.ProtoScene.MaterialInstance
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
