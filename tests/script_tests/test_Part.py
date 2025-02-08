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

"""
Test basic using part/body/face from script layer.
"""

import ansys.speos.core as script
from ansys.speos.core.speos import Speos


def test_create_root_part(speos: Speos):
    """Test create root part in project."""
    # Create an empty project
    p = script.Project(speos=speos)
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
    p = script.Project(speos=speos)
    root_part = p.create_root_part().commit()
    assert len(root_part._geom_features) == 0
    assert len(root_part.part_link.get().body_guids) == 0

    # Add empty body
    body1 = root_part.create_body(name="Body.1").commit()
    assert len(root_part._geom_features) == 1

    assert len(root_part.part_link.get().body_guids) == 1
    assert root_part.part_link.get().body_guids[0] == body1.body_link.key

    # Add another body + commit on root part
    body2 = root_part.create_body(name="Body.2")
    root_part.commit()
    assert len(root_part._geom_features) == 2

    assert len(root_part.part_link.get().body_guids) == 2
    assert root_part.part_link.get().body_guids[1] == body2.body_link.key

    # delete bodies
    body1.delete()
    body2.delete()
    assert len(root_part.part_link.get().body_guids) == 0


def test_create_face(speos: Speos):
    """Test create faces in body."""
    # Create an empty project with a root part containing a body
    p = script.Project(speos=speos)
    root_part = p.create_root_part()
    body1 = root_part.create_body(name="Body.1")
    root_part.commit()
    assert len(body1._geom_features) == 0
    assert len(body1.body_link.get().face_guids) == 0

    # Add a face
    face1 = (
        body1.create_face(name="Face.1")
        .set_vertices([0, 1, 0, 0, 2, 0, 1, 2, 0])
        .set_facets([0, 1, 2])
        .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
        .commit()
    )
    assert len(body1._geom_features) == 1

    assert len(body1.body_link.get().face_guids) == 1
    assert body1.body_link.get().face_guids[0] == face1.face_link.key
    assert face1.face_link.get().vertices == [0, 1, 0, 0, 2, 0, 1, 2, 0]
    assert face1.face_link.get().facets == [0, 1, 2]
    assert face1.face_link.get().normals == [0, 0, 1, 0, 0, 1, 0, 0, 1]

    # Add another face + commit on root part
    face2 = (
        body1.create_face(name="Face.2")
        .set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0])
        .set_facets([0, 2, 1])
        .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
        .commit()
    )
    assert len(body1._geom_features) == 2

    assert len(body1.body_link.get().face_guids) == 2
    assert body1.body_link.get().face_guids[1] == face2.face_link.key
    assert face2.face_link.get().vertices == [0, 0, 0, 1, 0, 0, 0, 1, 0]
    assert face2.face_link.get().facets == [0, 2, 1]
    assert face2.face_link.get().normals == [0, 0, 1, 0, 0, 1, 0, 0, 1]

    # Delete faces
    face1.delete()
    face2.delete()
    assert len(body1.body_link.get().face_guids) == 0


def test_create_subpart(speos: Speos):
    """Test create sub part in root part."""
    # Create an empty project with a root part
    p = script.Project(speos=speos)
    root_part = p.create_root_part().commit()
    assert len(root_part._geom_features) == 0
    assert len(root_part.part_link.get().parts) == 0

    # Add a sub part
    sp1 = (
        root_part.create_sub_part(name="SubPart.1")
        .set_axis_system(axis_system=[5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
        .commit()
    )
    assert len(root_part._geom_features) == 1
    assert len(root_part.part_link.get().parts) == 1
    assert root_part.part_link.get().parts[0] == sp1._part_instance
    assert sp1._part_instance.axis_system == [5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sp1._part_instance.part_guid == sp1.part_link.key
    assert (
        sp1.part_link.get().name == "SubPart.1"
    )  # part contained in a sub part gets same name as the sub part
    assert len(sp1.part_link.get().body_guids) == 0

    # Add another sub part + commit on root part
    sp2 = root_part.create_sub_part(name="SubPart.2").set_axis_system(
        axis_system=[15, 14, 14, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    )
    root_part.commit()
    assert len(root_part._geom_features) == 2
    assert len(root_part.part_link.get().parts) == 2
    assert root_part.part_link.get().parts[1] == sp2._part_instance
    assert sp2._part_instance.axis_system == [15, 14, 14, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sp2._part_instance.part_guid == sp2.part_link.key
    assert (
        sp2.part_link.get().name == "SubPart.2"
    )  # part contained in a sub part gets same name as the sub part
    assert len(sp2.part_link.get().body_guids) == 0

    # Delete sub parts
    sp1.delete()
    sp2.delete()
    assert len(root_part.part_link.get().parts) == 0


def test_create_subpart_body(speos: Speos):
    """Test create body in sub part."""
    # Create an empty project with a root part and sub part
    p = script.Project(speos=speos)
    root_part = p.create_root_part().commit()
    sp1 = (
        root_part.create_sub_part(name="SubPart.1")
        .set_axis_system(axis_system=[5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
        .commit()
    )
    assert len(sp1._geom_features) == 0
    assert len(sp1.part_link.get().body_guids) == 0

    # Add empty body
    body1 = sp1.create_body(name="Body.1").commit()
    assert len(sp1._geom_features) == 1

    assert len(sp1.part_link.get().body_guids) == 1
    assert sp1.part_link.get().body_guids[0] == body1.body_link.key

    # Add another body + commit on root part
    body2 = sp1.create_body(name="Body.2")
    root_part.commit()
    assert len(sp1._geom_features) == 2

    assert len(sp1.part_link.get().body_guids) == 2
    assert sp1.part_link.get().body_guids[1] == body2.body_link.key

    # delete bodies
    body1.delete()
    body2.delete()
    assert len(sp1.part_link.get().body_guids) == 0


def test_create_subpart_subpart(speos: Speos):
    """Test create sub part in sub part."""
    # Create an empty project with a root part and sub part
    p = script.Project(speos=speos)
    root_part = p.create_root_part().commit()
    sp1 = (
        root_part.create_sub_part(name="SubPart.1")
        .set_axis_system(axis_system=[5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
        .commit()
    )
    assert len(sp1._geom_features) == 0
    assert len(sp1.part_link.get().parts) == 0

    # Add a sub part
    sp11 = (
        sp1.create_sub_part(name="SubPart.11")
        .set_axis_system(axis_system=[-5, -4, -10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
        .commit()
    )
    assert len(sp1._geom_features) == 1
    assert len(sp1.part_link.get().parts) == 1
    assert sp1.part_link.get().parts[0] == sp11._part_instance
    assert sp11._part_instance.axis_system == [-5, -4, -10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sp11._part_instance.part_guid == sp11.part_link.key
    assert (
        sp11.part_link.get().name == "SubPart.11"
    )  # part contained in a sub part gets same name as the sub part
    assert len(sp11.part_link.get().body_guids) == 0

    # Add another sub part + commit on root part
    sp12 = sp1.create_sub_part(name="SubPart.12").set_axis_system(
        axis_system=[-15, -14, -14, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    )
    root_part.commit()
    assert len(sp1._geom_features) == 2
    assert len(sp1.part_link.get().parts) == 2
    assert sp1.part_link.get().parts[1] == sp12._part_instance
    assert sp12._part_instance.axis_system == [-15, -14, -14, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert sp12._part_instance.part_guid == sp12.part_link.key
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
    p = script.Project(speos=speos)

    # Create
    root_part = p.create_root_part()
    sp1 = root_part.create_sub_part(name="SubPart.1").set_axis_system(
        axis_system=[5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    )
    sp1.create_sub_part(name="SubPart.11").set_axis_system(
        axis_system=[-5, -4, -10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    )
    root_part.create_body(name="Body.1")
    assert root_part.part_link is None
    assert p.scene_link.get().part_guid == ""

    # Commit
    root_part.commit()
    assert root_part.part_link is not None
    assert p.scene_link.get().part_guid == root_part.part_link.key
    assert len(root_part.part_link.get().parts) == 1
    assert (
        len(speos.client.get_item(key=root_part.part_link.get().parts[0].part_guid).get().parts)
        == 1
    )
    assert len(root_part.part_link.get().body_guids) == 1

    # Change only in local not committed
    root_part._part.description = "new"
    assert root_part._part != root_part.part_link.get()

    root_part.delete()


def test_reset_part(speos: Speos):
    """Test reset of part."""
    p = script.Project(speos=speos)

    # Create + commit
    root_part = p.create_root_part()
    sp1 = root_part.create_sub_part(name="SubPart.1").set_axis_system(
        axis_system=[5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    )
    sp1.create_sub_part(name="SubPart.11").set_axis_system(
        axis_system=[-5, -4, -10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    )
    root_part.create_body(name="Body.1")
    root_part.commit()
    assert root_part.part_link is not None

    # Change local data (on template and on instance)
    root_part._part.description = "new"
    assert root_part._part != root_part.part_link.get()

    # Ask for reset
    root_part.reset()
    assert root_part._part == root_part.part_link.get()

    root_part.delete()


def test_delete_part(speos: Speos):
    """Test delete of part."""
    p = script.Project(speos=speos)

    # Create + commit
    root_part = p.create_root_part()
    sp1 = root_part.create_sub_part(name="SubPart.1").set_axis_system(
        axis_system=[5, 4, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    )
    sp1.create_sub_part(name="SubPart.11").set_axis_system(
        axis_system=[-5, -4, -10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    )
    root_part.create_body(name="Body.1")
    root_part.commit()
    assert root_part.part_link is not None

    # Delete
    root_part.delete()
    assert root_part.part_link is None

    assert p.scene_link.get().part_guid == ""
    assert root_part._part.name == "RootPart"  # local
    assert len(root_part._part.parts) == 0
    assert len(root_part._part.body_guids) == 0
