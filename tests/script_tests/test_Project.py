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
Test basic using project from script layer.
"""
import os

from ansys.speos.core.speos import Speos
import ansys.speos.script as script
from conftest import test_path


def test_find_feature(speos: Speos):
    """Test find a feature in project."""

    # Create an empty project
    p = script.Project(speos=speos)
    assert len(p._features) == 0

    # Create a surface source in the project
    source1 = p.create_source(name="Source.1")
    source1.set_surface()
    assert len(p._features) == 1
    source1.commit()
    assert len(p.scene_link.get().sources) == 1

    # Create an irradiance sensor in the project
    sensor1 = p.create_sensor(name="Sensor.1")
    sensor1.set_irradiance()
    sensor1.commit()
    assert len(p._features) == 2
    assert len(p.scene_link.get().sensors) == 1

    # Create an radiance sensor in the project
    sensor2 = p.create_sensor(name="Sensor.2")
    sensor2.set_radiance()
    sensor2.commit()
    assert len(p._features) == 3
    assert len(p.scene_link.get().sensors) == 2

    # Create an radiance sensor in the project
    sensor3 = p.create_sensor(name="Sensor.3")
    sensor3.set_radiance().set_layer_type_face()
    sensor3.commit()
    assert len(p._features) == 4
    assert len(p.scene_link.get().sensors) == 3

    # Find from name only

    # Wrong name
    feature = p.find(name="WrongName")
    assert feature is None

    # Existing name
    feature = p.find(name="Sensor.2")
    assert feature == sensor2

    feature = p.find(name="Source.1")
    assert feature == source1

    # Using regex for name
    feature = p.find(name=".*2", name_regex=True)
    assert feature == sensor2

    feature = p.find(name=".*8", name_regex=True)
    assert feature is None

    # With type filtering

    # Wrong combination name-type
    feature = p.find(name="Sensor.3", feature_type=script.Source)
    assert feature is None

    # Good combination name-type
    feature = p.find(name="Sensor.3", feature_type=script.Sensor)
    assert feature == sensor3

    # Wrong combination name-type specialized
    feature = p.find(name="Sensor.3", feature_type=script.Sensor.Irradiance)
    assert feature is None

    # Good combination name-type specialized
    feature = p.find(name="Sensor.3", feature_type=script.Sensor.Radiance)
    assert feature == sensor3

    # Good combination name-type specialized + regex
    feature = p.find(name=".*sor\.3", name_regex=True, feature_type=script.Sensor.Radiance)
    assert feature == sensor3


def test_delete(speos: Speos):
    """Test delete a project."""

    # Create an empty project
    p = script.Project(speos=speos)
    assert len(p._features) == 0

    # Create a surface source in the project
    source1 = p.create_source(name="Source.1")
    source1.set_surface()
    assert len(p._features) == 1
    source1.commit()
    assert len(p.scene_link.get().sources) == 1

    # Create an irradiance sensor in the project
    sensor1 = p.create_sensor(name="Sensor.1")
    sensor1.set_irradiance()
    sensor1.commit()
    assert len(p._features) == 2
    assert len(p.scene_link.get().sensors) == 1

    # Delete project
    p.delete()
    assert len(p._features) == 0


def test_from_file(speos: Speos):
    """Test create a project from file."""

    # Create a project from a file
    p = script.Project(speos=speos, path=os.path.join(test_path, "LG_50M_Colorimetric_short.sv5", "LG_50M_Colorimetric_short.sv5"))

    # Check that scene is filled
    assert len(p.scene_link.get().materials) == 4
    assert len(p.scene_link.get().sensors) == 1
    assert len(p.scene_link.get().sources) == 2
    assert len(p.scene_link.get().simulations) == 1

    feat_sim = p.find(name=p.scene_link.get().simulations[0].name)
    assert feat_sim is not None
    assert type(feat_sim) is script.Simulation

    # Check that feature can be retrieved
    feat_op3 = p.find(name=p.scene_link.get().materials[2].name)
    assert feat_op3 is not None
    assert type(feat_op3) is script.OptProp

    # And that the feature retrieved has a real impact on the project
    feat_op3.set_surface_mirror(reflectance=60).commit()
    assert speos.client.get_item(key=p.scene_link.get().materials[2].sop_guids[0]).get().HasField("mirror")
    assert speos.client.get_item(key=p.scene_link.get().materials[2].sop_guids[0]).get().mirror.reflectance == 60

    # Check that ambient mat has no sop
    feat_op_ambient = p.find(name=p.scene_link.get().materials[-1].name)
    assert feat_op_ambient.sop_template_link is None

    # Retrieve body with regex
    feat_body = p.find(name="RootPart/Solid Body in SOURCE2.*", name_regex=True)
    assert feat_body is not None

    # Retrieve another feature
    feat_ssr1 = p.find(name=p.scene_link.get().sensors[0].name)
    assert feat_ssr1 is not None
    assert type(feat_ssr1) is script.Sensor

    # And that we can modify it (and that other values are not overridden by default values)
    feat_ssr1.set_irradiance().set_type_colorimetric().set_wavelengths_range().set_end(value=800)
    feat_ssr1.commit()
    ssr_link = speos.client.get_item(key=p.scene_link.get().sensors[0].sensor_guid)
    ssr_data = ssr_link.get()
    assert speos.client.get_item(key=p.scene_link.get().sensors[0].sensor_guid).get().HasField("irradiance_sensor_template")
    assert (
        speos.client.get_item(key=p.scene_link.get().sensors[0].sensor_guid)
        .get()
        .irradiance_sensor_template.HasField("sensor_type_colorimetric")
    )
    assert (
        speos.client.get_item(key=p.scene_link.get().sensors[0].sensor_guid)
        .get()
        .irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_end
        == 800
    )
    assert (
        speos.client.get_item(key=p.scene_link.get().sensors[0].sensor_guid)
        .get()
        .irradiance_sensor_template.sensor_type_colorimetric.wavelengths_range.w_sampling
        == 25
    )
    assert (
        speos.client.get_item(key=p.scene_link.get().sensors[0].sensor_guid).get().irradiance_sensor_template.dimensions.x_sampling == 500
    )


def test_find_geom(speos: Speos):
    """Test find geometry feature in a project."""
    # Create a project from a file
    p = script.Project(speos=speos, path=os.path.join(test_path, "LG_50M_Colorimetric_short.sv5", "LG_50M_Colorimetric_short.sv5"))

    # Check that scene is filled
    assert p.scene_link.get().part_guid != ""

    # Check that RootPart feature can be retrieved
    part_data = speos.client.get_item(p.scene_link.get().part_guid).get()
    feat_rp = p.find(name=part_data.name)
    assert feat_rp is not None
    assert type(feat_rp) is script.Part

    # Check that body can be retrieved
    assert len(part_data.body_guids) == 3
    body1_data = speos.client.get_item(part_data.body_guids[1]).get()
    feat_body = p.find(name=part_data.name + "/" + body1_data.name)
    assert feat_body is not None
    assert type(feat_body) is script.Body

    # Check that face can be retrieved
    assert len(body1_data.face_guids) > 4
    face2_data = speos.client.get_item(body1_data.face_guids[2]).get()
    feat_face = p.find(name=part_data.name + "/" + body1_data.name + "/" + face2_data.name)
    assert feat_face is not None
    assert type(feat_face) is script.Face
