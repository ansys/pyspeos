"""
Test basic geometry database connection.
"""
from ansys.speos.core.body import BodyFactory
from ansys.speos.core.face import FaceFactory, FaceLink
from ansys.speos.core.geometry import CoordSys
from ansys.speos.core.speos import Speos


def test_face_factory(speos: Speos):
    """Test face factory."""
    assert speos.client.healthy is True
    # Get DB
    face_db = speos.client.faces()  # Create face stub from client channel

    # rectangle with values
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

    rectangle0.delete()
    rectangle1.delete()


def test_body_factory(speos: Speos):
    """Test body factory."""
    assert speos.client.healthy is True
    # Get DB
    body_db = speos.client.bodies()  # Create body stub from client channel
    face_db = speos.client.faces()  # Create face stub from client channel

    # box with values
    box0 = body_db.create(
        BodyFactory.box(
            name="box_0",
            face_stub=face_db,
            base=CoordSys(origin=[100, 100, 100], x_vect=[1, 0, 0], y_vect=[0, 1, 0], z_vect=[0, 0, 1]),
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

    faces_list_to_delete = box0.get().face_guids
    faces_list_to_delete.extend(box1.get().face_guids)
    box0.delete()
    box1.delete()
    for face_key in faces_list_to_delete:
        face = speos.client.get_item(key=face_key)
        assert isinstance(face, FaceLink)
        face.delete()
