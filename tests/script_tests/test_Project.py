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

from ansys.speos.core.speos import Speos
import ansys.speos.script as script


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

    # With type filtering

    # Wrong combination name-type
    feature = p.find(name="Sensor.3", feature_type=script.Source)
    assert feature is None

    # Good combination name-type
    feature = p.find(name="Sensor.3", feature_type=script.Sensor)
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
