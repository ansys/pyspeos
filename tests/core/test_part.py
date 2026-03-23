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

"""Test basic using part/body/face."""

import pytest

from ansys.speos.core import Project, Speos


def test_create_root_part(speos: Speos):
    """Test create root part in project."""
    # Create an empty project
    p = Project(speos=speos)
    assert len(p._features) == 0

    # Add empty root part
    root_part = p.create_root_part().commit()
    assert len(p._features) == 1
    assert p.scene_link.get().part_guid == root_part.part_link.key

    assert len(root_part.part_link.get().body_guids) == 0
    assert len(root_part.part_link.get().parts) == 0


def test_create_body(speos: Speos):
    """Test create bodies in root part."""
    # Create an empty project with a root part
    p = Project(speos=speos)
    root_part = p.create_root_part().commit()
    assert len(root_part._geom_features) == 0
    assert len(root_part.part_link.get().body_guids) == 0

    # Add empty body
    body1 = root_part.create_body(name="Body.1").commit()
    assert len(root_part._geom_features) == 1
    assert body1.geo_path.metadata["GeoPath"] == "Body.1"
    assert len(root_part.part_link.get().body_guids) == 1
    assert root_part.part_link.get().body_guids[0] == body1.body_link.key

    # Add another body + commit on root part
    body2 = root_part.create_body(name="Body.2")
    root_part.commit()
    assert len(root_part._geom_features) == 2
    assert body2.geo_path.metadata["GeoPath"] == "Body.2"
    assert len(root_part.part_link.get().body_guids) == 2
    assert root_part.part_link.get().body_guids[1] == body2.body_link.key

    # delete bodies
    body1.delete()
    assert len(root_part.bodies) == 1
    body2.delete()
    assert len(root_part.part_link.get().body_guids) == 0


def test_create_face(speos: Speos):
    """Test create faces in body."""
    # Create an empty project with a root part containing a body
    p = Project(speos=speos)
    root_part = p.create_root_part()
    body1 = root_part.create_body(name="Body.1")
    face0 = body1.create_face(name="TheFaceF")
    face0.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    face0.facets = [0, 1, 2]
    face0.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    root_part.commit()
    assert len(body1._geom_features) == 1
    assert len(body1.body_link.get().face_guids) == 1
    assert face0.geo_path.metadata["GeoPath"] == "Body.1/TheFaceF"
    # Add a face
    face1 = body1.create_face(name="Face.1")
    face1.vertices = [0, 1, 0, 0, 2, 0, 1, 2, 0]
    face1.facets = [0, 1, 2]
    face1.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    face1.commit()
    assert len(body1._geom_features) == 2
    assert face1.geo_path.metadata["GeoPath"] == "Body.1/Face.1"
    assert len(body1.body_link.get().face_guids) == 2
    assert body1.body_link.get().face_guids[1] == face1.face_link.key
    assert face1.face_link.get().vertices == [0, 1, 0, 0, 2, 0, 1, 2, 0]
    assert face1.face_link.get().facets == [0, 1, 2]
    assert face1.face_link.get().normals == [0, 0, 1, 0, 0, 1, 0, 0, 1]

    # Add another face + commit on root part
    face2 = body1.create_face(name="Face.2")
    face2.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    face2.facets = [0, 2, 1]
    face2.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    face2.commit()
    assert len(body1._geom_features) == 3
    assert face2.geo_path.metadata["GeoPath"] == "Body.1/Face.2"
    assert len(body1.body_link.get().face_guids) == 3
    assert body1.body_link.get().face_guids[2] == face2.face_link.key
    assert face2.face_link.get().vertices == [0, 0, 0, 1, 0, 0, 0, 1, 0]
    assert face2.face_link.get().facets == [0, 2, 1]
    assert face2.face_link.get().normals == [0, 0, 1, 0, 0, 1, 0, 0, 1]

    # Delete faces
    face0.delete()
    assert len(body1.faces) == 2
    face1.delete()
    assert len(body1.faces) == 1
    face2.delete()
    assert len(body1.body_link.get().face_guids) == 0


def test_create_subpart(speos: Speos):
    """Test create sub part in root part."""
    # Create an empty project with a root part
    p = Project(speos=speos)
    root_part = p.create_root_part().commit()
    assert len(root_part._geom_features) == 0
    assert len(root_part.part_link.get().parts) == 0

    # Add a sub part
    sp1 = root_part.create_sub_part(name="SubPart.1")
    sp1.axis_system = [5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sp1.commit()
    assert len(root_part._geom_features) == 1
    assert len(root_part.part_link.get().parts) == 1
    assert sp1.geo_path.metadata["GeoPath"] == "SubPart.1"
    assert root_part.part_link.get().parts[0] == sp1._part_instance
    assert sp1._part_instance.axis_system == [
        5,
        4,
        10,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    assert sp1._part_instance.part_guid == sp1.part_link.key
    assert (
        sp1.part_link.get().name == "SubPart.1"
    )  # part contained in a sub part gets same name as the sub part
    assert len(sp1.part_link.get().body_guids) == 0

    # Add another sub part + commit on root part
    sp2 = root_part.create_sub_part(name="SubPart.2")
    sp2.axis_system = [15, 14, 14, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    root_part.commit()
    assert len(root_part._geom_features) == 2
    assert len(root_part.part_link.get().parts) == 2
    assert sp2.geo_path.metadata["GeoPath"] == "SubPart.2"
    assert root_part.part_link.get().parts[1] == sp2._part_instance
    assert sp2._part_instance.axis_system == [
        15,
        14,
        14,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    assert sp2._part_instance.part_guid == sp2.part_link.key
    assert (
        sp2.part_link.get().name == "SubPart.2"
    )  # part contained in a sub part gets same name as the sub part
    assert len(sp2.part_link.get().body_guids) == 0

    # Modify axis system
    sp1.axis_system = [20, 20, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sp1.commit()

    # Check that the axis system is correctly updated on server data
    parent_part_data = sp1._parent_part.part_link.get()
    part_inst = next(
        (x for x in parent_part_data.parts if x.description == "UniqueId_" + sp1._unique_id),
        None,
    )
    assert part_inst is not None
    assert part_inst.axis_system == [20, 20, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    # Delete sub parts
    sp1.delete()
    sp2.delete()
    assert len(root_part.part_link.get().parts) == 0


def test_create_subpart_body(speos: Speos):
    """Test create body in sub part."""
    # Create an empty project with a root part and sub part
    p = Project(speos=speos)
    root_part = p.create_root_part().commit()
    sp1 = root_part.create_sub_part(name="SubPart.1")
    sp1.axis_system = [5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sp1.commit()
    assert len(sp1._geom_features) == 0
    assert len(sp1.part_link.get().body_guids) == 0

    # Add empty body
    body1 = sp1.create_body(name="Body.1").commit()
    assert len(sp1._geom_features) == 1
    assert body1.geo_path.metadata["GeoPath"] == "SubPart.1/Body.1"
    assert len(sp1.part_link.get().body_guids) == 1
    assert sp1.part_link.get().body_guids[0] == body1.body_link.key

    # Add another body + commit on root part
    body2 = sp1.create_body(name="Body.2")
    root_part.commit()
    assert len(sp1._geom_features) == 2
    assert body2.geo_path.metadata["GeoPath"] == "SubPart.1/Body.2"
    assert len(sp1.part_link.get().body_guids) == 2
    assert sp1.part_link.get().body_guids[1] == body2.body_link.key

    # delete bodies
    body1.delete()
    assert len(root_part.subparts[0].bodies) == 1
    body2.delete()
    assert len(sp1.part_link.get().body_guids) == 0


def test_create_subpart_subpart(speos: Speos):
    """Test create sub part in sub part."""
    # Create an empty project with a root part and sub part
    p = Project(speos=speos)
    root_part = p.create_root_part().commit()
    sp1 = root_part.create_sub_part(name="SubPart.1")
    sp1.axis_system = [5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sp1.commit()
    assert len(sp1._geom_features) == 0
    assert len(sp1.part_link.get().parts) == 0

    # Add a sub part
    sp11 = sp1.create_sub_part(name="SubPart.11")
    sp11.axis_system = [-5, -4, -10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sp11.commit()
    assert len(sp1._geom_features) == 1
    assert len(sp1.part_link.get().parts) == 1
    assert sp1.part_link.get().parts[0] == sp11._part_instance
    assert sp11._part_instance.axis_system == [
        -5,
        -4,
        -10,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    assert sp11._part_instance.part_guid == sp11.part_link.key
    assert sp11.geo_path.metadata["GeoPath"] == "SubPart.1/SubPart.11"
    assert (
        sp11.part_link.get().name == "SubPart.11"
    )  # part contained in a sub part gets same name as the sub part
    assert len(sp11.part_link.get().body_guids) == 0

    # Add another sub part + commit on root part
    sp12 = sp1.create_sub_part(name="SubPart.12")
    sp12.axis_system = [-15, -14, -14, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    root_part.commit()
    assert len(sp1._geom_features) == 2
    assert len(sp1.part_link.get().parts) == 2
    assert sp1.part_link.get().parts[1] == sp12._part_instance
    assert sp12._part_instance.axis_system == [
        -15,
        -14,
        -14,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    assert sp12._part_instance.part_guid == sp12.part_link.key
    assert sp12.geo_path.metadata["GeoPath"] == "SubPart.1/SubPart.12"
    assert (
        sp12.part_link.get().name == "SubPart.12"
    )  # part contained in a sub part gets same name as the sub part
    assert len(sp12.part_link.get().body_guids) == 0

    # Delete sub parts
    sp11.delete()
    sp12.delete()
    assert len(sp1.part_link.get().parts) == 0


def test_commit_part(speos: Speos):
    """Test commit of part."""
    p = Project(speos=speos)

    # Create
    root_part = p.create_root_part()
    sp1 = root_part.create_sub_part(name="SubPart.1")
    sp1.axis_system = [5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sp11 = sp1.create_sub_part(name="SubPart.11")
    sp11.axis_system = [-5, -4, -10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    body1 = root_part.create_body(name="Body.1")
    f = body1.create_face(name="TheFaceF")
    f.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    f.facets = [0, 1, 2]
    f.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    assert root_part.part_link is None
    assert p.scene_link.get().part_guid == ""

    # Commit
    root_part.commit()
    assert root_part.part_link is not None
    assert p.scene_link.get().part_guid == root_part.part_link.key
    assert len(root_part.part_link.get().parts) == 1
    assert len(speos.client[root_part.part_link.get().parts[0].part_guid].get().parts) == 1
    assert len(root_part.part_link.get().body_guids) == 1

    # Change only in local not committed
    root_part._part.description = "new"
    assert root_part._part != root_part.part_link.get()

    root_part.delete()


def test_reset_part(speos: Speos):
    """Test reset of part."""
    p = Project(speos=speos)

    # Create + commit
    root_part = p.create_root_part()
    sp1 = root_part.create_sub_part(name="SubPart.1")
    sp1.axis_system = [5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sp11 = sp1.create_sub_part(name="SubPart.11")
    sp11.axis_system = [-5, -4, -10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    body1 = root_part.create_body(name="Body.1")
    f = body1.create_face(name="TheFaceF")
    f.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    f.facets = [0, 1, 2]
    f.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    root_part.commit()
    assert root_part.part_link is not None

    # Change local data (on template and on instance)
    f.vertices = [1, 1, 1, 1, 0, 0, 0, 1, 0]
    f.facets = [1, 2, 0]
    f.normals = [0, 0, -1, 0, 0, -1, 0, 0, -1]
    root_part._part.description = "new"
    root_part.subparts[0].axis_system = [20, 20, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    root_part.subparts[0]._part.description = "new"
    assert root_part._part != root_part.part_link.get()
    assert root_part.subparts[0]._part != root_part.subparts[0].part_link.get()
    # Ask for reset
    root_part.reset()
    root_part.subparts[0].reset()
    f.reset()

    assert root_part._part == root_part.part_link.get()
    assert root_part.subparts[0]._part == root_part.subparts[0].part_link.get()
    assert root_part._part.description != "new"  # local changes are not kept
    assert root_part.subparts[0].axis_system == [5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert f.vertices == [0, 0, 0, 1, 0, 0, 0, 1, 0]
    assert f.facets == [0, 1, 2]
    assert f.normals == [0, 0, 1, 0, 0, 1, 0, 0, 1]

    root_part.delete()


def test_delete_part(speos: Speos):
    """Test delete of part."""
    p = Project(speos=speos)

    # Create + commit
    root_part = p.create_root_part()
    sp1 = root_part.create_sub_part(name="SubPart.1")
    sp1.axis_system = [5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    sp11 = sp1.create_sub_part(name="SubPart.11")
    sp11.axis_system = [-5, -4, -10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    body1 = root_part.create_body(name="Body.1")
    f = body1.create_face(name="TheFaceF")
    f.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    f.facets = [0, 1, 2]
    f.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
    root_part.commit()
    assert root_part.part_link is not None

    # Delete
    root_part.delete()
    assert root_part.part_link is None

    assert p.scene_link.get().part_guid == ""
    assert root_part._part.name == "RootPart"  # local
    assert len(root_part._part.parts) == 0
    assert len(root_part._part.body_guids) == 0


def test_axis_system_invalid_type_raises_type_error(speos: Speos):
    """Axis system setter should raise TypeError.

    When input is not list/tuple or contains non-numeric entries.
    """
    p = Project(speos=speos)
    root = p.create_root_part()
    sp = root.create_sub_part(name="SP")
    with pytest.raises(TypeError):
        sp.axis_system = "not-a-list"  # wrong type

    with pytest.raises(TypeError):
        # contains a non-numeric element
        sp.axis_system = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, "x"]


def test_axis_system_invalid_length_raises_value_error(speos: Speos):
    """Axis system setter should raise ValueError when input length is not 12."""
    p = Project(speos=speos)
    root = p.create_root_part()
    sp = root.create_sub_part(name="SP2")
    with pytest.raises(ValueError):
        sp.axis_system = [1, 2, 3]  # wrong length


def test_face_invalid_vertices_type_raises_type_error(speos: Speos):
    """Face.vertices setter should raise TypeError.

    When input is not list/tuple or contains non-numeric entries.
    """
    p = Project(speos=speos)
    root = p.create_root_part()
    b = root.create_body(name="B")
    f = b.create_face(name="F")
    with pytest.raises(TypeError):
        f.vertices = "not-a-list"
    with pytest.raises(TypeError):
        f.vertices = [0, 0, "x"]  # non-numeric element


def test_face_invalid_vertices_length_raises_value_error(speos: Speos):
    """Face.vertices setter should raise ValueError when length is not a multiple of 3."""
    p = Project(speos=speos)
    root = p.create_root_part()
    b = root.create_body(name="B2")
    f = b.create_face(name="F2")
    with pytest.raises(ValueError):
        f.vertices = [0, 1]  # not multiple of 3


def test_face_invalid_facets_type_and_length_raises(speos: Speos):
    """Face.facets setter should raise TypeError/ValueError.

    When wrong element types or for wrong length is provided.
    """
    p = Project(speos=speos)
    root = p.create_root_part()
    b = root.create_body(name="B3")
    f = b.create_face(name="F3")
    with pytest.raises(TypeError):
        f.facets = "bad"
    # also test out of range facets when vertices present
    f.vertices = [0, 0, 0, 1, 0, 0]  # 2 points
    with pytest.raises(ValueError):
        f.facets = [0, 1, 2]  # index 2 out of range


def test_face_invalid_normals_raises(speos: Speos):
    """Face.normals setter should raise TypeError/ValueError.

    For wrong element types or for length mismatch.
    """
    p = Project(speos=speos)
    root = p.create_root_part()
    b = root.create_body(name="B4")
    f = b.create_face(name="F4")
    with pytest.raises(TypeError):
        f.normals = "bad"
    with pytest.raises(ValueError):
        f.normals = [0, 0]  # not multiple of 3
    # mismatch with vertices
    f.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    with pytest.raises(ValueError):
        f.normals = [0, 0, 1, 0, 0, 1]  # length mismatch with vertices
