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
Test basic using intensity from script layer.
"""

import os

from ansys.speos.core.speos import Speos
import ansys.speos.script as script
from conftest import test_path


def test_create_intensity(speos: Speos):
    """Test creation of intensity."""

    # Default value
    intensity1 = script.Intensity(speos_client=speos.client, name="Intensity.1").commit()
    assert intensity1.intensity_template_link is not None
    assert intensity1.intensity_template_link.get().HasField("cos")
    assert intensity1.intensity_template_link.get().cos.N == 1
    assert intensity1.intensity_template_link.get().cos.total_angle == 180

    # library
    intensity1.set_library(
        intensity_file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies")
    ).set_library_properties().set_orientation_axis_system()
    intensity1.commit()
    assert intensity1.intensity_template_link.get().HasField("library")
    assert intensity1._intensity_properties.HasField("library_properties")
    assert intensity1._intensity_properties.library_properties.HasField("axis_system")
    assert intensity1._intensity_properties.library_properties.HasField("exit_geometries") == False

    intensity1.set_library_properties().set_orientation_normal_to_surface()
    intensity1.commit()
    assert intensity1._intensity_properties.HasField("library_properties")
    assert intensity1._intensity_properties.library_properties.HasField("normal_to_surface")

    intensity1.set_library_properties().set_orientation_normal_to_uv_map()
    intensity1.commit()
    assert intensity1._intensity_properties.HasField("library_properties")
    assert intensity1._intensity_properties.library_properties.HasField("normal_to_uv_map")

    intensity1.set_library_properties().set_exit_geometries([script.GeoRef.from_native_link(geopath="TheBodyB/TheFaceG")])
    intensity1.commit()
    assert intensity1._intensity_properties.HasField("library_properties")
    assert intensity1._intensity_properties.library_properties.HasField("exit_geometries")
    assert len(intensity1._intensity_properties.library_properties.exit_geometries.geo_paths) == 1
    assert intensity1._intensity_properties.library_properties.HasField("normal_to_uv_map")

    # cos
    intensity1.set_lambertian(total_angle=170).commit()
    assert intensity1.intensity_template_link.get().HasField("cos")
    assert intensity1.intensity_template_link.get().cos.N == 1
    assert intensity1.intensity_template_link.get().cos.total_angle == 170
    assert intensity1._intensity_properties.HasField("library_properties") == False

    intensity1.set_cos(N=2, total_angle=160).commit()
    assert intensity1.intensity_template_link.get().HasField("cos")
    assert intensity1.intensity_template_link.get().cos.N == 2
    assert intensity1.intensity_template_link.get().cos.total_angle == 160

    # gaussian
    intensity1.set_gaussian(FWHM_angle_x=20, FWHM_angle_y=30, total_angle=150)
    intensity1.commit()
    assert intensity1.intensity_template_link.get().HasField("gaussian")
    assert intensity1.intensity_template_link.get().gaussian.FWHM_angle_x == 20
    assert intensity1.intensity_template_link.get().gaussian.FWHM_angle_y == 30
    assert intensity1.intensity_template_link.get().gaussian.total_angle == 150
    assert intensity1._intensity_properties.HasField("gaussian_properties") == False

    intensity1.set_gaussian_properties()
    assert intensity1._intensity_properties.HasField("gaussian_properties")
    assert intensity1._intensity_properties.gaussian_properties.axis_system == []

    intensity1.set_gaussian_properties(axis_system=[10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    assert intensity1._intensity_properties.HasField("gaussian_properties")
    assert intensity1._intensity_properties.gaussian_properties.axis_system == [10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    intensity1.delete()


def test_commit_intensity(speos: Speos):
    """Test commit of intensity."""

    # Create
    intensity1 = script.Intensity(speos_client=speos.client, name="Intensity.1")
    intensity1.set_library(
        intensity_file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies")
    ).set_library_properties().set_orientation_axis_system()
    assert intensity1.intensity_template_link is None

    # Commit
    intensity1.commit()
    assert intensity1.intensity_template_link is not None
    assert intensity1.intensity_template_link.get().HasField("library")

    intensity1.delete()


def test_reset_intensity(speos: Speos):
    """Test reset of intensity."""

    # Create + commit
    intensity1 = script.Intensity(speos_client=speos.client, name="Intensity.1")
    intensity1.set_library(intensity_file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies")).commit()
    assert intensity1.intensity_template_link.get().HasField("library")

    # Change local data
    intensity1.set_cos()
    assert intensity1.intensity_template_link.get().HasField("library")
    assert intensity1._intensity_template.HasField("cos")

    # Ask for reset
    intensity1.reset()
    assert intensity1.intensity_template_link.get().HasField("library")
    assert intensity1._intensity_template.HasField("library")

    intensity1.delete()


def test_delete_intensity(speos: Speos):
    """Test delete of intensity."""

    # Create + commit
    intensity1 = script.Intensity(speos_client=speos.client, name="Intensity.1")
    intensity1.set_library(
        intensity_file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies")
    ).set_library_properties().set_orientation_axis_system()
    intensity1.commit()
    assert intensity1.intensity_template_link.get().HasField("library")
    assert intensity1._intensity_template.HasField("library")
    assert intensity1._intensity_properties.HasField("library_properties")

    # Delete
    intensity1.delete()
    assert intensity1.intensity_template_link is None
    assert intensity1._intensity_template.HasField("library")
    assert intensity1._intensity_properties.HasField("library_properties")
