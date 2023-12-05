"""
Test scene.
"""
import os

from ansys.speos.core.body import BodyFactory
from ansys.speos.core.face import FaceFactory
from ansys.speos.core.geometry_utils import AxisSystem, GeoPaths
from ansys.speos.core.intensity_template import IntensityTemplateFactory
from ansys.speos.core.part import PartFactory
from ansys.speos.core.scene import SceneFactory, SceneLink
from ansys.speos.core.sensor_template import SensorTemplateFactory
from ansys.speos.core.simulation_template import SimulationTemplateFactory
from ansys.speos.core.sop_template import SOPTemplateFactory
from ansys.speos.core.source_template import SourceTemplateFactory
from ansys.speos.core.spectrum import SpectrumFactory
from ansys.speos.core.speos import Speos
from ansys.speos.core.vop_template import VOPTemplateFactory
from conftest import test_path
from helper import clean_all_dbs


def create_basic_scene(speos: Speos) -> SceneLink:
    assert speos.client.healthy is True

    # Get DB
    scene_db = speos.client.scenes()  # Create scenes stub from client channel

    # Create part with two bodies
    main_part = speos.client.parts().create(
        PartFactory.new(
            name="main_part",
            description="main_part for scene_0",
            bodies=[
                speos.client.bodies().create(
                    message=BodyFactory.new(
                        name="BodySource:1",
                        description="Body used as support for source",
                        faces=[speos.client.faces().create(message=FaceFactory.rectangle(name="FaceSource:1", x_size=100, y_size=100))],
                    )
                ),
                speos.client.bodies().create(
                    message=BodyFactory.box(
                        name="Body0:1",
                        description="Body0:1 in main_part",
                        face_stub=speos.client.faces(),
                        base=AxisSystem(origin=[0, 0, 500]),
                    )
                ),
            ],
        )
    )

    # Create blackbody and monochromatic spectrums
    spec_bb_3500 = speos.client.spectrums().create(
        message=SpectrumFactory.blackbody(
            name="blackbody_3500",
            description="blackbody spectrum - T 3500K",
            temperature=3500,
        )
    )
    # Create lambertian intensity template
    intens_t_lamb_180 = speos.client.intensity_templates().create(
        message=IntensityTemplateFactory.lambertian(
            name="lambertian_180", description="lambertian intensity template 180", total_angle=180.0
        )
    )

    # Create a luminaire source template with flux from intensity file
    src_t_luminaire = speos.client.source_templates().create(
        message=SourceTemplateFactory.luminaire(
            name="luminaire_AA",
            description="Luminaire source template",
            intensity_file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies"),
            spectrum=spec_bb_3500,
        ),
    )
    # Create surface source template
    src_t_surface_bb = speos.client.source_templates().create(
        message=SourceTemplateFactory.surface(
            name="surface_with_monochromatic",
            description="Surface source template with blackbody spectrum",
            intensity_template=intens_t_lamb_180,
            flux=SourceTemplateFactory.Flux(unit=SourceTemplateFactory.Flux.Unit.Lumen, value=683.0),
            spectrum=spec_bb_3500,
        )
    )

    # Create two irradiance sensor templates: photometric, colorimetric
    ssr_t_irr_photo = speos.client.sensor_templates().create(
        message=SensorTemplateFactory.irradiance(
            name="irradiance_photometric",
            description="Irradiance sensor template photometric",
            type=SensorTemplateFactory.Type.Photometric,
            illuminance_type=SensorTemplateFactory.IlluminanceType.Planar,
            dimensions=SensorTemplateFactory.Dimensions(
                x_start=-1000.0, x_end=1000.0, x_sampling=200, y_start=-1000.0, y_end=1000.0, y_sampling=200
            ),
        )
    )
    ssr_t_irr_colo = speos.client.sensor_templates().create(
        message=SensorTemplateFactory.irradiance(
            name="irradiance_colorimetric",
            description="Irradiance sensor template colorimetric",
            type=SensorTemplateFactory.Type.Colorimetric,
            illuminance_type=SensorTemplateFactory.IlluminanceType.Planar,
            dimensions=SensorTemplateFactory.Dimensions(
                x_start=-1000.0, x_end=1000.0, x_sampling=200, y_start=-1000.0, y_end=1000.0, y_sampling=200
            ),
            wavelengths_range=SensorTemplateFactory.WavelengthsRange(start=300, end=700, sampling=13),
        )
    )
    irr_sensor_props = SceneFactory.irradiance_sensor_props(
        axis_system=AxisSystem(origin=[0, 0, 1000], x_vect=[1, 0, 0], y_vect=[0, 1, 0], z_vect=[0, 0, -1]),
        layer_type=SceneFactory.Properties.Sensor.LayerType.Source(),
        integration_direction=[0, 0, 1],
    )

    # Create simu templates with default params
    direct_t = speos.client.simulation_templates().create(
        message=SimulationTemplateFactory.direct_mc(name="direct_simu", description="Direct simulation template with default parameters")
    )
    inverse_t = speos.client.simulation_templates().create(
        message=SimulationTemplateFactory.inverse_mc(name="inverse_simu", description="Inverse simulation template with default parameters")
    )
    interactive_t = speos.client.simulation_templates().create(
        message=SimulationTemplateFactory.interactive(
            name="interactive_simu", description="Interactive simulation template with default parameters"
        )
    )

    scene = scene_db.create(
        message=SceneFactory.new(
            name="scene_0",
            description="scene from scratch",
            part=main_part,
            vop_instances=[
                SceneFactory.vop_instance(
                    name="opaque.1",
                    vop_template=speos.client.vop_templates().create(message=VOPTemplateFactory.opaque("opaque", "opaque vop template")),
                    geometries=GeoPaths(geo_paths=["Body0:1"]),
                )
            ],
            sop_instances=[
                SceneFactory.sop_instance(
                    name="mirror_100.1",
                    sop_template=speos.client.sop_templates().create(
                        message=SOPTemplateFactory.mirror("mirror_100", "mirror sop template - reflectance 100", reflectance=100)
                    ),
                    geometries=GeoPaths(geo_paths=["Body0:1", "BodySource:1/FaceSource:1"]),
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
                    name="surface_with_blackbody.1",
                    source_template=src_t_surface_bb,
                    properties=SceneFactory.surface_source_props(exitance_constant_geo_paths={"BodySource:1": False}),
                ),
            ],
            sensor_instances=[
                SceneFactory.sensor_instance(
                    name="irradiance_photometric.1",
                    sensor_template=ssr_t_irr_photo,
                    properties=irr_sensor_props,
                ),
                SceneFactory.sensor_instance(
                    name="irradiance_colorimetric.1",
                    sensor_template=ssr_t_irr_colo,
                    properties=irr_sensor_props,
                ),
            ],
            simulation_instances=[
                SceneFactory.simulation_instance(name="direct_simu.1", simulation_template=direct_t),
                SceneFactory.simulation_instance(
                    name="direct_simu.2",
                    simulation_template=direct_t,
                    source_paths=["surface_with_blackbody.1"],
                    sensor_paths=["irradiance_photometric.1", "irradiance_colorimetric.1"],
                    geometries=GeoPaths(["BodySource:1", "Body0:1"]),
                ),
                SceneFactory.simulation_instance(
                    name="inverse_simu.1", simulation_template=inverse_t, sensor_paths=["irradiance_colorimetric.1"]
                ),
                SceneFactory.simulation_instance(name="interactive_simu.1", simulation_template=interactive_t),
            ],
        )
    )
    return scene


def test_scene_factory(speos: Speos):
    """Test the scene factory."""
    assert speos.client.healthy is True

    scene0 = create_basic_scene(speos)
    assert scene0.key != ""

    clean_all_dbs(speos.client)
