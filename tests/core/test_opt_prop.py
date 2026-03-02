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

from ansys.speos.core import GeoRef, OptProp, Project, Speos
from ansys.speos.core.generic.parameters import (
    MappingOperator,
    MappingTypes,
    MaterialOpticParameters,
)
from ansys.speos.core.opt_prop import TextureLayer
from tests.conftest import test_path


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
    op1.vop_optic = MaterialOpticParameters(index=1.7, absorption=0.01, constringence=55)
    op1.commit()
    assert op1.vop_template_link.get().HasField("optic")
    assert op1.vop_template_link.get().optic.index == 1.7
    assert op1.vop_template_link.get().optic.absorption == 0.01
    assert op1.vop_template_link.get().optic.HasField("constringence")
    assert op1.vop_template_link.get().optic.constringence == 55
    op1.vop_optic = MaterialOpticParameters(index=1.7, absorption=0.01)
    op1.commit()
    assert op1.vop_template_link.get().optic.HasField("constringence") is False
    op1.set_volume_optic()
    op1.commit()
    assert op1.vop_template_link.get().optic.index == 1.5
    assert op1.vop_template_link.get().optic.absorption == 0.0
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
    op2.vop_optic = MaterialOpticParameters(1.7, 0.01, 55)
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


def test_error_reporting(speos: Speos):
    """Test error raising."""
    pass


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
    layer_1.image_property = MappingOperator("planar", 5)
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
    layer_1.normal_map_property = MappingOperator("cylindrical", 5)
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
    layer_1.commit()
    op1.texture = [layer_1]
    op1.commit()

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
    layer_2.commit()
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
    layer_2.commit()
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
    layer_2.reset()
    assert layer_2._sop_template.HasField("library")
    mapping_op = layer_2._texture_template.anisotropy_map_properties.mapping_operator
    assert mapping_op.axis_system == old_values.axis_system
    assert mapping_op.rotation == old_values.rotation
    assert mapping_op.HasField(old_values.mapping_type)
