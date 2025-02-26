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

"""
Test basic using project.
"""

import os
from pathlib import Path

from ansys.speos.core import Body, Face, Part, Project, Speos
from ansys.speos.core.opt_prop import OptProp
from ansys.speos.core.sensor import SensorIrradiance, SensorRadiance
from ansys.speos.core.simulation import SimulationDirect
from ansys.speos.core.source import SourceSurface
from tests.conftest import test_path


def test_find_feature(speos: Speos):
    """Test find a feature in project."""
    # Create an empty project
    p = Project(speos=speos)
    assert len(p._features) == 0

    # Create a surface source in the project
    source1 = p.create_source(name="Source.1")
    assert len(p._features) == 1
    source1.commit()
    assert len(p.scene_link.get().sources) == 1

    # Create an irradiance sensor in the project
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=SensorIrradiance)
    sensor1.commit()
    assert len(p._features) == 2
    assert len(p.scene_link.get().sensors) == 1

    # Create an radiance sensor in the project
    # TODO: enhance the initialize method
    sensor2 = p.create_sensor(name="Sensor.2", feature_type=SensorRadiance)
    sensor2.commit()
    assert len(p._features) == 3
    assert len(p.scene_link.get().sensors) == 2

    # Create an radiance sensor in the project
    sensor3 = p.create_sensor(name="Sensor.3", feature_type=SensorRadiance)
    sensor3.set_layer_type_face()
    sensor3.commit()
    assert len(p._features) == 4
    assert len(p.scene_link.get().sensors) == 3

    # Find from name only

    # Wrong name
    features = p.find(name="WrongName")
    assert features == []

    # Existing name
    features = p.find(name="Sensor.2")
    assert len(features) == 1
    assert features[0] == sensor2

    features = p.find(name="Source.1")
    assert len(features) == 1
    assert features[0] == source1

    # Using regex for name
    features = p.find(name=".*2", name_regex=True)
    assert len(features) == 1
    assert features[0] == sensor2

    features = p.find(name=".*8", name_regex=True)
    assert features == []

    # With type filtering

    # Wrong combination name-type
    features = p.find(name="Sensor.3", feature_type=SourceSurface)
    assert features == []

    # Good combination name-type
    features = p.find(name="Sensor.3", feature_type=SensorRadiance)
    assert len(features) == 1
    assert features[0] == sensor3

    # Wrong combination name-type specialized
    features = p.find(name="Sensor.3", feature_type=SensorIrradiance)
    assert features == []

    # Good combination name-type specialized
    features = p.find(name="Sensor.3", feature_type=SensorRadiance)
    assert len(features) == 1
    assert features[0] == sensor3

    # Good combination name-type specialized + regex
    features = p.find(name=r".*sor\.3", name_regex=True, feature_type=SensorRadiance)
    assert len(features) == 1
    assert features[0] == sensor3


def test_find_feature_geom(speos: Speos):
    """Test find a geometry feature in project loaded from speos file."""
    # Create a project from a file
    p = Project(
        speos=speos,
        path=str(
            Path(test_path) / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"
        ),
    )

    # Find root part
    feats = p.find(name="", feature_type=Part)
    assert len(feats) == 1

    # Retrieve body with regex
    feats = p.find(name="Solid Body in SOURCE2.*", name_regex=True, feature_type=Part)
    assert len(feats) == 1

    # Retrieve face
    feats = p.find(name="Solid Body in GUIDE:1379760262/Face in GUIDE:166", feature_type=Part)
    assert len(feats) == 1

    # Retrieve face with regex (regex at body and at face level)
    feats = p.find(name="Solid Body in GUIDE:.*/.*166", name_regex=True, feature_type=Part)
    assert len(feats) == 1

    # RootPart
    # |- Body.01
    # |  |- Face.011
    # |  |- Face.012
    # |- Body.02
    # |  |- Face.021
    # |  |- Face.022
    # |  |- Face.023
    # |- SubPart.1
    # |  |- Body.1
    # |  |  |- Face.11
    # |  |  |- Face.12
    # |  |- SubPart.11
    # |  |  |- Body.11
    # |  |  |  |- Face.111
    # |  |  |  |- Face.112
    # |- SubPart.2
    # |  |- Body.2
    # |  |  |- Face.21
    # |  |  |- Face.22
    # |  |  |- Face.23
    p2 = Project(speos=speos)
    root_part = p2.create_root_part()
    body_01 = root_part.create_body(name="Body.01")
    face_011 = body_01.create_face(name="Face.011")
    face_012 = body_01.create_face(name="Face.012")
    body_02 = root_part.create_body(name="Body.02")
    face_021 = body_01.create_face(name="Face.021")
    face_022 = body_01.create_face(name="Face.022")
    face_023 = body_01.create_face(name="Face.023")
    sub_part_1 = root_part.create_sub_part(name="SubPart.1")
    body_1 = sub_part_1.create_body(name="Body.1")
    face_11 = body_1.create_face(name="Face.11")
    face_12 = body_1.create_face(name="Face.12")
    sub_part_11 = sub_part_1.create_sub_part(name="SubPart.11")
    body_11 = sub_part_11.create_body(name="Body.11")
    face_111 = body_11.create_face(name="Face.111")
    face_112 = body_11.create_face(name="Face.112")
    sub_part_2 = root_part.create_sub_part(name="SubPart.2")
    body_2 = sub_part_2.create_body(name="Body.2")
    face_21 = body_2.create_face(name="Face.21")
    face_22 = body_2.create_face(name="Face.22")
    face_23 = body_2.create_face(name="Face.23")

    # Look at first level : 2 Bodies and 2 SubParts
    found_feats = p2.find(name=".*", name_regex=True, feature_type=Part)
    assert len(found_feats) == 4
    assert found_feats[2] == sub_part_1

    found_feats = p2.find(name=".*", name_regex=True, feature_type=Body)
    assert len(found_feats) == 2  # 2 Bodies
    assert found_feats[0] == body_01

    found_feats = p2.find(name=".*", name_regex=True, feature_type=Part.SubPart)
    assert len(found_feats) == 2  # 2 SubParts
    assert found_feats[1] == sub_part_2

    found_feats = p2.find(name=".*", name_regex=True, feature_type=Face)
    assert len(found_feats) == 0  # 0 Face

    # Look at second level : 5 Faces, 2 Bodies, 1 SubPart
    found_feats = p2.find(name=".*/.*", name_regex=True, feature_type=Part)
    assert len(found_feats) == 8
    assert found_feats[7] == body_2

    found_feats = p2.find(name=".*/.*", name_regex=True, feature_type=Face)
    assert len(found_feats) == 5  # 5 Faces
    assert found_feats[3] == face_022

    found_feats = p2.find(name=".*/.*", name_regex=True, feature_type=Body)
    assert len(found_feats) == 2  # 2 Bodies
    assert found_feats[0] == body_1

    found_feats = p2.find(name=".*/.*", name_regex=True, feature_type=Part.SubPart)
    assert len(found_feats) == 1  # 1 SubPart
    assert found_feats[0] == sub_part_11

    # Look at third level : 5 Faces, 1 Body
    found_feats = p2.find(name=".*/.*/.*", name_regex=True, feature_type=Part)
    assert len(found_feats) == 6
    assert found_feats[4] == face_22

    found_feats = p2.find(name=".*/.*/.*", name_regex=True, feature_type=Face)
    assert len(found_feats) == 5  # 5 Faces
    assert found_feats[2] == face_21

    found_feats = p2.find(name=".*/.*/.*", name_regex=True, feature_type=Body)
    assert len(found_feats) == 1  # 1 Body
    assert found_feats[0] == body_11

    # Look at fourth level : 2 Faces
    found_feats = p2.find(name=".*/.*/.*/.*", name_regex=True, feature_type=Part)
    assert len(found_feats) == 2
    assert found_feats[0] == face_111

    found_feats = p2.find(name=".*/.*/.*/.*", name_regex=True, feature_type=Face)
    assert len(found_feats) == 2
    assert found_feats[1] == face_112


def test_find_after_load(speos: Speos):
    """Test find feature in project loaded from speos file."""
    # Create a project from a file
    p = Project(
        speos=speos,
        path=str(
            Path(test_path) / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"
        ),
    )

    # Retrieve all surface sources
    src_feats = p.find(name=".*", name_regex=True, feature_type=SourceSurface)
    assert len(src_feats) == 2
    assert src_feats[0]._name == "Dom Source 2 (0) in SOURCE2"
    assert src_feats[1]._name == "Surface Source (0) in SOURCE1"

    # Retrieve all irradiance sensors
    ssr_feats = p.find(name=".*", name_regex=True, feature_type=SensorIrradiance)
    assert len(ssr_feats) == 1
    assert ssr_feats[0]._name == "Dom Irradiance Sensor (0)"

    # Retrieve all direct simulations
    sim_feats = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)
    assert len(sim_feats) == 1
    assert sim_feats[0]._name == "ASSEMBLY1.DS (0)"


def test_create_root_part_after_load(speos: Speos):
    """Test create_root_part feature in project loaded from speos file."""
    # Create a project from a file
    p = Project(
        speos=speos,
        path=str(
            Path(test_path) / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"
        ),
    )

    # Retrieve existing root part feature
    # assert p.find(name="", feature_type=Part) is p.create_root_part()
    rp = p.find(name="", feature_type=Part)[0]

    # Try to create root part (but it is already existing) -> the existing root part is returned
    rp2 = p.create_root_part()

    # Check object identity
    assert rp is rp2


def test_delete(speos: Speos):
    """Test delete a project."""
    # Create an empty project
    p = Project(speos=speos)
    assert len(p._features) == 0

    # Create a surface source in the project
    source1 = p.create_source(name="Source.1", feature_type=SourceSurface)
    assert len(p._features) == 1
    source1.commit()
    assert len(p.scene_link.get().sources) == 1

    # Create an irradiance sensor in the project
    sensor1 = p.create_sensor(name="Sensor.1", feature_type=SensorIrradiance)
    sensor1.commit()
    assert len(p._features) == 2
    assert len(p.scene_link.get().sensors) == 1

    # Delete project
    p.delete()
    assert len(p._features) == 0


def test_from_file(speos: Speos):
    """Test create a project from file."""
    # Create a project from a file
    p = Project(
        speos=speos,
        path=str(
            Path(test_path) / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"
        ),
    )

    # Check that scene is filled
    assert len(p.scene_link.get().materials) == 4
    assert len(p.scene_link.get().sensors) == 1
    assert len(p.scene_link.get().sources) == 2
    assert len(p.scene_link.get().simulations) == 1

    feat_sims = p.find(name=p.scene_link.get().simulations[0].name)
    assert len(feat_sims) == 1
    assert type(feat_sims[0]) is SimulationDirect

    # Check that feature can be retrieved
    feat_ops = p.find(name=p.scene_link.get().materials[2].name)
    assert len(feat_ops) == 1
    assert type(feat_ops[0]) is OptProp

    # And that the feature retrieved has a real impact on the project
    feat_ops[0].set_surface_mirror(reflectance=60).commit()
    assert speos.client[p.scene_link.get().materials[2].sop_guids[0]].get().HasField("mirror")
    assert speos.client[p.scene_link.get().materials[2].sop_guids[0]].get().mirror.reflectance == 60

    # Check that ambient mat has no sop
    feat_op_ambients = p.find(name=p.scene_link.get().materials[-1].name)
    assert len(feat_op_ambients) == 1
    assert feat_op_ambients[0].sop_template_link is None

    # Retrieve another feature
    feat_ssrs = p.find(name=p.scene_link.get().sensors[0].name)
    assert len(feat_ssrs) == 1
    assert type(feat_ssrs[0]) is SensorIrradiance

    # And that we can modify it (and that other values are not overridden by default values)
    feat_ssrs[0].set_type_colorimetric().set_wavelengths_range().set_end(value=800)
    feat_ssrs[0].commit()
    ssr_link = speos.client[p.scene_link.get().sensors[0].sensor_guid]
    ssr_data = ssr_link.get()
    assert ssr_data.HasField("irradiance_sensor_template")
    assert ssr_data.irradiance_sensor_template.HasField("sensor_type_colorimetric")
    assert (
        ssr_data.irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_end == 800
    )
    assert (
        ssr_data.irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling
        == 25
    )
    assert ssr_data.irradiance_sensor_template.dimensions.x_sampling == 500


def test_find_geom(speos: Speos):
    """Test find geometry feature in a project."""
    # Create a project from a file
    p = Project(
        speos=speos,
        path=str(
            Path(test_path) / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"
        ),
    )

    # Check that scene is filled
    assert p.scene_link.get().part_guid != ""

    # Check that RootPart feature can be retrieved
    part_data = speos.client[p.scene_link.get().part_guid].get()
    feat_rps = p.find(name="", feature_type=Part)
    assert len(feat_rps) == 1
    assert type(feat_rps[0]) is Part

    # Check that body can be retrieved
    assert len(part_data.body_guids) == 3
    body1_data = speos.client[part_data.body_guids[1]].get()
    feat_bodies = p.find(name=body1_data.name, feature_type=Part)
    assert len(feat_bodies) == 1
    assert type(feat_bodies[0]) is Body

    # Check that face can be retrieved
    assert len(body1_data.face_guids) > 4
    face2_data = speos.client[body1_data.face_guids[2]].get()
    feat_faces = p.find(name=body1_data.name + "/" + face2_data.name, feature_type=Part)
    assert len(feat_faces) == 1
    assert type(feat_faces[0]) is Face

    # Retrieve several features

    # All bodies
    all_bodies = p.find(name=".*", name_regex=True, feature_type=Part)
    assert len(all_bodies) == 3
    assert all_bodies[0]._name == "Solid Body in SOURCE2:2920204960"
    assert all_bodies[1]._name == "Solid Body in SOURCE1:2494956811"
    assert all_bodies[2]._name == "Solid Body in GUIDE:1379760262"

    # All faces of all bodies
    all_faces = p.find(name=".*/.*", name_regex=True, feature_type=Part)
    assert len(all_faces) == 23

    # All faces of specific body
    all_faces = p.find(name="Solid Body in GUIDE.*/.*", name_regex=True, feature_type=Part)
    assert len(all_faces) == 11
