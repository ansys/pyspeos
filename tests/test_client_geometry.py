"""
Test basic geometry database connection.
"""
from ansys.speos.core.geometry import FaceFactory, Point3f, Vector3f
from ansys.speos.core.speos import Speos


def test_face_factory(speos: Speos):
    """Test face factory."""
    assert speos.client.healthy is True
    # Get DB
    face_db = speos.client.faces()  # Create face stub from client channel

    # rectangle with values
    rectangle = face_db.create(
        message=FaceFactory.rectangle(
            name="rectangle_0",
            description="rectangle face",
            center=Point3f(x=100, y=50, z=0),
            x_axis=Vector3f(x=1, y=0, z=0),
            y_axis=Vector3f(x=0, y=1, z=0),
            x_size=200,
            y_size=100,
        )
    )
    assert rectangle.key != ""
    assert rectangle.get().vertices[0:3] == [0, 0, 0]
    assert rectangle.get().vertices[3:6] == [200, 0, 0]
    assert rectangle.get().vertices[6:9] == [200, 100, 0]
    assert rectangle.get().vertices[9:12] == [0, 100, 0]

    # default rectangle
    rectangle = face_db.create(message=FaceFactory.rectangle(name="rectangle_0", description="rectangle face"))
    assert rectangle.key != ""
    assert rectangle.get().vertices[0:3] == [-100, -50, 0]
    assert rectangle.get().vertices[3:6] == [100, -50, 0]
    assert rectangle.get().vertices[6:9] == [100, 50, 0]
    assert rectangle.get().vertices[9:12] == [-100, 50, 0]
