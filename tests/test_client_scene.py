"""
Test scene.
"""
import os

from ansys.speos.core.body import BodyFactory
from ansys.speos.core.geometry import AxisSystem, GeoPathReverseNormal, GeoPaths
from ansys.speos.core.intensity_template import IntensityTemplateFactory
from ansys.speos.core.part import PartFactory
from ansys.speos.core.scene import SceneFactory
from ansys.speos.core.sop_template import SOPTemplateFactory
from ansys.speos.core.source_template import SourceTemplateFactory
from ansys.speos.core.spectrum import SpectrumFactory
from ansys.speos.core.speos import Speos
from ansys.speos.core.vop_template import VOPTemplateFactory
from conftest import test_path


def test_scene_factory(speos: Speos):
    """Test the scene factory."""
    assert speos.client.healthy is True

    # Get DB
    scene_db = speos.client.scenes()  # Create scenes stub from client channel
    part_db = speos.client.parts()  # Create parts stub from client channel
    body_db = speos.client.bodies()  # Create bodies stub from client channel
    face_db = speos.client.faces()  # Create faces stub from client channel
    vop_t_db = speos.client.vop_templates()
    sop_t_db = speos.client.sop_templates()
    spec_db = speos.client.spectrums()
    intens_t_db = speos.client.intensity_templates()
    src_t_db = speos.client.source_templates()

    # Blackbody spectrum
    spec_bb_2500 = spec_db.create(
        SpectrumFactory.blackbody(
            name="blackbody_2500",
            description="blackbody spectrum - T 2500K",
            temperature=2500.0,
        )
    )
    # Luminaire source template with flux from intensity file
    src_t_luminaire = src_t_db.create(
        message=SourceTemplateFactory.luminaire(
            name="luminaire_AA",
            description="Luminaire source template",
            intensity_file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies"),
            spectrum=spec_bb_2500,
        ),
    )
    # Surface with luminous flux, exitance constant
    src_t_surface = src_t_db.create(
        message=SourceTemplateFactory.surface(
            name="surface_BB",
            description="Surface source template",
            intensity_template=intens_t_db.create(
                message=IntensityTemplateFactory.lambertian(
                    name="lambertian_180", description="lambertian intensity template 180", total_angle=180.0
                ),
            ),
            flux=SourceTemplateFactory.Flux(unit=SourceTemplateFactory.Flux.Unit.Lumen, value=683.0),
            spectrum=spec_bb_2500,
        )
    )
    assert src_t_surface.key != ""

    scene0 = scene_db.create(
        message=SceneFactory.scene(
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
                SceneFactory.vop_instance(
                    name="opaque.1",
                    vop_template=vop_t_db.create(message=VOPTemplateFactory.opaque("opaque", "opaque vop template")),
                    geometries=GeoPaths(geo_paths=["part_0"]),
                )
            ],
            sop_instances=[
                SceneFactory.sop_instance(
                    name="mirror_100.1",
                    sop_template=sop_t_db.create(
                        message=SOPTemplateFactory.mirror("mirror_100", "mirror sop template - reflectance 100", reflectance=100)
                    ),
                    geometries=GeoPaths(geo_paths=["part_0/body_0"]),
                )
            ],
            source_instances=[
                SceneFactory.source_instance(
                    name="luminaire_AA.1",
                    source_template=src_t_luminaire,
                    properties=SceneFactory.Properties.Luminaire(axis_system=AxisSystem(origin=[50, 50, 50])),
                ),
                SceneFactory.source_instance(
                    name="luminaire_AA.2",
                    source_template=src_t_luminaire,
                    properties=SceneFactory.Properties.Luminaire(axis_system=AxisSystem(origin=[0, 0, 500])),
                ),
                SceneFactory.source_instance(
                    name="surface_BB.1",
                    source_template=src_t_surface,
                    properties=SceneFactory.Properties.Surface(
                        exitance_props=SceneFactory.Properties.Surface.ExitanceConstant(
                            geo_paths=[
                                GeoPathReverseNormal("part_0/body_0/Face:2", reverse_normal=True),
                                GeoPathReverseNormal("part_0/body_0/Face:3"),
                            ]
                        )
                    ),
                ),
            ],
        )
    )
    assert scene0.key != ""
