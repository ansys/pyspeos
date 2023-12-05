"""
Test scene.
"""
import os

from ansys.speos.core.body import BodyFactory
from ansys.speos.core.geometry import AxisSystem, GeoPaths
from ansys.speos.core.intensity_template import IntensityTemplateFactory
from ansys.speos.core.part import PartFactory
from ansys.speos.core.scene import SceneFactory
from ansys.speos.core.sensor_template import SensorTemplateFactory
from ansys.speos.core.simulation_template import SimulationTemplateFactory
from ansys.speos.core.sop_template import SOPTemplateFactory
from ansys.speos.core.source_template import SourceTemplateFactory
from ansys.speos.core.spectrum import SpectrumFactory
from ansys.speos.core.speos import Speos
from ansys.speos.core.vop_template import VOPTemplateFactory
from conftest import test_path
from helper import clean_all_dbs


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
    ssr_t_db = speos.client.sensor_templates()
    sim_t_db = speos.client.simulation_templates()

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
    # Surface source template with luminous flux, exitance constant
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
    # Irradiance sensor template photometric
    ssr_t_irr = ssr_t_db.create(
        message=SensorTemplateFactory.irradiance(
            name="irradiance_photometric",
            description="Irradiance sensor template photometric",
            type=SensorTemplateFactory.Type.Photometric,
            illuminance_type=SensorTemplateFactory.IlluminanceType.Planar,
            dimensions=SensorTemplateFactory.Dimensions(
                x_start=-50.0, x_end=50.0, x_sampling=100, y_start=-50.0, y_end=50.0, y_sampling=100
            ),
        )
    )
    assert ssr_t_irr.key != ""
    # Direct simu with default params
    direct_t = sim_t_db.create(
        message=SimulationTemplateFactory.direct_mc(name="direct_sim", description="Direct simulation template with default parameters")
    )

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
                    geometries=GeoPaths(geo_paths=["body_0"]),
                )
            ],
            sop_instances=[
                SceneFactory.sop_instance(
                    name="mirror_100.1",
                    sop_template=sop_t_db.create(
                        message=SOPTemplateFactory.mirror("mirror_100", "mirror sop template - reflectance 100", reflectance=100)
                    ),
                    geometries=GeoPaths(geo_paths=["body_0"]),
                )
            ],
            source_instances=[
                SceneFactory.source_instance(
                    name="luminaire_AA.1",
                    source_template=src_t_luminaire,
                    properties=SceneFactory.luminaire_source_props(axis_system=AxisSystem(origin=[50, 50, 50])),
                ),
                SceneFactory.source_instance(
                    name="luminaire_AA.2",
                    source_template=src_t_luminaire,
                    properties=SceneFactory.luminaire_source_props(axis_system=AxisSystem(origin=[0, 0, 500])),
                ),
                SceneFactory.source_instance(
                    name="surface_BB.1",
                    source_template=src_t_surface,
                    properties=SceneFactory.surface_source_props(
                        exitance_constant_geo_paths={"body_0/Face:2": True, "body_0/Face:3": False, "body_0/Face:4": False}
                    ),
                ),
            ],
            sensor_instances=[
                SceneFactory.sensor_instance(
                    name="irradiance_photometric.1",
                    sensor_template=ssr_t_irr,
                    properties=SceneFactory.irradiance_sensor_props(
                        axis_system=AxisSystem(origin=[0, 50, 0], x_vect=[1, 0, 0], y_vect=[0, 0, -1], z_vect=[0, 1, 0]),
                        layer_type=SceneFactory.Properties.Sensor.LayerType.Source(),
                    ),
                ),
                SceneFactory.sensor_instance(
                    name="irradiance_photometric.2",
                    sensor_template=ssr_t_irr,
                    properties=SceneFactory.irradiance_sensor_props(
                        axis_system=AxisSystem(origin=[0, -50, 0], x_vect=[1, 0, 0], y_vect=[0, 0, 1], z_vect=[0, -1, 0]),
                    ),
                ),
                SceneFactory.sensor_instance(
                    name="irradiance_photometric.3",
                    sensor_template=ssr_t_irr,
                    properties=SceneFactory.irradiance_sensor_props(
                        axis_system=AxisSystem(origin=[0, 0, 100]),
                        layer_type=SceneFactory.Properties.Sensor.LayerType.Source(),
                    ),
                ),
            ],
            simulation_instances=[
                SceneFactory.simulation_instance(name="direct_sim.1", simulation_template=direct_t),
                SceneFactory.simulation_instance(
                    name="direct_sim.1",
                    simulation_template=direct_t,
                    source_paths=["luminaire_AA.1", "luminaire_AA.2"],
                    sensor_paths=["irradiance_photometric.1"],
                    geometries=GeoPaths(["body_0"]),
                ),
            ],
        )
    )
    assert scene0.key != ""

    clean_all_dbs(speos.client)
