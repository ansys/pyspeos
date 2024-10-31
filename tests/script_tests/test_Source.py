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
Test basic using source from script layer.
"""

import os

from ansys.speos.core.speos import Speos
import ansys.speos.script as script
from conftest import test_path


def test_create_luminaire_source(speos: Speos):
    """Test creation of luminaire source."""
    p = script.Project(speos=speos)

    # Default value
    source1 = p.create_source(name="Luminaire.1")
    source1.set_luminaire()
    assert source1._source_template.HasField("luminaire")
    assert source1._source_template.luminaire.intensity_file_uri == ""
    assert source1._source_template.luminaire.HasField("flux_from_intensity_file")
    assert source1._type._spectrum._spectrum.HasField("predefined")
    assert source1._type._spectrum._spectrum.predefined.HasField("incandescent")
    assert source1._source_instance.HasField("luminaire_properties")
    assert source1._source_instance.luminaire_properties.axis_system == [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    # intensity_file_uri
    source1.set_luminaire().set_intensity_file_uri(uri=os.path.join(test_path, "IES_C_DETECTOR.ies"))
    source1.commit()
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().luminaire.intensity_file_uri != ""

    # spectrum
    source1.set_luminaire().set_spectrum().set_halogen()
    source1.commit()
    spectrum = speos.client.get_item(key=source1.source_template_link.get().luminaire.spectrum_guid)
    assert spectrum.get().HasField("predefined")
    assert spectrum.get().predefined.HasField("halogen")

    # flux luminous_flux
    source1.set_luminaire().set_flux_luminous(value=650)
    source1.commit()
    assert source1.source_template_link.get().luminaire.HasField("luminous_flux")
    assert source1.source_template_link.get().luminaire.luminous_flux.luminous_value == 650

    # flux radiant_flux
    source1.set_luminaire().set_flux_radiant(value=1.2)
    source1.commit()
    assert source1.source_template_link.get().luminaire.HasField("radiant_flux")
    assert source1.source_template_link.get().luminaire.radiant_flux.radiant_value == 1.2

    # flux_from_intensity_file
    source1.set_luminaire().set_flux_from_intensity_file()
    source1.commit()
    assert source1.source_template_link.get().luminaire.HasField("flux_from_intensity_file")

    # Properties : axis_system
    source1.set_luminaire().set_axis_system(axis_system=[10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    source1.commit()
    assert source1._source_instance.HasField("luminaire_properties")
    assert source1._source_instance.luminaire_properties.axis_system == [10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    assert len(p.scene_link.get().sources) == 1
    assert p.scene_link.get().sources[0].luminaire_properties.axis_system == [10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    source1.delete()
    assert len(p.scene_link.get().sources) == 0


def test_create_surface_source(speos: Speos):
    """Test creation of surface source."""
    p = script.Project(speos=speos)

    # Default value
    source1 = p.create_source(name="Surface.1")
    source1.set_surface()
    source1.commit()
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().HasField("surface")
    assert source1.source_template_link.get().surface.HasField("exitance_constant")
    assert source1.source_template_link.get().surface.HasField("luminous_flux")
    assert source1.source_template_link.get().surface.luminous_flux.luminous_value == 683
    assert source1.source_template_link.get().surface.HasField("spectrum_guid")
    spectrum = speos.client.get_item(key=source1.source_template_link.get().surface.spectrum_guid)
    assert spectrum.get().HasField("monochromatic")
    assert source1.source_template_link.get().surface.intensity_guid != ""
    intensity = speos.client.get_item(key=source1.source_template_link.get().surface.intensity_guid)
    assert intensity.get().HasField("cos")

    # set intensity as library to be able to use flux_from_intensity_file
    source1.set_surface().set_intensity().set_library().set_intensity_file_uri(uri=os.path.join(test_path, "IES_C_DETECTOR.ies"))
    source1.set_surface().set_flux_from_intensity_file()
    source1.commit()
    assert source1.source_template_link.get().surface.HasField("flux_from_intensity_file")
    intensity = speos.client.get_item(key=source1.source_template_link.get().surface.intensity_guid)
    assert intensity.get().HasField("library")
    assert source1._source_instance.HasField("surface_properties")
    assert source1._source_instance.surface_properties.HasField("intensity_properties")
    assert source1._source_instance.surface_properties.intensity_properties.HasField("library_properties")
    assert source1._source_instance.surface_properties.intensity_properties.library_properties.HasField("axis_system")

    # luminous_flux
    source1.set_surface().set_flux_luminous(value=630)
    source1.commit()
    assert source1.source_template_link.get().surface.HasField("luminous_flux")
    assert source1.source_template_link.get().surface.luminous_flux.luminous_value == 630

    # radiant_flux
    source1.set_surface().set_flux_radiant(value=1.1)
    source1.commit()
    assert source1.source_template_link.get().surface.HasField("radiant_flux")
    assert source1.source_template_link.get().surface.radiant_flux.radiant_value == 1.1

    # luminous_intensity_flux
    source1.set_surface().set_flux_luminous_intensity(value=5.5)
    source1.commit()
    assert source1.source_template_link.get().surface.HasField("luminous_intensity_flux")
    assert source1.source_template_link.get().surface.luminous_intensity_flux.luminous_intensity_value == 5.5

    # exitance_variable + spectrum_from_xmp_file
    source1.set_surface().set_exitance_variable().set_xmp_file_uri(
        uri=os.path.join(test_path, "PROJECT.Direct-no-Ray.Irradiance Ray Spectral.xmp")
    )
    source1.set_surface().set_spectrum_from_xmp_file()
    source1.commit()
    assert source1.source_template_link.get().surface.HasField("exitance_variable")
    assert source1.source_template_link.get().surface.exitance_variable.exitance_xmp_file_uri != ""
    assert source1.source_template_link.get().surface.HasField("spectrum_from_xmp_file")
    assert source1._source_instance.surface_properties.HasField("exitance_variable_properties")
    assert source1._source_instance.surface_properties.exitance_variable_properties.axis_plane == [0, 0, 0, 1, 0, 0, 0, 1, 0]

    # Properties
    # exitance_variable axis_plane
    source1.set_surface().set_exitance_variable().set_axis_plane(axis_plane=[10, 10, 15, 1, 0, 0, 0, 1, 0])
    source1.commit()
    assert source1._source_instance.surface_properties.HasField("exitance_variable_properties")
    assert source1._source_instance.surface_properties.exitance_variable_properties.axis_plane == [10, 10, 15, 1, 0, 0, 0, 1, 0]

    # exitance_constant geometries
    source1.set_surface().set_exitance_constant(
        geometries=[(script.GeoRef.from_native_link("BodyB/FaceB1"), False), (script.GeoRef.from_native_link("BodyB/FaceB2"), True)]
    ).set_spectrum().set_blackbody()
    source1.commit()
    assert source1._source_instance.surface_properties.HasField("exitance_constant_properties")
    assert len(source1._source_instance.surface_properties.exitance_constant_properties.geo_paths) == 2
    assert source1._source_instance.surface_properties.exitance_constant_properties.geo_paths[0].geo_path == "BodyB/FaceB1"
    assert source1._source_instance.surface_properties.exitance_constant_properties.geo_paths[0].reverse_normal == False
    assert source1._source_instance.surface_properties.exitance_constant_properties.geo_paths[1].geo_path == "BodyB/FaceB2"
    assert source1._source_instance.surface_properties.exitance_constant_properties.geo_paths[1].reverse_normal == True

    source1.set_surface().set_exitance_constant(geometries=[])  # clear geometries
    source1.commit()
    assert source1._source_instance.surface_properties.HasField("exitance_constant_properties")
    assert len(source1._source_instance.surface_properties.exitance_constant_properties.geo_paths) == 0

    source1.delete()


def test_create_rayfile_source(speos: Speos):
    """Test creation of ray file source."""
    p = script.Project(speos=speos)

    # Default value : not committed because not valid by default due to ray_file_uri needed
    source1 = p.create_source(name="Ray-file.1")
    source1.set_rayfile()
    assert source1._source_instance.HasField("rayfile_properties")
    assert source1._source_instance.rayfile_properties.axis_system == [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert source1._source_template.HasField("rayfile")
    assert source1._source_template.rayfile.HasField("flux_from_ray_file")
    assert source1._source_template.rayfile.HasField("spectrum_from_ray_file")
    assert source1._source_template.rayfile.ray_file_uri == ""

    # ray_file_uri
    source1.set_rayfile().set_ray_file_uri(uri=os.path.join(test_path, "Rays.ray"))
    source1.commit()
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().HasField("rayfile")
    assert source1.source_template_link.get().rayfile.ray_file_uri != ""
    assert source1.source_template_link.get().rayfile.HasField("flux_from_ray_file")
    assert source1.source_template_link.get().rayfile.HasField("spectrum_from_ray_file")

    # luminous_flux
    source1.set_rayfile().set_flux_luminous(value=641)
    source1.commit()
    assert source1.source_template_link.get().rayfile.HasField("luminous_flux")
    assert source1.source_template_link.get().rayfile.luminous_flux.luminous_value == 641

    # radiant_flux
    source1.set_rayfile().set_flux_radiant(value=1.3)
    source1.commit()
    assert source1.source_template_link.get().rayfile.HasField("radiant_flux")
    assert source1.source_template_link.get().rayfile.radiant_flux.radiant_value == 1.3

    # flux_from_ray_file
    source1.set_rayfile().set_flux_from_ray_file()
    source1.commit()
    assert source1.source_template_link.get().rayfile.HasField("flux_from_ray_file")

    # spectrum (need to change ray file so that it does not contain spectral data)
    source1.set_rayfile().set_ray_file_uri(uri=os.path.join(test_path, "RaysWithoutSpectralData.RAY"))
    source1.set_rayfile().set_spectrum().set_blackbody()
    source1.commit()
    assert source1.source_template_link.get().rayfile.spectrum_guid != ""
    spectrum = speos.client.get_item(key=source1.source_template_link.get().rayfile.spectrum_guid)
    assert spectrum.get().HasField("blackbody")

    # properties
    # axis_system
    source1.set_rayfile().set_axis_system(axis_system=[50, 40, 50, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    source1.commit()
    assert source1._source_instance.HasField("rayfile_properties")
    assert source1._source_instance.rayfile_properties.axis_system == [50, 40, 50, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    # exit_geometries
    source1.set_rayfile().set_exit_geometries(
        exit_geometries=[script.GeoRef.from_native_link("BodyB"), script.GeoRef.from_native_link("BodyC")]
    )
    source1.commit()
    assert source1._source_instance.rayfile_properties.HasField("exit_geometries")
    assert len(source1._source_instance.rayfile_properties.exit_geometries.geo_paths) == 2
    assert source1._source_instance.rayfile_properties.exit_geometries.geo_paths == ["BodyB", "BodyC"]

    source1.set_rayfile().set_exit_geometries()  # use default [] to reset exit geometries
    source1.commit()
    assert source1._source_instance.rayfile_properties.HasField("exit_geometries") == False

    source1.delete()


def test_keep_same_internal_feature(speos: Speos):
    """Test regarding source internal features (like spectrum, intensity).
    The aim is not to pollute server each time a spectrum/intensity is modified in a source.
    So use better update of the spectrum/intensity instead of create.
    But when changing source type, those elements cannot be kept
    """
    p = script.Project(speos=speos)

    # SURFACE SOURCE
    source1 = p.create_source(name="Source.1")
    source1.set_surface()
    source1.commit()
    spectrum_guid = source1.source_template_link.get().surface.spectrum_guid
    intensity_guid = source1.source_template_link.get().surface.intensity_guid

    # Modify intensity
    source1.set_surface().set_intensity().set_gaussian()
    source1.commit()
    assert source1.source_template_link.get().surface.intensity_guid == intensity_guid

    # Modify spectrum
    source1.set_surface().set_spectrum().set_halogen()
    source1.commit()
    assert source1.source_template_link.get().surface.spectrum_guid == spectrum_guid

    # LUMINAIRE SOURCE
    source1.set_luminaire().set_intensity_file_uri(uri=os.path.join(test_path, "IES_C_DETECTOR.ies"))
    source1.commit()
    spectrum_guid = source1.source_template_link.get().luminaire.spectrum_guid

    # Modify spectrum
    source1.set_luminaire().set_spectrum().set_halogen()
    source1.commit()
    assert source1.source_template_link.get().luminaire.spectrum_guid == spectrum_guid

    # RAY FILE SOURCE
    source1 = p.create_source(name="Ray-file.1")
    source1.set_rayfile().set_ray_file_uri(uri=os.path.join(test_path, "RaysWithoutSpectralData.RAY")).set_spectrum().set_blackbody()
    source1.commit()
    spectrum_guid = source1.source_template_link.get().rayfile.spectrum_guid

    # Modify spectrum
    source1.set_rayfile().set_spectrum().set_monochromatic()
    source1.commit()
    assert source1.source_template_link.get().rayfile.spectrum_guid == spectrum_guid


def test_commit_source(speos: Speos):
    """Test commit of source."""
    p = script.Project(speos=speos)

    # Create
    source1 = p.create_source(name="Ray-file.1")
    source1.set_rayfile().set_ray_file_uri(uri=os.path.join(test_path, "Rays.ray"))
    assert source1.source_template_link is None
    assert len(p.scene_link.get().sources) == 0

    # Commit
    source1.commit()
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().HasField("rayfile")
    assert len(p.scene_link.get().sources) == 1
    assert p.scene_link.get().sources[0] == source1._source_instance

    # Change only in local not committed
    source1.set_rayfile().set_axis_system(axis_system=[10, 10, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    assert p.scene_link.get().sources[0] != source1._source_instance

    source1.delete()


def test_reset_source(speos: Speos):
    """Test reset of source."""
    p = script.Project(speos=speos)

    # Create + commit
    source1 = p.create_source(name="Source.1")
    source1.set_rayfile().set_ray_file_uri(uri=os.path.join(test_path, "Rays.ray"))
    source1.commit()
    assert source1.source_template_link is not None
    assert source1.source_template_link.get().HasField("rayfile")
    assert len(p.scene_link.get().sources) == 1
    assert p.scene_link.get().sources[0].HasField("rayfile_properties")

    # Change local data (on template and on instance)
    source1.set_surface().set_exitance_constant(geometries=[(script.GeoRef.from_native_link("TheBodyB/TheFaceB1"), False)])
    assert source1.source_template_link.get().HasField("rayfile")
    assert source1._source_template.HasField("surface")  # local template
    assert p.scene_link.get().sources[0].HasField("rayfile_properties")
    assert source1._source_instance.HasField("surface_properties")  # local instance

    # Ask for reset
    source1.reset()
    assert source1.source_template_link.get().HasField("rayfile")
    assert source1._source_template.HasField("rayfile")  # local template
    assert p.scene_link.get().sources[0].HasField("rayfile_properties")
    assert source1._source_instance.HasField("rayfile_properties")  # local instance

    source1.delete()


def test_delete_source(speos: Speos):
    """Test delete of source."""
    p = script.Project(speos=speos)

    # Create + commit
    source1 = p.create_source(name="Source.1")
    source1.set_rayfile().set_ray_file_uri(uri=os.path.join(test_path, "Rays.ray"))
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
    p = script.Project(speos=speos)

    # TYPE
    # Create + commit : type Surface
    source1 = p.create_source(name="Source.1")
    source1.set_surface()
    source1.commit()

    # Retrieve print
    str_before = str(source1)

    # Modify the type as Luminaire : only in local (no commit)
    source1.set_luminaire()

    # Check that print is not modified
    str_after = str(source1)
    assert str_before == str_after
