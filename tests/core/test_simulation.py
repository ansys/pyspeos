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

"""Test basic using simulation."""

from pathlib import Path

from ansys.api.speos.simulation.v1 import simulation_template_pb2
import pytest

from ansys.speos.core import Body, GeoRef, Project, Speos
from ansys.speos.core.sensor import BaseSensor, Sensor3DIrradiance, SensorIrradiance
from ansys.speos.core.simulation import (
    SimulationDirect,
    SimulationInteractive,
    SimulationInverse,
    SimulationVirtualBSDF,
)
from ansys.speos.core.source import SourceLuminaire
from tests.conftest import config, test_path
from tests.helper import does_file_exist, remove_file

IS_DOCKER = config.get("SpeosServerOnDocker")


@pytest.mark.supported_speos_versions(min=251)
def test_create_direct(speos: Speos):
    """Test creation of Direct Simulation."""
    p = Project(speos=speos)

    # Default value
    sim1 = p.create_simulation(name="Direct.1")
    sim1 = SimulationDirect(project=p, name="Direct.1")
    # sim1.set_direct()  # do not commit to avoid issues about No sensor in simulation
    assert sim1._simulation_template.HasField("direct_mc_simulation_template")
    simulation_template = sim1._simulation_template.direct_mc_simulation_template
    assert simulation_template.geom_distance_tolerance == 0.01
    assert simulation_template.max_impact == 100
    assert simulation_template.colorimetric_standard == simulation_template_pb2.CIE_1931
    assert simulation_template.dispersion is True
    assert simulation_template.fast_transmission_gathering is False
    assert simulation_template.ambient_material_uri == ""
    assert simulation_template.HasField("weight")
    assert simulation_template.weight.minimum_energy_percentage == 0.005
    assert len(sim1._simulation_instance.sensor_paths) == 0
    assert len(sim1._simulation_instance.source_paths) == 0
    assert len(sim1._simulation_instance.geometries.geo_paths) == 0
    assert sim1._job.HasField("direct_mc_simulation_properties")
    assert sim1._job.direct_mc_simulation_properties.HasField("stop_condition_rays_number")
    assert sim1._job.direct_mc_simulation_properties.stop_condition_rays_number == 200000
    assert sim1._job.direct_mc_simulation_properties.HasField("stop_condition_duration") is False
    assert sim1._job.direct_mc_simulation_properties.automatic_save_frequency == 1800

    # Change value
    # geom_distance_tolerance
    sim1.geom_distance_tolerance = 0.1
    assert simulation_template.geom_distance_tolerance == 0.1

    # max_impact
    sim1.max_impact = 200
    assert simulation_template.max_impact == 200

    # weight - minimum_energy_percentage
    sim1.set_weight_none()
    assert simulation_template.HasField("weight") is False

    sim1.set_weight().set_minimum_energy_percentage(value=0.7)
    assert simulation_template.HasField("weight")
    assert simulation_template.weight.minimum_energy_percentage == 0.7

    # colorimetric_standard
    sim1.set_colorimetric_standard_CIE_1964()
    assert simulation_template.colorimetric_standard == simulation_template_pb2.CIE_1964

    # dispersion
    sim1.set_dispersion(value=False)
    assert simulation_template.dispersion is False

    # fast_transmission_gathering
    # sim1.set_fast_transmission_gathering(value=True)
    # assert simulation_template.fast_transmission_gathering is True

    # ambient_material_uri
    sim1.set_ambient_material_file_uri(uri=str(Path(test_path) / "AIR.material"))
    assert simulation_template.ambient_material_uri.endswith("AIR.material")

    # stop_condition_rays_number
    sim1.set_stop_condition_rays_number(value=None)
    assert sim1._job.direct_mc_simulation_properties.HasField("stop_condition_rays_number") is False

    # stop_condition_duration
    sim1.set_stop_condition_duration(value=600)
    assert sim1._job.direct_mc_simulation_properties.HasField("stop_condition_duration")
    assert sim1._job.direct_mc_simulation_properties.stop_condition_duration == 600

    # automatic_save_frequency
    sim1.set_automatic_save_frequency(3200)
    assert sim1._job.direct_mc_simulation_properties.automatic_save_frequency == 3200

    # sensor_paths
    sim1.set_sensor_paths(sensor_paths=["sensor.1", "sensor.2"])
    assert sim1._simulation_instance.sensor_paths == ["sensor.1", "sensor.2"]

    # source_paths
    sim1.set_source_paths(source_paths=["source.1"])
    assert sim1._simulation_instance.source_paths == ["source.1"]

    # geometries
    # sim1.set_geometries(
    #    geometries=[
    #        GeoRef.from_native_link(geopath="mybody1"),
    #        GeoRef.from_native_link(geopath="mybody2"),
    #        GeoRef.from_native_link(geopath="mybody3"),
    #    ]
    # )
    # assert sim1._simulation_instance.geometries.geo_paths == ["mybody1", "mybody2", "mybody3"]

    sim1.delete()


@pytest.mark.supported_speos_versions(min=251)
def test_create_inverse(speos: Speos):
    """Test creation of Inverse Simulation."""
    p = Project(speos=speos)

    # Default value
    sim1 = p.create_simulation(name="Inverse.1")
    sim1 = SimulationInverse(project=p, name="Inverse.1")
    # sim1.set_inverse()  # do not commit to avoid issues about No sensor in simulation
    assert sim1._simulation_template.HasField("inverse_mc_simulation_template")
    simulation_template = sim1._simulation_template.inverse_mc_simulation_template
    assert simulation_template.geom_distance_tolerance == 0.01
    assert simulation_template.max_impact == 100
    assert simulation_template.colorimetric_standard == simulation_template_pb2.CIE_1931
    assert simulation_template.HasField("weight")
    assert simulation_template.weight.minimum_energy_percentage == 0.005
    assert simulation_template.dispersion is False
    assert simulation_template.splitting is False
    assert simulation_template.number_of_gathering_rays_per_source == 1
    assert simulation_template.maximum_gathering_error == 0
    assert simulation_template.fast_transmission_gathering is False
    assert simulation_template.ambient_material_uri == ""
    assert len(sim1._simulation_instance.sensor_paths) == 0
    assert len(sim1._simulation_instance.source_paths) == 0
    assert len(sim1._simulation_instance.geometries.geo_paths) == 0
    assert sim1._job.HasField("inverse_mc_simulation_properties")
    assert sim1._job.inverse_mc_simulation_properties.HasField("optimized_propagation_none")
    assert (
        sim1._job.inverse_mc_simulation_properties.optimized_propagation_none.stop_condition_passes_number
        == 5
    )
    assert sim1._job.inverse_mc_simulation_properties.HasField("stop_condition_duration") is False
    assert sim1._job.inverse_mc_simulation_properties.automatic_save_frequency == 1800

    # Change value
    # geom_distance_tolerance
    sim1.geom_distance_tolerance = 0.1
    assert simulation_template.geom_distance_tolerance == 0.1

    # max_impact
    sim1.max_impact = 200
    assert simulation_template.max_impact == 200

    # weight - minimum_energy_percentage
    sim1.set_weight_none()
    assert simulation_template.HasField("weight") is False

    sim1.set_weight().set_minimum_energy_percentage(value=0.7)
    assert simulation_template.HasField("weight")
    assert simulation_template.weight.minimum_energy_percentage == 0.7

    # colorimetric_standard
    sim1.set_colorimetric_standard_CIE_1964()
    assert simulation_template.colorimetric_standard == simulation_template_pb2.CIE_1964

    # dispersion
    sim1.set_dispersion(value=True)
    assert simulation_template.dispersion is True

    # splitting
    sim1.set_splitting(value=True)
    assert simulation_template.splitting is True

    # number_of_gathering_rays_per_source
    sim1.set_number_of_gathering_rays_per_source(value=2)
    assert simulation_template.number_of_gathering_rays_per_source == 2

    # maximum_gathering_error
    sim1.set_maximum_gathering_error(value=3)
    assert simulation_template.maximum_gathering_error == 3

    # fast_transmission_gathering
    # sim1.set_fast_transmission_gathering(value=True)
    # assert simulation_template.fast_transmission_gathering == True

    # ambient_material_uri
    sim1.set_ambient_material_file_uri(uri=str(Path(test_path) / "AIR.material"))
    assert simulation_template.ambient_material_uri.endswith("AIR.material")

    # stop_condition_passes_number
    sim1.set_stop_condition_passes_number(value=None)
    assert sim1._job.inverse_mc_simulation_properties.HasField("optimized_propagation_none") is True
    assert (
        sim1._job.inverse_mc_simulation_properties.optimized_propagation_none.HasField(
            "stop_condition_passes_number"
        )
        is False
    )

    # stop_condition_duration
    sim1.set_stop_condition_duration(value=50)
    assert sim1._job.inverse_mc_simulation_properties.HasField("stop_condition_duration")
    assert sim1._job.inverse_mc_simulation_properties.stop_condition_duration == 50

    # automatic_save_frequency
    sim1.set_automatic_save_frequency(value=5000)
    assert sim1._job.inverse_mc_simulation_properties.automatic_save_frequency == 5000

    # sensor_paths
    sim1.set_sensor_paths(sensor_paths=["sensor.1", "sensor.2"])
    assert sim1._simulation_instance.sensor_paths == ["sensor.1", "sensor.2"]

    # source_paths
    sim1.set_source_paths(source_paths=["source.1"])
    assert sim1._simulation_instance.source_paths == ["source.1"]

    # geometries
    # sim1.set_geometries(
    #    geometries=[
    #        GeoRef.from_native_link(geopath="mybody1"),
    #        GeoRef.from_native_link(geopath="mybody2"),
    #        GeoRef.from_native_link(geopath="mybody3"),
    #    ]
    # )
    # assert sim1._simulation_instance.geometries.geo_paths == ["mybody1", "mybody2", "mybody3"]

    sim1.delete()


@pytest.mark.supported_speos_versions(min=251)
def test_create_interactive(speos: Speos):
    """Test creation of Interactive Simulation."""
    p = Project(speos=speos)

    # Default value
    sim1 = p.create_simulation(name="Interactive.1")
    sim1 = SimulationInteractive(project=p, name="Interactive.1")
    # sim1.set_interactive()  # do not commit to avoid issues about No sensor in simulation
    assert sim1._simulation_template.HasField("interactive_simulation_template")
    assert sim1._simulation_template.interactive_simulation_template.geom_distance_tolerance == 0.01
    assert sim1._simulation_template.interactive_simulation_template.max_impact == 100
    assert (
        sim1._simulation_template.interactive_simulation_template.colorimetric_standard
        == simulation_template_pb2.CIE_1931
    )
    assert sim1._simulation_template.interactive_simulation_template.HasField("weight")
    assert (
        sim1._simulation_template.interactive_simulation_template.weight.minimum_energy_percentage
        == 0.005
    )
    assert sim1._simulation_template.interactive_simulation_template.ambient_material_uri == ""
    assert len(sim1._simulation_instance.sensor_paths) == 0
    assert len(sim1._simulation_instance.source_paths) == 0
    assert len(sim1._simulation_instance.geometries.geo_paths) == 0
    assert sim1._job.HasField("interactive_simulation_properties")
    assert len(sim1._job.interactive_simulation_properties.rays_number_per_sources) == 0
    assert sim1._job.interactive_simulation_properties.light_expert is False
    assert sim1._job.interactive_simulation_properties.impact_report is False

    # Change value
    # geom_distance_tolerance
    sim1.geom_distance_tolerance = 0.1
    assert sim1._simulation_template.interactive_simulation_template.geom_distance_tolerance == 0.1

    # max_impact
    sim1.max_impact = 200
    assert sim1._simulation_template.interactive_simulation_template.max_impact == 200

    # weight - minimum_energy_percentage
    sim1.set_weight_none()
    assert sim1._simulation_template.interactive_simulation_template.HasField("weight") is False

    sim1.set_weight().set_minimum_energy_percentage(value=0.7)
    assert sim1._simulation_template.interactive_simulation_template.HasField("weight")
    assert (
        sim1._simulation_template.interactive_simulation_template.weight.minimum_energy_percentage
        == 0.7
    )

    # colorimetric_standard
    sim1.set_colorimetric_standard_CIE_1964()
    assert (
        sim1._simulation_template.interactive_simulation_template.colorimetric_standard
        == simulation_template_pb2.CIE_1964
    )

    # ambient_material_uri
    sim1.set_ambient_material_file_uri(uri=str(Path(test_path) / "AIR.material"))
    assert sim1._simulation_template.interactive_simulation_template.ambient_material_uri.endswith(
        "AIR.material"
    )

    # rays_number_per_sources
    sim1.set_rays_number_per_sources(
        values=[
            SimulationInteractive.RaysNumberPerSource(source_path="Source.1", rays_nb=50),
            SimulationInteractive.RaysNumberPerSource(source_path="Source.2", rays_nb=150),
        ]
    )
    assert len(sim1._job.interactive_simulation_properties.rays_number_per_sources) == 2
    assert (
        sim1._job.interactive_simulation_properties.rays_number_per_sources[0].source_path
        == "Source.1"
    )
    assert sim1._job.interactive_simulation_properties.rays_number_per_sources[0].rays_nb == 50
    assert (
        sim1._job.interactive_simulation_properties.rays_number_per_sources[1].source_path
        == "Source.2"
    )
    assert sim1._job.interactive_simulation_properties.rays_number_per_sources[1].rays_nb == 150

    sim1.set_rays_number_per_sources(values=[])
    assert len(sim1._job.interactive_simulation_properties.rays_number_per_sources) == 0

    # light_expert
    sim1.set_light_expert(value=True)
    assert sim1._job.interactive_simulation_properties.light_expert is True

    # impact_report
    sim1.set_impact_report(value=True)
    assert sim1._job.interactive_simulation_properties.impact_report is True

    # sensor_paths
    sim1.set_sensor_paths(sensor_paths=["sensor.1", "sensor.2"])
    assert sim1._simulation_instance.sensor_paths == ["sensor.1", "sensor.2"]

    # source_paths
    sim1.set_source_paths(source_paths=["source.1"])
    assert sim1._simulation_instance.source_paths == ["source.1"]

    # geometries
    # sim1.set_geometries(
    #    geometries=[
    #        GeoRef.from_native_link(geopath="mybody1"),
    #        GeoRef.from_native_link(geopath="mybody2"),
    #        GeoRef.from_native_link(geopath="mybody3"),
    #    ]
    # )
    # assert sim1._simulation_instance.geometries.geo_paths == ["mybody1", "mybody2", "mybody3"]

    sim1.delete()


@pytest.mark.supported_speos_versions(min=252)
def test_create_virtual_bsdf_bench(speos: Speos):
    """Test creation of Virtual BSDF Bench Simulation."""
    p = Project(speos=speos)
    vbb = p.create_simulation("virtual_bsdf_bench_1", feature_type=SimulationVirtualBSDF)

    # Check default properties
    # Check backend property
    assert vbb._simulation_template.HasField("virtual_bsdf_bench_simulation_template")
    assert (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.geom_distance_tolerance
        == 0.01
    )
    assert vbb._simulation_template.virtual_bsdf_bench_simulation_template.max_impact == 100
    assert vbb._simulation_template.virtual_bsdf_bench_simulation_template.HasField("weight")
    assert (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.weight.minimum_energy_percentage
        == 0.005
    )
    assert (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.colorimetric_standard
        is simulation_template_pb2.CIE_1931
    )
    assert (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.wavelengths_range.w_start
        == 400
    )
    assert (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.wavelengths_range.w_end
        == 700
    )
    assert (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.wavelengths_range.w_sampling
        == 13
    )
    assert vbb._simulation_instance.vbb_properties.axis_system[:] == [
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
    ]
    assert vbb._simulation_instance.vbb_properties.analysis_x_ratio == 100
    assert vbb._simulation_instance.vbb_properties.analysis_y_ratio == 100

    # Check mode and source settings
    assert vbb._simulation_template.virtual_bsdf_bench_simulation_template.HasField(
        "all_characteristics"
    )
    backend_properties = (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.all_characteristics
    )
    assert backend_properties.is_bsdf180 is False
    assert backend_properties.sensor_reflection_and_transmission is False
    assert backend_properties.HasField("no_iridescence")
    assert backend_properties.no_iridescence.HasField("isotropic")
    assert backend_properties.no_iridescence.isotropic.HasField("uniform_isotropic")
    assert backend_properties.no_iridescence.isotropic.uniform_isotropic.theta_sampling == 18

    # Check sensor settings
    assert (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.sensor.integration_angle
        == 2
    )
    assert vbb._simulation_template.virtual_bsdf_bench_simulation_template.sensor.HasField(
        "uniform"
    )
    assert (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.sensor.uniform.theta_sampling
        == 45
    )
    assert (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.sensor.uniform.phi_sampling
        == 180
    )

    # Check frontend property
    assert vbb.geom_distance_tolerance == 0.01
    assert vbb.max_impact == 100
    assert vbb.integration_angle == 2
    assert vbb.axis_system == [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert vbb.analysis_x_ratio == 100
    assert vbb.analysis_y_ratio == 100
    assert vbb.set_wavelengths_range().start == 400
    assert vbb.set_wavelengths_range().end == 700
    assert vbb.set_wavelengths_range().sampling == 13
    assert vbb.set_mode_all_characteristics().is_bsdf180 is False
    assert vbb.set_mode_all_characteristics().reflection_and_transmission is False
    assert (
        vbb.set_mode_all_characteristics()
        .set_non_iridescence()
        .set_isotropic()
        .set_uniform()
        .theta_sampling
        == 18
    )
    assert vbb.set_sensor_sampling_uniform().theta_sampling == 45
    assert vbb.set_sensor_sampling_uniform().phi_sampling == 180

    # Change isotropic adaptive source sampling
    vbb.set_mode_all_characteristics().set_non_iridescence().set_isotropic().set_adaptive()
    # Check backend properties
    backend_properties = (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.all_characteristics
    )
    assert backend_properties.no_iridescence.isotropic.HasField("adaptive")
    assert backend_properties.no_iridescence.isotropic.adaptive.file_uri == ""
    # Check frontend properties
    assert (
        vbb.set_mode_all_characteristics()
        .set_non_iridescence()
        .set_isotropic()
        .set_adaptive()
        .adaptive_uri
        == ""
    )

    # Check if properties are saved
    vbb.set_mode_all_characteristics().set_non_iridescence().set_isotropic()
    # Check backend properties
    backend_properties = (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.all_characteristics
    )
    assert backend_properties.no_iridescence.isotropic.HasField("adaptive")
    assert backend_properties.no_iridescence.isotropic.adaptive.file_uri == ""
    # Check frontend properties
    assert (
        vbb.set_mode_all_characteristics()
        .set_non_iridescence()
        .set_isotropic()
        .set_adaptive()
        .adaptive_uri
        == ""
    )

    # Change back to isotropic uniform source sampling
    vbb.set_mode_all_characteristics().set_non_iridescence().set_isotropic().set_uniform()
    # Check backend properties
    backend_properties = (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.all_characteristics
    )
    assert backend_properties.no_iridescence.isotropic.HasField("uniform_isotropic")
    # Check frontend properties
    assert backend_properties.no_iridescence.isotropic.uniform_isotropic.theta_sampling == 18

    # Change anisotropic uniform
    vbb.set_mode_all_characteristics().set_non_iridescence().set_anisotropic()
    # Check backend properties
    backend_properties = (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.all_characteristics
    )
    assert backend_properties.no_iridescence.HasField("anisotropic")
    assert backend_properties.no_iridescence.anisotropic.HasField("uniform_anisotropic")
    assert backend_properties.no_iridescence.anisotropic.uniform_anisotropic.theta_sampling == 18
    assert backend_properties.no_iridescence.anisotropic.uniform_anisotropic.phi_sampling == 36
    assert backend_properties.no_iridescence.anisotropic.uniform_anisotropic.symmetry_type == 1
    # Check frontend properties
    assert (
        vbb.set_mode_all_characteristics()
        .set_non_iridescence()
        .set_anisotropic()
        .set_uniform()
        .theta_sampling
        == 18
    )
    assert (
        vbb.set_mode_all_characteristics()
        .set_non_iridescence()
        .set_anisotropic()
        .set_uniform()
        .phi_sampling
        == 36
    )

    # Change anisotropic adaptive
    vbb.set_mode_all_characteristics().set_non_iridescence().set_anisotropic().set_adaptive()
    # Check backend properties
    backend_properties = (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.all_characteristics
    )
    assert backend_properties.no_iridescence.anisotropic.HasField("adaptive")
    assert backend_properties.no_iridescence.anisotropic.adaptive.file_uri == ""
    # Check frontend properties
    assert (
        vbb.set_mode_all_characteristics()
        .set_non_iridescence()
        .set_anisotropic()
        .set_adaptive()
        .adaptive_uri
        == ""
    )

    # Change color depending on viewing angle
    vbb.set_mode_all_characteristics().set_iridescence()
    # Check backend properties
    backend_properties = (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.all_characteristics
    )
    assert backend_properties.HasField("iridescence")
    assert backend_properties.iridescence.HasField("uniform_isotropic")
    assert backend_properties.iridescence.uniform_isotropic.theta_sampling == 18
    # Check frontend properties
    assert vbb.set_mode_all_characteristics().set_iridescence().set_uniform().theta_sampling == 18

    # Change color depending on viewing angle with adaptive source sampling
    vbb.set_mode_all_characteristics().set_iridescence().set_adaptive()
    # Check backend properties
    backend_properties = (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.all_characteristics
    )
    assert backend_properties.iridescence.HasField("adaptive")
    assert backend_properties.iridescence.adaptive.file_uri == ""
    # Check frontend properties
    assert vbb.set_mode_all_characteristics().set_iridescence().set_adaptive().adaptive_uri == ""

    # Change mode to surface roughness only
    vbb.set_mode_roughness_only()
    # Check backend property
    assert not vbb._simulation_template.virtual_bsdf_bench_simulation_template.HasField(
        "all_characteristics"
    )
    assert vbb._simulation_template.virtual_bsdf_bench_simulation_template.HasField(
        "roughness_only"
    )
    backend_properties = (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.roughness_only
    )
    assert backend_properties.HasField("uniform_isotropic")
    assert backend_properties.uniform_isotropic.theta_sampling == 18
    # Check frontend properties
    assert vbb.set_mode_roughness_only().set_uniform().theta_sampling == 18

    # Change to adaptive source sampling
    vbb.set_mode_roughness_only().set_adaptive()
    # Check backend properties
    backend_properties = (
        vbb._simulation_template.virtual_bsdf_bench_simulation_template.roughness_only
    )
    assert backend_properties.HasField("adaptive")
    assert backend_properties.adaptive.file_uri == ""
    # Check frontend properties
    assert vbb.set_mode_roughness_only().set_adaptive().adaptive_uri == ""

    # Change sensor to automatic
    vbb.set_sensor_sampling_automatic()
    assert vbb._simulation_template.virtual_bsdf_bench_simulation_template.sensor.HasField(
        "automatic"
    )
    vbb.delete()


def test_load_virtual_bsdf_bench(speos: Speos):
    """Test load of a exported virtual bsdf bench simulation."""
    p = Project(
        speos=speos, path=str(Path(test_path) / "nx_vbb_export.speos" / "nx_vbb_export.speos")
    )
    assert p is not None
    sims = p.find(name=".*", name_regex=True, feature_type=SimulationVirtualBSDF)
    assert len(sims) > 0


def test_commit(speos: Speos):
    """Test commit of simulation."""
    p = Project(speos=speos)

    # Prerequisites: a source and a sensor are needed (bug also a rootpart and optical property)
    root_part = p.create_root_part()
    root_part.create_body(name="Body.1").create_face(name="Face.1").set_vertices(
        [0, 1, 0, 0, 2, 0, 1, 2, 0]
    ).set_facets([0, 1, 2]).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    opt_prop = p.create_optical_property(name="Material.1")
    opt_prop.set_volume_none().set_surface_mirror()
    opt_prop.set_geometries(geometries=[GeoRef.from_native_link(geopath="Body.1")])
    opt_prop.commit()

    ssr = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    ssr.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr.commit()

    ssr2 = p.create_sensor(name="Irradiance.2", feature_type=SensorIrradiance)
    ssr2.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr2.commit()

    src = p.create_source(name="Luminaire.1", feature_type=SourceLuminaire)
    src.set_intensity_file_uri(uri=str(Path(test_path) / "IES_C_DETECTOR.ies"))
    src.commit()

    # Create
    sim1 = SimulationDirect(project=p, name="Direct.1")
    sim1.set_sensor_paths(sensor_paths=[ssr._name]).set_source_paths(source_paths=[src._name])
    assert sim1.simulation_template_link is None
    assert len(p.scene_link.get().simulations) == 0
    assert sim1.job_link is None
    assert sim1._job.HasField("direct_mc_simulation_properties")  # local

    # Commit
    sim1.commit()
    assert sim1.simulation_template_link is not None
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")
    assert sim1.job_link is None  # Job will be committed only at compute time

    assert len(p.scene_link.get().simulations) == 1
    assert p.scene_link.get().simulations[0] == sim1._simulation_instance

    # Change only in local not committed (on template, on instance)
    sim1.geom_distance_tolerance = 0.1
    assert sim1.simulation_template_link.get() != sim1._simulation_template
    sim1.set_sensor_paths(["Irradiance.1, Irradiance.2"])
    assert p.scene_link.get().simulations[0] != sim1._simulation_instance

    sim1.delete()


def test_reset(speos: Speos):
    """Test reset of simulation."""
    p = Project(speos=speos)

    # Prerequisites: a source and a sensor are needed (bug also a rootpart and optical property)
    root_part = p.create_root_part()
    root_part.create_body(name="Body.1").create_face(name="Face.1").set_vertices(
        [0, 1, 0, 0, 2, 0, 1, 2, 0]
    ).set_facets([0, 1, 2]).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    opt_prop = p.create_optical_property(name="Material.1")
    opt_prop.set_volume_none().set_surface_mirror()
    opt_prop.set_geometries(geometries=[GeoRef.from_native_link(geopath="Body.1")])
    opt_prop.commit()

    ssr = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    ssr.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr.commit()

    ssr2 = p.create_sensor(name="Irradiance.2", feature_type=SensorIrradiance)
    ssr2.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr2.commit()

    src = p.create_source(name="Luminaire.1", feature_type=SourceLuminaire)
    src.set_intensity_file_uri(uri=str(Path(test_path) / "IES_C_DETECTOR.ies"))
    src.commit()

    # Create + commit

    sim1 = SimulationDirect(project=p, name="Direct.1")
    sim1.set_sensor_paths(sensor_paths=[ssr._name]).set_source_paths(
        source_paths=[src._name]
    ).commit()
    assert sim1.simulation_template_link is not None
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")
    assert len(p.scene_link.get().simulations) == 1
    assert sim1.job_link is None  # Job will be committed only at compute time
    assert sim1._job.HasField("direct_mc_simulation_properties")  # local

    # Change local data (on template, on instance)
    sim1.geom_distance_tolerance = 0.1
    assert sim1.simulation_template_link.get() != sim1._simulation_template
    sim1.set_sensor_paths(["Irradiance.1, Irradiance.2"])
    assert p.scene_link.get().simulations[0] != sim1._simulation_instance

    # Ask for reset
    sim1.reset()
    assert sim1.simulation_template_link.get() == sim1._simulation_template
    assert p.scene_link.get().simulations[0] == sim1._simulation_instance

    sim1.delete()


@pytest.mark.supported_speos_versions(min=251)
def test_direct_modify_after_reset(speos: Speos):
    """Test reset of direct simulation, and then modify."""
    p = Project(speos=speos)

    # Prerequisites: a source and a sensor are needed (bug also a rootpart and optical property)
    root_part = p.create_root_part()
    root_part.create_body(name="Body.1").create_face(name="Face.1").set_vertices(
        [0, 1, 0, 0, 2, 0, 1, 2, 0]
    ).set_facets([0, 1, 2]).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    opt_prop = p.create_optical_property(name="Material.1")
    opt_prop.set_volume_none().set_surface_mirror()
    opt_prop.set_geometries(geometries=[GeoRef.from_native_link(geopath="Body.1")])
    opt_prop.commit()

    ssr = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    ssr.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr.commit()

    ssr2 = p.create_sensor(name="Irradiance.2", feature_type=SensorIrradiance)
    ssr2.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr2.commit()

    src = p.create_source(name="Luminaire.1", feature_type=SourceLuminaire)
    src.set_intensity_file_uri(uri=str(Path(test_path) / "IES_C_DETECTOR.ies"))
    src.commit()

    # Create + commit
    sim1 = p.create_simulation(name="Direct.1", feature_type=SimulationDirect)
    sim1.set_sensor_paths(sensor_paths=[ssr._name]).set_source_paths(
        source_paths=[src._name]
    ).commit()

    # Light expert
    sim1.set_light_expert(True, 1000)
    for item in sim1._project._features:
        if isinstance(item, BaseSensor):
            assert item._sensor_instance.HasField("lxp_properties")
            assert item._sensor_instance.lxp_properties.nb_max_paths == 1000
            assert item.lxp_path_number == 1000

    sim1.set_light_expert(False, 1000)
    for item in sim1._project._features:
        if isinstance(item, BaseSensor):
            assert item._sensor_instance.HasField("lxp_properties") is False
            assert item.lxp_path_number is None

    # Ask for reset
    sim1.reset()

    # Modify after a reset
    # Template
    assert sim1._simulation_template.direct_mc_simulation_template.geom_distance_tolerance == 0.01
    sim1.geom_distance_tolerance = 0.05
    assert sim1._simulation_template.direct_mc_simulation_template.geom_distance_tolerance == 0.05

    # Props
    assert sim1._simulation_instance.sensor_paths == [ssr._name]
    sim1.set_sensor_paths(["NewSensor"])
    assert sim1._simulation_instance.sensor_paths == ["NewSensor"]

    # Job Props
    assert sim1._job.direct_mc_simulation_properties.stop_condition_rays_number == 200000
    sim1.set_stop_condition_rays_number(value=500)
    assert sim1._job.direct_mc_simulation_properties.stop_condition_rays_number == 500

    p.delete()


@pytest.mark.supported_speos_versions(min=251)
def test_inverse_modify_after_reset(speos: Speos):
    """Test reset of inverse simulation, and then modify."""
    p = Project(speos=speos)

    # Prerequisites: a source and a sensor are needed (bug also a rootpart and optical property)
    root_part = p.create_root_part()
    root_part.create_body(name="Body.1").create_face(name="Face.1").set_vertices(
        [0, 1, 0, 0, 2, 0, 1, 2, 0]
    ).set_facets([0, 1, 2]).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    opt_prop = p.create_optical_property(name="Material.1")
    opt_prop.set_volume_none().set_surface_mirror()
    opt_prop.set_geometries(geometries=[GeoRef.from_native_link(geopath="Body.1")])
    opt_prop.commit()

    ssr = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    ssr.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1]).set_type_colorimetric()
    ssr.commit()

    ssr2 = p.create_sensor(name="Irradiance.2", feature_type=SensorIrradiance)
    ssr2.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1]).set_type_colorimetric()
    ssr2.commit()

    src = p.create_source(name="Luminaire.1", feature_type=SourceLuminaire)
    src.set_intensity_file_uri(uri=str(Path(test_path) / "IES_C_DETECTOR.ies"))
    src.commit()

    # Create + commit
    sim1 = p.create_simulation(name="Inverse.1", feature_type=SimulationInverse)
    sim1.set_sensor_paths(sensor_paths=[ssr._name]).set_source_paths(
        source_paths=[src._name]
    ).commit()

    # Light expert
    sim1.set_light_expert(True, 1000)
    for item in sim1._project._features:
        if isinstance(item, BaseSensor):
            assert item._sensor_instance.HasField("lxp_properties")
            assert item._sensor_instance.lxp_properties.nb_max_paths == 1000
            assert item.lxp_path_number == 1000

    sim1.set_light_expert(False, 1000)
    for item in sim1._project._features:
        if isinstance(item, BaseSensor):
            assert item._sensor_instance.HasField("lxp_properties") is False
            assert item.lxp_path_number is None

    # Ask for reset
    sim1.reset()

    # Modify after a reset
    # Template
    assert sim1._simulation_template.inverse_mc_simulation_template.geom_distance_tolerance == 0.01
    sim1.geom_distance_tolerance = 0.05
    assert sim1._simulation_template.inverse_mc_simulation_template.geom_distance_tolerance == 0.05

    # Props
    assert sim1._simulation_instance.sensor_paths == [ssr._name]
    sim1.set_sensor_paths(["NewSensor"])
    assert sim1._simulation_instance.sensor_paths == ["NewSensor"]

    # Job Props
    assert (
        sim1._job.inverse_mc_simulation_properties.optimized_propagation_none.stop_condition_passes_number
        == 5
    )
    sim1.set_stop_condition_passes_number(value=10)
    assert (
        sim1._job.inverse_mc_simulation_properties.optimized_propagation_none.stop_condition_passes_number
        == 10
    )

    p.delete()


@pytest.mark.supported_speos_versions(min=251)
def test_interactive_modify_after_reset(speos: Speos):
    """Test reset of interactive simulation, and then modify."""
    p = Project(speos=speos)

    # Prerequisites: a source and a sensor are needed (bug also a rootpart and optical property)
    root_part = p.create_root_part()
    root_part.create_body(name="Body.1").create_face(name="Face.1").set_vertices(
        [0, 1, 0, 0, 2, 0, 1, 2, 0]
    ).set_facets([0, 1, 2]).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    opt_prop = p.create_optical_property(name="Material.1")
    opt_prop.set_volume_none().set_surface_mirror()
    opt_prop.set_geometries(geometries=[GeoRef.from_native_link(geopath="Body.1")])
    opt_prop.commit()

    ssr = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    ssr.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1]).set_type_colorimetric()
    ssr.commit()

    ssr2 = p.create_sensor(name="Irradiance.2", feature_type=SensorIrradiance)
    ssr2.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1]).set_type_colorimetric()
    ssr2.commit()

    src = p.create_source(name="Luminaire.1", feature_type=SourceLuminaire)
    src.set_intensity_file_uri(uri=str(Path(test_path) / "IES_C_DETECTOR.ies"))
    src.commit()

    # Create + commit
    sim1 = p.create_simulation(name="Interactive.1", feature_type=SimulationInteractive)
    sim1.set_sensor_paths(sensor_paths=[ssr._name]).set_source_paths(
        source_paths=[src._name]
    ).commit()

    # Ask for reset
    sim1.reset()

    # Modify after a reset
    # Template
    assert sim1._simulation_template.interactive_simulation_template.geom_distance_tolerance == 0.01
    sim1.geom_distance_tolerance = 0.05
    assert sim1._simulation_template.interactive_simulation_template.geom_distance_tolerance == 0.05

    # Props
    assert sim1._simulation_instance.sensor_paths == [ssr._name]
    sim1.set_sensor_paths(["NewSensor"])
    assert sim1._simulation_instance.sensor_paths == ["NewSensor"]

    # Job Props
    assert sim1._job.interactive_simulation_properties.light_expert is False
    sim1.set_light_expert(value=True)
    assert sim1._job.interactive_simulation_properties.light_expert is True

    p.delete()


def test_delete(speos: Speos):
    """Test delete of simulation."""
    p = Project(speos=speos)

    # Prerequisites: a source and a sensor are needed (bug also a rootpart and optical property)
    root_part = p.create_root_part()
    root_part.create_body(name="Body.1").create_face(name="Face.1").set_vertices(
        [0, 1, 0, 0, 2, 0, 1, 2, 0]
    ).set_facets([0, 1, 2]).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    opt_prop = p.create_optical_property(name="Material.1")
    opt_prop.set_volume_none().set_surface_mirror()
    opt_prop.set_geometries(geometries=[GeoRef.from_native_link(geopath="Body.1")])
    opt_prop.commit()

    ssr = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
    ssr.set_axis_system(axis_system=[0, 0, -20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    ssr.commit()

    src = p.create_source(name="Luminaire.1", feature_type=SourceLuminaire)
    src.set_intensity_file_uri(uri=str(Path(test_path) / "IES_C_DETECTOR.ies"))
    src.commit()

    # Create + commit
    sim1 = SimulationDirect(project=p, name="Direct.1")
    sim1.set_sensor_paths(sensor_paths=[ssr._name]).set_source_paths(
        source_paths=[src._name]
    ).commit()
    assert sim1.simulation_template_link.get().HasField("direct_mc_simulation_template")
    assert sim1._simulation_template.HasField("direct_mc_simulation_template")  # local template
    assert len(p.scene_link.get().simulations) == 1
    assert len(p.scene_link.get().simulations[0].sensor_paths) == 1
    assert len(sim1._simulation_instance.sensor_paths) == 1  # local
    assert sim1.job_link is None  # Job will be committed only at compute time
    assert sim1._job.HasField("direct_mc_simulation_properties")  # local

    # Delete
    sim1.delete()
    assert sim1._unique_id is None
    assert len(sim1._simulation_instance.metadata) == 0

    assert sim1.simulation_template_link is None
    assert sim1._simulation_template.HasField("direct_mc_simulation_template")  # local

    assert len(p.scene_link.get().simulations) == 0
    assert len(sim1._simulation_instance.sensor_paths) == 1  # local


def test_get_simulation(speos: Speos, capsys):
    """Test get of a simulation."""
    p = Project(speos=speos)
    sim1 = p.create_simulation(name="Sim.1", feature_type=SimulationDirect)
    sim2 = p.create_simulation(name="Sim.2", feature_type=SimulationInteractive)
    sim3 = p.create_simulation(name="Sim.3", feature_type=SimulationInverse)
    # test when key exists
    name1 = sim1.get(key="name")
    assert name1 == "Sim.1"
    property_info = sim2.get(key="rays_number_per_sources")
    assert property_info is not None
    property_info = sim3.get(key="source_paths")
    assert property_info is not None

    # test when key does not exist
    get_result1 = sim1.get(key="geometry")
    stdout, stderr = capsys.readouterr()
    assert get_result1 is None
    assert "Used key: geometry not found in key list" in stdout
    get_result2 = sim2.get(key="geometry")
    stdout, stderr = capsys.readouterr()
    assert get_result2 is None
    assert "Used key: geometry not found in key list" in stdout
    get_result3 = sim3.get(key="geometry")
    stdout, stderr = capsys.readouterr()
    assert get_result3 is None
    assert "Used key: geometry not found in key list" in stdout


def test_export(speos: Speos):
    """Test export of simulation."""
    p = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism.speos"),
    )
    sim_first = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
    sim_second = p.create_simulation(name="Sim.2", feature_type=SimulationInverse)
    sim_second.set_sensor_paths(["Irradiance.1:564"])
    sim_second.set_source_paths(["Surface.1:7758"])
    sim_second.commit()
    sim_first.export(export_path=Path(test_path) / "export_test")
    assert does_file_exist(
        str(
            Path(test_path)
            / "export_test"
            / (sim_first.get(key="name") + ".speos")
            / (sim_first.get(key="name") + ".speos")
        )
    )
    with pytest.raises(
        ValueError,
        match="Selected simulation is not the first simulation feature, it can't be exported.",
    ):
        sim_second.export(export_path=str(Path(test_path) / "export_test"))

    remove_file(str(Path(test_path) / "export_test"))


@pytest.mark.skipif(IS_DOCKER, reason="COM API is only available locally")
@pytest.mark.supported_speos_versions(min=252)
def test_export_vtp(speos: Speos):
    """Test export of xm3 and xmp as vtp files."""
    import numpy as np
    import pyvista as pv

    from ansys.speos.core.workflow.open_result import _Speos3dData

    p = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism_3D.speos"),
    )
    sim = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]

    # ==== test 3d sensor photometric ===
    # verify illuminance, reflection, transmission, absorption are saved in vtp
    # verify the vtp data is same as calculated
    sensor_3d = p.find(name=".*", name_regex=True, feature_type=Sensor3DIrradiance)[0]
    sensor_3d_geos = p.find(name="PrismBody", name_regex=True, feature_type=Body)[0]._geom_features
    sensor_3d_mesh = [sensor_3d_geo._face for sensor_3d_geo in sensor_3d_geos]
    sensor_3d.set_type_photometric()
    sensor_3d.commit()
    speos_results, vtp_results = sim.compute_CPU(export_vtp=True)
    assert does_file_exist(vtp_results[1])

    vtp_data = pv.read(vtp_results[1]).point_data
    assert np.allclose(vtp_data.get("Reflection"), 0.0) is not True
    assert np.allclose(vtp_data.get("Illuminance [lx]"), 0.0) is not True
    assert np.allclose(vtp_data.get("Transmission"), 0.0) is not True
    assert np.allclose(vtp_data.get("Absorption"), 0.0) is True

    export_data_xm3 = [result.path for result in speos_results if result.path.endswith(".xm3")][0]
    export_data_xm3_txt = Path(export_data_xm3).with_suffix(".txt")
    file = export_data_xm3_txt.open("r")
    xm3_data = []
    content = file.readlines()
    for line in content[1:]:
        line_content = line.split()
        xm3_data.append(
            _Speos3dData(
                x=line_content[0],
                y=line_content[1],
                z=line_content[2],
                illuminance=0.0 if "Illuminance" not in content[0] else line_content[3],
                reflection=0.0 if "Reflection" not in content[0] else line_content[4],
                transmission=0.0 if "Transmission" not in content[0] else line_content[5],
                absorption=0.0 if "Absorption" not in content[0] else line_content[6],
            )
        )
    vtp_meshes = None
    for geo in sensor_3d_mesh:
        vertices = np.array(geo.vertices).reshape(-1, 3)
        facets = np.array(geo.facets).reshape(-1, 3)
        temp = np.full(facets.shape[0], 3)
        temp = np.vstack(temp)
        facets = np.hstack((temp, facets))
        if vtp_meshes is None:
            vtp_meshes = pv.PolyData(vertices, facets)
        else:
            vtp_meshes = vtp_meshes.append_polydata(pv.PolyData(vertices, facets))

    vtp_meshes["Illuminance [lx]"] = [item.illuminance for item in xm3_data]
    vtp_meshes["Reflection"] = [item.reflection for item in xm3_data]
    vtp_meshes["Transmission"] = [item.transmission for item in xm3_data]
    vtp_meshes["Absorption"] = [item.absorption for item in xm3_data]
    assert all(
        np.isclose(
            vtp_meshes.point_data.get("Illuminance [lx]"),
            vtp_data.get("Illuminance [lx]"),
            rtol=1e-5,
            atol=1e-8,
        )
    )
    assert all(
        np.isclose(
            vtp_meshes.point_data.get("Reflection"),
            vtp_data.get("Reflection"),
            rtol=1e-5,
            atol=1e-8,
        )
    )
    assert all(
        np.isclose(
            vtp_meshes.point_data.get("Transmission"),
            vtp_data.get("Transmission"),
            rtol=1e-5,
            atol=1e-8,
        )
    )
    assert all(
        np.isclose(
            vtp_meshes.point_data.get("Absorption"),
            vtp_data.get("Absorption"),
            rtol=1e-5,
            atol=1e-8,
        )
    )

    # === test 3d sensor photometric with radial integration ===
    # only illuminance value is saved in vtp file
    p2 = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism_3D.speos"),
    )
    sim = p2.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]

    sensor_3d = p2.find(name=".*", name_regex=True, feature_type=Sensor3DIrradiance)[0]
    sensor_3d.set_type_photometric().set_integration_radial()
    sensor_3d.commit()
    speos_results, vtp_results = sim.compute_CPU(export_vtp=True)
    assert does_file_exist(vtp_results[1])

    vtp_data = pv.read(vtp_results[1]).point_data
    assert np.allclose(vtp_data.get("Reflection"), 0.0) is True
    assert np.allclose(vtp_data.get("Illuminance [lx]"), 0.0) is not True
    assert np.allclose(vtp_data.get("Irradiance [W/m2]"), 0.0) is True
    assert np.allclose(vtp_data.get("Transmission"), 0.0) is True
    assert np.allclose(vtp_data.get("Absorption"), 0.0) is True

    # ===  test 3d sensor radiometric ===
    # only irradiance, reflection, transmission, absorption value is saved in vtp file
    # verify the vtp results are the same as calculated ones.
    p3 = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism_3D.speos"),
    )
    sim = p3.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]

    sensor_3d = p3.find(name=".*", name_regex=True, feature_type=Sensor3DIrradiance)[0]
    sensor_3d_geos = p3.find(name="PrismBody", name_regex=True, feature_type=Body)[0]._geom_features
    sensor_3d_mesh = [sensor_3d_geo._face for sensor_3d_geo in sensor_3d_geos]
    sensor_3d.set_type_radiometric()
    sensor_3d.commit()
    speos_results, vtp_results = sim.compute_CPU(export_vtp=True)
    assert does_file_exist(vtp_results[1])

    vtp_data = pv.read(vtp_results[1]).point_data
    assert np.allclose(vtp_data.get("Reflection"), 0.0) is not True
    assert np.allclose(vtp_data.get("Irradiance [W/m2]"), 0.0) is not True
    assert np.allclose(vtp_data.get("Transmission"), 0.0) is not True
    assert np.allclose(vtp_data.get("Absorption"), 0.0) is True
    assert np.allclose(vtp_data.get("Illuminance [lx]"), 0.0) is True

    export_data_xm3 = [result.path for result in speos_results if result.path.endswith(".xm3")][0]
    export_data_xm3_txt = Path(export_data_xm3).with_suffix(".txt")
    file = export_data_xm3_txt.open("r")
    xm3_data = []
    content = file.readlines()
    for line in content[1:]:
        line_content = line.split()
        xm3_data.append(
            _Speos3dData(
                x=line_content[0],
                y=line_content[1],
                z=line_content[2],
                illuminance=0.0 if "Illuminance" not in content[0] else line_content[3],
                irradiance=0.0 if "Irradiance" not in content[0] else line_content[3],
                reflection=0.0 if "Reflection" not in content[0] else line_content[4],
                transmission=0.0 if "Transmission" not in content[0] else line_content[5],
                absorption=0.0 if "Absorption" not in content[0] else line_content[6],
            )
        )
    vtp_meshes = None
    for geo in sensor_3d_mesh:
        vertices = np.array(geo.vertices).reshape(-1, 3)
        facets = np.array(geo.facets).reshape(-1, 3)
        temp = np.full(facets.shape[0], 3)
        temp = np.vstack(temp)
        facets = np.hstack((temp, facets))
        if vtp_meshes is None:
            vtp_meshes = pv.PolyData(vertices, facets)
        else:
            vtp_meshes = vtp_meshes.append_polydata(pv.PolyData(vertices, facets))

    vtp_meshes["Illuminance [lx]"] = [item.illuminance for item in xm3_data]
    vtp_meshes["Irradiance [W/m2]"] = [item.irradiance for item in xm3_data]
    vtp_meshes["Reflection"] = [item.reflection for item in xm3_data]
    vtp_meshes["Transmission"] = [item.transmission for item in xm3_data]
    vtp_meshes["Absorption"] = [item.absorption for item in xm3_data]
    assert all(
        np.isclose(
            vtp_meshes.point_data.get("Illuminance [lx]"),
            vtp_data.get("Illuminance [lx]"),
            rtol=1e-5,
            atol=1e-8,
        )
    )
    assert all(
        np.isclose(
            vtp_meshes.point_data.get("Irradiance [W/m2]"),
            vtp_data.get("Irradiance [W/m2]"),
            rtol=1e-5,
            atol=1e-8,
        )
    )
    assert all(
        np.isclose(
            vtp_meshes.point_data.get("Reflection"),
            vtp_data.get("Reflection"),
            rtol=1e-5,
            atol=1e-8,
        )
    )
    assert all(
        np.isclose(
            vtp_meshes.point_data.get("Transmission"),
            vtp_data.get("Transmission"),
            rtol=1e-5,
            atol=1e-8,
        )
    )
    assert all(
        np.isclose(
            vtp_meshes.point_data.get("Absorption"),
            vtp_data.get("Absorption"),
            rtol=1e-5,
            atol=1e-8,
        )
    )

    #  === test 3d sensor colorimetric ===
    # verify if only illuminate data is saved in vtp
    p4 = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism_3D.speos"),
    )
    sim = p4.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]

    sensor_3d = p4.find(name=".*", name_regex=True, feature_type=Sensor3DIrradiance)[0]
    sensor_3d.set_type_colorimetric()
    sensor_3d.commit()
    speos_results, vtp_results = sim.compute_CPU(export_vtp=True)
    assert does_file_exist(vtp_results[1])

    vtp_data = pv.read(vtp_results[1]).point_data
    assert np.allclose(vtp_data.get("Reflection"), 0.0) is True
    assert np.allclose(vtp_data.get("Illuminance [lx]"), 0.0) is not True
    assert np.allclose(vtp_data.get("Irradiance [W/m2]"), 0.0) is True
    assert np.allclose(vtp_data.get("Transmission"), 0.0) is True
    assert np.allclose(vtp_data.get("Absorption"), 0.0) is True

    # === test irradiance xmp photometric ===
    # verify the result is photometric
    p5 = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism.speos"),
    )
    sim = p5.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
    sensor_irra = p5.find(name=".*", name_regex=True, feature_type=SensorIrradiance)[0]
    sensor_irra.set_dimensions().set_x_sampling(10).set_y_sampling(10)
    sensor_irra.set_type_photometric()
    sensor_irra.commit()
    speos_results, vtp_results = sim.compute_CPU(export_vtp=True)
    assert does_file_exist(vtp_results[0])

    vtp_data = pv.read(vtp_results[0]).point_data
    assert np.allclose(vtp_data.get("Photometric"), 0.0) is not True

    export_data_xmp = [result.path for result in speos_results if result.path.endswith(".xmp")][0]
    export_data_xmp_txt = Path(export_data_xmp).with_suffix(".txt")
    file = export_data_xmp_txt.open("r")
    content = file.readlines()
    file.close()
    skip_lines = 9 if "SeparatedByLayer" in content[7] else 8
    resolution_x = 10
    resolution_y = 10
    xmp_data = []
    if "2" not in content[0]:  # not spectral data
        for line in content[skip_lines : skip_lines + resolution_y]:
            line_content = line.strip().split()
            xmp_data.append(list(map(float, line_content)))
    else:  # spectral data within number of data tables
        spectral_tables = int(content[6].strip().split()[2])
        xmp_data = [
            [0 for _ in range(len(content[skip_lines].strip().split()))]
            for _ in range(resolution_y)
        ]
        for _ in range(spectral_tables):
            for i in range(resolution_y):
                row = list(map(float, content[skip_lines].strip().split()))
                for j in range(resolution_x):
                    xmp_data[i][j] += row[j]
                skip_lines += 1
            # Skip one line between tables
            skip_lines += 1
    assert np.all(
        np.isclose(
            np.array(xmp_data),
            vtp_data.get("Photometric").reshape((10, 10)).T,
            rtol=1e-5,
            atol=1e-8,
        )
    )

    # === test irradiance xmp radiometric ===
    # verify the result is radiometric
    p6 = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism.speos"),
    )
    sim = p6.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
    sensor_irra = p6.find(name=".*", name_regex=True, feature_type=SensorIrradiance)[0]
    sensor_irra.set_dimensions().set_x_sampling(10).set_y_sampling(10)
    sensor_irra.set_type_radiometric()
    sensor_irra.commit()
    speos_results, vtp_results = sim.compute_CPU(export_vtp=True)
    assert does_file_exist(vtp_results[0])

    vtp_data = pv.read(vtp_results[0]).point_data
    assert np.allclose(vtp_data.get("Radiometric"), 0.0) is not True

    # === test irradiance colorimetric ===
    # verify it has x, photometric, radiometric, z value in vtp file
    p7 = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism.speos"),
    )
    sim = p7.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
    sensor_irra = p7.find(name=".*", name_regex=True, feature_type=SensorIrradiance)[0]
    sensor_irra.set_dimensions().set_x_sampling(10).set_y_sampling(10)
    sensor_irra.set_type_colorimetric()
    sensor_irra.commit()

    speos_results, vtp_results = sim.compute_CPU(export_vtp=True)
    assert does_file_exist(vtp_results[0])

    vtp_data = pv.read(vtp_results[0]).point_data
    assert np.allclose(vtp_data.get("X"), 0.0) is not True
    assert np.allclose(vtp_data.get("Photometric"), 0.0) is not True
    assert np.allclose(vtp_data.get("Radiometric"), 0.0) is not True
    assert np.allclose(vtp_data.get("Z"), 0.0) is not True

    # === test irradiance spectral ===
    # verify it has x, photometric, radiometric, z value in vtp file
    # verify the summing up per spectral layer
    p8 = Project(
        speos=speos,
        path=str(Path(test_path) / "Prism.speos" / "Prism.speos"),
    )
    sim = p8.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
    sensor_irra = p8.find(name=".*", name_regex=True, feature_type=SensorIrradiance)[0]
    sensor_irra.set_dimensions().set_x_sampling(10).set_y_sampling(10)
    sensor_irra.set_type_spectral()
    sensor_irra.commit()
    speos_results, vtp_results = sim.compute_CPU(export_vtp=True)
    assert does_file_exist(vtp_results[0])

    vtp_data = pv.read(vtp_results[0]).point_data
    assert np.allclose(vtp_data.get("Radiometric"), 0.0) is not True

    # # test radiance photometric
    # # test radiance radiometric
    # # test radiance colorimetric
    # # test radiance spectral
