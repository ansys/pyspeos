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
    sim1.set_direct()
    sim1.commit()
    assert sim1.simulation_template_link is not None
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.HasField("geom_distance_tolerance")
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.geom_distance_tolerance == 0.05
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.HasField("max_impact")
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.max_impact == 100
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.HasField("colorimetric_standard_CIE")
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.colorimetric_standard == simulation_template_pb2.CIE1931
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.HasField("dispersion")
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.dispersion == True
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.HasField("fast_transmission_gathering")
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.fast_transmission_gathering == False
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.HasField("ambient_material_uri")
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.ambient_material_uri == ""
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.HasField("weight")
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.weight == simulation_template_pb2.Weight
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.weight.HasField("minimum_energy_percentage")
    assert sim1.simulation_template_link.get().direct_mc_simulation_template.weight.minimum_energy_percentage == 0.5

    # Change value
    sim1.set_direct().set_geom_distance_tolerance(value=0.1)
    sim1.set_direct().set_max_impact(value=200)
    sim1.set_direct().set_colorimetric_standard_CIE_1964()
    sim1.set_direct().set_dispersion(False)
    sim1.set_direct().set_fast_transmission_gathering(True)
    sim1.set_direct().set_ambient_material_file_uri(uri=os.path.join(test_path, "material.material"))
    sim1.set_direct().set_weight().set_minimum_energy_percentage(value=0.6)
    sim1.commit()

    sim1.set_sensor_paths(sensor_paths=["sensor.1", "sensor.2"])
    sim1.set_source_paths(source_paths=["source.1"])

    sim1.set_geometries(
        values=[
            script.GeoRef.from_native_link(geopath="mybody1"),
            script.GeoRef.from_native_link(geopath="mybody2"),
            script.GeoRef.from_native_link(geopath="mybody3"),
        ]
    )

    assert len(sim1._simulation_instance.sensor_paths) == 2
    assert len(sim1._simulation_instance.source_paths) == 1
    assert len(sim1._simulation_instance.geometries) == 3

    sim1.delete()

    assert len(sim1._simulation_instance.sensor_paths) == 0
    assert len(sim1._simulation_instance.source_paths) == 0
    assert len(sim1._simulation_instance.geometries) == 0


def test_create_inverse(speos: Speos):
    """Test creation of Inverse Simulation."""
    p = script.Project(speos=speos)

    # Default value
    sim1 = p.create_simulation(name="Inverse.1")
    sim1.set_inverse()
    sim1.commit()
    assert sim1.simulation_template_link is not None
    assert sim1.simulation_template_link.get().HasField("inverse_mc_simulation_template")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.HasField("geom_distance_tolerance")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.geom_distance_tolerance == 0.05
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.HasField("max_impact")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.max_impact == 100
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.HasField("colorimetric_standard_CIE")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.colorimetric_standard == simulation_template_pb2.CIE1931
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.HasField("weight")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.weight == simulation_template_pb2.Weight
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.weight.HasField("minimum_energy_percentage")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.weight.minimum_energy_percentage == 0.5
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.HasField("dispersion")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.dispersion == True
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.HasField("splitting")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.splitting == False
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.HasField("number_of_gathering_rays_per_source")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.number_of_gathering_rays_per_source == 1
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.HasField("maximum_gathering_error")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.maximum_gathering_error == 0
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.HasField("fast_transmission_gathering")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.fast_transmission_gathering == False
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.HasField("ambient_material_uri")
    assert sim1.simulation_template_link.get().inverse_mc_simulation_template.ambient_material_uri == ""

    # Change value
    sim1.set_inverse().set_geom_distance_tolerance(value=0.1)
    sim1.set_inverse().set_max_impact(value=200)
    sim1.set_inverse().set_colorimetric_standard_CIE_1964()
    sim1.set_inverse().set_dispersion(False)
    sim1.set_inverse().set_splitting(True)
    sim1.set_inverse().set_number_of_gathering_rays_per_source(value=2)
    sim1.set_inverse().set_maximum_gathering_error(value=0.1)
    sim1.set_inverse().set_ambient_material_file_uri(uri=os.path.join(test_path, "material.material"))
    sim1.commit()

    sim1.set_sensor_paths(sensor_paths=["sensor.1", "sensor.2"])
    sim1.set_source_paths(source_paths=["source.1"])

    sim1.set_geometries(
        values=[
            script.GeoRef.from_native_link(geopath="mybody1"),
            script.GeoRef.from_native_link(geopath="mybody2"),
            script.GeoRef.from_native_link(geopath="mybody3"),
        ]
    )

    assert len(sim1._simulation_instance.sensor_paths) == 2
    assert len(sim1._simulation_instance.source_paths) == 1
    assert len(sim1._simulation_instance.geometries) == 3

    sim1.delete()

    assert len(sim1._simulation_instance.sensor_paths) == 0
    assert len(sim1._simulation_instance.source_paths) == 0
    assert len(sim1._simulation_instance.geometries) == 0


def test_create_interactive(speos: Speos):
    """Test creation of Interactive Simulation."""
    p = script.Project(speos=speos)

    # Default value
    sim1 = p.create_simulation(name="Interactive.1")
    sim1.set_interactive()
    sim1.commit()
    assert sim1.simulation_template_link is not None
    assert sim1.simulation_template_link.get().HasField("interactive_simulation_template")
    assert sim1.simulation_template_link.get().interactive_simulation_template.HasField("geom_distance_tolerance")
    assert sim1.simulation_template_link.get().interactive_simulation_template.geom_distance_tolerance == 0.05
    assert sim1.simulation_template_link.get().interactive_simulation_template.HasField("max_impact")
    assert sim1.simulation_template_link.get().interactive_simulation_template.max_impact == 100
    assert sim1.simulation_template_link.get().interactive_simulation_template.HasField("colorimetric_standard_CIE")
    assert sim1.simulation_template_link.get().interactive_simulation_template.colorimetric_standard == simulation_template_pb2.CIE1931
    assert sim1.simulation_template_link.get().interactive_simulation_template.HasField("weight")
    assert sim1.simulation_template_link.get().interactive_simulation_template.weight == simulation_template_pb2.Weight
    assert sim1.simulation_template_link.get().interactive_simulation_template.weight.HasField("minimum_energy_percentage")
    assert sim1.simulation_template_link.get().interactive_simulation_template.weight.minimum_energy_percentage == 0.5
    assert sim1.simulation_template_link.get().interactive_simulation_template.HasField("ambient_material_uri")
    assert sim1.simulation_template_link.get().interactive_simulation_template.ambient_material_uri == ""

    # Change value
    sim1.set_interactive().set_geom_distance_tolerance(value=0.1)
    sim1.set_interactive().set_max_impact(value=200)
    sim1.set_interactive().set_colorimetric_standard_CIE_1964()
    sim1.set_interactive().set_ambient_material_file_uri(uri=os.path.join(test_path, "material.material"))
    sim1.set_interactive().set_weight().set_minimum_energy_percentage(value=0.6)

    sim1.commit()

    sim1.set_sensor_paths(sensor_paths=["sensor.1", "sensor.2"])
    sim1.set_source_paths(source_paths=["source.1"])

    sim1.set_geometries(
        values=[
            script.GeoRef.from_native_link(geopath="mybody1"),
            script.GeoRef.from_native_link(geopath="mybody2"),
            script.GeoRef.from_native_link(geopath="mybody3"),
        ]
    )

    assert len(sim1._simulation_instance.sensor_paths) == 2
    assert len(sim1._simulation_instance.source_paths) == 1
    assert len(sim1._simulation_instance.geometries) == 3

    sim1.delete()

    assert len(sim1._simulation_instance.sensor_paths) == 0
    assert len(sim1._simulation_instance.source_paths) == 0
    assert len(sim1._simulation_instance.geometries) == 0


def test_commit(speos: Speos):
    """Test commit of simulation."""
    p = script.Project(speos=speos)

    # Create
    sim1 = p.create_simulation(name="Direct.1")
    sim1.set_direct()
    sim1.set_direct().set_ambient_material_file_uri(uri=os.path.join(test_path, "material.material"))
    assert sim1.simulation_template_link is None
    assert len(p.scene_link.get().simulations) == 0

    # Commit
    sim1.commit()
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")

    assert len(p.scene_link.get().simulations) == 1
    assert p.scene_link.get().simulations[0] == sim1._simulation_instance

    # Change only in local not committed
    sim1.set_direct().set_geom_distance_tolerance(value=0.1)
    assert p.scene_link.get().sources[0] != sim1._source_instance

    sim1.delete()


def test_reset(speos: Speos):
    """Test reset of simulation."""
    p = script.Project(speos=speos)

    # Create + commit
    sim1 = p.create_simulation(name="Direct.1")
    sim1.set_direct()
    sim1.set_direct().set_ambient_material_file_uri(uri=os.path.join(test_path, "material.material"))
    sim1.commit()
    assert sim1.simulation_template_link is not None
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")
    assert len(p.scene_link.get().simulations) == 1
    assert p.scene_link.get().simulations[0].HasField("ambient_material_uri")
    # Change local data (on template and on instance)

    # Ask for reset
    sim1.reset()
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")
    assert sim1._simulation_template.HasField("direct_mc_simulation_template")  # local template
    assert p.scene_link.get().simulations[0].HasField("ambient_material_uri")
    assert sim1._simulation_instance.HasField("ambient_material_uri")  # local instance

    sim1.delete()


def test_delete_source(speos: Speos):
    """Test delete of source."""
    p = script.Project(speos=speos)

    # Create + commit
    sim1 = p.create_simulation(name="Direct.1")
    sim1.set_direct()
    sim1.set_direct().set_ambient_material_file_uri(uri=os.path.join(test_path, "material.material"))
    sim1.commit()
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")
    assert sim1._simulation_template.HasField("direct_mc_simulation_template")  # local template
    assert len(p.scene_link.get().simulations) == 1
    assert p.scene_link.get().simulations[0].HasField("ambient_material_uri")
    assert sim1._simulation_instance.HasField("ambient_material_uri")  # local instance

    # Delete
    sim1.delete()
    assert sim1._unique_id is None
    assert len(sim1._simulation_instance.metadata) == 0

    assert sim1.simulation_template_link is None
    assert sim1._simulation_template.HasField("direct_mc_simulation_template")  # local

    assert len(p.scene_link.get().simulations) == 0
    assert sim1._simulation_instance.HasField("ambient_material_uri")  # local
