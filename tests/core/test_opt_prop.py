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
    MappingOperator,
    MappingTypes,
    MaterialOpticParameters,
    MeshData,
)
from ansys.speos.core.kernel import ProtoFace
from ansys.speos.core.opt_prop import TextureLayer
from tests.conftest import test_path
from tests.helper import approx_arrays


def create_rect_face(my_body, name, pos, x, y) -> Face:
    """Create rectangular face."""
    face = my_body.create_face(name=name)
    face.set_vertices(
        [
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
    )
    face.set_facets([0, 1, 2, 1, 2, 3])
    face.set_normals([0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0])
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
    op1.vop_library = Path(test_path) / "AIR.material"
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
    op1.set_surface_library()
    op1.sop_library = Path(test_path) / "R_test.anisotropicbsdf"
    op1.commit()
    assert op1.sop_template_link.get().HasField("library")
    assert op1.sop_template_link.get().library.sop_file_uri.endswith("R_test.anisotropicbsdf")

    # SOP mirror
    op1.set_surface_mirror()
    op1.sop_reflectance = 80
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
    (
        body_b.create_face(name="TheFaceF")
        .set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0])
        .set_facets([0, 1, 2])
        .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    )
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
    body_b.create_face(name="TheFaceF").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
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
    face = (
        body_a.create_face(name="TheFaceF")
        .set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0])
        .set_facets([0, 1, 2])
        .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    )
    body_b = root_part.create_body(name="TheBodyB")
    body_b.create_face(name="TheFaceF").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
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
    op3.set_surface_library()
    op3.sop_library = Path(test_path) / "R_test.anisotropicbsdf"
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
                assert mat.sop_type == "mirror"
                assert mat.sop_reflectance == 80
                assert mat.vop_type == "opaque"
            case "None_Library":
                assert mat.vop_type is None
                assert mat.sop_type == "library"
                assert mat.sop_library.endswith(".scattering")
            case "FOP_mirror75":
                assert mat.sop_type == "mirror"
                assert mat.sop_reflectance == 75
                assert mat.vop_type is None
            case "Optic_OP":
                assert mat.sop_type == "optical_polished"
                assert mat.vop_type == "optic"
                assert mat.vop_optic.index == 1.49
                assert mat.vop_optic.constringence == 30
                assert mat.vop_optic.absorption == 0.001
            case "Library_OP":
                assert mat.sop_type == "optical_polished"
                assert mat.vop_type == "library"
                assert mat.vop_library.endswith(".material")


@pytest.mark.supported_speos_versions(min=252)
def test_error_reporting(speos: Speos):
    """Test error raising."""
    p = Project(speos=speos)
    op = p.create_optical_property(name="ErrMat")

    # sop_reflectance setter should raise if SOP is not mirror
    op.set_surface_opticalpolished()
    with pytest.raises(TypeError):
        op.sop_reflectance = 50

    # sop_library setter should raise if SOP is not library
    op.set_surface_mirror()
    with pytest.raises(TypeError):
        op.sop_library = Path("somefile.scattering")

    # vop_optic setter should raise if VOP is not optic
    op.set_volume_opaque()

    # vop_library setter should raise if VOP is not library
    with pytest.raises(TypeError):
        op.vop_library = Path("somefile.material")

    # texture setter on OptProp should raise when value is not TextureLayer instances
    with pytest.raises(ValueError):
        op.texture = ["not_a_texture"]

    # geometries setter should raise for unsupported types
    with pytest.raises(TypeError):
        op.geometries = [123]  # int is unsupported

    # TextureLayer related errors
    layer = TextureLayer(op, "LayerErr")
    # setting image file creates texture but no normal_map -> roughness setter should raise
    layer.set_image_texture().image_texture_file_uri = Path("some_image.png")
    with pytest.raises(AttributeError):
        layer.normal_map.roughness = 2.0


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
    layer_1.commit()
    op1.texture = [layer_1]
    op1.commit()

    assert op1._material_instance.HasField("texture")
    assert layer_1.sop_template_link.get().HasField("mirror")
    assert layer_1.sop_template_link.get().mirror.reflectance == 100
    assert (
        layer_1.sop_template_link.get()
        == p.client[op1._material_instance.texture.layers[0].sop_guid].get()
    )

    layer_1.image_texture_file_uri = Path(test_path) / "Texture.1.speos" / "black_leather.jpg.png"
    for map_type in MappingTypes:
        layer_1.image_property = MappingOperator(map_type, 5)
        assert map_type == layer_1.image_property.mapping_type
    layer_1.image_property = MappingOperator("planar", 5)
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
        == layer_1.image_property.u_length
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.u_scale_factor
        == layer_1.image_property.u_scale
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.v_scale_factor
        == layer_1.image_property.v_scale
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.rotation
        == layer_1.image_property.rotation
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.axis_system
        == layer_1.image_property.axis_system
    )

    layer_1.set_normal_map_from_image()
    layer_1.normal_map_file_uri = Path(test_path) / "Texture.1.speos" / "black_leather.jpg.png"
    for map_type in MappingTypes:
        layer_1.normal_map_property = MappingOperator(map_type, 5)
        assert map_type == layer_1.normal_map_property.mapping_type
    layer_1.normal_map_property = MappingOperator("cylindrical", 5)
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
        == layer_1.image_property.u_length
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.u_scale_factor
        == layer_1.image_property.u_scale
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.v_scale_factor
        == layer_1.image_property.v_scale
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.rotation
        == layer_1.image_property.rotation
    )
    assert (
        op1._material_instance.texture.layers[0].image_properties.mapping_operator.axis_system
        == layer_1.image_property.axis_system
    )
    assert op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.HasField(
        "cylindrical"
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.u_length
        == layer_1.normal_map_property.u_length
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].normal_map_properties.mapping_operator.u_scale_factor
        == layer_1.normal_map_property.u_scale
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].normal_map_properties.mapping_operator.v_scale_factor
        == layer_1.normal_map_property.v_scale
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.rotation
        == layer_1.normal_map_property.rotation
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.axis_system
        == layer_1.normal_map_property.axis_system
    )

    layer_1.set_normal_map_from_normal_map()
    layer_1.normal_map_file_uri = Path(test_path) / "Texture.1.speos" / "Facets_NM.png"
    layer_1.normal_map_property = MappingOperator(
        "cubic", 5, 10, False, False, [1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1], 10, 10, 45
    )
    layer_1.roughness = 0.42
    assert pytest.approx(layer_1.roughness, rel=1e-6) == 0.42

    # change again to ensure value updates
    layer_1.roughness = 0.123
    assert pytest.approx(layer_1.roughness, rel=1e-6) == 0.123
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
        == layer_1.normal_map_property.u_length
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].normal_map_properties.mapping_operator.u_scale_factor
        == layer_1.normal_map_property.u_scale
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].normal_map_properties.mapping_operator.v_scale_factor
        == layer_1.normal_map_property.v_scale
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.rotation
        == layer_1.normal_map_property.rotation
    )
    assert (
        op1._material_instance.texture.layers[0].normal_map_properties.mapping_operator.axis_system
        == layer_1.normal_map_property.axis_system
    )

    layer_2 = TextureLayer(op1, "Layer.2")
    layer_2.set_surface_library()
    layer_2.sop_library = Path(test_path) / "Texture.1.speos" / "aniso_bsdf.anisotropicbsdf"
    for map_type in MappingTypes:
        layer_2.anisotropic_property = MappingOperator(map_type, 5)
        assert map_type == layer_2.anisotropic_property.mapping_type
    layer_2.anisotropic_property = MappingOperator(
        MappingTypes.spherical,
        5,
        10,
        False,
        False,
        [1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        10,
        10,
        90,
        10,
    )
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
        == layer_2.anisotropic_property.rotation
    )
    assert (
        op1._material_instance.texture.layers[
            1
        ].anisotropy_map_properties.mapping_operator.axis_system
        == layer_2.anisotropic_property.axis_system
    )
    assert (
        op1._material_instance.texture.layers[
            1
        ].anisotropy_map_properties.mapping_operator.spherical.sphere_perimeter
        == layer_2.anisotropic_property.perimeter
    )


@pytest.mark.supported_speos_versions(min=252)
def test_reset_texture_property(speos: Speos):
    """Test reset of Optical Properties with texture."""
    p = Project(speos=speos)

    # Default value
    op1 = p.create_optical_property(name="texture.1")
    layer_2 = TextureLayer(op1, "Layer.2")
    layer_2.set_surface_library()
    layer_2.sop_library = Path(test_path) / "Texture.1.speos" / "aniso_bsdf.anisotropicbsdf"
    layer_2.anisotropic_property = MappingOperator(
        MappingTypes.spherical,
        5,
        10,
        False,
        False,
        [1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        10,
        10,
        90,
        10,
    )
    layer_2.set_normal_map_from_normal_map()
    layer_2.normal_map_file_uri = Path(test_path) / "Texture.1.speos" / "Facets_NM.png"
    layer_2.normal_map_property = MappingOperator(
        "cubic", 5, 10, False, False, [1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1], 10, 10, 45
    )
    layer_2.image_texture_file_uri = Path(test_path) / "Texture.1.speos" / "black_leather.jpg.png"
    layer_2.image_property = MappingOperator("planar", 5)
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
        == layer_2.anisotropic_property.rotation
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].anisotropy_map_properties.mapping_operator.axis_system
        == layer_2.anisotropic_property.axis_system
    )
    assert (
        op1._material_instance.texture.layers[
            0
        ].anisotropy_map_properties.mapping_operator.spherical.sphere_perimeter
        == layer_2.anisotropic_property.perimeter
    )
    layer_2.set_surface_mirror()
    assert layer_2._sop_template.HasField("mirror")
    old_values = layer_2.anisotropic_property
    new_values = MappingOperator(
        MappingTypes.planar,
        20,
        5,
        False,
        False,
        [2, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        15,
        15,
        45,
        10,
    )
    layer_2.anisotropic_property = new_values
    mapping_op = layer_2._texture_template.anisotropy_map_properties.mapping_operator
    assert mapping_op.axis_system == new_values.axis_system
    assert mapping_op.rotation == new_values.rotation
    assert mapping_op.HasField(new_values.mapping_type)
    layer_2._reset()
    assert layer_2._sop_template.HasField("library")
    mapping_op = layer_2._texture_template.anisotropy_map_properties.mapping_operator
    assert mapping_op.axis_system == old_values.axis_system
    assert mapping_op.rotation == old_values.rotation
    assert mapping_op.HasField(old_values.mapping_type)


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
                mapping_opp = mat.texture[0].normal_map.mapping_properties.__todict__()
                expected = MappingOperator(
                    mapping_type=MappingTypes.spherical,
                    u_length=10,
                    v_length=7.46268656716,
                    axis_system=[0, 1, 4.98, 0, 0, 1, 1, 0, 0, 0, 1, 0],
                    u_offset=0,
                    v_offset=0,
                    u_scale=0.1,
                    v_scale=0.1,
                    perimeter=6.28,
                ).__dict__
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
            case "Texture_spherical_Optic_OP_normal_map":
                assert mat._sop_template is None
                assert mat.vop_type == "optic"
                assert MaterialOpticParameters(
                    mat.vop_optic.index, mat.vop_optic.absorption, mat.vop_optic.constringence
                ) == MaterialOpticParameters(1.5, 0, None)

            case "Texture_cylindrical_opaque_mirror40_normal_map|UV mapping.2":
                assert mat._material_instance.HasField("texture")
                assert len(mat.texture) == 1
                assert mat.texture[0]._sop_template.HasField("mirror")
                assert mat.texture[0].sop_reflectance == 40
                assert mat.texture[0].normal_map.roughness == 1
                assert mat.texture[0].normal_map.repeat_u
                assert mat.texture[0].normal_map.repeat_v
                assert mat.texture[0].normal_map.normal_map_file_uri.endswith("png")
                mapping_opp = mat.texture[0].normal_map.mapping_properties.__todict__()
                expected = MappingOperator(
                    mapping_type=MappingTypes.cylindrical,
                    u_length=10,
                    v_length=10,
                    axis_system=[4, 1, 4.98, 0, 0, 1, 1, 0, 0, 0, 1, 0],
                    u_offset=0,
                    v_offset=0,
                    u_scale=0.1,
                    v_scale=0.1,
                    perimeter=6.28,
                ).__dict__
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
            case "Texture_cylindrical_opaque_mirror40_normal_map":
                assert mat._sop_template is None
                assert mat.vop_type == "opaque"
            case "Texture_cubic_opaque_library_normal_map_image|UV mapping.3":
                assert mat._material_instance.HasField("texture")
                assert len(mat.texture) == 1
                assert mat.texture[0]._sop_template.HasField("library")
                assert mat.texture[0].sop_library.endswith("simplescattering")
                assert mat.texture[0].normal_map.roughness == 5
                assert mat.texture[0].normal_map.normal_map_file_uri.endswith("png")
                mapping_opp = mat.texture[0].normal_map.mapping_properties.__todict__()
                expected = MappingOperator(
                    mapping_type=MappingTypes.cubic,
                    u_length=100,
                    v_length=100,
                    axis_system=[8, 1, 4.98, 0, 0, 1, 1, 0, 0, 0, 1, 0],
                    u_offset=0,
                    v_offset=0,
                    u_scale=0.01,
                    v_scale=0.01,
                ).__dict__
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
                assert mat.texture[0].image_texture.image_file_uri.endswith("png")
                mapping_opp = mat.texture[0].image_texture.mapping_properties.__todict__()
                expected = MappingOperator(
                    mapping_type=MappingTypes.cubic,
                    u_length=50,
                    v_length=50,
                    axis_system=[8, 1, 4.98, 0, 0, 1, 1, 0, 0, 0, 1, 0],
                    u_offset=0,
                    v_offset=0,
                    u_scale=0.01,
                    v_scale=0.01,
                ).__dict__
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
            case "Texture_cubic_opaque_library_normal_map_image":
                assert mat._sop_template is None
                assert mat.vop_type == "opaque"
            case "Texture_planar_FOP_aniso|UV mapping.4":
                assert mat._material_instance.HasField("texture")
                assert len(mat.texture) == 2
                assert mat.texture[0]._sop_template.HasField("library")
                assert mat.texture[0].sop_library.endswith("anisotropicbsdf")
                mapping_opp = mat.texture[0].anisotropic_map.mapping_properties.__todict__()
                expected = MappingOperator(
                    mapping_type=MappingTypes.planar,
                    u_length=0,
                    v_length=0,
                    axis_system=[
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
                    u_offset=0,
                    v_offset=0,
                    u_scale=0.1,
                    v_scale=0.1,
                    rotation=90,
                ).__dict__
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
                mapping_opp = mat.texture[1].normal_map.mapping_properties.__todict__()
                expected = MappingOperator(
                    mapping_type=MappingTypes.planar,
                    u_length=10,
                    v_length=10,
                    axis_system=[
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
                    u_offset=0,
                    v_offset=0,
                    u_scale=0.1,
                    v_scale=0.1,
                    rotation=90,
                ).__dict__
                for k1, k2 in zip(sorted(expected.keys()), sorted(mapping_opp.keys())):
                    assert k1 == k2
                for k1 in expected.keys():
                    if isinstance(expected.get(k1), (float, list, int)):
                        assert approx_arrays(expected.get(k1), mapping_opp.get(k1))
                    else:
                        assert expected.get(k1) == mapping_opp.get(k1)
            case "Base_white_notexture":
                assert mat._sop_template.HasField("library")
                assert mat.sop_library.endswith("simplescattering")
                assert mat.vop_type == "optic"
                assert MaterialOpticParameters(
                    mat.vop_optic.index, mat.vop_optic.absorption, mat.vop_optic.constringence
                ) == MaterialOpticParameters(1.5, 10, None)
            case "Texture_gltf":
                assert mat._sop_template is None
                assert mat.vop_type is None
            case "Texture_gltf|UV mapping.1":
                assert mat._material_instance.HasField("texture")
                assert len(mat.texture) == 1
                assert mat.texture[0]._sop_template.HasField("library")
                assert mat.texture[0].sop_library.endswith("gltfsvbrdf")


@pytest.mark.supported_speos_versions(min=252)
def test_delete_texture_property(speos: Speos):
    """Ensure TextureLayer.delete clears local links/refs after commit."""
    p = Project(speos=speos)

    op = p.create_optical_property(name="Material.DeleteTest")
    # create layer, commit SOP template, assign to material and commit material to scene
    layer = TextureLayer(op, "Layer.Delete")
    layer._commit()
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
    layer_1.set_surface_library().sop_library = Path(test_path) / "L100 2.simplescattering"
    layer_1.set_image_texture().image_texture_file_uri = Path(test_path) / "textureColors.jpg"
    layer_1.image_texture.repeat_u = False
    layer_1.image_texture.repeat_v = False
    layer_1.image_texture.set_mapping_by_data().vertices_data_index = 0
    opt_prop.commit()
    assert layer_1._texture_template.normal_map_properties.vertices_data_index == 0
    assert not layer_1._sop_template.texture.image.repeat_along_u
    assert not layer_1._sop_template.texture.image.repeat_along_v

    opt_prop.texture = [layer_1]
    opt_prop.commit()
