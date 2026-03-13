# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
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

"""Test basic using component."""

from pathlib import Path

import pytest

from ansys.speos.core import Project, Speos
from ansys.speos.core.component import LightBox, LightBoxFileInstance
from ansys.speos.core.generic.parameters import ORIGIN
from ansys.speos.core.simulation import (
    SimulationDirect,
)
from tests.conftest import test_path


@pytest.mark.supported_speos_versions(min=261)
def test_create_lightbox(speos: Speos):
    """Test creation of LightBox."""
    p = Project(speos=speos)

    # Default value
    lightbox = p.create_lightbox_import(name="Light Box Import.1")
    lightbox.set_speos_light_box(
        lightbox=LightBoxFileInstance(
            file=Path(test_path) / "lightbox" / "Light Box Export.2.SPEOSLightBox",
        )
    )
    lightbox.commit()
    assert lightbox.name == "Light Box Import.1"
    assert lightbox.axis_system == ORIGIN
    assert lightbox._scene_instance.name == "Light Box Import.1"
    assert lightbox._scene_instance.axis_system == ORIGIN
    assert lightbox._scene_instance.scene_guid is not None
    assert p.client[lightbox._scene_instance.scene_guid].get().name == "Light Box Export.2"
    assert p.client[lightbox._scene_instance.scene_guid].get().part_guid is not None
    assert len(p.client[lightbox._scene_instance.scene_guid].get().sources) == 1
    assert len(p.client[lightbox._scene_instance.scene_guid].get().materials) == 1
    assert p.client[lightbox._scene_instance.scene_guid].get().sources[0].name == "Surface.2:1"
    assert lightbox.source_paths == [
        "{}/{}".format(
            lightbox.name, p.client[lightbox._scene_instance.scene_guid].get().sources[0].name
        )
    ]
    lightbox.delete()


@pytest.mark.supported_speos_versions(min=261)
def test_load_lightbox(speos: Speos):
    """Test load a simulation with lightbox inside."""
    p = Project(
        speos=speos,
        path=Path(test_path) / "lightbox" / "Direct.1.speos",
    )
    assert len(p.find(name=".*", name_regex=True, feature_type=LightBox)) != 0
    lightbox = p.find(name=".*", name_regex=True, feature_type=LightBox)[0]
    simulation = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
    assert lightbox.name == "3"
    assert lightbox.axis_system == [
        -40.99999999999999,
        -89.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ]
    assert lightbox.source_paths == ["3/Surface.1:258"]
    assert lightbox._scene_instance.name == "3"
    assert lightbox._scene_instance.axis_system == [
        -40.99999999999999,
        -89.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ]
    assert len(simulation._simulation_instance.source_paths) == 2
    assert simulation._simulation_instance.source_paths == [
        "3/Surface.1:258",
        "Light Box Import.2/Surface.2:1",
    ]

    new_lightbox = LightBoxFileInstance(
        file=Path(test_path) / "lightbox" / "Light Box Export.2.SPEOSLightBox",
    )
    lightbox.set_speos_light_box(new_lightbox)
    lightbox.commit()

    assert lightbox.name == "3"
    assert lightbox.axis_system == [
        -40.99999999999999,
        -89.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ]
    assert lightbox.source_paths == ["3/Surface.2:1"]
    assert lightbox._scene_instance.name == "3"
    assert lightbox._scene_instance.axis_system == [
        -40.99999999999999,
        -89.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ]
    assert len(simulation._simulation_instance.source_paths) == 1
    assert simulation._simulation_instance.source_paths == ["Light Box Import.2/Surface.2:1"]
