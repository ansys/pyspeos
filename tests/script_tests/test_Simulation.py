# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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
Test basic using simulation from script layer.
"""

import os

from ansys.api.speos.simulation.v1 import simulation_template_pb2

from ansys.speos.core.speos import Speos
import ansys.speos.script as script
from conftest import test_path


def test_create_direct(speos: Speos):
    """Test creation of Direct Simulation."""
    p = script.Project(speos=speos)

    # Default value
    sim1 = p.create_simulation(name="Direct.1")
    sim1.set_direct()  # do not commit to avoid issues about No sensor in simulation
    assert sim1._simulation_template.HasField("direct_mc_simulation_template")
    assert sim1._simulation_template.direct_mc_simulation_template.geom_distance_tolerance == 0.01
    assert sim1._simulation_template.direct_mc_simulation_template.max_impact == 100
    assert sim1._simulation_template.direct_mc_simulation_template.colorimetric_standard == simulation_template_pb2.CIE_1931
    assert sim1._simulation_template.direct_mc_simulation_template.dispersion == True
    assert sim1._simulation_template.direct_mc_simulation_template.fast_transmission_gathering == False
    assert sim1._simulation_template.direct_mc_simulation_template.ambient_material_uri == ""
    assert sim1._simulation_template.direct_mc_simulation_template.HasField("weight")
    assert sim1._simulation_template.direct_mc_simulation_template.weight.minimum_energy_percentage == 0.005
    assert len(sim1._simulation_instance.sensor_paths) == 0
    assert len(sim1._simulation_instance.source_paths) == 0
    assert len(sim1._simulation_instance.geometries.geo_paths) == 0

    # Change value
    # geom_distance_tolerance
    sim1.set_direct().set_geom_distance_tolerance(value=0.1)
    assert sim1._simulation_template.direct_mc_simulation_template.geom_distance_tolerance == 0.1

    # max_impact
    sim1.set_direct().set_max_impact(value=200)
    assert sim1._simulation_template.direct_mc_simulation_template.max_impact == 200

    # weight - minimum_energy_percentage
    sim1.set_direct().set_weight_none()
    assert sim1._simulation_template.direct_mc_simulation_template.HasField("weight") == False

    sim1.set_direct().set_weight().set_minimum_energy_percentage(value=0.7)
    assert sim1._simulation_template.direct_mc_simulation_template.HasField("weight")
    assert sim1._simulation_template.direct_mc_simulation_template.weight.minimum_energy_percentage == 0.7

    # colorimetric_standard
    sim1.set_direct().set_colorimetric_standard_CIE_1964()
    assert sim1._simulation_template.direct_mc_simulation_template.colorimetric_standard == simulation_template_pb2.CIE_1964

    # dispersion
    sim1.set_direct().set_dispersion(value=False)
    assert sim1._simulation_template.direct_mc_simulation_template.dispersion == False

    # fast_transmission_gathering
    # sim1.set_direct().set_fast_transmission_gathering(value=True)
    # assert sim1._simulation_template.direct_mc_simulation_template.fast_transmission_gathering == True

    # ambient_material_uri
    sim1.set_direct().set_ambient_material_file_uri(uri=os.path.join(test_path, "AIR.material"))
    assert sim1._simulation_template.direct_mc_simulation_template.ambient_material_uri.endswith("AIR.material")

    # sensor_paths
    sim1.set_sensor_paths(sensor_paths=["sensor.1", "sensor.2"])
    assert sim1._simulation_instance.sensor_paths == ["sensor.1", "sensor.2"]

    # source_paths
    sim1.set_source_paths(source_paths=["source.1"])
    assert sim1._simulation_instance.source_paths == ["source.1"]

    # geometries
    # sim1.set_geometries(
    #    geometries=[
    #        script.GeoRef.from_native_link(geopath="mybody1"),
    #        script.GeoRef.from_native_link(geopath="mybody2"),
    #        script.GeoRef.from_native_link(geopath="mybody3"),
    #    ]
    # )
    # assert sim1._simulation_instance.geometries.geo_paths == ["mybody1", "mybody2", "mybody3"]

    sim1.delete()


def test_create_inverse(speos: Speos):
    """Test creation of Inverse Simulation."""
    p = script.Project(speos=speos)

    # Default value
    sim1 = p.create_simulation(name="Inverse.1")
    sim1.set_inverse()  # do not commit to avoid issues about No sensor in simulation
    assert sim1._simulation_template.HasField("inverse_mc_simulation_template")
    assert sim1._simulation_template.inverse_mc_simulation_template.geom_distance_tolerance == 0.01
    assert sim1._simulation_template.inverse_mc_simulation_template.max_impact == 100
    assert sim1._simulation_template.inverse_mc_simulation_template.colorimetric_standard == simulation_template_pb2.CIE_1931
    assert sim1._simulation_template.inverse_mc_simulation_template.HasField("weight")
    assert sim1._simulation_template.inverse_mc_simulation_template.weight.minimum_energy_percentage == 0.005
    assert sim1._simulation_template.inverse_mc_simulation_template.dispersion == False
    assert sim1._simulation_template.inverse_mc_simulation_template.splitting == False
    assert sim1._simulation_template.inverse_mc_simulation_template.number_of_gathering_rays_per_source == 1
    assert sim1._simulation_template.inverse_mc_simulation_template.maximum_gathering_error == 0
    assert sim1._simulation_template.inverse_mc_simulation_template.fast_transmission_gathering == False
    assert sim1._simulation_template.inverse_mc_simulation_template.ambient_material_uri == ""
    assert len(sim1._simulation_instance.sensor_paths) == 0
    assert len(sim1._simulation_instance.source_paths) == 0
    assert len(sim1._simulation_instance.geometries.geo_paths) == 0

    # Change value
    # geom_distance_tolerance
    sim1.set_inverse().set_geom_distance_tolerance(value=0.1)
    assert sim1._simulation_template.inverse_mc_simulation_template.geom_distance_tolerance == 0.1

    # max_impact
    sim1.set_inverse().set_max_impact(value=200)
    assert sim1._simulation_template.inverse_mc_simulation_template.max_impact == 200

    # weight - minimum_energy_percentage
    sim1.set_inverse().set_weight_none()
    assert sim1._simulation_template.inverse_mc_simulation_template.HasField("weight") == False

    sim1.set_inverse().set_weight().set_minimum_energy_percentage(value=0.7)
    assert sim1._simulation_template.inverse_mc_simulation_template.HasField("weight")
    assert sim1._simulation_template.inverse_mc_simulation_template.weight.minimum_energy_percentage == 0.7

    # colorimetric_standard
    sim1.set_inverse().set_colorimetric_standard_CIE_1964()
    assert sim1._simulation_template.inverse_mc_simulation_template.colorimetric_standard == simulation_template_pb2.CIE_1964

    # dispersion
    sim1.set_inverse().set_dispersion(value=True)
    assert sim1._simulation_template.inverse_mc_simulation_template.dispersion == True

    # splitting
    sim1.set_inverse().set_splitting(value=True)
    assert sim1._simulation_template.inverse_mc_simulation_template.splitting == True

    # number_of_gathering_rays_per_source
    sim1.set_inverse().set_number_of_gathering_rays_per_source(value=2)
    assert sim1._simulation_template.inverse_mc_simulation_template.number_of_gathering_rays_per_source == 2

    # maximum_gathering_error
    sim1.set_inverse().set_maximum_gathering_error(value=3)
    assert sim1._simulation_template.inverse_mc_simulation_template.maximum_gathering_error == 3

    # fast_transmission_gathering
    # sim1.set_inverse().set_fast_transmission_gathering(value=True)
    # assert sim1._simulation_template.inverse_mc_simulation_template.fast_transmission_gathering == True

    # ambient_material_uri
    sim1.set_inverse().set_ambient_material_file_uri(uri=os.path.join(test_path, "AIR.material"))
    assert sim1._simulation_template.inverse_mc_simulation_template.ambient_material_uri.endswith("AIR.material")

    # sensor_paths
    sim1.set_sensor_paths(sensor_paths=["sensor.1", "sensor.2"])
    assert sim1._simulation_instance.sensor_paths == ["sensor.1", "sensor.2"]

    # source_paths
    sim1.set_source_paths(source_paths=["source.1"])
    assert sim1._simulation_instance.source_paths == ["source.1"]

    # geometries
    # sim1.set_geometries(
    #    geometries=[
    #        script.GeoRef.from_native_link(geopath="mybody1"),
    #        script.GeoRef.from_native_link(geopath="mybody2"),
    #        script.GeoRef.from_native_link(geopath="mybody3"),
    #    ]
    # )
    # assert sim1._simulation_instance.geometries.geo_paths == ["mybody1", "mybody2", "mybody3"]

    sim1.delete()


def test_create_interactive(speos: Speos):
    """Test creation of Interactive Simulation."""
    p = script.Project(speos=speos)

    # Default value
    sim1 = p.create_simulation(name="Interactive.1")
    sim1.set_interactive()  # do not commit to avoid issues about No sensor in simulation
    assert sim1._simulation_template.HasField("interactive_simulation_template")
    assert sim1._simulation_template.interactive_simulation_template.geom_distance_tolerance == 0.01
    assert sim1._simulation_template.interactive_simulation_template.max_impact == 100
    assert sim1._simulation_template.interactive_simulation_template.colorimetric_standard == simulation_template_pb2.CIE_1931
    assert sim1._simulation_template.interactive_simulation_template.HasField("weight")
    assert sim1._simulation_template.interactive_simulation_template.weight.minimum_energy_percentage == 0.005
    assert sim1._simulation_template.interactive_simulation_template.ambient_material_uri == ""
    assert len(sim1._simulation_instance.sensor_paths) == 0
    assert len(sim1._simulation_instance.source_paths) == 0
    assert len(sim1._simulation_instance.geometries.geo_paths) == 0

    # Change value
    # geom_distance_tolerance
    sim1.set_interactive().set_geom_distance_tolerance(value=0.1)
    assert sim1._simulation_template.interactive_simulation_template.geom_distance_tolerance == 0.1

    # max_impact
    sim1.set_interactive().set_max_impact(value=200)
    assert sim1._simulation_template.interactive_simulation_template.max_impact == 200

    # weight - minimum_energy_percentage
    sim1.set_interactive().set_weight_none()
    assert sim1._simulation_template.interactive_simulation_template.HasField("weight") == False

    sim1.set_interactive().set_weight().set_minimum_energy_percentage(value=0.7)
    assert sim1._simulation_template.interactive_simulation_template.HasField("weight")
    assert sim1._simulation_template.interactive_simulation_template.weight.minimum_energy_percentage == 0.7

    # colorimetric_standard
    sim1.set_interactive().set_colorimetric_standard_CIE_1964()
    assert sim1._simulation_template.interactive_simulation_template.colorimetric_standard == simulation_template_pb2.CIE_1964

    # ambient_material_uri
    sim1.set_interactive().set_ambient_material_file_uri(uri=os.path.join(test_path, "AIR.material"))
    assert sim1._simulation_template.interactive_simulation_template.ambient_material_uri.endswith("AIR.material")

    # sensor_paths
    sim1.set_sensor_paths(sensor_paths=["sensor.1", "sensor.2"])
    assert sim1._simulation_instance.sensor_paths == ["sensor.1", "sensor.2"]

    # source_paths
    sim1.set_source_paths(source_paths=["source.1"])
    assert sim1._simulation_instance.source_paths == ["source.1"]

    # geometries
    # sim1.set_geometries(
    #    geometries=[
    #        script.GeoRef.from_native_link(geopath="mybody1"),
    #        script.GeoRef.from_native_link(geopath="mybody2"),
    #        script.GeoRef.from_native_link(geopath="mybody3"),
    #    ]
    # )
    # assert sim1._simulation_instance.geometries.geo_paths == ["mybody1", "mybody2", "mybody3"]

    sim1.delete()


def test_commit(speos: Speos):
    """Test commit of simulation."""
    p = script.Project(speos=speos)

    # Prerequisites: a source and a sensor are needed (bug also a rootpart)
    root_part = p.create_root_part()
    root_part.create_body(name="Body.1").create_face(name="Face.1").set_vertices([0, 1, 0, 0, 2, 0, 1, 2, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    ssr = p.create_sensor(name="Irradiance.1")
    ssr.set_irradiance().set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr.commit()

    ssr2 = p.create_sensor(name="Irradiance.2")
    ssr2.set_irradiance().set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr2.commit()

    src = p.create_source(name="Luminaire.1")
    src.set_luminaire().set_intensity_file_uri(uri=os.path.join(test_path, "IES_C_DETECTOR.ies"))
    src.commit()

    # Create
    sim1 = p.create_simulation(name="Direct.1")
    sim1.set_direct()
    sim1.set_sensor_paths(sensor_paths=[ssr._name]).set_source_paths(source_paths=[src._name])
    assert sim1.simulation_template_link is None
    assert len(p.scene_link.get().simulations) == 0

    # Commit
    sim1.commit()
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")

    assert len(p.scene_link.get().simulations) == 1
    assert p.scene_link.get().simulations[0] == sim1._simulation_instance

    # Change only in local not committed (on template and on instance)
    sim1.set_direct().set_geom_distance_tolerance(value=0.1)
    assert sim1.simulation_template_link.get() != sim1._simulation_template
    sim1.set_sensor_paths(["Irradiance.1, Irradiance.2"])
    assert p.scene_link.get().simulations[0] != sim1._simulation_instance

    sim1.delete()


def test_reset(speos: Speos):
    """Test reset of simulation."""
    p = script.Project(speos=speos)

    # Prerequisites: a source and a sensor are needed (bug also a rootpart)
    root_part = p.create_root_part()
    root_part.create_body(name="Body.1").create_face(name="Face.1").set_vertices([0, 1, 0, 0, 2, 0, 1, 2, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    ssr = p.create_sensor(name="Irradiance.1")
    ssr.set_irradiance().set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr.commit()

    ssr2 = p.create_sensor(name="Irradiance.2")
    ssr2.set_irradiance().set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr2.commit()

    src = p.create_source(name="Luminaire.1")
    src.set_luminaire().set_intensity_file_uri(uri=os.path.join(test_path, "IES_C_DETECTOR.ies"))
    src.commit()

    # Create + commit
    sim1 = p.create_simulation(name="Direct.1")
    sim1.set_direct()
    sim1.set_sensor_paths(sensor_paths=[ssr._name]).set_source_paths(source_paths=[src._name]).commit()
    assert sim1.simulation_template_link is not None
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")
    assert len(p.scene_link.get().simulations) == 1

    # Change local data (on template and on instance)
    sim1.set_direct().set_geom_distance_tolerance(value=0.1)
    assert sim1.simulation_template_link.get() != sim1._simulation_template
    sim1.set_sensor_paths(["Irradiance.1, Irradiance.2"])
    assert p.scene_link.get().simulations[0] != sim1._simulation_instance

    # Ask for reset
    sim1.reset()
    assert sim1.simulation_template_link.get() == sim1._simulation_template
    assert p.scene_link.get().simulations[0] == sim1._simulation_instance

    sim1.delete()


def test_delete_source(speos: Speos):
    """Test delete of source."""
    p = script.Project(speos=speos)

    # Prerequisites: a source and a sensor are needed (bug also a rootpart)
    root_part = p.create_root_part()
    root_part.create_body(name="Body.1").create_face(name="Face.1").set_vertices([0, 1, 0, 0, 2, 0, 1, 2, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    ssr = p.create_sensor(name="Irradiance.1")
    ssr.set_irradiance().set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr.commit()

    src = p.create_source(name="Luminaire.1")
    src.set_luminaire().set_intensity_file_uri(uri=os.path.join(test_path, "IES_C_DETECTOR.ies"))
    src.commit()

    # Create + commit
    sim1 = p.create_simulation(name="Direct.1")
    sim1.set_direct()
    sim1.set_sensor_paths(sensor_paths=[ssr._name]).set_source_paths(source_paths=[src._name]).commit()
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")
    assert sim1._simulation_template.HasField("direct_mc_simulation_template")  # local template
    assert len(p.scene_link.get().simulations) == 1
    assert len(p.scene_link.get().simulations[0].sensor_paths) == 1
    assert len(sim1._simulation_instance.sensor_paths) == 1  # local

    # Delete
    sim1.delete()
    assert sim1._unique_id is None
    assert len(sim1._simulation_instance.metadata) == 0

    assert sim1.simulation_template_link is None
    assert sim1._simulation_template.HasField("direct_mc_simulation_template")  # local

    assert len(p.scene_link.get().simulations) == 0
    assert len(sim1._simulation_instance.sensor_paths) == 1  # local
