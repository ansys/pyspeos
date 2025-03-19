# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
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

from ansys.speos.core import GeoRef, Project, Speos
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
    op1.set_volume_optic(index=1.7, absorption=0.01, constringence=55).commit()
    assert op1.vop_template_link.get().HasField("optic")
    assert op1.vop_template_link.get().optic.index == 1.7
    assert op1.vop_template_link.get().optic.absorption == 0.01
    assert op1.vop_template_link.get().optic.HasField("constringence")
    assert op1.vop_template_link.get().optic.constringence == 55

    op1.set_volume_optic().commit()
    assert op1.vop_template_link.get().optic.index == 1.5
    assert op1.vop_template_link.get().optic.absorption == 0.0
    assert op1.vop_template_link.get().optic.HasField("constringence") is False

    # VOP library
    op1.set_volume_library(path=str(Path(test_path) / "AIR.material")).commit()
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
    op1.set_surface_library(path=str(Path(test_path) / "R_test.anisotropicbsdf")).commit()
    assert op1.sop_template_link.get().HasField("library")
    assert op1.sop_template_link.get().library.sop_file_uri.endswith("R_test.anisotropicbsdf")

    # SOP mirror
    op1.set_surface_mirror(reflectance=80).commit()
    assert op1.sop_template_link.get().HasField("mirror")
    assert op1.sop_template_link.get().mirror.reflectance == 80

    # geometries
    op1.set_geometries(
        geometries=[
            GeoRef.from_native_link("TheBodyB1"),
            GeoRef.from_native_link("TheBodyB2"),
        ]
    )
    assert op1._material_instance.HasField("geometries")
    op1._material_instance.geometries.geo_paths == ["TheBody1", "TheBodyB2"]

    op1.set_geometries(geometries=None)  # means no geometry
    assert op1._material_instance.HasField("geometries") is False

    op1.set_geometries(geometries=[])  # means all geometries
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
    op1.set_geometries(geometries=[GeoRef.from_native_link("TheBodyB")])
    assert p.scene_link.get().materials[0] != op1._material_instance

    op1.delete()


def test_reset_optical_property(speos: Speos):
    """Test reset of optical property."""
    p = Project(speos=speos)

    # Create + commit
    op1 = (
        p.create_optical_property(name="Material.1")
        .set_volume_opaque()
        .set_geometries(geometries=[GeoRef.from_native_link("TheBodyB")])
        .commit()
    )
    assert op1.vop_template_link is not None
    assert op1.vop_template_link.get().HasField("opaque")
    assert op1.sop_template_link is not None
    assert op1.sop_template_link.get().HasField("mirror")
    assert len(p.scene_link.get().materials) == 1
    assert p.scene_link.get().materials[0].HasField("geometries")

    # Change local data (on template and on instance)
    op1.set_surface_opticalpolished().set_volume_optic().set_geometries(geometries=None)
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

    # Create + commit
    op1 = (
        p.create_optical_property(name="Material.1")
        .set_volume_opaque()
        .set_geometries(geometries=[GeoRef.from_native_link("TheBodyB")])
        .commit()
    )
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
    op1 = (
        p.create_optical_property(name="Material.1")
        .set_volume_opaque()
        .set_geometries(geometries=[GeoRef.from_native_link("TheBodyA")])
        .commit()
    )

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

    op2 = (
        p.create_optical_property(name="OpticalProperty2")
        .set_volume_optic(index=1.7, absorption=0.01, constringence=55)
        .set_surface_opticalpolished()
        .set_geometries(geometries=[GeoRef.from_native_link("TheBodyB")])
        .commit()
    )

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

    op3 = (
        p.create_optical_property(name="OpticalProperty3")
        .set_volume_none()
        .set_surface_library(path=str(Path(test_path) / "R_test.anisotropicbsdf"))
        .commit()
    )

    name = op3.get(key="name")
    assert name == "OpticalProperty3"
    # test vop
    assert op3.get(key="vop") is None
    # test sops
    sop_property_info = op3.get(key="sops")[0]
    assert "mirror" not in sop_property_info
    assert "optical_polished" not in sop_property_info
    assert "library" in sop_property_info
