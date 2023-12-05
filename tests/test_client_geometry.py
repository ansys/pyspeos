"""
Test basic geometry database connection.
"""
from ansys.speos.core.body import BodyFactory, BodyLink
from ansys.speos.core.face import FaceFactory, FaceLink
from ansys.speos.core.geometry_utils import AxisSystem
from ansys.speos.core.part import PartFactory
from ansys.speos.core.speos import Speos


def test_face_factory(speos: Speos):
    """Test face factory."""
    assert speos.client.healthy is True
    # Get DB
    face_db = speos.client.faces()  # Create face stub from client channel

    # triangle with passing all data
    triangle0 = face_db.create(
        message=FaceFactory.new(
            name="triangle_0",
            description="triangle from data",
            vertices=[0, 0, 0, 100, 0, 0, 0, 100, 0],
            facets=[0, 1, 2],
            normals=[0, 0, 1, 0, 0, 1, 0, 0, 1],
            metadata={"key_0": "val_0", "key_1": "val_1"},
        )
    )
    assert triangle0.key != ""

    # rectangle by using factory rectangle creator with values
    rectangle0 = face_db.create(
        message=FaceFactory.rectangle(
            name="rectangle_0",
            description="rectangle face",
            center=[100, 50, 0],
            x_axis=[1, 0, 0],
            y_axis=[0, 1, 0],
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
    rectangle1 = face_db.create(message=FaceFactory.rectangle(name="rectangle_1", description="rectangle face - default"))
    assert rectangle1.key != ""
    assert rectangle1.get().vertices[0:3] == [-100, -50, 0]
    assert rectangle1.get().vertices[3:6] == [100, -50, 0]
    assert rectangle1.get().vertices[6:9] == [100, 50, 0]
    assert rectangle1.get().vertices[9:12] == [-100, 50, 0]

    triangle0.delete()
    rectangle0.delete()
    rectangle1.delete()


def test_body_factory(speos: Speos):
    """Test body factory."""
    assert speos.client.healthy is True
    # Get DB
    body_db = speos.client.bodies()  # Create body stub from client channel
    face_db = speos.client.faces()  # Create face stub from client channel

    # Body by referencing directly FaceLinks
    body0 = body_db.create(
        message=BodyFactory.new(
            name="body_0",
            description="body from data containing one face",
            faces=[
                face_db.create(
                    FaceFactory.rectangle(name="face_0", description="face_0 for body_0", metadata={"key_0": "val_0", "key_1": "val_1"})
                )
            ],
        )
    )
    assert body0.key != ""

    # box with values
    box0 = body_db.create(
        BodyFactory.box(
            name="box_0",
            face_stub=face_db,
            base=AxisSystem(origin=[100, 100, 100], x_vect=[1, 0, 0], y_vect=[0, 1, 0], z_vect=[0, 0, 1]),
            x_size=200,
            y_size=200,
            z_size=200,
            idx_face=0,
        )
    )
    assert box0.key != ""

    # default box
    box1 = body_db.create(BodyFactory.box(name="box_1", description="box - default", face_stub=face_db))
    assert box1.key != ""

    faces_to_delete = body0.get().face_guids
    faces_to_delete.extend(box0.get().face_guids)
    faces_to_delete.extend(box1.get().face_guids)
    body0.delete()
    box0.delete()
    box1.delete()
    for face_key in faces_to_delete:
        face = speos.client.get_item(key=face_key)
        assert isinstance(face, FaceLink)
        face.delete()


def test_part_factory(speos: Speos):
    """Test part factory."""
    assert speos.client.healthy is True
    # Get DB
    part_db = speos.client.parts()  # Create part stub from client channel
    body_db = speos.client.bodies()  # Create body stub from client channel
    face_db = speos.client.faces()  # Create face stub from client channel

    # Part by referencing directly BodyLinks
    part1 = part_db.create(
        message=PartFactory.new(
            name="part_0",
            description="part with one box as body",
            bodies=[body_db.create(BodyFactory.box(name="box_2", face_stub=face_db, metadata={"key_0": "val_0", "key_1": "val_1"}))],
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
