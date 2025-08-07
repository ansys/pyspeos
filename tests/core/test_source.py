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

"""Unit test for Source Class."""

import datetime
from pathlib import Path

import pytest

from ansys.speos.core import GeoRef, Project, Speos
from ansys.speos.core.source import (
    SourceAmbientNaturalLight,
    SourceLuminaire,
    SourceRayFile,
    SourceSurface,
)
from tests.conftest import test_path


def test_create_luminaire_source(speos: Speos):
    """Test creation of luminaire source."""
    p = Project(speos=speos)

    # Default value
    # source1 = p.create_source(name="Luminaire.1")
    source1 = SourceLuminaire(p, "Luminaire.1")
    assert source1._source_template.HasField("luminaire")
    assert source1._source_template.luminaire.intensity_file_uri == ""
    assert source1._source_template.luminaire.HasField("flux_from_intensity_file")
    assert source1._spectrum._spectrum._spectrum.HasField("predefined")
    assert source1._spectrum._spectrum._spectrum.predefined.HasField("incandescent")
    assert source1._spectrum._spectrum._spectrum.name == "Luminaire.1.Spectrum"
    assert source1._source_instance.HasField("luminaire_properties")
    assert source1._source_instance.luminaire_properties.axis_system == [
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

    # intensity_file_uri
    source1.intensity_file_uri = Path(test_path) / "IES_C_DETECTOR.ies"
    source1.commit()
    assert source1.intensity_file_uri == str(Path(test_path) / "IES_C_DETECTOR.ies")
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().luminaire.intensity_file_uri != ""

    # spectrum
    source1.set_spectrum().set_halogen()
    source1.commit()
    spectrum = speos.client[source1.source_template_link.get().luminaire.spectrum_guid]
    assert spectrum.get().HasField("predefined")
    assert spectrum.get().predefined.HasField("halogen")

    # flux luminous_flux
    source1.set_flux_luminous().value = 650
    source1.commit()
    assert source1.set_flux_luminous().value == 650
    assert source1.source_template_link.get().luminaire.HasField("luminous_flux")
    assert source1.source_template_link.get().luminaire.luminous_flux.luminous_value == 650

    # flux radiant_flux
    source1.set_flux_radiant().value = 1.2
    source1.commit()
    assert source1.set_flux_radiant().value == 1.2
    assert source1.source_template_link.get().luminaire.HasField("radiant_flux")
    assert source1.source_template_link.get().luminaire.radiant_flux.radiant_value == 1.2

    # flux_from_intensity_file
    source1.set_flux_from_intensity_file()
    source1.commit()
    assert source1.source_template_link.get().luminaire.HasField("flux_from_intensity_file")

    # Properties : axis_system
    source1.axis_system = [10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    # source1.set_axis_system(axis_system=[10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    source1.commit()
    assert source1.axis_system == [10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert source1._source_instance.HasField("luminaire_properties")
    assert source1._source_instance.luminaire_properties.axis_system == [
        10,
        20,
        10,
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

    assert len(p.scene_link.get().sources) == 1
    assert p.scene_link.get().sources[0].luminaire_properties.axis_system == [
        10,
        20,
        10,
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

    with pytest.raises(RuntimeError, match="Luminous class instantiated outside of class scope"):
        SourceLuminaire.Luminous(
            luminous_flux=source1._source_template.luminaire.luminous_flux,
            default_values=True,
            stable_ctr=False,
        )

    with pytest.raises(RuntimeError, match="Radiant class instantiated outside of class scope"):
        SourceLuminaire.Radiant(
            radiant_flux=source1._source_template.luminaire.radiant_flux,
            default_values=True,
            stable_ctr=False,
        )

    source1.delete()
    assert len(p.scene_link.get().sources) == 0


def test_create_surface_source(speos: Speos):
    """Test creation of surface source."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="BodyB")
    body_b.create_face(name="FaceB1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    body_b.create_face(name="FaceB2").set_vertices([1, 0, 0, 2, 0, 0, 1, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    # Default value
    # source1 = p.create_source(name="Surface.1")
    source1 = SourceSurface(project=p, name="Surface.1")
    source1.set_exitance_constant().geometries = [(GeoRef.from_native_link("BodyB"), False)]
    source1.commit()
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().HasField("surface")
    assert source1.source_template_link.get().surface.HasField("exitance_constant")
    assert source1.source_template_link.get().surface.HasField("luminous_flux")
    assert source1.source_template_link.get().surface.luminous_flux.luminous_value == 683
    assert source1.source_template_link.get().surface.HasField("spectrum_guid")
    spectrum = speos.client[source1.source_template_link.get().surface.spectrum_guid]
    assert spectrum.get().name == "Surface.1.Spectrum"
    assert spectrum.get().HasField("monochromatic")
    assert source1.source_template_link.get().surface.intensity_guid != ""
    intensity = speos.client[source1.source_template_link.get().surface.intensity_guid]
    assert intensity.get().HasField("cos")

    # set intensity as library to be able to use flux_from_intensity_file
    source1.set_intensity().set_library().set_intensity_file_uri(
        uri=str(Path(test_path) / "IES_C_DETECTOR.ies")
    )
    source1.set_flux_from_intensity_file()
    source1.commit()
    assert source1.source_template_link.get().surface.HasField("flux_from_intensity_file")
    intensity = speos.client[source1.source_template_link.get().surface.intensity_guid]
    assert intensity.get().HasField("library")
    assert source1._source_instance.HasField("surface_properties")
    surface_properties = source1._source_instance.surface_properties
    assert surface_properties.HasField("intensity_properties")
    assert surface_properties.intensity_properties.HasField("library_properties")
    assert surface_properties.intensity_properties.library_properties.HasField("axis_system")

    # luminous_flux
    source1.set_flux_luminous().value = 630
    source1.commit()
    assert source1.source_template_link.get().surface.HasField("luminous_flux")
    assert source1.source_template_link.get().surface.luminous_flux.luminous_value == 630

    # radiant_flux
    source1.set_flux_radiant().value = 1.1
    source1.commit()
    assert source1.source_template_link.get().surface.HasField("radiant_flux")
    assert source1.source_template_link.get().surface.radiant_flux.radiant_value == 1.1

    # luminous_intensity_flux
    source1.set_flux_luminous_intensity().value = 5.5
    source1.commit()
    assert source1.set_flux_luminous_intensity().value == 5.5
    assert source1.source_template_link.get().surface.HasField("luminous_intensity_flux")
    assert (
        source1.source_template_link.get().surface.luminous_intensity_flux.luminous_intensity_value
        == 5.5
    )

    # exitance_variable + spectrum_from_xmp_file
    source1.set_exitance_variable().xmp_file_uri = (
        Path(test_path) / "PROJECT.Direct-no-Ray.Irradiance Ray Spectral.xmp"
    )
    source1.set_spectrum_from_xmp_file()
    source1.commit()
    assert source1.set_exitance_variable().xmp_file_uri == str(
        Path(test_path) / "PROJECT.Direct-no-Ray.Irradiance Ray Spectral.xmp"
    )
    assert source1.source_template_link.get().surface.HasField("exitance_variable")
    assert source1.source_template_link.get().surface.exitance_variable.exitance_xmp_file_uri != ""
    assert source1.source_template_link.get().surface.HasField("spectrum_from_xmp_file")
    assert surface_properties.HasField("exitance_variable_properties")
    assert surface_properties.exitance_variable_properties.axis_plane == [
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
        0,
    ]

    # Properties
    # exitance_variable axis_plane
    source1.set_exitance_variable().axis_plane = [10, 10, 15, 1, 0, 0, 0, 1, 0]
    source1.commit()
    assert source1.set_exitance_variable().axis_plane == [10, 10, 15, 1, 0, 0, 0, 1, 0]
    assert surface_properties.HasField("exitance_variable_properties")
    assert surface_properties.exitance_variable_properties.axis_plane == [
        10,
        10,
        15,
        1,
        0,
        0,
        0,
        1,
        0,
    ]

    # exitance_constant geometries
    source1.set_exitance_constant().geometries = [
        (GeoRef.from_native_link("BodyB/FaceB1"), False),
        (GeoRef.from_native_link("BodyB/FaceB2"), True),
    ]
    source1.set_spectrum().set_blackbody()
    source1.commit()
    assert len(source1.set_exitance_constant().geometries) == 2
    assert surface_properties.HasField("exitance_constant_properties")
    assert len(surface_properties.exitance_constant_properties.geo_paths) == 2
    assert surface_properties.exitance_constant_properties.geo_paths[0].geo_path == "BodyB/FaceB1"
    assert surface_properties.exitance_constant_properties.geo_paths[0].reverse_normal is False
    assert surface_properties.exitance_constant_properties.geo_paths[1].geo_path == "BodyB/FaceB2"
    assert surface_properties.exitance_constant_properties.geo_paths[1].reverse_normal is True

    source1.set_exitance_constant().geometries = []  # clear geometries
    assert surface_properties.HasField("exitance_constant_properties")
    assert len(surface_properties.exitance_constant_properties.geo_paths) == 0

    with pytest.raises(RuntimeError, match="Intensity class instantiated outside of class scope"):
        SourceSurface.Intensity(
            intensity_flux=source1._source_template.surface.luminous_intensity_flux,
            default_values=True,
            stable_ctr=False,
        )

    with pytest.raises(
        RuntimeError, match="ExitanceConstant class instantiated outside of class scope"
    ):
        SourceSurface.ExitanceConstant(
            exitance_constant=source1._source_template.surface.exitance_constant,
            exitance_constant_props=source1._source_instance.surface_properties.exitance_constant_properties,
            default_values=True,
            stable_ctr=False,
        )

    with pytest.raises(
        RuntimeError, match="ExitanceVariable class instantiated outside of class scope"
    ):
        SourceSurface.ExitanceVariable(
            exitance_variable=source1._source_template.surface.exitance_variable,
            exitance_variable_props=source1._source_instance.surface_properties.exitance_variable_properties,
            default_values=True,
            stable_ctr=False,
        )

    source1.delete()


def test_create_rayfile_source(speos: Speos):
    """Test creation of ray file."""
    p = Project(speos=speos)

    # Default value : not committed because not valid by default due to ray_file_uri needed
    source1 = SourceRayFile(
        p,
        name="Ray-file.1",
    )
    assert source1._source_instance.HasField("rayfile_properties")
    assert source1._source_instance.rayfile_properties.axis_system == [
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
    assert source1._source_template.HasField("rayfile")
    assert source1._source_template.rayfile.HasField("flux_from_ray_file")
    assert source1._source_template.rayfile.HasField("spectrum_from_ray_file")
    assert source1._source_template.rayfile.ray_file_uri == ""

    # ray_file_uri
    source1.ray_file_uri = Path(test_path) / "Rays.ray"
    source1.commit()
    assert source1.ray_file_uri == str(Path(test_path) / "Rays.ray")
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().HasField("rayfile")
    assert source1.source_template_link.get().rayfile.ray_file_uri != ""
    assert source1.source_template_link.get().rayfile.HasField("flux_from_ray_file")
    assert source1.source_template_link.get().rayfile.HasField("spectrum_from_ray_file")

    # luminous_flux
    source1.set_flux_luminous().value = 641
    source1.commit()
    assert source1.set_flux_luminous().value == 641
    assert source1.source_template_link.get().rayfile.HasField("luminous_flux")
    assert source1.source_template_link.get().rayfile.luminous_flux.luminous_value == 641

    # radiant_flux
    source1.set_flux_radiant().value = 1.3
    source1.commit()
    assert source1.set_flux_radiant().value == 1.3
    assert source1.source_template_link.get().rayfile.HasField("radiant_flux")
    assert source1.source_template_link.get().rayfile.radiant_flux.radiant_value == 1.3

    # flux_from_ray_file
    source1.set_flux_from_ray_file()
    source1.commit()
    assert source1.source_template_link.get().rayfile.HasField("flux_from_ray_file")

    # spectrum (need to change ray file so that it does not contain spectral data)
    source1.ray_file_uri = Path(test_path) / "RaysWithoutSpectralData.RAY"
    # source1.set_ray_file_uri(uri=str(Path(test_path) / "RaysWithoutSpectralData.RAY"))
    source1.set_spectrum().set_blackbody()
    source1.commit()
    assert source1.source_template_link.get().rayfile.spectrum_guid != ""
    spectrum = speos.client[source1.source_template_link.get().rayfile.spectrum_guid]
    assert spectrum.get().name == "Ray-file.1.Spectrum"
    assert spectrum.get().HasField("blackbody")

    # properties
    # axis_system
    source1.axis_system = [50, 40, 50, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    source1.commit()
    assert source1.axis_system == [50, 40, 50, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert source1._source_instance.HasField("rayfile_properties")
    assert source1._source_instance.rayfile_properties.axis_system == [
        50,
        40,
        50,
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

    # exit_geometries
    source1.set_exit_geometries().geometries = [
        GeoRef.from_native_link("BodyB"),
        GeoRef.from_native_link("BodyC"),
    ]
    source1.commit()
    assert len(source1.set_exit_geometries().geometries) == 2
    assert source1._source_instance.rayfile_properties.HasField("exit_geometries")
    assert len(source1._source_instance.rayfile_properties.exit_geometries.geo_paths) == 2
    assert source1._source_instance.rayfile_properties.exit_geometries.geo_paths == [
        "BodyB",
        "BodyC",
    ]

    source1.set_exit_geometries().geometries = []  # use default [] to reset exit geometries
    source1.commit()
    assert source1._source_instance.rayfile_properties.HasField("exit_geometries") is False

    source1.delete()


def test_create_natural_light_source(speos: Speos):
    """Test creation of ambient natural light source."""
    p = Project(speos=speos)

    # Default value :
    source1 = SourceAmbientNaturalLight(
        p,
        name="NaturalLight.1",
    )
    now = datetime.datetime.now()
    assert source1._source_instance.HasField("ambient_properties")
    assert source1._source_instance.ambient_properties.zenith_direction == [
        0,
        0,
        1,
    ]
    assert source1._source_instance.ambient_properties.HasField("natural_light_properties")
    tmp_natural_light_property = (
        source1._source_instance.ambient_properties.natural_light_properties
    )
    assert tmp_natural_light_property.north_direction == [
        0,
        1,
        0,
    ]
    assert tmp_natural_light_property.HasField("sun_axis_system")
    assert tmp_natural_light_property.sun_axis_system.HasField("automatic_sun")
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.year == now.year
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.month == now.month
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.day == now.day
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.hour == now.hour
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.minute == now.minute
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.time_zone_uri == "CET"

    assert source1._source_template.HasField("ambient")
    assert source1._source_template.ambient.HasField("natural_light")
    assert source1._source_template.ambient.natural_light.turbidity == 3
    assert source1._source_template.ambient.natural_light.with_sky is True

    # Check property method
    assert source1.zenith_direction == [0, 0, 1]
    assert source1.reverse_zenith_direction is False
    assert source1.north_direction == [0, 1, 0]
    assert source1.reverse_north_direction is False

    source1.zenith_direction = [0, 0, 1]
    source1.reverse_zenith_direction = True
    source1.north_direction = [1, 0, 0]
    source1.reverse_north_direction = True
    source1.turbidity = 4
    source1.with_sky = False
    source1.commit()
    assert source1._source_template.ambient.natural_light.turbidity == 4
    assert source1._source_template.ambient.natural_light.with_sky is False
    assert source1._source_instance.ambient_properties.zenith_direction == [
        0,
        0,
        1,
    ]
    assert source1._source_instance.ambient_properties.natural_light_properties.north_direction == [
        1,
        0,
        0,
    ]
    assert (
        source1._source_instance.ambient_properties.natural_light_properties.reverse_north is True
    )
    assert source1._source_instance.ambient_properties.reverse_zenith is True

    source1.set_sun_manual().direction = [0, 0, 1]
    source1.commit()

    # check the backend
    tmp_natural_light_property = (
        source1._source_instance.ambient_properties.natural_light_properties
    )
    assert tmp_natural_light_property.sun_axis_system.HasField("manual_sun")
    assert tmp_natural_light_property.sun_axis_system.manual_sun.sun_direction == [0, 0, 1]
    assert tmp_natural_light_property.sun_axis_system.manual_sun.reverse_sun is False

    # check the property method
    assert source1.turbidity == 4
    assert source1.with_sky is False
    assert source1.set_sun_manual().direction == [0, 0, 1]
    assert source1.set_sun_manual().reverse_sun is False

    source1.set_sun_automatic().year = 2026
    source1.set_sun_automatic().month = 12
    source1.set_sun_automatic().day = 31
    source1.set_sun_automatic().hour = 12
    source1.set_sun_automatic().minute = 23
    source1.set_sun_automatic().longitude = 10
    source1.set_sun_automatic().latitude = 45
    source1.set_sun_automatic().time_zone = "CST"
    source1.commit()

    # check the backend
    tmp_natural_light_property = (
        source1._source_instance.ambient_properties.natural_light_properties
    )
    assert tmp_natural_light_property.sun_axis_system.HasField("automatic_sun")
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.year == 2026
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.month == 12
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.day == 31
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.hour == 12
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.minute == 23
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.longitude == 10
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.latitude == 45
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.time_zone_uri == "CST"

    # check property methods
    assert source1.set_sun_automatic().year == 2026
    assert source1.set_sun_automatic().month == 12
    assert source1.set_sun_automatic().day == 31
    assert source1.set_sun_automatic().hour == 12
    assert source1.set_sun_automatic().minute == 23
    assert source1.set_sun_automatic().longitude == 10
    assert source1.set_sun_automatic().latitude == 45
    assert source1.set_sun_automatic().time_zone == "CST"

    source1.delete()

    source2 = p.create_source(name="NaturalLight.2", feature_type=SourceAmbientNaturalLight)
    now = datetime.datetime.now()
    assert source2._source_instance.HasField("ambient_properties")
    assert source2._source_instance.ambient_properties.zenith_direction == [
        0,
        0,
        1,
    ]
    assert source2._source_instance.ambient_properties.HasField("natural_light_properties")
    tmp_natural_light_property = (
        source2._source_instance.ambient_properties.natural_light_properties
    )
    assert tmp_natural_light_property.north_direction == [
        0,
        1,
        0,
    ]
    assert tmp_natural_light_property.HasField("sun_axis_system")
    assert tmp_natural_light_property.sun_axis_system.HasField("automatic_sun")
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.year == now.year
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.month == now.month
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.day == now.day
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.hour == now.hour
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.minute == now.minute
    assert tmp_natural_light_property.sun_axis_system.automatic_sun.time_zone_uri == "CET"

    assert source2._source_template.HasField("ambient")
    assert source2._source_template.ambient.HasField("natural_light")
    assert source2._source_template.ambient.natural_light.turbidity == 3
    assert source2._source_template.ambient.natural_light.with_sky is True

    source2.delete()


def test_keep_same_internal_feature(speos: Speos):
    """Test regarding source internal features (like spectrum, intensity).

    The aim is not to pollute server each time a spectrum/intensity is modified in a
    So use better update of the spectrum/intensity instead of create.
    """
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="BodyB")
    body_b.create_face(name="FaceB1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    # SURFACE SOURCE
    source1 = SourceSurface(project=p, name="Surface.1")
    source1.set_exitance_constant().geometries = [(body_b, False)]
    source1.commit()
    spectrum_guid = source1.source_template_link.get().surface.spectrum_guid
    intensity_guid = source1.source_template_link.get().surface.intensity_guid

    # Modify intensity
    source1.set_intensity().set_gaussian()
    source1.commit()
    assert source1.source_template_link.get().surface.intensity_guid == intensity_guid

    # Modify spectrum
    source1.set_spectrum().set_halogen()
    source1.commit()
    assert source1.source_template_link.get().surface.spectrum_guid == spectrum_guid

    # LUMINAIRE SOURCE
    source2 = SourceLuminaire(project=p, name="Luminaire.1")
    source2.intensity_file_uri = Path(test_path) / "IES_C_DETECTOR.ies"
    source2.commit()
    spectrum_guid = source2.source_template_link.get().luminaire.spectrum_guid

    # Modify spectrum
    source2.set_spectrum().set_halogen()
    source2.commit()
    assert source2.source_template_link.get().luminaire.spectrum_guid == spectrum_guid

    # RAY FILE SOURCE
    source3 = SourceRayFile(project=p, name="Ray-fiile.1")
    source3.ray_file_uri = Path(test_path) / "RaysWithoutSpectralData.RAY"
    source3.set_spectrum().set_blackbody()
    # source3.set_ray_file_uri(
    #     uri=str(Path(test_path) / "RaysWithoutSpectralData.RAY")
    # ).set_spectrum().set_blackbody()
    source3.commit()
    spectrum_guid = source3.source_template_link.get().rayfile.spectrum_guid

    # Modify spectrum
    source3.set_spectrum().set_monochromatic()
    source3.commit()
    assert source3.source_template_link.get().rayfile.spectrum_guid == spectrum_guid

    source1.delete()
    source2.delete()
    source3.delete()


def test_commit_source(speos: Speos):
    """Test commit of source."""
    p = Project(speos=speos)

    # Create
    source1 = SourceRayFile(project=p, name="Ray-file.1")
    source1.ray_file_uri = Path(test_path) / "Rays.ray"
    assert source1.source_template_link is None
    assert len(p.scene_link.get().sources) == 0

    # Commit
    source1.commit()
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().HasField("rayfile")
    assert len(p.scene_link.get().sources) == 1
    assert p.scene_link.get().sources[0] == source1._source_instance

    # Change only in local isn't committed
    source1.axis_system = [10, 10, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert p.scene_link.get().sources[0] != source1._source_instance

    source1.delete()


def test_reset_source(speos: Speos):
    """Test reset of a source."""
    p = Project(speos=speos)

    # Create + commit
    source1 = SourceRayFile(project=p, name="1")
    source1.ray_file_uri = Path(test_path) / "Rays.ray"
    # source1.set_ray_file_uri(uri=str(Path(test_path) / "Rays.ray"))
    source1.commit()
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().HasField("rayfile")
    assert len(p.scene_link.get().sources) == 1
    assert p.scene_link.get().sources[0].HasField("rayfile_properties")

    # Change local data (on template and on instance)
    source1.set_flux_radiant().value = 3.5  # template
    source1.set_exit_geometries().geometries = [
        GeoRef.from_native_link("TheBodyB/TheFaceB1")
    ]  # instance
    assert len(source1.set_exit_geometries().geometries) == 1
    assert source1.source_template_link.get().rayfile.HasField("flux_from_ray_file")
    assert source1._source_template.rayfile.HasField("radiant_flux")  # local template
    assert p.scene_link.get().sources[0].rayfile_properties.exit_geometries.geo_paths == []
    assert source1._source_instance.rayfile_properties.exit_geometries.geo_paths == [
        "TheBodyB/TheFaceB1"
    ]  # local instance

    # Ask for reset
    source1.reset()
    assert source1.source_template_link.get().rayfile.HasField("flux_from_ray_file")
    assert source1._source_template.rayfile.HasField("flux_from_ray_file")  # local template
    assert p.scene_link.get().sources[0].rayfile_properties.exit_geometries.geo_paths == []
    assert (
        source1._source_instance.rayfile_properties.exit_geometries.geo_paths == []
    )  # local instance

    source1.delete()


def test_luminaire_modify_after_reset(speos: Speos):
    """Test reset of luminaire source, and then modify."""
    p = Project(speos=speos)

    # Create + commit
    source = SourceLuminaire(project=p, name="Luminaire.1")
    source.intensity_file_uri = Path(test_path) / "IES_C_DETECTOR.ies"
    source.set_flux_luminous()
    source.commit()

    # Ask for reset
    source.reset()

    # Modify after a reset
    # Template
    assert source.set_flux_luminous().value == 683
    assert source._source_template.luminaire.luminous_flux.luminous_value == 683
    source.set_flux_luminous().value = 500
    assert source._source_template.luminaire.luminous_flux.luminous_value == 500

    # Intermediate class for spectrum
    assert source._spectrum._spectrum._spectrum.HasField("predefined")
    source.set_spectrum().set_blackbody()
    assert source._spectrum._spectrum._spectrum.HasField("blackbody")

    # Props
    assert source._source_instance.luminaire_properties.axis_system == [
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
    source.axis_system = [50, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert source._source_instance.luminaire_properties.axis_system == [
        50,
        20,
        10,
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

    source.delete()


def test_rayfile_modify_after_reset(speos: Speos):
    """Test reset of ray file source, and then modify."""
    p = Project(speos=speos)

    # Create + commit
    source = SourceRayFile(project=p, name="1")
    source.set_flux_luminous()
    source.ray_file_uri = Path(test_path) / "RaysWithoutSpectralData.RAY"
    source.set_spectrum()
    source.commit()

    # Ask for reset
    source.reset()

    # Modify after a reset
    # Template
    assert source._source_template.rayfile.luminous_flux.luminous_value == 683
    source.set_flux_luminous().value = 500
    assert source._source_template.rayfile.luminous_flux.luminous_value == 500

    # Intermediate class for spectrum
    assert source._spectrum._spectrum._spectrum.HasField("monochromatic")
    source.set_spectrum().set_blackbody()
    assert source._spectrum._spectrum._spectrum.HasField("blackbody")

    # Props
    assert source._source_instance.rayfile_properties.axis_system == [
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
    source.axis_system = [50, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert source._source_instance.rayfile_properties.axis_system == [
        50,
        20,
        10,
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

    source.delete()


def test_surface_modify_after_reset(speos: Speos):
    """Test reset of surface source, and then modify."""
    p = Project(speos=speos)

    # Create + commit
    source = SourceSurface(project=p, name="Surface.2")
    source.set_flux_luminous()
    source.set_spectrum_from_xmp_file()
    source.set_exitance_variable().xmp_file_uri = (
        Path(test_path) / "PROJECT.Direct-no-Ray.Irradiance Ray Spectral.xmp"
    )
    source.commit()

    # Ask for reset
    source.reset()

    # Modify after a reset
    # Template
    assert source._source_template.surface.luminous_flux.luminous_value == 683
    source.set_flux_luminous().value = 500
    assert source._source_template.surface.luminous_flux.luminous_value == 500

    # Intermediate class for spectrum
    assert source._spectrum._spectrum._spectrum.HasField("monochromatic")
    source.set_spectrum().set_blackbody()
    assert source._spectrum._spectrum._spectrum.HasField("blackbody")

    # Intermediate class for intensity
    assert source._intensity._intensity_template.HasField("cos")
    source.set_intensity().set_gaussian()
    assert source._intensity._intensity_template.HasField("gaussian")

    # Intermediate class for exitance variable + Props
    assert source._source_instance.surface_properties.exitance_variable_properties.axis_plane == [
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        1,
        0,
    ]
    source.set_exitance_variable().axis_plane = [50, 20, 10, 1, 0, 0, 0, 1, 0]
    assert source._source_instance.surface_properties.exitance_variable_properties.axis_plane == [
        50,
        20,
        10,
        1,
        0,
        0,
        0,
        1,
        0,
    ]

    source.delete()


def test_delete_source(speos: Speos):
    """Test delete of source."""
    p = Project(speos=speos)

    # Create + commit
    source1 = p.create_source(name="1", feature_type=SourceRayFile)
    # source1 = SourceRayFile(project=p, name="1")
    source1.ray_file_uri = Path(test_path) / "Rays.ray"
    source1.commit()
    assert source1.source_template_link.get().HasField("rayfile")
    assert source1._source_template.HasField("rayfile")  # local
    assert len(p.scene_link.get().sources) == 1
    assert p.scene_link.get().sources[0].HasField("rayfile_properties")
    assert source1._source_instance.HasField("rayfile_properties")  # local

    # Delete
    source1.delete()
    assert source1._unique_id is None
    assert len(source1._source_instance.metadata) == 0

    assert source1.source_template_link is None
    assert source1._source_template.HasField("rayfile")  # local

    assert len(p.scene_link.get().sources) == 0
    assert source1._source_instance.HasField("rayfile_properties")  # local


def test_print_source(speos: Speos):
    """Test delete of source."""
    p = Project(speos=speos)

    root_part = p.create_root_part()
    body_b = root_part.create_body(name="BodyB")
    body_b.create_face(name="FaceB1").set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0]).set_facets(
        [0, 1, 2]
    ).set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    root_part.commit()

    # LUMINAIRE - SPECTRUM
    # Create + commit
    # source = p.create_source(name="Luminaire.1")
    source = SourceLuminaire(project=p, name="Luminaire.1")
    source.intensity_file_uri = Path(test_path) / "IES_C_DETECTOR.ies"
    source.commit()

    # Retrieve print
    str_before = str(source)

    # Modify : spectrum type
    # No commit
    source.set_spectrum().set_blackbody()

    # Check that print is not modified
    str_after = str(source)
    assert str_before == str_after
    source.delete()

    # RAYFILE - SPECTRUM
    # Create + commit
    # source = p.create_source(name="1")
    source = SourceRayFile(project=p, name="1")
    source.ray_file_uri = Path(test_path) / "RaysWithoutSpectralData.RAY"
    source.set_spectrum()
    source.commit()

    # Retrieve print
    str_before = str(source)

    # Modify : spectrum_from_ray_file
    # No commit
    source.set_spectrum_from_ray_file()

    # Check that print is not modified
    str_after = str(source)
    assert str_before == str_after
    source.delete()

    # SURFACE - SPECTRUM
    source = SourceSurface(project=p, name="Surface.1")
    source.set_exitance_constant().geometries = [(GeoRef.from_native_link("BodyB"), False)]
    source.commit()

    # Retrieve print
    str_before = str(source)

    # Modify : spectrum_from_xmp_file
    # No commit
    source.set_spectrum_from_xmp_file()

    # Check that print is not modified
    str_after = str(source)
    assert str_before == str_after
    source.delete()


def test_get_source(speos: Speos, capsys):
    """Test get method of the source class."""
    p = Project(speos=speos)
    source1 = p.create_source(name="rayfile_source", feature_type=SourceRayFile)
    source2 = p.create_source(name="source2", feature_type=SourceLuminaire)
    source3 = p.create_source(name="source4", feature_type=SourceSurface)
    # test when key exists
    name = source1.get(key="name")
    assert name == "rayfile_source"
    property_info = source2.get(key="axis_system")
    assert property_info is not None
    property_info = source3.get(key="geo_path")
    assert property_info is not None

    # test when key does not exist
    get_result1 = source1.get(key="geometry")
    stdout, stderr = capsys.readouterr()
    assert get_result1 is None
    assert "Used key: geometry not found in key list" in stdout
    get_result2 = source2.get(key="geometry")
    stdout, stderr = capsys.readouterr()
    assert get_result2 is None
    assert "Used key: geometry not found in key list" in stdout
    get_result3 = source3.get(key="geometry")
    stdout, stderr = capsys.readouterr()
    assert get_result3 is None
    assert "Used key: geometry not found in key list" in stdout
