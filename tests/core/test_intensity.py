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

"""Test basic using intensity."""

import os
from pathlib import Path

from ansys.speos.core import GeoRef, Intensity, Speos
from tests.conftest import test_path


def test_create_intensity(speos: Speos):
    """Test creation of intensity."""
    # Default value
    intensity1 = Intensity(speos_client=speos.client, name="Intensity.1").commit()
    assert intensity1.intensity_template_link is not None
    assert intensity1.intensity_template_link.get().HasField("cos")
    assert intensity1.intensity_template_link.get().cos.N == 1
    assert intensity1.intensity_template_link.get().cos.total_angle == 180

    # library
    intensity1.set_library().set_intensity_file_uri(
        uri=str(Path(test_path) / "IES_C_DETECTOR.ies")
    ).set_orientation_axis_system()
    intensity1.commit()
    assert intensity1.intensity_template_link.get().HasField("library")
    assert intensity1._intensity_properties.HasField("library_properties")
    assert intensity1._intensity_properties.library_properties.HasField("axis_system")
    assert intensity1._intensity_properties.library_properties.HasField("exit_geometries") == False

    intensity1.set_library().set_orientation_normal_to_surface()
    intensity1.commit()
    assert intensity1._intensity_properties.HasField("library_properties")
    assert intensity1._intensity_properties.library_properties.HasField("normal_to_surface")

    intensity1.set_library().set_orientation_normal_to_uv_map()
    intensity1.commit()
    assert intensity1._intensity_properties.HasField("library_properties")
    assert intensity1._intensity_properties.library_properties.HasField("normal_to_uv_map")

    intensity1.set_library().set_exit_geometries(
        [GeoRef.from_native_link(geopath="TheBodyB/TheFaceG")]
    )
    intensity1.commit()
    assert intensity1._intensity_properties.HasField("library_properties")
    assert intensity1._intensity_properties.library_properties.HasField("exit_geometries")
    assert len(intensity1._intensity_properties.library_properties.exit_geometries.geo_paths) == 1
    assert intensity1._intensity_properties.library_properties.HasField("normal_to_uv_map")

    intensity1.set_library().set_exit_geometries()  # use default [] to reset exit geometries
    intensity1.commit()
    assert intensity1._intensity_properties.library_properties.HasField("exit_geometries") == False

    # cos
    intensity1.set_cos(N=2, total_angle=160).commit()
    assert intensity1.intensity_template_link.get().HasField("cos")
    assert intensity1.intensity_template_link.get().cos.N == 2
    assert intensity1.intensity_template_link.get().cos.total_angle == 160
    assert intensity1._intensity_properties.HasField("library_properties") == False

    # gaussian
    intensity1.set_gaussian().set_FWHM_angle_x(value=20).set_FWHM_angle_y(value=30).set_total_angle(
        value=150
    )
    intensity1.commit()
    assert intensity1.intensity_template_link.get().HasField("gaussian")
    assert intensity1.intensity_template_link.get().gaussian.FWHM_angle_x == 20
    assert intensity1.intensity_template_link.get().gaussian.FWHM_angle_y == 30
    assert intensity1.intensity_template_link.get().gaussian.total_angle == 150
    assert intensity1._intensity_properties.HasField("gaussian_properties")

    intensity1.set_gaussian().set_axis_system(axis_system=[10, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    assert intensity1._intensity_properties.HasField("gaussian_properties")
    assert intensity1._intensity_properties.gaussian_properties.axis_system == [
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

    intensity1.set_gaussian().set_axis_system(
        axis_system=None
    )  # cancel chosen axis system for gaussian properties
    assert intensity1._intensity_properties.HasField("gaussian_properties")
    assert intensity1._intensity_properties.gaussian_properties.axis_system == []

    intensity1.delete()


def test_switch_intensity(speos: Speos):
    """Test switch of intensity : from one with properties to one without.

    Properties should be emptied.
    """
    # Use intensity library with some default properties
    intensity1 = Intensity(speos_client=speos.client, name="Intensity.1")
    intensity1.set_library().set_intensity_file_uri(uri=str(Path(test_path) / "IES_C_DETECTOR.ies"))
    intensity1.commit()
    assert intensity1._intensity_properties.HasField("properties")
    assert intensity1._intensity_properties.HasField("library_properties")
    assert intensity1._intensity_properties.library_properties.HasField("axis_system")

    # Switch to cos that has no properties
    intensity1.set_cos().commit()
    assert intensity1._intensity_properties.HasField("properties") == False


def test_commit_intensity(speos: Speos):
    """Test commit of intensity."""
    # Create
    intensity1 = Intensity(speos_client=speos.client, name="Intensity.1")
    intensity1.set_library().set_intensity_file_uri(
        uri=str(Path(test_path) / "IES_C_DETECTOR.ies")
    ).set_orientation_axis_system()
    assert intensity1.intensity_template_link is None

    # Commit
    intensity1.commit()
    assert intensity1.intensity_template_link is not None
    assert intensity1.intensity_template_link.get().HasField("library")

    intensity1.delete()


def test_reset_intensity(speos: Speos):
    """Test reset of intensity."""
    # Create + commit
    intensity1 = Intensity(speos_client=speos.client, name="Intensity.1")
    intensity1.set_library().set_intensity_file_uri(uri=str(Path(test_path) / "IES_C_DETECTOR.ies"))
    intensity1.commit()
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


def test_library_modify_after_reset(speos: Speos):
    """Test modify library intensity feature after reset."""
    # Create + commit
    intensity1 = Intensity(speos_client=speos.client, name="Intensity.1")
    intensity1.set_library().set_intensity_file_uri(uri=str(Path(test_path) / "IES_C_DETECTOR.ies"))
    intensity1.commit()

    # Ask for reset
    intensity1.reset()

    # Template modification
    intensity1.set_library().set_intensity_file_uri(
        uri=str(Path(test_path) / "PROJECT.Direct-no-Ray.Irradiance Ray Spectral.xmp")
    )
    assert intensity1._intensity_template.library.intensity_file_uri.endswith("xmp")

    # Properties modification
    intensity1.set_library().set_orientation_axis_system(
        axis_system=[50, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    )
    assert intensity1._intensity_properties.library_properties.axis_system.values == [
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

    intensity1.delete()


def test_gaussian_modify_after_reset(speos: Speos):
    """Test modify gaussian intensity feature after reset."""
    # Create + commit
    intensity1 = Intensity(speos_client=speos.client, name="Intensity.1").commit()
    intensity1.set_gaussian()
    intensity1.commit()

    # Ask for reset
    intensity1.reset()

    # Template modification
    intensity1.set_gaussian().set_FWHM_angle_y(value=40)
    assert intensity1._intensity_template.gaussian.FWHM_angle_y == 40

    # Properties modification
    intensity1.set_gaussian().set_axis_system(axis_system=[50, 20, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    assert intensity1._intensity_properties.gaussian_properties.axis_system == [
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


def test_delete_intensity(speos: Speos):
    """Test delete of intensity."""
    # Create + commit
    intensity1 = Intensity(speos_client=speos.client, name="Intensity.1")
    intensity1.set_library().set_intensity_file_uri(
        uri=str(Path(test_path) / "IES_C_DETECTOR.ies")
    ).set_orientation_axis_system()
    intensity1.commit()
    assert intensity1.intensity_template_link.get().HasField("library")
    assert intensity1._intensity_template.HasField("library")
    assert intensity1._intensity_properties.HasField("library_properties")

    # Delete
    intensity1.delete()
    assert intensity1.intensity_template_link is None
    assert intensity1._intensity_template.HasField("library")
    assert intensity1._intensity_properties.HasField("library_properties")
