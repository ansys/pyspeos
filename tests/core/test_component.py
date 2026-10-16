# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

import json
from pathlib import Path

import pytest

from ansys.speos.core import Project, Speos, part
from ansys.speos.core.component import LightBox, LightBoxFileInstance, Texture3D
from ansys.speos.core.generic.parameters import (
    ORIGIN,
    OptPropParameters,
    SopTypes,
    Texture3DPatternOperations,
    VopOpticParameters,
)
from ansys.speos.core.opt_prop import OptProp
from ansys.speos.core.sensor import SensorIrradiance
from ansys.speos.core.simulation import (
    SimulationDirect,
)
from ansys.speos.core.source import SourceRayFile, SourceSurface
from tests.conftest import test_path
from tests.helper import does_file_exist, remove_file


def _normalize_json_value(value):
    """Recursively normalize JSON values for order-insensitive comparison."""
    if isinstance(value, dict):
        return {key: _normalize_json_value(inner_value) for key, inner_value in value.items()}
    if isinstance(value, list):
        normalized_items = [_normalize_json_value(item) for item in value]
        return sorted(
            normalized_items,
            key=lambda item: json.dumps(item, sort_keys=True),
        )
    return value


@pytest.mark.supported_speos_versions(min=261)
def test_create_lightbox(speos: Speos):
    """Test creation of LightBox."""
    p = Project(speos=speos)

    # Default value
    ### Create Lightbox with given lightbox file path
    lightbox = p.create_lightbox(
        name="Light Box Import.1",
        lightbox=LightBoxFileInstance(
            file=Path(test_path) / "lightbox" / "Light Box Export.2.SPEOSLightBox",
        ),
    )
    assert lightbox.__str__().startswith("local") is True
    assert lightbox.axis_system == ORIGIN
    assert len(lightbox.project._features) == 3
    assert lightbox.trajectory_file_uri == ""
    lightbox_material = lightbox.find(name=".*", name_regex=True, feature_type=OptProp)
    assert len(lightbox_material) == 1
    assert lightbox_material[0].get(key="name") == "Material.2"
    assert lightbox_material[0].sop_mirror.reflectance == 100
    lightbox_source = lightbox.find(name=".*", name_regex=True, feature_type=SourceSurface)
    assert len(lightbox_source) == 1
    assert lightbox_source[0]._name == "Surface.2:1"
    lightbox_part = lightbox.find(name="", feature_type=part.Part)
    assert len(lightbox_part) == 1
    assert len(lightbox_part[0].bodies) == 1
    assert len(lightbox_part[0].bodies[0].faces) == 1
    assert lightbox_part[0].bodies[0].faces[0]._name == "face.1:3037138295"
    lightbox.trajectory_file_uri = Path(test_path) / "lightbox" / "Trajectory.json"

    lightbox.commit()
    assert lightbox.__str__().startswith("local") is False
    assert lightbox.trajectory_file_uri == str(Path(test_path) / "lightbox" / "Trajectory.json")
    lightbox.trajectory_file_uri = ""
    lightbox_material[0].sop_mirror.reflectance = 90
    lightbox_material[0].commit()
    lightbox_material = lightbox.find(name=".*", name_regex=True, feature_type=OptProp)[0]
    assert lightbox_material.sop_mirror.reflectance == 90
    assert lightbox.trajectory_file_uri == ""

    lightbox.create_optical_property(name="new material")
    lightbox_material = lightbox.find(name=".*", name_regex=True, feature_type=OptProp)
    assert len(lightbox_material) == 2

    lightbox.create_source(name="new rayfile", feature_type=SourceRayFile)
    lightbox_source = lightbox.find(name=".*", name_regex=True, feature_type=SourceRayFile)
    assert len(lightbox_source) == 1

    ### Create Lightbox without given lightbox file path

    lightbox_2 = p.create_lightbox(name="Light Box Import.2")
    assert lightbox_2.axis_system == ORIGIN
    assert len(lightbox_2.project._features) == 0
    lightbox_part = lightbox_2.find(name="", feature_type=part.Part)
    assert len(lightbox_part) == 0

    lightbox_2.create_optical_property(name="new material")
    lightbox_material = lightbox_2.find(name=".*", name_regex=True, feature_type=OptProp)
    assert len(lightbox_material) == 1
    lightbox_2.create_source(name="new rayfile", feature_type=SourceRayFile)
    lightbox_source = lightbox_2.find(name=".*", name_regex=True, feature_type=SourceRayFile)
    assert len(lightbox_source) == 1
    lightbox_2.create_root_part()
    lightbox_part = lightbox_2.find(name="", feature_type=part.Part)
    assert len(lightbox_part) == 1

    # lightbox = p.create_lightbox(name="Light Box Import.3")
    # lightbox.set_speos_light_box(
    #     lightbox=LightBoxFileInstance(
    #         file=Path(test_path) / "lightbox" / "Light Box Export.2.SPEOSLightBox",
    #     )
    # )
    # lightbox.commit()
    # assert len(lightbox._features) == 3
    #
    # lightbox_material = lightbox.find(name=".*", name_regex=True, feature_type=OptProp)[0]
    # assert lightbox_material.get(key="name") == "Material.2"
    # assert lightbox_material.sop_mirror.reflectance == 100
    #
    # lightbox_source = lightbox.find(name=".*", name_regex=True, feature_type=SourceSurface)[0]
    # assert lightbox_source._name == "Surface.2:1"
    #
    # lightbox_part = lightbox.find(name="", feature_type=part.Part)[0]
    # assert len(lightbox_part.bodies) == 1
    # assert len(lightbox_part.bodies[0].faces) == 1
    # assert lightbox_part.bodies[0].faces[0]._name == "face.1:3037138295"

    with pytest.raises(
        ValueError,
        match="Lightbox: Light Box Import.1 has a conflict name with an existing feature.",
    ):
        p.create_lightbox(name="Light Box Import.1")

    assert isinstance(lightbox.visual_data, list)
    assert all([type(data).__name__ == "_VisualData" for data in lightbox.visual_data])

    out_dict = lightbox._to_dict()
    assert out_dict["name"] == "Light Box Import.1"
    assert out_dict["scene"]["sources"][0]["name"] == "Surface.2:1"
    assert lightbox.get("name") == "Light Box Import.1"

    # string comparison
    lb_str1 = str(lightbox)
    lb_str2 = lightbox.__str__()

    # Compare the parsed JSON content after normalizing list order so that
    # semantically equivalent payloads do not fail when list items are reordered.
    normalized_lb_1 = _normalize_json_value(json.loads(lb_str1))
    normalized_lb_2 = _normalize_json_value(json.loads(lb_str2))
    assert normalized_lb_1 == normalized_lb_2
    lightbox3 = p.create_lightbox(
        name="Light Box Import.3",
        lightbox=LightBoxFileInstance(
            file=Path(test_path) / "lightbox" / "WhiteLightBox.SPEOSLightBox",
            axis_system=[100, 50, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        ),
    )
    lightbox3.commit()
    assert lightbox3.name == "Light Box Import.3"
    assert lightbox3.axis_system == [100, 50, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert lightbox3._scene_instance.name == "Light Box Import.3"
    assert lightbox3._scene_instance.axis_system == [100, 50, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert lightbox3._scene_instance.scene_guid is not None
    assert p.client[lightbox3._scene_instance.scene_guid].get().name == "WhiteLightBox"
    assert len(p.client[lightbox3._scene_instance.scene_guid].get().sources) == 2
    assert len(p.client[lightbox3._scene_instance.scene_guid].get().materials) == 1

    assert len(lightbox3.project._features) == 4

    lightbox_material = lightbox3.find(name=".*", name_regex=True, feature_type=OptProp)[0]
    assert lightbox_material.get(key="name") == "Material.1"
    assert lightbox_material.vop_optic.index == 1.5
    assert lightbox_material.vop_optic.absorption == 0

    lightbox_source = lightbox3.find(name=".*", name_regex=True, feature_type=SourceSurface)[0]
    assert lightbox_source._name == "Surface.1:370"
    lightbox_source = lightbox3.find(name=".*", name_regex=True, feature_type=SourceRayFile)[0]
    assert lightbox_source._name == "Ray-file.1:399"

    lightbox_part = lightbox3.find(name="", feature_type=part.Part)[0]
    assert len(lightbox_part.bodies) == 2
    assert len(lightbox_part.bodies[0].faces) == 6
    assert len(lightbox_part.bodies[1].faces) == 7

    ## Add features from lightbox to simulation
    sensor = p.create_sensor(name="sensor_helper", feature_type=SensorIrradiance)
    sim = p.create_simulation(name="sim_helper", feature_type=SimulationDirect)
    sim.sensor_paths = [sensor]
    sim.source_paths = lightbox3.source_paths
    sim.commit()
    assert len(sim.source_paths) == 2
    lightbox_source = lightbox3.find(name=".*", name_regex=True, feature_type=SourceSurface)[0]
    sim.source_paths = [lightbox_source]
    sim.commit()
    assert len(sim.source_paths) == 1

    lightbox.delete()


def test_compare_json_strings_ignoring_list_order():
    """Test JSON string comparison when list order is not stable."""
    lb_str1 = '{"test": ["test1", "test2"]}'
    lb_str2 = '{"test": ["test2", "test1"]}'

    assert lb_str1 != lb_str2
    assert _normalize_json_value(json.loads(lb_str1)) == _normalize_json_value(json.loads(lb_str2))


@pytest.mark.supported_speos_versions(min=261)
def test_create_balck_lightbox(speos: Speos):
    """Test load a simulation with lightbox inside."""
    p = Project(speos=speos)

    # Default value
    ### Create Lightbox with given lightbox file path
    lightbox = p.create_lightbox(
        name="Light Box Import.1",
        lightbox=LightBoxFileInstance(
            file=Path(test_path) / "lightbox" / "BlackLightBox.SPEOSLightBox",
        ),
    )
    assert lightbox.axis_system == ORIGIN
    assert len(lightbox.project._features) == 0
    assert len(lightbox.source_paths) == 0


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
    # new_lightbox = LightBoxFileInstance(
    #     file=Path(test_path) / "lightbox" / "Light Box Export.2.SPEOSLightBox",
    # )
    # lightbox_1.set_speos_light_box(new_lightbox)
    # lightbox_1.commit()
    #
    # assert lightbox_1.name == "3"
    # assert lightbox_1.axis_system == [
    #     -40.99999999999999,
    #     -89.0,
    #     0.0,
    #     1.0,
    #     0.0,
    #     0.0,
    #     0.0,
    #     1.0,
    #     0.0,
    #     0.0,
    #     0.0,
    #     1.0,
    # ]
    # assert lightbox_1.source_paths == ["3/Surface.2:1"]
    # assert lightbox_1._scene_instance.name == "3"
    # assert lightbox_1._scene_instance.axis_system == [
    #     -40.99999999999999,
    #     -89.0,
    #     0.0,
    #     1.0,
    #     0.0,
    #     0.0,
    #     0.0,
    #     1.0,
    #     0.0,
    #     0.0,
    #     0.0,
    #     1.0,
    # ]
    # assert len(simulation._simulation_instance.source_paths) == 2
    # assert simulation._simulation_instance.source_paths == [
    #     "Light Box Import.2/Surface.2:1",
    #     "Light Box Import.2/Ray-file.1:12",
    # ]
    #
    # # modify the lightbox which will keep the source paths if still in new lightbox
    # simulation.source_paths = [
    #     "Light Box Import.2/Surface.2:1",
    #     "Light Box Import.2/Ray-file.1:12",
    #     "3/Surface.2:1",
    # ]
    # simulation.commit()
    # assert len(simulation._simulation_instance.source_paths) == 3
    # lightbox_2.set_speos_light_box(new_lightbox)
    # lightbox_2.commit()
    # assert len(simulation._simulation_instance.source_paths) == 2
    # assert simulation._simulation_instance.source_paths == [
    #     "Light Box Import.2/Surface.2:1",
    #     "3/Surface.2:1",
    # ]


@pytest.mark.supported_speos_versions(min=261)
def test_reset_lightbox(speos: Speos):
    """Test reset a lightbox."""
    p = Project(
        speos=speos,
        path=Path(test_path) / "lightbox" / "Direct.1.speos",
    )
    lightbox_1 = p.find(name=".*", name_regex=True, feature_type=LightBox)[0]
    lightbox_1.axis_system = [100, 50, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert lightbox_1.axis_system == [100, 50, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
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


@pytest.mark.supported_speos_versions(min=261)
def test_export_lightbox(speos: Speos):
    """Test reset a lightbox."""
    # test lightbox from a loaded speos file can be exported as white or black lightbox.
    p = Project(
        speos=speos,
        path=Path(test_path) / "lightbox" / "Direct.1.speos",
    )
    lightbox_1 = p.find(name=".*", name_regex=True, feature_type=LightBox)[0]
    exported_file_1 = lightbox_1.export(export_path=Path(test_path) / "export_test.SPEOSLightBox")
    exported_file_2 = lightbox_1.export(
        export_path=Path(test_path) / "export_test_blackbox.SPEOSLightBox", black_boxed=True
    )
    assert does_file_exist(str(exported_file_1))
    assert does_file_exist(str(exported_file_2))
    remove_file(str(exported_file_1))
    remove_file(str(exported_file_2))

    # test imported lightbox feature can be exported
    lightbox_2 = p.create_lightbox(
        name="New Import",
        lightbox=LightBoxFileInstance(
            file=Path(test_path) / "lightbox" / "Light Box Export.2.SPEOSLightBox",
        ),
    )
    exported_file_3 = lightbox_2.export(export_path=Path(test_path) / "export_test_2.SPEOSLightBox")
    assert does_file_exist(str(exported_file_3))
    remove_file(str(exported_file_3))

    # test black lightbox / empty lightbox cannot be exported
    lightbox_3 = p.create_lightbox(
        name="Black Import",
        lightbox=LightBoxFileInstance(
            file=Path(test_path) / "lightbox" / "BlackLightBox.SPEOSLightBox",
        ),
    )
    with pytest.raises(
        ValueError,
        match="LightBox file cannot be saved due to is a black lightbox or no features inside.",
    ):
        lightbox_3.export(export_path=Path(test_path) / "export_test_3.SPEOSLightBox")

    # test new feature cannot be added in black lightbox
    with pytest.raises(
        ValueError,
        match="A black lightbox does not allow creating features.",
    ):
        lightbox_3.create_source(name="Black LightBox Source", feature_type=SourceRayFile)


@pytest.mark.supported_speos_versions(min=261)
def test_delete_lightbox(speos: Speos):
    """Test delete a lightbox."""
    p = Project(speos=speos)
    lightbox_1 = p.create_lightbox(
        name="Light Box Import.1",
        lightbox=LightBoxFileInstance(
            file=Path(test_path) / "lightbox" / "Light Box Export.2.SPEOSLightBox",
        ),
    )
    assert lightbox_1.project.scene_link is not None
    assert len(lightbox_1.project._features) == 3

    # Delete
    lightbox_1.delete()
    assert len(p.scene_link.get().scenes) == 0
    assert len(lightbox_1.project._features) == 0
    assert lightbox_1.project.scene_link is None

    lightbox = p.find(name=".*", name_regex=True, feature_type=LightBox)
    assert len(lightbox) == 0


def _create_geometry(p: Project):
    """Create a root part with a volume support body and a volume pattern body."""
    root_part = p.create_root_part()
    support_body = root_part.create_body(name="SupportBody")
    support_body_face_1 = support_body.create_face(name="button")
    support_body_face_1.vertices = [0, 0, 0, 10, 0, 0, 10, 10, 0, 0, 10, 0]
    support_body_face_1.facets = [0, 1, 2, 0, 2, 3]
    support_body_face_1.normals = [0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1]
    support_body_face_2 = support_body.create_face(name="top")
    support_body_face_2.vertices = [0, 0, 10, 10, 0, 10, 10, 10, 10, 0, 10, 10]
    support_body_face_2.facets = [0, 1, 2, 0, 2, 3]
    support_body_face_2.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1]
    support_body_face_3 = support_body.create_face(name="left")
    support_body_face_3.vertices = [0, 0, 0, 10, 0, 0, 10, 0, 10, 0, 0, 10]
    support_body_face_3.facets = [0, 1, 2, 0, 2, 3]
    support_body_face_3.normals = [0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0]
    support_body_face_4 = support_body.create_face(name="right")
    support_body_face_4.vertices = [0, 10, 0, 10, 10, 0, 10, 10, 10, 0, 10, 10]
    support_body_face_4.facets = [0, 1, 2, 0, 2, 3]
    support_body_face_4.normals = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0]
    support_body_face_5 = support_body.create_face(name="front")
    support_body_face_5.vertices = [10, 0, 0, 10, 10, 0, 10, 10, 10, 10, 0, 10]
    support_body_face_5.facets = [0, 1, 2, 0, 2, 3]
    support_body_face_5.normals = [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0]
    support_body_face_6 = support_body.create_face(name="back")
    support_body_face_6.vertices = [0, 0, 0, 0, 10, 0, 0, 10, 10, 0, 0, 10]
    support_body_face_6.facets = [0, 1, 2, 0, 2, 3]
    support_body_face_6.normals = [-1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0]
    support_body.commit()

    pattern_body = root_part.create_body(name="PatternBody")
    pattern_body_face_1 = pattern_body.create_face(name="button")
    pattern_body_face_1.vertices = [0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0]
    pattern_body_face_1.facets = [0, 1, 2, 0, 2, 3]
    pattern_body_face_1.normals = [0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1]
    pattern_body_face_2 = pattern_body.create_face(name="top")
    pattern_body_face_2.vertices = [0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1]
    pattern_body_face_2.facets = [0, 1, 2, 0, 2, 3]
    pattern_body_face_2.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1]
    pattern_body_face_3 = pattern_body.create_face(name="left")
    pattern_body_face_3.vertices = [0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1]
    pattern_body_face_3.facets = [0, 1, 2, 0, 2, 3]
    pattern_body_face_3.normals = [0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0]
    pattern_body_face_4 = pattern_body.create_face(name="right")
    pattern_body_face_4.vertices = [0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1]
    pattern_body_face_4.facets = [0, 1, 2, 0, 2, 3]
    pattern_body_face_4.normals = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0]
    pattern_body_face_5 = pattern_body.create_face(name="front")
    pattern_body_face_5.vertices = [1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1]
    pattern_body_face_5.facets = [0, 1, 2, 0, 2, 3]
    pattern_body_face_5.normals = [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0]
    pattern_body_face_6 = pattern_body.create_face(name="back")
    pattern_body_face_6.vertices = [0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1]
    pattern_body_face_6.facets = [0, 1, 2, 0, 2, 3]
    pattern_body_face_6.normals = [-1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0]
    pattern_body.commit()
    root_part.commit()
    return support_body, pattern_body


@pytest.mark.supported_speos_versions(min=271)
def test_create_3d_texture(speos: Speos):
    """Test creation of a 3D texture with default values."""
    p = Project(speos=speos)
    support_body, pattern_body = _create_geometry(p)
    opt_prop = p.create_optical_property(
        name="OptProp.1",
        parameters=OptPropParameters(
            vop_parameters=VopOpticParameters(index=1.5, absorption=0.0),
            sop_parameters=SopTypes.optical_polished,
        ),
    )
    opt_prop.geometries = [support_body]
    opt_prop.commit()

    texture = p.create_3d_texture(name="Texture3D.1")
    assert isinstance(texture, Texture3D)
    assert texture.name == "Texture3D.1"
    assert texture.axis_system == ORIGIN
    assert texture.support_body == ""
    assert texture.pattern_body == ""
    assert texture.pattern_operation == Texture3DPatternOperations.add_on_same_material
    assert texture.global_scale == 1.0
    assert texture.mapping_3d_file_uri == ""
    assert texture.pattern_materials == []
    assert texture.__str__().startswith("local") is True

    # The feature is registered in the project
    assert len(p.find(name="Texture3D.1", feature_type=Texture3D)) == 1

    # Fill the 3D texture and commit it
    texture.axis_system = [10, 20, 30, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    texture.support_body = support_body
    texture.pattern_body = pattern_body
    texture.pattern_operation = Texture3DPatternOperations.add_in
    texture.global_scale = 2.5
    texture.mapping_3d_file_uri = (
        Path(test_path) / "texture3d" / "Component1.3D Texture.1.OPT3DMapping"
    )
    texture_opt = texture.create_pattern_material(
        name="PatternMaterial",
        parameters=OptPropParameters(
            vop_parameters=VopOpticParameters(index=1.5, absorption=0.0),
            sop_parameters=SopTypes.optical_polished,
        ),
    )
    texture_opt.geometries = [pattern_body]
    texture_opt.commit()
    texture.commit()

    assert texture.__str__().startswith("local") is False

    textures_3d = p.scene_link.get().textures_3d
    assert len(textures_3d) == 1
    assert textures_3d[0].axis_system == [10, 20, 30, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    assert textures_3d[0].support_body_geo_path == "SupportBody"
    assert textures_3d[0].pattern.body_guid == pattern_body.body_link.key
    assert textures_3d[0].pattern_operation == Texture3DPatternOperations.add_in.value
    assert textures_3d[0].global_scale == 2.5
    assert textures_3d[0].mapping_3d_file_uri == str(
        Path(test_path) / "texture3d" / "Component1.3D Texture.1.OPT3DMapping"
    )

    # Read only access
    assert texture.get(key="support_body_geo_path") == "SupportBody"
    assert texture.get()["global_scale"] == 2.5
