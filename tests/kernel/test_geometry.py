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
Test basic geometry database connection.
"""

from tests.kernel.test_scene import create_face_rectangle

from ansys.speos.core.kernel.body import BodyLink, ProtoBody
from ansys.speos.core.kernel.face import FaceLink, ProtoFace
from ansys.speos.core.kernel.part import ProtoPart
from ansys.speos.core.speos import Speos


def test_create_big_face(speos: Speos):
    """Test create big face."""
    assert speos.client.healthy is True
    # Get DB
    face_db = speos.client.faces()  # Create face stub from client channel

    size = 3 * 1024 * 1024
    vertices = [10.0] * size
    facets = [20] * size

    # Create face
    face_link = face_db.create(
        message=ProtoFace(
            name="Face.1",
            description="Face one",
            vertices=vertices,
            facets=facets,
            normals=vertices,
            metadata={"key_0": "val_0", "key_1": "val_1"},
        )
    )
    assert face_link.key != ""

    # Read face
    face_read = face_link.get()
    assert face_read.name == "Face.1"
    assert face_read.description == "Face one"
    assert face_read.metadata == {"key_0": "val_0", "key_1": "val_1"}
    assert face_read.vertices == vertices
    assert face_read.facets == facets
    assert face_read.normals == vertices

    face_link.delete()


def test_update_big_face(speos: Speos):
    """Test create big face."""
    assert speos.client.healthy is True
    # Get DB
    face_db = speos.client.faces()  # Create face stub from client channel

    size = 3 * 1024 * 1024
    vertices = [10.0] * size
    facets = [20] * size

    size_2 = 9 * 1024
    vertices_2 = [9.5] * size_2
    facets_2 = [15] * size_2

    # Create face
    face_link = face_db.create(
        message=ProtoFace(
            name="Face.1",
            description="Face one",
            vertices=vertices,
            facets=facets,
            normals=vertices,
            metadata={"key_0": "val_0", "key_1": "val_1"},
        )
    )
    assert face_link.key != ""

    # Update
    face_link.set(
        data=ProtoFace(
            name="Face.2",
            description="Face two",
            vertices=vertices_2,
            facets=facets_2,
            normals=vertices_2,
            metadata={"key_0": "val_00", "key_1": "val_11"},
        )
    )

    # Read face
    face_read = face_link.get()
    assert face_read.name == "Face.2"
    assert face_read.description == "Face two"
    assert face_read.metadata == {"key_0": "val_00", "key_1": "val_11"}
    assert face_read.vertices == vertices_2
    assert face_read.facets == facets_2
    assert face_read.normals == vertices_2

    face_link.delete()


def test_face(speos: Speos):
    """Test face creation."""
    assert speos.client.healthy is True
    # Get DB
    face_db = speos.client.faces()  # Create face stub from client channel

    # rectangle
    rectangle0 = face_db.create(
        message=create_face_rectangle(
            name="rectangle_0",
            description="rectangle face",
            base=[100, 50, 0, 1, 0, 0, 0, 1, 0],
            x_size=200,
            y_size=100,
        )
    )
    assert rectangle0.key != ""
    assert rectangle0.get().vertices[0:3] == [0, 0, 0]
    assert rectangle0.get().vertices[3:6] == [200, 0, 0]
    assert rectangle0.get().vertices[6:9] == [200, 100, 0]
    assert rectangle0.get().vertices[9:12] == [0, 100, 0]

    # default rectangle
    rectangle1 = face_db.create(
        message=create_face_rectangle(name="rectangle_1", description="rectangle face - default")
    )
    assert rectangle1.key != ""
    assert rectangle1.get().vertices[0:3] == [-100, -50, 0]
    assert rectangle1.get().vertices[3:6] == [100, -50, 0]
    assert rectangle1.get().vertices[6:9] == [100, 50, 0]
    assert rectangle1.get().vertices[9:12] == [-100, 50, 0]

    rectangle0.delete()
    rectangle1.delete()


def test_body(speos: Speos):
    """Test body creation."""
    assert speos.client.healthy is True
    # Get DB
    body_db = speos.client.bodies()  # Create body stub from client channel
    face_db = speos.client.faces()  # Create face stub from client channel

    # Body by referencing directly FaceLinks
    body0 = body_db.create(
        message=ProtoBody(
            name="body_0",
            description="body from data containing one face",
            face_guids=[
                face_db.create(
                    message=create_face_rectangle(
                        name="face_0",
                        description="face_0 for body_0",
                        metadata={"key_0": "val_0", "key_1": "val_1"},
                    )
                ).key
            ],
        )
    )
    assert body0.key != ""

    faces_to_delete = body0.get().face_guids
    body0.delete()
    for face_key in faces_to_delete:
        face = speos.client.get_item(key=face_key)
        assert isinstance(face, FaceLink)
        face.delete()


def test_part(speos: Speos):
    """Test part creation."""
    assert speos.client.healthy is True
    # Get DB
    part_db = speos.client.parts()  # Create part stub from client channel
    body_db = speos.client.bodies()  # Create body stub from client channel
    face_db = speos.client.faces()  # Create face stub from client channel

    # Part by referencing directly BodyLinks
    part1 = part_db.create(
        message=ProtoPart(
            name="part_0",
            description="part with one box as body",
            body_guids=[
                body_db.create(
                    ProtoBody(
                        name="body_0",
                        description="body from data containing one face",
                        face_guids=[
                            face_db.create(
                                message=create_face_rectangle(
                                    name="face_0",
                                    description="face_0 for body_0",
                                    metadata={"key_0": "val_0", "key_1": "val_1"},
                                )
                            ).key
                        ],
                    )
                ).key
            ],
            metadata={"my_key0": "my_value0", "my_key1": "my_value1"},
        )
    )
    assert part1.key != ""

    for body_key in part1.get().body_guids:
        body = speos.client.get_item(key=body_key)
        assert isinstance(body, BodyLink)
        for face_key in body.get().face_guids:
            face = speos.client.get_item(key=face_key)
            assert isinstance(face, FaceLink)
            face.delete()
        body.delete()
    part1.delete()
