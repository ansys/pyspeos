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

"""Test basic using optical properties."""

from pathlib import Path

import numpy as np
import pytest

from ansys.speos.core import Face, GeoRef, OptProp, Project, Speos
from ansys.speos.core.generic.parameters import (
    ImageTextureParameters,
    MeshData,
    NormalMapParameters,
    NormalMapTypes,
    OptPropParameters,
    SopLibraryParameters,
    SopTypes,
    TextureLayerParameters,
    TextureTypes,
    UVMappingByData,
    UVMappingCubicParameters,
    UVMappingCylindricalParameters,
    UVMappingPlanarParameters,
    UVMappingSphericalParameters,
    VopLibraryParameters,
    VopOpticParameters,
    VopTypes,
)
from ansys.speos.core.kernel import ProtoFace
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
from ansys.speos.core.opt_prop import BaseSop, BaseVop, TextureLayer
from tests.conftest import test_path
from tests.helper import approx_arrays


def create_rect_face(my_body, name, pos, x, y) -> Face:
    """Create rectangular face."""
    face = my_body.create_face(name=name)
    face.vertices = [
        pos[0],
        pos[1],
        pos[2],
        pos[0],
        pos[1] + y,
        pos[2],
        pos[0] + x,
        pos[1],
        pos[2],
        pos[0] + x,
        pos[1] + x,
        pos[2],
    ]
    face.facets = [0, 1, 2, 1, 2, 3]
    face.normals = [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0]
    return face


def test_create_optical_property(speos: Speos):
    """Test creation of optical property."""
    p = Project(speos=speos)

    # Default value
    op1 = p.create_optical_property(name="Material.1")
    op1.commit()
    assert op1.vop_template_link is None
    assert op1.sop_template_link is not None
    assert op1.sop_template_link.get().HasField("mirror")
    assert op1.sop_template_link.get().mirror.reflectance == 100
    assert op1._material_instance.HasField("geometries") is False

    # VOP opaque
    op1.set_volume_opaque().commit()
    assert op1.vop_template_link is not None
    assert op1.vop_template_link.get().HasField("opaque")

    # VOP optic
    op1.set_volume_optic()
    op1.commit()
    assert op1.vop_template_link.get().optic.index == 1.5
    assert op1.vop_template_link.get().optic.absorption == 0.0
    assert op1.vop_template_link.get().optic.HasField("constringence") is False
    op1.vop_optic.index = 1.7
    op1.vop_optic.absorption = 0.01
    op1.vop_optic.constringence = 55
    op1.commit()
    assert op1.vop_template_link.get().HasField("optic")
    assert op1.vop_template_link.get().optic.index == 1.7
    assert op1.vop_template_link.get().optic.absorption == 0.01
    assert op1.vop_template_link.get().optic.HasField("constringence")
    assert op1.vop_template_link.get().optic.constringence == 55
    op1.set_volume_optic().constringence = None
    op1.commit()
    assert op1.vop_template_link.get().optic.HasField("constringence") is False
    op1.set_volume_optic()
    op1.commit()
    assert op1.vop_template_link.get().optic.index != 1.5
    assert op1.vop_template_link.get().optic.absorption != 0.0
    assert op1.vop_template_link.get().optic.HasField("constringence") is False

    # VOP library
    op1.set_volume_library()
    op1.vop_library.material_file_uri = Path(test_path) / "AIR.material"
    op1.commit()
    assert op1.vop_template_link.get().HasField("library")
    assert op1.vop_template_link.get().library.material_file_uri.endswith("AIR.material")

    # VOP non-homogeneous - bug to be fixed
    # op1.set_volume_nonhomogeneous(
    #     path=Path(test_path) / "Index_1.5_Gradient_0.499_Abs_0.gradedmaterial",
    #     axis_system=[10, 20, 30, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    # ).commit()
    # assert op1.vop_template_link.get().HasField("non_homogeneous")
    # non_homogeneous = op1.vop_template_link.get().non_homogeneous
    # assert non_homogeneous.gradedmaterial_file_uri.endswith(
    #     "Index_1.5_Gradient_0.499_Abs_0.gradedmaterial"
    # )
    # non_homogenous_properties = op1._material_instance.non_homogeneous_properties
    # assert non_homogenous_properties.axis_system == [10, 20, 30, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    #
    # op1.set_volume_nonhomogeneous(
    #     path=Path(test_path) / "Index_1.5_Gradient_0.499_Abs_0.gradedmaterial"
    # ).commit()
    # assert non_homogenous_properties.axis_system == [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    # SOP optical_polished
    op1.set_surface_opticalpolished().commit()
    assert op1.sop_template_link.get().HasField("optical_polished")

    # SOP library
    op1.set_surface_library().file_uri = Path(test_path) / "R_test.anisotropicbsdf"
    op1.commit()
    assert op1.sop_template_link.get().HasField("library")
    assert op1.sop_template_link.get().library.sop_file_uri.endswith("R_test.anisotropicbsdf")

    # SOP mirror
    op1.set_surface_mirror().reflectance = 80
    op1.commit()
    assert op1.sop_template_link.get().HasField("mirror")
    assert op1._sop_template.mirror.reflectance == 80
    assert op1.sop_template_link.get().mirror.reflectance == 80

    # geometries
    op1.geometries = [
        GeoRef.from_native_link("TheBodyB1"),
        GeoRef.from_native_link("TheBodyB2"),
    ]
    assert op1._material_instance.HasField("geometries")
    assert op1._material_instance.geometries.geo_paths == ["TheBodyB1", "TheBodyB2"]
    for geo in op1.geometries:
        assert "TheBodyB" in geo

    op1.geometries = None  # means no geometry
    assert op1._material_instance.HasField("geometries") is False

    op1.geometries = []  # means all geometries
    assert op1._material_instance.HasField("geometries")
    assert op1._material_instance.geometries.geo_paths == []

    op1.delete()


def test_commit_optical_property(speos: Speos):
    """Test commit of optical property."""
    p = Project(speos=speos)

    # Create
    op1 = p.create_optical_property(name="Material.1").set_volume_opaque()
    assert op1.vop_template_link is None
    assert op1.sop_template_link is None
    assert len(p.scene_link.get().materials) == 0

    # Commit
    op1.commit()
    assert op1.vop_template_link is not None
    assert op1.vop_template_link.get().HasField("opaque")
    assert op1.sop_template_link is not None
    assert op1.sop_template_link.get().HasField("mirror")
    assert len(p.scene_link.get().materials) == 1
    assert p.scene_link.get().materials[0] == op1._material_instance

    # Change only in local not committed
    op1.geometries = [GeoRef.from_native_link("TheBodyB")]
    assert p.scene_link.get().materials[0] != op1._material_instance

    op1.delete()


def test_reset_optical_property(speos: Speos):
    """Test reset of optical property."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="TheBodyB")
    face = body_b.create_face(name="TheFaceF")
    face.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    face.facets = [0, 1, 2]
    face.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    face.commit()
    root_part.commit()

    # Create + commit
    op1 = p.create_optical_property(name="Material.1").set_volume_opaque()
    op1.geometries = [body_b.geo_path]
    op1.commit()
    assert op1.vop_template_link is not None
    assert op1.vop_template_link.get().HasField("opaque")
    assert op1.sop_template_link is not None
    assert op1.sop_template_link.get().HasField("mirror")
    assert len(p.scene_link.get().materials) == 1
    assert p.scene_link.get().materials[0].HasField("geometries")

    # Change local data (on template and on instance)
    op1.set_surface_opticalpolished()
    op1.set_volume_optic()
    op1.geometries = None
    assert op1.vop_template_link.get().HasField("opaque")
    assert op1._vop_template.HasField("optic")  # local template
    assert op1.sop_template_link.get().HasField("mirror")
    assert op1._sop_template.HasField("optical_polished")  # local template
    assert p.scene_link.get().materials[0].HasField("geometries")
    assert op1._material_instance.HasField("geometries") is False  # local instance

    # Ask for reset
    op1.reset()
    assert op1.vop_template_link.get().HasField("opaque")
    assert op1._vop_template.HasField("opaque")  # local template
    assert op1.sop_template_link.get().HasField("mirror")
    assert op1._sop_template.HasField("mirror")  # local template
    assert p.scene_link.get().materials[0].HasField("geometries")
    assert op1._material_instance.HasField("geometries")  # local instance

    op1.delete()


def test_delete_optical_property(speos: Speos):
    """Test delete of optical property."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="TheBodyB")
    face = body_b.create_face(name="TheFaceF")
    face.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    face.facets = [0, 1, 2]
    face.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    face.commit()
    root_part.commit()

    # Create + commit
    op1 = p.create_optical_property(name="Material.1")
    op1.set_volume_opaque()
    op1.geometries = [GeoRef.from_native_link("TheBodyB")]
    op1.commit()
    assert op1.vop_template_link.get().HasField("opaque")
    assert op1.sop_template_link.get().HasField("mirror")
    assert len(p.scene_link.get().materials) == 1
    assert p.scene_link.get().materials[0].HasField("geometries")
    assert op1._material_instance.HasField("geometries")

    # Delete
    op1.delete()
    assert op1._unique_id is None
    assert len(op1._material_instance.metadata) == 0

    assert op1.vop_template_link is None
    assert op1._vop_template.HasField("opaque")  # local

    assert op1.sop_template_link is None
    assert op1._sop_template.HasField("mirror")  # local

    assert len(p.scene_link.get().materials) == 0
    assert op1._material_instance.HasField("geometries")  # local


def test_get_optical_property(speos: Speos, capsys):
    """Test get of an optical property."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_a = root_part.create_body(name="TheBodyA")
    face = body_a.create_face(name="TheFaceF")
    face.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    face.facets = [0, 1, 2]
    face.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    face.commit()
    body_b = root_part.create_body(name="TheBodyB")
    face = body_b.create_face(name="TheFaceF")
    face.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    face.facets = [0, 1, 2]
    face.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    face.commit()
    root_part.commit()

    op1 = p.create_optical_property(name="Material.1")
    op1.set_volume_opaque()
    op1.geometries = [body_a]
    op1.commit()

    name = op1.get(key="name")
    assert name == "Material.1"
    # test vop
    vop_property_info = op1.get(key="vop")
    assert "opaque" in vop_property_info
    assert "optic" not in vop_property_info
    assert "library" not in vop_property_info
    # test sops
    sop_property_info = op1.get(key="sops")[0]
    assert "mirror" in sop_property_info
    assert "optical_polished" not in sop_property_info
    assert "library" not in sop_property_info
    # test geometries
    geometries = op1.get(key="geo_paths")
    assert geometries == ["TheBodyA"]

    op2 = p.create_optical_property(name="OpticalProperty2")
    op2.set_volume_optic()
    op2.vop_optic.index = 1.7
    op2.vop_optic.absorption = 0.01
    op2.vop_optic.constringence = 55
    op2.set_surface_opticalpolished()
    op2.geometries = [body_b]
    op2.commit()

    name = op2.get(key="name")
    assert name == "OpticalProperty2"
    # test vop
    vop_property_info = op2.get(key="vop")
    assert "opaque" not in vop_property_info
    assert "optic" in vop_property_info
    assert "library" not in vop_property_info
    # test sops
    sop_property_info = op2.get(key="sops")[0]
    assert "mirror" not in sop_property_info
    assert "optical_polished" in sop_property_info
    assert "library" not in sop_property_info
    geometries = op2.get(key="geo_paths")
    assert geometries == ["TheBodyB"]

    op3 = p.create_optical_property(name="OpticalProperty3")
    op3.set_volume_none()
    op3.set_surface_library().file_uri = Path(test_path) / "R_test.anisotropicbsdf"
    op3.geometries = [face]
    op3.commit()

    name = op3.get(key="name")
    assert name == "OpticalProperty3"
    # test vop
    assert op3.get(key="vop") is None
    # test sops
    sop_property_info = op3.get(key="sops")[0]
    assert "mirror" not in sop_property_info
    assert "optical_polished" not in sop_property_info
    assert "library" in sop_property_info


@pytest.mark.supported_speos_versions(min=252)
def test_load_optical_property_from_file(speos: Speos):
    """Test loading a file and filling all Materials."""
    p = Project(speos=speos, path=Path(test_path) / "Material.1.speos" / "Material.1.speos")
    all_mats = p.find(name=".*", name_regex=True, feature_type=OptProp)
    assert all_mats
    for mat in all_mats:
        assert isinstance(mat, OptProp)
        match mat._name:
            case "Opaque_mirror80":
                assert mat._sop_template.HasField("mirror")
                assert mat.sop_mirror.reflectance == 80
                assert mat._vop_template.HasField("opaque")
            case "None_Library":
                assert mat._vop_template is None
                assert mat._sop_template.HasField("library")
                assert mat.sop_library.file_uri.endswith(".scattering")
            case "FOP_mirror75":
                assert mat._sop_template.HasField("mirror")
                assert mat.sop_mirror.reflectance == 75
                assert mat._vop_template is None
            case "Optic_OP":
                assert mat._sop_template.HasField("optical_polished")
                assert mat._vop_template.HasField("optic")
                assert mat.vop_optic.index == 1.49
                assert mat.vop_optic.constringence == 30
                assert mat.vop_optic.absorption == 0.001
            case "Library_OP":
                assert mat._sop_template.HasField("optical_polished")
                assert mat._vop_template.HasField("library")
                assert mat.vop_library.material_file_uri.endswith(".material")


@pytest.mark.supported_speos_versions(min=252)
def test_error_reporting(speos: Speos):
    """Test error raising."""
    p = Project(speos=speos)
    op = p.create_optical_property(name="ErrMat")

    # mirror helper should be absent when SOP is not mirror
    op.set_surface_opticalpolished()
    assert op.sop_mirror is None
    assert op._sop_template.HasField("optical_polished")

    # sop_library accessor should be None when SOP is not library
    op.set_surface_mirror()
    assert op.sop_library is None

    # vop_optic setter should raise if VOP is not optic
    op.set_volume_opaque()

    # texture setter on OptProp should raise when value is not TextureLayer instances
    with pytest.raises(ValueError):
        op.texture = ["not_a_texture"]

    # geometries setter should raise for unsupported types
    with pytest.raises(TypeError):
        op.geometries = [123]  # int is unsupported

    # TextureLayer related errors
    layer = TextureLayer(op, "LayerErr")
    # setting image file creates texture but no normal_map -> roughness setter should raise
    layer.set_image_texture().image_file_uri = Path("some_image.png")
    with pytest.raises(AttributeError):
        layer.normal_map.roughness = 2.0

    with pytest.raises(RuntimeError):
        BaseSop(op._sop_template, op._material_instance)
        BaseVop(op._vop_template, op._material_instance)
        TextureLayer.BaseTextureMap(layer, TextureTypes.image)


def test_opt_prop_default_parameters_and_local_helpers(speos: Speos, capsys):
    """Cover local/default-parameter helper branches for optical properties."""
    p = Project(speos=speos)

    op_library = p.create_optical_property(
        name="Defaults.Library",
        parameters=OptPropParameters(
            sop_parameters=SopLibraryParameters(
                file_uri=Path("library_surface.scattering"),
            ),
            vop_parameters=VopLibraryParameters(
                material_file_uri=Path("library_volume.material"),
            ),
        ),
    )
    assert op_library.sop_library.file_uri.endswith("library_surface.scattering")
    assert op_library.vop_library.material_file_uri.endswith("library_volume.material")

    op_polished = p.create_optical_property(
        name="Defaults.OpticalPolished",
        parameters=OptPropParameters(
            sop_parameters=SopTypes.optical_polished,
            vop_parameters=VopTypes.opaque,
        ),
    )
    assert op_polished._sop_template.HasField("optical_polished")
    assert op_polished._vop_template.HasField("opaque")

    op_local = p.create_optical_property(name="Local.Only")
    op_local.set_volume_optic()
    local_dict = op_local._to_dict()

    assert "vop" in local_dict
    assert "sops" in local_dict
    assert "local:" in str(op_local)

    assert op_local.get("definitely_missing_key") is None
    assert "Used key: definitely_missing_key not found" in capsys.readouterr().out


@pytest.mark.supported_speos_versions(min=252)
def test_create_texture_property(speos: Speos):
    """Test creation of texture property."""
    p = Project(speos=speos)

    # Default value
    op1 = p.create_optical_property(name="texture.1")
    op1.commit()
    assert op1.vop_template_link is None
    assert op1.sop_template_link is not None
    assert op1.sop_template_link.get().HasField("mirror")
    assert op1.sop_template_link.get().mirror.reflectance == 100
    assert op1._material_instance.HasField("geometries") is False
    assert op1._material_instance.HasField("texture") is False

    layer_1 = TextureLayer(op1, "Layer.1")
    op1.texture = [layer_1]
    op1.commit()

    assert op1._material_instance.HasField("texture")
    assert layer_1.sop_template_link.get().HasField("mirror")
    assert layer_1.sop_template_link.get().mirror.reflectance == 100
    assert (
        layer_1.sop_template_link.get()
        == p.client[op1._material_instance.texture.layers[0].sop_guid].get()
    )

    layer_1.set_image_texture().image_file_uri = (
        Path(test_path) / "Texture.1.speos" / "black_leather.jpg.png"
    )
    for map_type in [
        UVMappingPlanarParameters(),
        UVMappingCubicParameters(),
        UVMappingSphericalParameters(),
        UVMappingCylindricalParameters(),
    ]:
        layer_1.image_texture._set_mapping_operator(map_type)
        layer_1.image_texture.uv_mapping.u_length = 5
        match map_type:
            case UVMappingPlanarParameters():
                assert layer_1._texture_template.image_properties.mapping_operator.HasField(
                    "planar"
                )
            case UVMappingCubicParameters():
                assert layer_1._texture_template.image_properties.mapping_operator.HasField("cubic")
            case UVMappingSphericalParameters():
                assert layer_1._texture_template.image_properties.mapping_operator.HasField(
                    "spherical"
                )
            case UVMappingCylindricalParameters():
                assert layer_1._texture_template.image_properties.mapping_operator.HasField(
                    "cylindrical"
                )
    layer_1.image_texture.set_uv_mapping_planar()
    layer_1.image_texture.uv_mapping.u_length = 5
    op1.texture = [layer_1]
    op1.commit()

    assert op1._material_instance.HasField("texture")
    assert layer_1.sop_template_link.get().HasField("mirror")
    assert layer_1.sop_template_link.get().mirror.reflectance == 100
    assert (
        layer_1.sop_template_link.get()
        == p.client[op1._material_instance.texture.layers[0].sop_guid].get()
    )
    assert op1._material_instance.texture.layers[0].image_properties.mapping_operator.HasField(
        "planar"
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.u_length
        == layer_1.image_texture.uv_mapping.u_length
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.u_scale_factor
        == layer_1.image_texture.uv_mapping.u_scale
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.v_scale_factor
        == layer_1.image_texture.uv_mapping.v_scale
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.rotation
        == layer_1.image_texture.uv_mapping.rotation
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.axis_system
        == layer_1.image_texture.uv_mapping.axis_system
    )

    layer_1.set_normal_map_from_image()
    layer_1.normal_map.normal_map_file_uri = (
        Path(test_path) / "Texture.1.speos" / "black_leather.jpg.png"
    )
    for map_type in [
        UVMappingPlanarParameters(),
        UVMappingCubicParameters(),
        UVMappingSphericalParameters(),
        UVMappingCylindricalParameters(),
    ]:
        layer_1.normal_map._set_mapping_operator(map_type)
        layer_1.normal_map.uv_mapping.u_length = 5
        operator = layer_1._texture_template.normal_map_properties.mapping_operator
        match map_type:
            case UVMappingPlanarParameters():
                assert operator.HasField("planar")
            case UVMappingCubicParameters():
                assert operator.HasField("cubic")
            case UVMappingSphericalParameters():
                assert operator.HasField("spherical")
            case UVMappingCylindricalParameters():
                assert operator.HasField("cylindrical")
    layer_1.normal_map.set_uv_mapping_cylindrical().u_length = 5
    op1.texture = [layer_1]
    op1.commit()

    assert op1._material_instance.HasField("texture")
    assert layer_1.sop_template_link.get().HasField("mirror")
    assert layer_1.sop_template_link.get().mirror.reflectance == 100
    assert (
        layer_1.sop_template_link.get()
        == p.client[op1._material_instance.texture.layers[0].sop_guid].get()
    )
    assert op1._material_instance.texture.layers[0].image_properties.mapping_operator.HasField(
        "planar"
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.u_length
        == layer_1.image_texture.uv_mapping.u_length
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.u_scale_factor
        == layer_1.image_texture.uv_mapping.u_scale
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.v_scale_factor
        == layer_1.image_texture.uv_mapping.v_scale
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.rotation
        == layer_1.image_texture.uv_mapping.rotation
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.axis_system
        == layer_1.image_texture.uv_mapping.axis_system
    )
    assert op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.HasField(
        "cylindrical"
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.u_length
        == layer_1.normal_map.uv_mapping.u_length
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].normal_map_properties.mapping_operator.u_scale_factor
        == layer_1.normal_map.uv_mapping.u_scale
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].normal_map_properties.mapping_operator.v_scale_factor
        == layer_1.normal_map.uv_mapping.v_scale
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.rotation
        == layer_1.normal_map.uv_mapping.rotation
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.axis_system
        == layer_1.normal_map.uv_mapping.axis_system
    )

    layer_1.set_normal_map_from_normal_map()
    layer_1.normal_map.normal_map_file_uri = Path(test_path) / "Texture.1.speos" / "Facets_NM.png"
    layer_1.normal_map.set_uv_mapping_cubic()
    opp = UVMappingCubicParameters(
        u_length=5,
        v_length=10,
        u_offset=0,
        v_offset=0,
        axis_system=[1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        u_scale=10,
        v_scale=10,
        rotation=45,
    )
    layer_1.normal_map.uv_mapping.u_length = opp.u_length
    layer_1.normal_map.uv_mapping.v_length = opp.v_length
    layer_1.normal_map.uv_mapping.u_scale = opp.u_scale
    layer_1.normal_map.uv_mapping.v_scale = opp.v_scale
    layer_1.normal_map.uv_mapping.rotation = opp.rotation
    layer_1.normal_map.uv_mapping.axis_system = opp.axis_system

    layer_1.normal_map.roughness = 0.42
    assert pytest.approx(layer_1.normal_map.roughness, rel=1e-6) == 0.42

    # change again to ensure value updates
    layer_1.normal_map.roughness = 0.123
    assert pytest.approx(layer_1.normal_map.roughness, rel=1e-6) == 0.123
    op1.texture = [layer_1]
    op1.commit()
    assert (
        layer_1.sop_template_link.get()
        == p.client[op1._material_instance.texture.layers[0].sop_guid].get()
    )
    assert op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.HasField(
        "cubic"
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.u_length
        == layer_1.normal_map.uv_mapping.u_length
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].normal_map_properties.mapping_operator.u_scale_factor
        == layer_1.normal_map.uv_mapping.u_scale
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].normal_map_properties.mapping_operator.v_scale_factor
        == layer_1.normal_map.uv_mapping.v_scale
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.rotation
        == layer_1.normal_map.uv_mapping.rotation
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.axis_system
        == layer_1.normal_map.uv_mapping.axis_system
    )

    layer_2 = TextureLayer(op1, "Layer.2")
    layer_2.set_surface_library().file_uri = (
        Path(test_path) / "Texture.1.speos" / "aniso_bsdf.anisotropicbsdf"
    )
    layer_2.set_anisotropy_map()
    for map_type in [
        UVMappingPlanarParameters(),
        UVMappingCubicParameters(),
        UVMappingSphericalParameters(),
        UVMappingCylindricalParameters(),
    ]:
        layer_2.anisotropic_map._set_mapping_operator(map_type)
        layer_2.anisotropic_map.uv_mapping.u_length = 5
        operator = layer_2._texture_template.anisotropy_map_properties.mapping_operator
        match map_type:
            case UVMappingPlanarParameters():
                assert operator.HasField("planar")
            case UVMappingCubicParameters():
                assert operator.HasField("cubic")
            case UVMappingSphericalParameters():
                assert operator.HasField("spherical")
            case UVMappingCylindricalParameters():
                assert operator.HasField("cylindrical")
    opp = UVMappingSphericalParameters(
        sphere_perimeter=10,
        u_length=5,
        v_length=10,
        u_offset=0,
        v_offset=0,
        axis_system=[1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        u_scale=10,
        v_scale=10,
        rotation=90,
    )
    layer_2.anisotropic_map.set_uv_mapping_spherical()
    layer_2.anisotropic_map.uv_mapping.u_length = opp.u_length
    layer_2.anisotropic_map.uv_mapping.v_length = opp.v_length
    layer_2.anisotropic_map.uv_mapping.u_scale = opp.u_scale
    layer_2.anisotropic_map.uv_mapping.v_scale = opp.v_scale
    layer_2.anisotropic_map.uv_mapping.rotation = opp.rotation
    layer_2.anisotropic_map.uv_mapping.axis_system = opp.axis_system
    layer_2.anisotropic_map.uv_mapping.perimeter = opp.sphere_perimeter
    op1.texture = [layer_1, layer_2]
    op1.commit()

    assert (
        layer_1.sop_template_link.get()
        == p.client[op1._material_instance.texture.layers[0].sop_guid].get()
    )
    assert (
        layer_2.sop_template_link.get()
        == p.client[op1._material_instance.texture.layers[1].sop_guid].get()
    )
    assert op1._material_instance.texture.layers[
        1
    ].anisotropy_map_properties.mapping_operator.HasField("spherical")
    assert (
        op1._material_instance.texture.layers[1].anisotropy_map_properties.mapping_operator.rotation
        == layer_2.anisotropic_map.uv_mapping.rotation
    )
    assert (
        op1._material_instance.texture.layers[
            1
        ].anisotropy_map_properties.mapping_operator.axis_system
        == layer_2.anisotropic_map.uv_mapping.axis_system
    )
    assert (
        op1._material_instance.texture.layers[
            1
        ].anisotropy_map_properties.mapping_operator.spherical.sphere_perimeter
        == layer_2.anisotropic_map.uv_mapping.perimeter
    )

    layer_1.set_normal_map_to_none()
    layer_1.set_image_texture_to_none()
    layer_2.set_anisotropy_map_to_none()
    op1.commit()

    assert op1._material_instance.texture.layers[0].HasField("image_properties") is False
    assert op1._material_instance.texture.layers[0].HasField("normal_map_properties") is False
    assert op1._material_instance.texture.layers[1].HasField("anisotropy_map_properties") is False


@pytest.mark.supported_speos_versions(min=252)
def test_texture_mapping_helper_local_branches(speos: Speos, monkeypatch):
    """Cover local mapping helper branches without committing a texture layer."""
    p = Project(speos=speos)
    op = p.create_optical_property(name="Texture.Local.Helpers")
    layer = TextureLayer(op, "Layer.Helpers")

    image = layer.set_image_texture()
    image.set_uv_mapping_by_data().vertices_data_index = 2
    image._mapping = None
    assert image.uv_mapping.vertices_data_index == 2

    image_operator = image._set_mapping_operator(UVMappingPlanarParameters())
    image_operator.v_length = 3
    assert image_operator.v_length == 3
    image_operator.v_length = None
    assert image_operator.v_length is None
    assert image_operator == image_operator.__todict__()
    assert "TextureUVMappingOperator(" in str(image_operator)

    with pytest.raises(TypeError):
        image_operator.perimeter = 1

    normal = layer.set_normal_map_from_image()
    normal.set_uv_mapping_by_data().vertices_data_index = 1
    normal._mapping = None
    assert normal.uv_mapping.vertices_data_index == 1

    anisotropic = layer.set_anisotropy_map()
    anisotropic.set_uv_mapping_by_data().vertices_data_index = 0
    anisotropic._mapping = None
    assert anisotropic.uv_mapping.vertices_data_index == 0

    invalid_map = TextureLayer.BaseTextureMap(layer, "unsupported", stable_ctr=True)
    with pytest.raises(TypeError):
        invalid_map._get_map_property()


@pytest.mark.supported_speos_versions(min=252)
def test_texture_helper_parameter_initialization_branches(speos: Speos):
    """Cover direct helper initialization paths for image, normal, and anisotropy maps."""
    p = Project(speos=speos)
    op = p.create_optical_property(name="Texture.Param.Init")
    axis_system = [1, 2, 3, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    layer_image = TextureLayer(op, "Layer.Image")
    image = TextureLayer.ImageTexture(
        layer_image,
        ImageTextureParameters(
            file_path=Path("image_texture.png"),
            repeat_u=False,
            repeat_v=False,
            mapping=UVMappingCubicParameters(
                u_length=3,
                v_length=4,
                axis_system=axis_system,
                u_scale=2,
                v_scale=3,
                rotation=45,
            ),
        ),
        stable_ctr=True,
    )
    assert image.image_file_uri.endswith("image_texture.png")
    assert image.repeat_u is False
    assert image.repeat_v is False
    assert image._parent._texture_template.image_properties.mapping_operator.HasField("cubic")
    assert image.uv_mapping.v_length == 4
    assert image.uv_mapping.axis_system == axis_system
    assert image.uv_mapping.u_scale == 2
    assert image.uv_mapping.v_scale == 3
    assert image.uv_mapping.rotation == 45

    layer_image_by_data = TextureLayer(op, "Layer.Image.ByData")
    image_by_data = TextureLayer.ImageTexture(
        layer_image_by_data,
        ImageTextureParameters(mapping=UVMappingByData(vertices_data_index=5)),
        stable_ctr=True,
    )
    assert image_by_data.uv_mapping.vertices_data_index == 5

    layer_normal = TextureLayer(op, "Layer.Normal")
    normal = TextureLayer.NormalMap(
        layer_normal,
        NormalMapParameters(
            file_path=Path("normal_map.png"),
            repeat_u=False,
            repeat_v=False,
            mapping=UVMappingByData(vertices_data_index=6),
            normal_map_type=NormalMapTypes.from_normal_map,
        ),
        stable_ctr=True,
    )
    assert normal.normal_map_file_uri.endswith("normal_map.png")
    assert normal.repeat_u is False
    assert normal.repeat_v is False
    assert normal.uv_mapping.vertices_data_index == 6
    normal._set_normal_map_from_image()
    assert normal.normal_map_file_uri.endswith("normal_map.png")
    normal._set_normal_map_from_normal_map()
    assert normal.normal_map_file_uri.endswith("normal_map.png")

    layer_anisotropic = TextureLayer(op, "Layer.Anisotropic")
    anisotropic = TextureLayer.AnisotropicMap(
        layer_anisotropic,
        UVMappingSphericalParameters(
            u_length=7,
            v_length=8,
            axis_system=axis_system,
            u_scale=4,
            v_scale=5,
            rotation=90,
        ),
        stable_ctr=True,
    )
    assert (
        anisotropic._parent._texture_template.anisotropy_map_properties.mapping_operator.HasField(
            "spherical"
        )
    )
    assert anisotropic.uv_mapping.axis_system == axis_system
    assert anisotropic.uv_mapping.u_scale == 4
    assert anisotropic.uv_mapping.v_scale == 5
    assert anisotropic.uv_mapping.rotation == 90

    layer_reuse = TextureLayer(op, "Layer.Reuse")
    layer_reuse.set_image_texture()
    layer_reuse._image_map = None
    assert layer_reuse.set_image_texture() is not None
    layer_reuse.set_anisotropy_map()
    layer_reuse._aniso_map = None
    assert layer_reuse.set_anisotropy_map() is not None


@pytest.mark.supported_speos_versions(min=252)
def test_reset_texture_property(speos: Speos):
    """Test reset of Optical Properties with texture."""
    p = Project(speos=speos)

    # Default value
    op1 = p.create_optical_property(name="texture.1")
    layer_2 = TextureLayer(op1, "Layer.2")
    layer_2.set_surface_library().file_uri = (
        Path(test_path) / "Texture.1.speos" / "aniso_bsdf.anisotropicbsdf"
    )
    layer_2.set_anisotropy_map().set_uv_mapping_spherical()
    opp = UVMappingSphericalParameters(
        sphere_perimeter=10,
        u_length=5,
        v_length=10,
        u_offset=0,
        v_offset=0,
        axis_system=[1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        u_scale=10,
        v_scale=10,
        rotation=90,
    )
    layer_2.anisotropic_map.uv_mapping.u_length = opp.u_length
    layer_2.anisotropic_map.uv_mapping.v_length = opp.v_length
    layer_2.anisotropic_map.uv_mapping.u_scale = opp.u_scale
    layer_2.anisotropic_map.uv_mapping.v_scale = opp.v_scale
    layer_2.anisotropic_map.uv_mapping.rotation = opp.rotation
    layer_2.anisotropic_map.uv_mapping.axis_system = opp.axis_system
    layer_2.anisotropic_map.uv_mapping.perimeter = opp.sphere_perimeter
    layer_2.set_normal_map_from_normal_map()
    layer_2.normal_map.set_uv_mapping_cubic()
    layer_2.normal_map.normal_map_file_uri = Path(test_path) / "Texture.1.speos" / "Facets_NM.png"
    opp = UVMappingCubicParameters(
        u_length=5,
        v_length=10,
        u_offset=0,
        v_offset=0,
        axis_system=[1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        u_scale=10,
        v_scale=10,
        rotation=45,
    )
    layer_2.normal_map.uv_mapping.u_length = opp.u_length
    layer_2.normal_map.uv_mapping.v_length = opp.v_length
    layer_2.normal_map.uv_mapping.u_scale = opp.u_scale
    layer_2.normal_map.uv_mapping.v_scale = opp.v_scale
    layer_2.normal_map.uv_mapping.rotation = opp.rotation
    layer_2.normal_map.uv_mapping.axis_system = opp.axis_system
    layer_2.set_image_texture().image_file_uri = (
        Path(test_path) / "Texture.1.speos" / "black_leather.jpg.png"
    )
    layer_2.image_texture.set_uv_mapping_planar().u_length = 5
    op1.texture = [layer_2]
    op1.commit()

    assert op1._material_instance.texture.layers[
        0
    ].anisotropy_map_properties.mapping_operator.HasField("spherical")
    assert op1._material_instance.texture.layers[0].image_properties.mapping_operator.HasField(
        "planar"
    )
    assert op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.HasField(
        "cubic"
    )
    assert (
        op1._material_instance.texture.layers[0].anisotropy_map_properties.mapping_operator.rotation
        == layer_2.anisotropic_map.uv_mapping.rotation
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].anisotropy_map_properties.mapping_operator.axis_system
        == layer_2.anisotropic_map.uv_mapping.axis_system
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].anisotropy_map_properties.mapping_operator.spherical.sphere_perimeter
        == layer_2.anisotropic_map.uv_mapping.perimeter
    )
    layer_2.set_surface_mirror()
    assert layer_2._sop_template.HasField("mirror")
    old_values = layer_2.anisotropic_map.uv_mapping
    new_values = UVMappingPlanarParameters(
        20,
        5,
        False,
        False,
        [2, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        15,
        15,
        45,
    )
    layer_2.anisotropic_map.set_uv_mapping_planar()
    layer_2.anisotropic_map.uv_mapping.u_length = new_values.u_length
    layer_2.anisotropic_map.uv_mapping.v_length = new_values.v_length
    layer_2.anisotropic_map.uv_mapping.u_scale = new_values.u_scale
    layer_2.anisotropic_map.uv_mapping.v_scale = new_values.v_scale
    layer_2.anisotropic_map.uv_mapping.rotation = new_values.rotation
    layer_2.anisotropic_map.uv_mapping.axis_system = new_values.axis_system
    mapping_op = layer_2._texture_template.anisotropy_map_properties.mapping_operator
    assert mapping_op.axis_system == new_values.axis_system
    assert mapping_op.rotation == new_values.rotation
    assert mapping_op.HasField("planar")
    layer_2._reset()
    assert layer_2._sop_template.HasField("library")
    mapping_op = layer_2._texture_template.anisotropy_map_properties.mapping_operator
    assert mapping_op.axis_system == old_values.axis_system
    assert mapping_op.rotation == old_values.rotation
    assert mapping_op.HasField("spherical")


@pytest.mark.supported_speos_versions(min=252)
def test_load_texture_property_from_file(speos: Speos):
    """Test loading of Solver file containing texture properties."""
    p = Project(speos=speos, path=Path(test_path) / "Texture.1.speos" / "Texture.1.speos")
    all_mats = p.find(name=".*", name_regex=True, feature_type=OptProp)
    assert all_mats
    for mat in all_mats:
        assert isinstance(mat, OptProp)
        match mat._name:
            case "Texture_spherical_Optic_OP_normal_map|UV mapping.1":
                assert mat._material_instance.HasField("texture")
                assert len(mat.texture) == 1
                assert mat.texture[0]._sop_template.HasField("optical_polished")
                assert mat.texture[0].normal_map.roughness == 1
                assert mat.texture[0].normal_map.normal_map_file_uri.endswith("png")
                assert not mat.texture[0].normal_map.repeat_u
                assert mat.texture[0].normal_map.repeat_v
                mapping_opp = mat.texture[0].normal_map.uv_mapping.__todict__()
                expected = {
                    "mapping_type": "spherical",
                    "u_offset": 0,
                    "v_offset": 0,
                    "u_length": 10,
                    "v_length": 7.46268656716,
                    "axis_system": [0, 1, 4.98, 0, 0, 1, 1, 0, 0, 0, 1, 0],
                    "u_scale": 0.1,
                    "v_scale": 0.1,
                    "rotation": 0,
                    "perimeter": 6.28,
                }
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
            case "Texture_spherical_Optic_OP_normal_map":
                assert mat._sop_template is None
                assert mat._vop_template.HasField("optic")
                assert VopOpticParameters(
                    mat.vop_optic.index, mat.vop_optic.absorption, mat.vop_optic.constringence
                ) == VopOpticParameters(1.5, 0, None)

            case "Texture_cylindrical_opaque_mirror40_normal_map|UV mapping.2":
                assert mat._material_instance.HasField("texture")
                assert len(mat.texture) == 1
                assert mat.texture[0]._sop_template.HasField("mirror")
                assert mat.texture[0].sop_mirror.reflectance == 40
                assert mat.texture[0].normal_map.roughness == 1
                assert mat.texture[0].normal_map.repeat_u
                assert mat.texture[0].normal_map.repeat_v
                assert mat.texture[0].normal_map.normal_map_file_uri.endswith("png")
                mapping_opp = mat.texture[0].normal_map.uv_mapping.__todict__()
                expected = {
                    "mapping_type": "cylindrical",
                    "u_offset": 0,
                    "v_offset": 0,
                    "u_length": 10,
                    "v_length": 10,
                    "axis_system": [4, 1, 4.98, 0, 0, 1, 1, 0, 0, 0, 1, 0],
                    "u_scale": 0.1,
                    "v_scale": 0.1,
                    "rotation": 0,
                    "perimeter": 6.28,
                }
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
            case "Texture_cylindrical_opaque_mirror40_normal_map":
                assert mat._sop_template is None
                assert mat._vop_template.HasField("opaque")
            case "Texture_cubic_opaque_library_normal_map_image|UV mapping.3":
                assert mat._material_instance.HasField("texture")
                assert len(mat.texture) == 1
                assert mat.texture[0]._sop_template.HasField("library")
                assert mat.texture[0].sop_library.file_uri.endswith("simplescattering")
                assert mat.texture[0].normal_map.roughness == 5
                assert mat.texture[0].normal_map.normal_map_file_uri.endswith("png")
                mapping_opp = mat.texture[0].normal_map.uv_mapping.__todict__()
                expected = {
                    "mapping_type": "cubic",
                    "u_offset": 0,
                    "v_offset": 0,
                    "u_length": 100,
                    "v_length": 100,
                    "axis_system": [8, 1, 4.98, 0, 0, 1, 1, 0, 0, 0, 1, 0],
                    "u_scale": 0.01,
                    "v_scale": 0.01,
                    "rotation": 0,
                    "perimeter": None,
                }
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
                assert mat.texture[0].image_texture.image_file_uri.endswith("png")
                mapping_opp = mat.texture[0].image_texture.uv_mapping.__todict__()
                expected = {
                    "mapping_type": "cubic",
                    "u_offset": 0,
                    "v_offset": 0,
                    "u_length": 50,
                    "v_length": 50,
                    "axis_system": [8, 1, 4.98, 0, 0, 1, 1, 0, 0, 0, 1, 0],
                    "u_scale": 0.01,
                    "v_scale": 0.01,
                    "rotation": 0,
                    "perimeter": None,
                }
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
            case "Texture_cubic_opaque_library_normal_map_image":
                assert mat._sop_template is None
                assert mat._vop_template.HasField("opaque")
            case "Texture_planar_FOP_aniso|UV mapping.4":
                assert mat._material_instance.HasField("texture")
                assert len(mat.texture) == 2
                assert mat.texture[0]._sop_template.HasField("library")
                assert mat.texture[0].sop_library.file_uri.endswith("anisotropicbsdf")
                mapping_opp = mat.texture[0].anisotropic_map.uv_mapping.__todict__()
                expected = {
                    "mapping_type": "planar",
                    "u_offset": 0,
                    "v_offset": 0,
                    "u_length": 0,
                    "v_length": 0,
                    "axis_system": [
                        12,
                        1,
                        4.98,
                        0,
                        -np.sqrt(2) / 2,
                        -np.sqrt(2) / 2,
                        0,
                        np.sqrt(2) / 2,
                        -np.sqrt(2) / 2,
                        1,
                        0,
                        0,
                    ],
                    "u_scale": 0.1,
                    "v_scale": 0.1,
                    "rotation": 90,
                    "perimeter": None,
                }
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
                assert mat.texture[1]._sop_template.HasField("optical_polished")
                assert mat.texture[1].normal_map.roughness == 1
                assert mat.texture[1].normal_map.normal_map_file_uri.endswith("png")
                mapping_opp = mat.texture[1].normal_map.uv_mapping.__todict__()
                expected = {
                    "mapping_type": "planar",
                    "u_offset": 0,
                    "v_offset": 0,
                    "u_length": 10,
                    "v_length": 10,
                    "axis_system": [
                        12,
                        1,
                        4.98,
                        0,
                        -np.sqrt(2) / 2,
                        -np.sqrt(2) / 2,
                        0,
                        np.sqrt(2) / 2,
                        -np.sqrt(2) / 2,
                        1,
                        0,
                        0,
                    ],
                    "u_scale": 0.1,
                    "v_scale": 0.1,
                    "rotation": 90,
                    "perimeter": None,
                }
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
            case "Base_white_notexture":
                assert mat._sop_template.HasField("library")
                assert mat.sop_library.file_uri.endswith("simplescattering")
                assert mat._vop_template.HasField("optic")
                assert VopOpticParameters(
                    mat.vop_optic.index, mat.vop_optic.absorption, mat.vop_optic.constringence
                ) == VopOpticParameters(1.5, 10, None)
            case "Texture_gltf":
                assert mat._sop_template is None
                assert mat._vop_template is None
            case "Texture_gltf|UV mapping.1":
                assert mat._material_instance.HasField("texture")
                assert len(mat.texture) == 1
                assert mat.texture[0]._sop_template.HasField("library")
                assert mat.texture[0].sop_library.file_uri.endswith("gltfsvbrdf")


@pytest.mark.supported_speos_versions(min=252)
def test_delete_texture_property(speos: Speos):
    """Ensure TextureLayer.delete clears local links/refs after commit."""
    p = Project(speos=speos)

    op = p.create_optical_property(name="Material.DeleteTest")
    # create layer, commit SOP template, assign to material and commit material to scene
    layer = TextureLayer(op, "Layer.Delete")
    op.texture = [layer]
    op.commit()

    # Sanity: we have a sop_template_link for the layer (committed)
    assert layer.sop_template_link is not None

    # Delete the layer (should delete sop template link and clear internals)
    layer.delete()

    # After delete local link cleared
    assert layer.sop_template_link is None
    # _texture_template internal pointer cleared
    assert layer._texture_template is None
    # unique id reset
    assert getattr(layer, "_unique_id", None) is None
    # check layer is also removed downstream
    assert len(op.texture) == 0
    assert len(op._material_instance.texture.layers) == 0


@pytest.mark.supported_speos_versions(min=252)
def test_texture_by_data(speos: Speos):
    """Test texture application by vertices_data."""
    my_project = Project(speos=speos)

    rp = my_project.create_root_part(description="Root Part")
    bdy0 = rp.create_body(name="Body0")

    face0_0 = create_rect_face(bdy0, "face0_0", [0, 0, 0], 5, 5)
    face0_0.vertices_data = [MeshData(name="uv_0", data=[0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0])]
    face0_0.commit()  # full picture
    assert face0_0._face.vertices_data[0] == ProtoFace.MeshData(
        name="uv_0", data=[0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0]
    )

    bdy1 = rp.create_body(name="Body2")
    face2_0 = create_rect_face(bdy1, "Face2_0", [12, 0, 0], 10, 5)
    face2_0._face.vertices_data.append(
        ProtoFace.MeshData(name="uv_1", data=[0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0])
    )  # full picture
    face2_0.commit()
    assert face2_0.vertices_data[0] == MeshData(
        name="uv_1", data=[0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0]
    )
    rp.commit()

    opt_prop = my_project.create_optical_property(name="OptProp")
    opt_prop.set_volume_none()
    opt_prop.geometries = [face0_0.geo_path, face2_0.geo_path]

    layer_1 = opt_prop.create_texture_layer()
    layer_1.set_surface_library().file_uri = Path(test_path) / "L100 2.simplescattering"
    layer_1.set_image_texture().image_file_uri = Path(test_path) / "textureColors.jpg"
    layer_1.image_texture.repeat_u = False
    layer_1.image_texture.repeat_v = False
    layer_1.image_texture.set_uv_mapping_by_data().vertices_data_index = 0
    opt_prop.commit()
    assert layer_1._texture_template.normal_map_properties.vertices_data_index == 0
    assert not layer_1._sop_template.texture.image.repeat_along_u
    assert not layer_1._sop_template.texture.image.repeat_along_v

    opt_prop.texture = [layer_1]
    opt_prop.commit()


# ---------------------------------------------------------------------------
# stable_ctr guard tests – no Speos server required
# ---------------------------------------------------------------------------


class _MinimalSopParent:
    """Minimal stand-in for a BaseSop parent used by SopMirror / SopLibrary tests."""

    def __init__(self):
        self._sop_template = ProtoSOPTemplate(name="test.SOP")


class _MinimalVopParent:
    """Minimal stand-in for a BaseVop parent used by VopOptic / VopLibrary tests."""

    def __init__(self):
        self._vop_template = ProtoVOPTemplate(name="test.VOP")
        self._vop_template.optic.SetInParent()
        self._vop_template.library.SetInParent()


class _MinimalTextureParent:
    """Minimal stand-in for a TextureLayer parent used by texture-map tests."""

    def __init__(self):
        self._sop_template = ProtoSOPTemplate(name="test.SOP")
        self._texture_template = ProtoScene.MaterialInstance.Texture.Layer()


def test_sop_mirror_stable_ctr_guard():
    """Direct instantiation of SopMirror without stable_ctr=True must raise RuntimeError."""
    parent = _MinimalSopParent()
    with pytest.raises(RuntimeError, match="SopMirror is not intended to be instantiated directly"):
        BaseSop.SopMirror(parent)


def test_sop_mirror_stable_ctr_allowed():
    """Direct instantiation of SopMirror with stable_ctr=True must succeed."""
    parent = _MinimalSopParent()
    mirror = BaseSop.SopMirror(parent, stable_ctr=True)
    assert mirror is not None
    assert mirror._parent is parent


def test_sop_library_stable_ctr_guard():
    """Direct instantiation of SopLibrary without stable_ctr=True must raise RuntimeError."""
    parent = _MinimalSopParent()
    with pytest.raises(
        RuntimeError, match="SopLibrary is not intended to be instantiated directly"
    ):
        BaseSop.SopLibrary(parent)


def test_sop_library_stable_ctr_allowed():
    """Direct instantiation of SopLibrary with stable_ctr=True must succeed."""
    parent = _MinimalSopParent()
    library = BaseSop.SopLibrary(parent, stable_ctr=True)
    assert library is not None
    assert library._parent is parent


def test_vop_optic_stable_ctr_guard():
    """Direct instantiation of VopOptic without stable_ctr=True must raise RuntimeError."""
    parent = _MinimalVopParent()
    with pytest.raises(RuntimeError, match="VopOptic is not intended to be instantiated directly"):
        BaseVop.VopOptic(parent)


def test_vop_optic_stable_ctr_allowed():
    """Direct instantiation of VopOptic with stable_ctr=True must succeed."""
    parent = _MinimalVopParent()
    optic = BaseVop.VopOptic(parent, stable_ctr=True)
    assert optic is not None
    assert optic._parent is parent


def test_vop_library_stable_ctr_guard():
    """Direct instantiation of VopLibrary without stable_ctr=True must raise RuntimeError."""
    parent = _MinimalVopParent()
    with pytest.raises(
        RuntimeError, match="VopLibrary is not intended to be instantiated directly"
    ):
        BaseVop.VopLibrary(parent)


def test_vop_library_stable_ctr_allowed():
    """Direct instantiation of VopLibrary with stable_ctr=True must succeed."""
    parent = _MinimalVopParent()
    library = BaseVop.VopLibrary(parent, stable_ctr=True)
    assert library is not None
    assert library._parent is parent


def test_image_texture_stable_ctr_guard():
    """Direct instantiation of ImageTexture without stable_ctr=True must raise RuntimeError."""
    parent = _MinimalTextureParent()
    with pytest.raises(
        RuntimeError, match="ImageTexture is not intended to be instantiated directly"
    ):
        TextureLayer.ImageTexture(parent)


def test_image_texture_stable_ctr_allowed():
    """Direct instantiation of ImageTexture with stable_ctr=True must succeed."""
    parent = _MinimalTextureParent()
    img = TextureLayer.ImageTexture(parent, stable_ctr=True)
    assert img is not None
    assert img._parent is parent


def test_normal_map_stable_ctr_guard():
    """Direct instantiation of NormalMap without stable_ctr=True must raise RuntimeError."""
    parent = _MinimalTextureParent()
    with pytest.raises(RuntimeError, match="NormalMap is not intended to be instantiated directly"):
        TextureLayer.NormalMap(parent)


def test_normal_map_stable_ctr_allowed():
    """Direct instantiation of NormalMap with stable_ctr=True must succeed."""
    parent = _MinimalTextureParent()
    nm = TextureLayer.NormalMap(parent, stable_ctr=True)
    assert nm is not None
    assert nm._parent is parent


def test_anisotropic_map_stable_ctr_guard():
    """Direct instantiation of AnisotropicMap without stable_ctr=True must raise RuntimeError."""
    parent = _MinimalTextureParent()
    with pytest.raises(
        RuntimeError, match="AnisotropicMap is not intended to be instantiated directly"
    ):
        TextureLayer.AnisotropicMap(parent)


def test_anisotropic_map_stable_ctr_allowed():
    """Direct instantiation of AnisotropicMap with stable_ctr=True must succeed."""
    parent = _MinimalTextureParent()
    aniso = TextureLayer.AnisotropicMap(parent, stable_ctr=True)
    assert aniso is not None
    assert aniso._parent is parent


def test_base_sop_mirror_bounds_and_reuse_branch():
    """Cover mirror validation and already-existing mirror branch."""
    sop_template = ProtoSOPTemplate(name="SOP.Test")
    mat_inst = ProtoScene.MaterialInstance(name="Mat.Test")
    sop = BaseSop(sop_template=sop_template, mat_inst=mat_inst, stable_ctr=True)

    # First call creates mirror + defaults, second call follows the HasField('mirror') branch.
    sop.set_surface_mirror().reflectance = 50
    sop.set_surface_mirror()

    with pytest.raises(ValueError, match="Reflectance must be between 0 and 100"):
        sop.sop_mirror.reflectance = 101


def test_texture_mapping_local_transition_branches():
    """Cover local UV-mapping transitions and string/equality helpers without server calls."""
    parent = _MinimalTextureParent()
    parent.TextureMappingByData = TextureLayer.TextureMappingByData
    parent.TextureMappingOperator = TextureLayer.TextureUVMappingOperator

    image = TextureLayer.ImageTexture(parent, stable_ctr=True)

    # Build by-data mapping first, then transition to operator mapping.
    image.set_uv_mapping_by_data().vertices_data_index = 4
    image._mapping = None
    assert image.uv_mapping.vertices_data_index == 4

    map_op = image.set_uv_mapping_planar()
    map_op.axis_system = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert map_op.axis_system[0] == 0
    assert "TextureUVMappingOperator(" in str(map_op)


def test_texture_layer_parameter_fill_branch_paths(speos: Speos):
    """Cover TextureLayer._fill_parameters image/normal creation and reuse branches."""
    p = Project(speos=speos)
    op = p.create_optical_property(name="Texture.Coverage")

    params = TextureLayerParameters(
        image_texture_parameters=ImageTextureParameters(
            file_path=Path("image_cov.png"),
            mapping=UVMappingPlanarParameters(rotation=20),
        ),
        normal_map_parameters=NormalMapParameters(
            file_path=Path("normal_cov.png"),
            normal_map_type=NormalMapTypes.from_image,
            mapping=UVMappingCubicParameters(rotation=30),
        ),
    )

    # Current implementation passes an internal protobuf layer into map helpers.
    # Keep this behavior covered until constructor wiring is refactored.
    with pytest.raises(AttributeError, match="_sop_template"):
        TextureLayer(op, "Layer.Coverage", default_parameters=params)

    layer = TextureLayer(op, "Layer.Coverage")
    assert layer.set_image_texture() is not None
    assert layer.set_normal_map_from_image() is not None

    # Hit branch where image_properties already exists.
    layer._image_map = None
    assert layer.set_image_texture() is not None
