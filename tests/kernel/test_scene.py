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

"""Test scene."""

import os
from typing import List, Mapping, Optional

import numpy as np

from ansys.api.speos.sensor.v1 import common_pb2, irradiance_sensor_pb2
from ansys.api.speos.simulation.v1 import simulation_template_pb2
from ansys.speos.core.kernel.body import ProtoBody
from ansys.speos.core.kernel.face import FaceStub, ProtoFace
from ansys.speos.core.kernel.intensity_template import ProtoIntensityTemplate
from ansys.speos.core.kernel.part import ProtoPart
from ansys.speos.core.kernel.scene import ProtoScene, SceneLink
from ansys.speos.core.kernel.sensor_template import ProtoSensorTemplate
from ansys.speos.core.kernel.simulation_template import ProtoSimulationTemplate
from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
from ansys.speos.core.kernel.source_template import ProtoSourceTemplate
from ansys.speos.core.kernel.spectrum import ProtoSpectrum
from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
from ansys.speos.core.speos import Speos
from tests.conftest import test_path
from tests.helper import clean_all_dbs


def create_basic_scene(speos: Speos) -> SceneLink:
    """Function to create basic scene"""
    assert speos.client.healthy is True

    # Get DB
    scene_db = speos.client.scenes()  # Create scenes stub from client channel

    # Create part with two bodies
    main_part = speos.client.parts().create(
        ProtoPart(
            name="main_part",
            description="main_part for scene_0",
            body_guids=[
                speos.client.bodies()
                .create(
                    message=ProtoBody(
                        name="BodySource:1",
                        description="Body used as support for source",
                        face_guids=[
                            speos.client.faces()
                            .create(
                                message=create_face_rectangle(
                                    name="FaceSource:1", x_size=100, y_size=100
                                )
                            )
                            .key
                        ],
                    )
                )
                .key,
                speos.client.bodies()
                .create(
                    message=create_body_box(
                        name="Body0:1",
                        description="Body0:1 in main_part",
                        face_stub=speos.client.faces(),
                        base=[0, 0, 500, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                    )
                )
                .key,
            ],
        )
    )

    # Create blackbody and monochromatic spectrums
    spec_bb_3500 = speos.client.spectrums().create(
        message=ProtoSpectrum(
            name="blackbody_3500",
            description="blackbody spectrum - T 3500K",
            blackbody=ProtoSpectrum.BlackBody(temperature=3500),
        )
    )
    # Create lambertian intensity template
    intens_t_lamb_180 = speos.client.intensity_templates().create(
        message=ProtoIntensityTemplate(
            name="lambertian_180",
            description="lambertian intensity template 180",
            cos=ProtoIntensityTemplate.Cos(N=1.0, total_angle=180.0),
        )
    )

    # Create a luminaire source template with flux from intensity file
    src_t_luminaire = speos.client.source_templates().create(
        message=ProtoSourceTemplate(
            name="luminaire_AA",
            description="Luminaire source template",
            luminaire=ProtoSourceTemplate.Luminaire(
                flux_from_intensity_file=ProtoSourceTemplate.FromIntensityFile(),
                intensity_file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies"),
                spectrum_guid=spec_bb_3500.key,
            ),
        )
    )

    # Create surface source template
    src_t_surface_bb = speos.client.source_templates().create(
        message=ProtoSourceTemplate(
            name="surface_with_monochromatic",
            description="Surface source template with blackbody spectrum",
            surface=ProtoSourceTemplate.Surface(
                luminous_flux=ProtoSourceTemplate.Luminous(luminous_value=683),
                intensity_guid=intens_t_lamb_180.key,
                exitance_constant=ProtoSourceTemplate.Surface.ExitanceConstant(),
                spectrum_guid=spec_bb_3500.key,
            ),
        )
    )

    # Create two irradiance sensor templates: photometric, colorimetric
    ssr_t_irr_photo = speos.client.sensor_templates().create(
        message=ProtoSensorTemplate(
            name="irradiance_photometric",
            description="Irradiance sensor template photometric",
            irradiance_sensor_template=irradiance_sensor_pb2.IrradianceSensorTemplate(
                sensor_type_photometric=common_pb2.SensorTypePhotometric(),
                illuminance_type_planar=common_pb2.IlluminanceTypePlanar(),
                dimensions=common_pb2.SensorDimensions(
                    x_start=-1000.0,
                    x_end=1000.0,
                    x_sampling=200,
                    y_start=-1000.0,
                    y_end=1000.0,
                    y_sampling=200,
                ),
            ),
        )
    )
    ssr_t_irr_colo = speos.client.sensor_templates().create(
        message=ProtoSensorTemplate(
            name="irradiance_colorimetric",
            description="Irradiance sensor template colorimetric",
            irradiance_sensor_template=irradiance_sensor_pb2.IrradianceSensorTemplate(
                sensor_type_colorimetric=common_pb2.SensorTypeColorimetric(
                    wavelengths_range=common_pb2.WavelengthsRange(
                        w_start=300, w_end=700, w_sampling=13
                    )
                ),
                illuminance_type_planar=common_pb2.IlluminanceTypePlanar(),
                dimensions=common_pb2.SensorDimensions(
                    x_start=-1000.0,
                    x_end=1000.0,
                    x_sampling=200,
                    y_start=-1000.0,
                    y_end=1000.0,
                    y_sampling=200,
                ),
            ),
        )
    )

    irr_sensor_props = ProtoScene.SensorInstance.IrradianceProperties(
        axis_system=[0, 0, 1000, -1, 0, 0, 0, 1, 0, 0, 0, -1],
        ray_file_type=ProtoScene.SensorInstance.EnumRayFileType.RayFileNone,
        layer_type_source=ProtoScene.SensorInstance.LayerTypeSource(),
    )

    # Create simu templates with default params
    direct_t = speos.client.simulation_templates().create(
        message=ProtoSimulationTemplate(
            name="direct_simu",
            description="Direct simulation template with default parameters",
            direct_mc_simulation_template=simulation_template_pb2.DirectMCSimulationTemplate(
                geom_distance_tolerance=0.01,
                max_impact=100,
                weight=simulation_template_pb2.Weight(minimum_energy_percentage=0.005),
                colorimetric_standard=simulation_template_pb2.CIE_1931,
                dispersion=True,
            ),
        )
    )
    inverse_t = speos.client.simulation_templates().create(
        message=ProtoSimulationTemplate(
            name="inverse_simu",
            description="Inverse simulation template with default parameters",
            inverse_mc_simulation_template=simulation_template_pb2.InverseMCSimulationTemplate(
                geom_distance_tolerance=0.01,
                max_impact=100,
                weight=simulation_template_pb2.Weight(minimum_energy_percentage=0.005),
                colorimetric_standard=simulation_template_pb2.CIE_1931,
                dispersion=False,
                splitting=False,
                number_of_gathering_rays_per_source=1,
                maximum_gathering_error=0,
            ),
        )
    )
    interactive_t = speos.client.simulation_templates().create(
        message=ProtoSimulationTemplate(
            name="interactive_simu",
            description="Interactive simulation template with default parameters",
            interactive_simulation_template=ProtoSimulationTemplate.Interactive(
                geom_distance_tolerance=0.01,
                max_impact=100,
                weight=simulation_template_pb2.Weight(minimum_energy_percentage=0.005),
                colorimetric_standard=simulation_template_pb2.CIE_1931,
            ),
        )
    )

    # Create a sop template that can be used in different materials
    mirror_100_t = speos.client.sop_templates().create(
        message=ProtoSOPTemplate(
            name="mirror_100",
            description="mirror sop template - reflectance 100",
            mirror=ProtoSOPTemplate.Mirror(reflectance=100),
        )
    )

    # Create a vop template
    opaque_t = speos.client.vop_templates().create(
        message=ProtoVOPTemplate(
            name="opaque", description="opaque vop template", opaque=ProtoVOPTemplate.Opaque()
        )
    )

    # Create scene
    scene = scene_db.create(
        message=ProtoScene(
            name="scene_0",
            description="scene from scratch",
            part_guid=main_part.key,
            materials=[
                ProtoScene.MaterialInstance(
                    name="Material.1",
                    vop_guid=opaque_t.key,
                    sop_guids=[mirror_100_t.key],
                    geometries=ProtoScene.GeoPaths(geo_paths=["Body0:1"]),
                ),
                ProtoScene.MaterialInstance(
                    name="FOP.1",
                    sop_guids=[mirror_100_t.key],
                    geometries=ProtoScene.GeoPaths(geo_paths=["BodySource:1/FaceSource:1"]),
                ),
            ],
            sources=[
                ProtoScene.SourceInstance(
                    name="luminaire_AA.1",
                    source_guid=src_t_luminaire.key,
                    luminaire_properties=ProtoScene.SourceInstance.LuminaireProperties(
                        axis_system=[50, 50, 50, 1, 0, 0, 0, 1, 0, 0, 0, 1]
                    ),
                ),
                ProtoScene.SourceInstance(
                    name="luminaire_AA.2",
                    source_guid=src_t_luminaire.key,
                    luminaire_properties=ProtoScene.SourceInstance.LuminaireProperties(
                        axis_system=[0, 0, 500, 1, 0, 0, 0, 1, 0, 0, 0, 1]
                    ),
                ),
                ProtoScene.SourceInstance(
                    name="surface_with_blackbody.1",
                    source_guid=src_t_surface_bb.key,
                    surface_properties=ProtoScene.SourceInstance.SurfaceProperties(
                        exitance_constant_properties=ProtoScene.SourceInstance.SurfaceProperties.ExitanceConstantProperties(
                            geo_paths=[
                                ProtoScene.GeoPath(geo_path="BodySource:1", reverse_normal=False)
                            ]
                        )
                    ),
                ),
            ],
            sensors=[
                ProtoScene.SensorInstance(
                    name="irradiance_photometric.1",
                    sensor_guid=ssr_t_irr_photo.key,
                    irradiance_properties=irr_sensor_props,
                ),
                ProtoScene.SensorInstance(
                    name="irradiance_colorimetric.1",
                    sensor_guid=ssr_t_irr_colo.key,
                    irradiance_properties=irr_sensor_props,
                ),
            ],
            simulations=[
                ProtoScene.SimulationInstance(
                    name="direct_simu.1",
                    simulation_guid=direct_t.key,
                    source_paths=["luminaire_AA.1", "luminaire_AA.2", "surface_with_blackbody.1"],
                    sensor_paths=["irradiance_photometric.1", "irradiance_colorimetric.1"],
                ),
                ProtoScene.SimulationInstance(
                    name="direct_simu.2",
                    simulation_guid=direct_t.key,
                    source_paths=["surface_with_blackbody.1"],
                    sensor_paths=["irradiance_photometric.1", "irradiance_colorimetric.1"],
                ),
                ProtoScene.SimulationInstance(
                    name="inverse_simu.1",
                    simulation_guid=inverse_t.key,
                    source_paths=["surface_with_blackbody.1"],
                    sensor_paths=["irradiance_colorimetric.1"],
                ),
                ProtoScene.SimulationInstance(
                    name="interactive_simu.1",
                    simulation_guid=interactive_t.key,
                    source_paths=["luminaire_AA.1", "luminaire_AA.2", "surface_with_blackbody.1"],
                    sensor_paths=["irradiance_photometric.1", "irradiance_colorimetric.1"],
                ),
            ],
        )
    )
    return scene


def create_face_rectangle(
    name: str,
    description: str = "",
    base: Optional[List[float]] = None,
    x_size: float = 200,
    y_size: float = 100,
    metadata: Optional[Mapping[str, str]] = None,
) -> ProtoFace:
    """Function to create Rectangular face

    Parameters
    ----------
    name : str
        Name of the face
    description : str
        Description of the face.
        By default, ``""``.
    base : Optional[List[float]]
        Start location and horizontal and vertical direction
        By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0]``.
    x_size : float
        first base vector size
        By default, ``100``
    y_size : float
        second base vector size
        By default, ``100``
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.

    Returns
    -------
    ansys.speos.core.kerne.face.ProtoFace
        A rectangular Face
    """
    if base is None:
        base = [0, 0, 0, 1, 0, 0, 0, 1, 0]
    if metadata is None:
        metadata = {}

    face = ProtoFace(name=name, description=description, metadata=metadata)

    face.vertices.extend(
        base[:3] - np.multiply(0.5 * x_size, base[3:6]) - np.multiply(0.5 * y_size, base[6:9])
    )
    face.vertices.extend(
        base[:3] + np.multiply(0.5 * x_size, base[3:6]) - np.multiply(0.5 * y_size, base[6:9])
    )
    face.vertices.extend(
        base[:3] + np.multiply(0.5 * x_size, base[3:6]) + np.multiply(0.5 * y_size, base[6:9])
    )
    face.vertices.extend(
        base[:3] - np.multiply(0.5 * x_size, base[3:6]) + np.multiply(0.5 * y_size, base[6:9])
    )

    normal = np.cross(base[3:6], base[6:9])
    for i in range(4):
        face.normals.extend(normal)

    face.facets.extend([0, 1, 3, 1, 2, 3])

    return face


def create_body_box(
    name: str,
    face_stub: FaceStub,
    description: str = "",
    base: Optional[List[float]] = None,
    x_size: float = 200,
    y_size: float = 200,
    z_size: float = 100,
    idx_face: int = 0,
    metadata: Optional[Mapping[str, str]] = None,
) -> ProtoBody:
    """Function to create a box in a scene.

    Parameters
    ----------
    name : str
        Name of the face
    face_stub : ansys.speos.core.kernel.face.FaceStub
        facestub to create faces in scene
    description : str
        Description of the face.
        By default, ``""``.
    base : Optional[List[float]]
        Start location and horizontal and vertical direction
        By default, ``[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]``.
    x_size : float
        first base vector size
        By default, ``100``
    y_size : float
        second base vector size
        By default, ``100``
    z_size : float
        third base vector sizee
    idx_face : int
        Starting number for Face counter
    metadata : Optional[Mapping[str, str]]
        Metadata of the feature.
        By default, ``{}``.

    Returns
    -------
    ansys.speos.core.kernel.body.ProtoBody
        ProtoBody
    """
    if base is None:
        base = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    if metadata is None:
        metadata = {}

    body = ProtoBody(name=name, description=description, metadata=metadata)

    base0 = []
    base0.extend(base[:3] - np.multiply(0.5 * z_size, base[9:]))  # origin
    base0.extend(np.multiply(-1, base[3:6]))  # x_vect
    base0.extend(base[6:9])  # y_vect
    face0 = face_stub.create(
        message=create_face_rectangle(
            name="Face:" + str(idx_face), base=base0, x_size=x_size, y_size=y_size
        )
    )

    base1 = []
    base1.extend(base[:3] + np.multiply(0.5 * z_size, base[9:]))
    base1.extend(base[3:6])
    base1.extend(base[6:9])
    face1 = face_stub.create(
        message=create_face_rectangle(
            name="Face:" + str(idx_face + 1), base=base1, x_size=x_size, y_size=y_size
        )
    )

    base2 = []
    base2.extend(base[:3] - np.multiply(0.5 * x_size, base[3:6]))
    base2.extend(base[9:])
    base2.extend(base[6:9])
    face2 = face_stub.create(
        message=create_face_rectangle(
            name="Face:" + str(idx_face + 2), base=base2, x_size=z_size, y_size=y_size
        )
    )

    base3 = []
    base3.extend(base[:3] + np.multiply(0.5 * x_size, base[3:6]))
    base3.extend(np.multiply(-1, base[9:]))
    base3.extend(base[6:9])
    face3 = face_stub.create(
        message=create_face_rectangle(
            name="Face:" + str(idx_face + 3), base=base3, x_size=z_size, y_size=y_size
        )
    )

    base4 = []
    base4.extend(base[:3] - np.multiply(0.5 * y_size, base[6:9]))
    base4.extend(base[3:6])
    base4.extend(base[9:])
    face4 = face_stub.create(
        message=create_face_rectangle(
            name="Face:" + str(idx_face + 4), base=base4, x_size=x_size, y_size=z_size
        )
    )

    base5 = []
    base5.extend(base[:3] + np.multiply(0.5 * y_size, base[6:9]))
    base5.extend(base[3:6])
    base5.extend(np.multiply(-1, base[9:]))
    face5 = face_stub.create(
        message=create_face_rectangle(
            name="Face:" + str(idx_face + 5), base=base5, x_size=x_size, y_size=z_size
        )
    )

    body.face_guids.extend([face0.key, face1.key, face2.key, face3.key, face4.key, face5.key])
    return body


def test_scene(speos: Speos):
    """Test the scene creation."""
    assert speos.client.healthy is True

    scene0 = create_basic_scene(speos)
    assert scene0.key != ""

    clean_all_dbs(speos.client)


def test_scene_actions_load(speos: Speos):
    """Test the scene action: load file."""
    assert speos.client.healthy is True
    speos_file_path = os.path.join(
        test_path, os.path.join("LG_50M_Colorimetric_short.sv5", "LG_50M_Colorimetric_short.sv5")
    )

    # Create empty scene + load_file
    scene = speos.client.scenes().create()
    scene.load_file(file_uri=speos_file_path)

    scene_dm = scene.get()
    assert len(scene_dm.sources) == 2
    assert len(scene_dm.sensors) == 1
    assert len(scene_dm.simulations) == 1

    clean_all_dbs(speos.client)


def test_scene_actions_load_modify(speos: Speos):
    """Test the scene action: load file and modify sensors."""
    assert speos.client.healthy is True
    speos_file_path = os.path.join(
        test_path, os.path.join("LG_50M_Colorimetric_short.sv5", "LG_50M_Colorimetric_short.sv5")
    )

    # Create empty scene + load_file
    scene = speos.client.scenes().create()
    scene.load_file(file_uri=speos_file_path)

    # Modify existing sensor : layer_type_source -> layer_type_none
    scene_dm = scene.get()  # Retrieve scene data from DB
    assert len(scene_dm.sensors) == 1
    assert scene_dm.sensors[0].HasField("irradiance_properties")
    assert scene_dm.sensors[0].irradiance_properties.HasField("layer_type_source")
    scene_dm.sensors[0].irradiance_properties.layer_type_none.SetInParent()
    scene.set(data=scene_dm)  # Update the scene in DB

    # Retrieve scene data from DB
    scene_dm = scene.get()
    # Check that our change was effective layer_type_source -> layer_type_none
    assert scene_dm.sensors[0].irradiance_properties.HasField("layer_type_none")

    # Adding a sensor
    scene_dm.sensors.append(
        ProtoScene.SensorInstance(
            name="Irradiance.1",
            sensor_guid=scene_dm.sensors[0].sensor_guid,
            irradiance_properties=ProtoScene.SensorInstance.IrradianceProperties(
                axis_system=[-42, 2, 5, 0, 1, 0, 0, 0, -1, -1, 0, 0],
                layer_type_incidence_angle=ProtoScene.SensorInstance.LayerTypeIncidenceAngle(
                    sampling=9
                ),
            ),
        )
    )
    scene.set(data=scene_dm)  # Update the scene in DB

    assert len(scene.get().sensors) == 2

    clean_all_dbs(speos.client)


def test_scene_actions_get_source_ray_paths(speos: Speos):
    """Test the scene action: load file and modify sensors."""
    assert speos.client.healthy is True

    # Creation of a basic scene with a luminaire source
    main_part = speos.client.parts().create(message=ProtoPart(name="MainPart", body_guids=[]))

    blackbody_2856 = speos.client.spectrums().create(
        message=ProtoSpectrum(
            name="Blackbody_2856", blackbody=ProtoSpectrum.BlackBody(temperature=2856)
        )
    )
    luminaire_t = speos.client.source_templates().create(
        message=ProtoSourceTemplate(
            name="Luminaire",
            luminaire=ProtoSourceTemplate.Luminaire(
                flux_from_intensity_file=ProtoSourceTemplate.FromIntensityFile(),
                intensity_file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies"),
                spectrum_guid=blackbody_2856.key,
            ),
        )
    )

    scene = speos.client.scenes().create(
        message=ProtoScene(
            name="Scene with sources",
            part_guid=main_part.key,
            materials=[],
            sources=[
                ProtoScene.SourceInstance(
                    name="Luminaire.1",
                    source_guid=luminaire_t.key,
                    luminaire_properties=ProtoScene.SourceInstance.LuminaireProperties(
                        axis_system=[0, 0, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]
                    ),
                )
            ],
            sensors=[],
            simulations=[],
        )
    )

    # Get ray_paths
    for ray_path in scene.get_source_ray_paths(source_path="Luminaire.1", rays_nb=20):
        assert ray_path.impacts_coordinates == [0, 0, 20]

    clean_all_dbs(speos.client)
