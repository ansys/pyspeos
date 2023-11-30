"""
Test scene.
"""
from ansys.speos.core.body import BodyFactory
from ansys.speos.core.part import PartFactory
from ansys.speos.core.scene import GeoPaths, SceneFactory
from ansys.speos.core.speos import Speos
from ansys.speos.core.vop_template import VOPTemplateFactory


def test_scene_factory(speos: Speos):
    """Test the scene factory."""
    assert speos.client.healthy is True

    # Get DB
    scene_db = speos.client.scenes()  # Create scenes stub from client channel
    part_db = speos.client.parts()  # Create parts stub from client channel
    body_db = speos.client.bodies()  # Create bodies stub from client channel
    face_db = speos.client.faces()  # Create faces stub from client channel
    vop_t_db = speos.client.vop_templates()

    scene0 = scene_db.create(
        message=SceneFactory.new(
            name="scene_0",
            description="scene from scratch",
            part=part_db.create(
                PartFactory.new(
                    name="part_0",
                    description="part_0 for scene_0",
                    bodies=[
                        body_db.create(
                            message=BodyFactory.box(name="body_0", description="body_0 in part_0 for scene_0", face_stub=face_db)
                        )
                    ],
                )
            ),
            vop_instances=[
                SceneFactory.VOPInstance(
                    name="opaque.1",
                    vop_template=vop_t_db.create(message=VOPTemplateFactory.opaque("opaque", "opaque vop template")),
                    geometries=GeoPaths(geo_paths=["part_0"]),
                )
            ],
        )
    )
    assert scene0.key != ""
