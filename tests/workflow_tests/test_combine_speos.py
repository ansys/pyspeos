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
Test using combine_speos module in workflow layer
"""

import os

from ansys.speos.core.speos import Speos
import ansys.speos.script as script
from ansys.speos.workflow.combine_speos import LocatedSpeos, combine_speos, insert_speos
from conftest import test_path


def test_combine_speos(speos: Speos):
    """Test combining several speos files."""
    # Combine several speos files into a new project - only geometries + materials are retrieved
    p = combine_speos(
        speos=speos,
        speos_to_combine=[
            LocatedSpeos(
                speos_file=os.path.join(test_path, "Env_Simplified.speos", "Env_Simplified.speos"),
                axis_system=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            ),
            LocatedSpeos(
                speos_file=os.path.join(test_path, "BlueCar.speos", "BlueCar.speos"),
                axis_system=[2000, 0, 35000, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            ),
            LocatedSpeos(
                speos_file=os.path.join(test_path, "RedCar.speos", "RedCar.speos"),
                axis_system=[-4000, 0, 48000, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0],
            ),
        ],
    )

    # Check that scene is filled
    assert len(p.scene_link.get().materials) == 8
    assert len(p.scene_link.get().sensors) == 0
    assert len(p.scene_link.get().sources) == 0
    assert len(p.scene_link.get().simulations) == 0

    # Check that the root part contains one part per speos to combine
    root_part = p.find(name="RootPart")
    assert type(root_part) == script.Part
    rp_data = root_part.part_link.get()
    assert len(rp_data.parts) == 3

    # Check that materials geo_paths are well updated by using subparts
    mat_es1 = p.find(name="Env_Simplified.Material.1")
    assert type(mat_es1) == script.OptProp
    assert len(mat_es1._material_instance.geometries.geo_paths) > 0
    assert mat_es1._material_instance.geometries.geo_paths[0].startswith("Env_Simplified/")

    mat_bc1 = p.find(name="BlueCar.Material.1")
    assert type(mat_bc1) == script.OptProp
    assert len(mat_bc1._material_instance.geometries.geo_paths) > 0
    assert mat_bc1._material_instance.geometries.geo_paths[0].startswith("BlueCar/")

    mat_rc1 = p.find(name="RedCar.Material.1")
    assert type(mat_rc1) == script.OptProp
    assert len(mat_rc1._material_instance.geometries.geo_paths) > 0
    assert mat_rc1._material_instance.geometries.geo_paths[0].startswith("RedCar/")


def test_insert_speos(speos: Speos):
    """Test inserting several speos files in an existing project."""
    # Create a project from a speos file
    p = script.Project(speos=speos, path=os.path.join(test_path, "Env_Simplified.speos", "Env_Simplified.speos"))

    # Check that scene is filled
    assert len(p.scene_link.get().materials) == 4
    assert len(p.scene_link.get().sensors) == 1
    assert len(p.scene_link.get().sources) == 0
    assert len(p.scene_link.get().simulations) == 1

    # Insert several speos files into the project - only geometries + materials are retrieved
    insert_speos(
        project=p,
        speos_to_insert=[
            LocatedSpeos(
                speos_file=os.path.join(test_path, "BlueCar.speos", "BlueCar.speos"),
                axis_system=[2000, 0, 35000, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            ),
            LocatedSpeos(
                speos_file=os.path.join(test_path, "RedCar.speos", "RedCar.speos"),
                axis_system=[-4000, 0, 48000, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0],
            ),
        ],
    )

    assert len(p.scene_link.get().materials) == 9  # 8 + 1 (ambient material)
    assert len(p.scene_link.get().sensors) == 1
    assert len(p.scene_link.get().sources) == 0
    assert len(p.scene_link.get().simulations) == 1

    # Check that the root part contains one part per speos to insert
    root_part = p.find(name="RootPart")
    assert type(root_part) == script.Part
    rp_data = root_part.part_link.get()
    assert len(rp_data.parts) == 2

    # Check that materials geo_paths are well updated by using subparts
    mat_bc1 = p.find(name="BlueCar.Material.1")
    assert type(mat_bc1) == script.OptProp
    assert len(mat_bc1._material_instance.geometries.geo_paths) > 0
    assert mat_bc1._material_instance.geometries.geo_paths[0].startswith("BlueCar/")

    mat_rc1 = p.find(name="RedCar.Material.1")
    assert type(mat_rc1) == script.OptProp
    assert len(mat_rc1._material_instance.geometries.geo_paths) > 0
    assert mat_rc1._material_instance.geometries.geo_paths[0].startswith("RedCar/")
