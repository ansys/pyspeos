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

from ansys.speos.core import Project, Speos, part
from ansys.speos.core.component import LightBox, LightBoxFile
from ansys.speos.core.generic.parameters import ORIGIN
from ansys.speos.core.opt_prop import OptProp
from ansys.speos.core.simulation import (
    SimulationDirect,
)
from ansys.speos.core.source import SourceRayFile, SourceSurface
from tests.conftest import test_path


@pytest.mark.supported_speos_versions(min=261)
def test_create_lightbox(speos: Speos):
    """Test creation of LightBox."""
    p = Project(speos=speos)

    # Default value
    lightbox = p.create_lightbox_import(name="Light Box Import.1")
    lightbox.set_speos_light_box(
        lightbox=LightBoxFile(
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

    assert len(lightbox._features) == 3

    lightbox_material = lightbox.find(name=".*", name_regex=True, feature_type=OptProp)[0]
    assert lightbox_material.get(key="name") == "Material.2"
    assert lightbox_material.sop_mirror.reflectance == 100

    lightbox_source = lightbox.find(name=".*", name_regex=True, feature_type=SourceSurface)[0]
    assert lightbox_source._name == "Surface.2:1"

    lightbox_part = lightbox.find(name="", feature_type=part.Part)[0]
    assert len(lightbox_part.bodies) == 1
    assert len(lightbox_part.bodies[0].faces) == 1
    assert lightbox_part.bodies[0].faces[0]._name == "face.1:3037138295"

    with pytest.raises(
        ValueError,
        match="Lightbox: Light Box Import.1 has a conflict name with an existing feature.",
    ):
        p.create_lightbox_import(name="Light Box Import.1")

    with pytest.raises(
        TypeError,
        match="Incorrect parameter dataclass provided <class 'str'> instead of LightBoxParameters",
    ):
        p.create_lightbox_import(name="Light Box Import.2", parameters="test")

    assert isinstance(lightbox.visual_data, list)
    assert all([type(data).__name__ == "_VisualData" for data in lightbox.visual_data])

    out_dict = lightbox._to_dict()
    assert out_dict["name"] == "Light Box Import.1"
    assert out_dict["scene"]["sources"][0]["name"] == "Surface.2:1"
    assert lightbox.get("name") == "Light Box Import.1"

    assert str(lightbox) == lightbox.__str__()

    lightbox.set_speos_light_box(
        lightbox=LightBoxFile(
            file=Path(test_path) / "lightbox" / "WhiteLightBox.SPEOSLightBox",
        )
    )
    assert lightbox.name == "Light Box Import.1"
    assert lightbox.axis_system == ORIGIN
    assert lightbox._scene_instance.name == "Light Box Import.1"
    assert lightbox._scene_instance.axis_system == ORIGIN
    assert lightbox._scene_instance.scene_guid is not None
    assert p.client[lightbox._scene_instance.scene_guid].get().name == "WhiteLightBox"
    assert len(p.client[lightbox._scene_instance.scene_guid].get().sources) == 2
    assert len(p.client[lightbox._scene_instance.scene_guid].get().materials) == 1

    assert len(lightbox._features) == 4

    lightbox_material = lightbox.find(name=".*", name_regex=True, feature_type=OptProp)[0]
    assert lightbox_material.get(key="name") == "Material.1"
    assert lightbox_material.vop_optic.index == 1.5
    assert lightbox_material.vop_optic.absorption == 0

    lightbox_source = lightbox.find(name=".*", name_regex=True, feature_type=SourceSurface)[0]
    assert lightbox_source._name == "Surface.1:370"
    lightbox_source = lightbox.find(name=".*", name_regex=True, feature_type=SourceRayFile)[0]
    assert lightbox_source._name == "Ray-file.1:399"

    lightbox_part = lightbox.find(name="", feature_type=part.Part)[0]
    assert len(lightbox_part.bodies) == 2
    assert len(lightbox_part.bodies[0].faces) == 6
    assert len(lightbox_part.bodies[1].faces) == 7

    lightbox.delete()


@pytest.mark.supported_speos_versions(min=261)
def test_load_lightbox(speos: Speos):
    """Test load a simulation with lightbox inside."""
    p = Project(
        speos=speos,
        path=Path(test_path) / "lightbox" / "Direct.1.speos",
    )
    assert len(p.find(name=".*", name_regex=True, feature_type=LightBox)) == 2
    lightbox_1 = p.find(name=".*", name_regex=True, feature_type=LightBox)[0]
    lightbox_2 = p.find(name=".*", name_regex=True, feature_type=LightBox)[1]
    simulation = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
    assert lightbox_1.name == "3"
    assert lightbox_2.name == "Light Box Import.2"
    assert lightbox_1.name == lightbox_1.get(key="name")
    assert lightbox_2.name == lightbox_2.get(key="name")
    assert lightbox_1.axis_system == [
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
    assert lightbox_2.axis_system == [
        -40.99999999999999,
        -167.53,
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
    assert lightbox_1.source_paths == ["3/Surface.1:258"]
    lightbox_source = lightbox_1.find(name=".*", name_regex=True, feature_type=SourceSurface)[0]
    assert lightbox_source._name == "Surface.1:258"
    assert lightbox_2.source_paths == [
        "Light Box Import.2/Surface.2:1",
        "Light Box Import.2/Ray-file.1:12",
    ]
    lightbox_source = lightbox_2.find(name=".*", name_regex=True, feature_type=SourceSurface)[0]
    assert lightbox_source._name == "Surface.2:1"
    lightbox_source = lightbox_2.find(name=".*", name_regex=True, feature_type=SourceRayFile)[0]
    assert lightbox_source._name == "Ray-file.1:12"
    assert lightbox_1._scene_instance.name == "3"
    assert lightbox_1._scene_instance.axis_system == [
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
    assert len(simulation._simulation_instance.source_paths) == 3
    assert simulation._simulation_instance.source_paths == [
        "3/Surface.1:258",
        "Light Box Import.2/Surface.2:1",
        "Light Box Import.2/Ray-file.1:12",
    ]

    # modify the lightbox which will remove the old source path
    new_lightbox = LightBoxFile(
        file=Path(test_path) / "lightbox" / "Light Box Export.2.SPEOSLightBox",
    )
    lightbox_1.set_speos_light_box(new_lightbox)
    lightbox_1.commit()

    assert lightbox_1.name == "3"
    assert lightbox_1.axis_system == [
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
    assert lightbox_1.source_paths == ["3/Surface.2:1"]
    assert lightbox_1._scene_instance.name == "3"
    assert lightbox_1._scene_instance.axis_system == [
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
        "Light Box Import.2/Surface.2:1",
        "Light Box Import.2/Ray-file.1:12",
    ]

    # modify the lightbox which will keep the source paths if still in new lightbox
    simulation.source_paths = [
        "Light Box Import.2/Surface.2:1",
        "Light Box Import.2/Ray-file.1:12",
        "3/Surface.2:1",
    ]
    simulation.commit()
    assert len(simulation._simulation_instance.source_paths) == 3
    lightbox_2.set_speos_light_box(new_lightbox)
    lightbox_2.commit()
    assert len(simulation._simulation_instance.source_paths) == 2
    assert simulation._simulation_instance.source_paths == [
        "Light Box Import.2/Surface.2:1",
        "3/Surface.2:1",
    ]


def test_reset_lightbox(speos: Speos):
    """Test reset a lightbox."""
    p = Project(
        speos=speos,
        path=Path(test_path) / "lightbox" / "Direct.1.speos",
    )
    lightbox_1 = p.find(name=".*", name_regex=True, feature_type=LightBox)[0]
    lightbox_1.axis_system = ORIGIN
    lightbox_1.__str__().startswith("local")
    assert lightbox_1.axis_system == ORIGIN
    lightbox_1.reset()
    assert lightbox_1.axis_system == [
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
