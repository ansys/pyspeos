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

"""Tests for workflow feature transformations."""

from types import SimpleNamespace

import numpy as np
import pytest

from ansys.speos.core import body as body_module, component, part, sensor, source
from ansys.speos.core.kernel.body import ProtoBody
from ansys.speos.core.kernel.face import ProtoFace
from ansys.speos.core.kernel.part import ProtoPart
from ansys.speos.core.kernel.scene import ProtoScene
from ansys.speos.core.kernel.sensor_template import ProtoSensorTemplate
from ansys.speos.core.kernel.source_template import ProtoSourceTemplate
from ansys.speos.core.workflow import axis_to_axis_feature, move_feature, rotate_feature
from ansys.speos.core.workflow.transform import (
    _axis_frame,
    _copy_name,
    _feature_siblings,
    _normalize,
    _prepare_transform,
    _rotation_matrix,
    _validate_axis_system12,
    _validate_scalar,
    _validate_vector3,
)


class _TestSource(source.BaseSource):
    """Minimal source wrapper for exercising axis-system transforms."""

    def __init__(self, project=None, name="test_source", description="", metadata=None):
        """Initialize a source-like feature."""
        self._name = name
        self._source_path = name
        self._project = project
        self._unique_id = None
        self.source_template_link = None
        self._source_instance = ProtoScene.SourceInstance(
            name=name, description=description, metadata=metadata or {}
        )
        self._source_instance.luminaire_properties.axis_system[:] = [
            0,
            0,
            0,
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
        self._source_template = ProtoSourceTemplate(
            name=name, description=description, metadata=metadata or {}
        )
        self.commit_count = 0

    @property
    def axis_system(self):
        """Return the test axis system."""
        return self._source_instance.luminaire_properties.axis_system

    @axis_system.setter
    def axis_system(self, value):
        self._source_instance.luminaire_properties.axis_system[:] = value

    def _fill_parameters(self, default_parameters=None):
        """Avoid server-side parameter setup in unit tests."""

    def commit(self):
        """Count commits without using a Speos server."""
        self.commit_count += 1
        return self


class _TestSensor(sensor.BaseSensor):
    """Minimal sensor wrapper for testing sensor transform copies."""

    def __init__(self, project=None, name="test_sensor", description="", metadata=None):
        """Initialize the test sensor."""
        self._project = project
        self._name = name
        self._unique_id = None
        self.sensor_template_link = None
        self._sensor_instance = ProtoScene.SensorInstance(
            name=name, description=description, metadata=metadata or {}
        )
        self._sensor_instance.irradiance_properties.axis_system[:] = [
            0,
            0,
            0,
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
        self._sensor_template = ProtoSensorTemplate(
            name=name, description=description, metadata=metadata or {}
        )
        self.commit_count = 0

    @property
    def axis_system(self):
        """Return the test axis system."""
        return self._sensor_instance.irradiance_properties.axis_system

    @axis_system.setter
    def axis_system(self, value):
        self._sensor_instance.irradiance_properties.axis_system[:] = value

    def _fill_parameters(self, default_parameters=None):
        """Avoid server-side parameter setup in unit tests."""

    def commit(self):
        """Count commits without using a Speos server."""
        self.commit_count += 1
        return self


def _make_body(parent_part=None):
    body = object.__new__(body_module.Body)
    body._name = "mesh"
    body._speos_client = None
    body._parent_part = parent_part
    body._body = ProtoBody(name="mesh")
    body.body_link = None
    body._geom_features = []
    face = body.create_face("triangle")
    face._face.CopyFrom(
        ProtoFace(
            name="triangle",
            vertices=[0, 0, 0, 1, 0, 0, 0, 1, 0],
            facets=[0, 1, 2],
            normals=[0, 0, 1, 0, 0, 1, 0, 0, 1],
        )
    )
    return body, face


def _make_subpart(parent, name="subpart"):
    subpart = object.__new__(part.Part.SubPart)
    subpart._name = name
    subpart._parent_part = parent
    subpart._part_instance = ProtoPart.PartInstance(
        name=name, axis_system=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    )
    subpart._part = ProtoPart(name=name)
    subpart.part_link = None
    subpart._unique_id = None
    subpart._geom_features = []
    return subpart


def _make_lightbox(parent, name="test_lightbox"):
    lightbox = object.__new__(component.LightBox)
    lightbox._name = name
    lightbox._parent_project = parent
    lightbox._unique_id = "existing-id"
    lightbox._scene_instance = ProtoScene.SceneInstance(
        name=name,
        axis_system=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        scene_guid="nested-scene",
        metadata={"UniqueId": "existing-id", "custom": "value"},
    )
    return lightbox


def test_move_feature_normalizes_direction_and_commits():
    """Normalize the translation vector and commit the source."""
    feature = _TestSource()

    result = move_feature(feature, [0, 3, 0], 2)

    assert result is feature
    assert feature.axis_system[:3] == pytest.approx([0, 2, 0])
    assert feature.axis_system[3:] == pytest.approx([1, 0, 0, 0, 1, 0, 0, 0, 1])
    assert feature.commit_count == 1


def test_rotate_feature_around_point_and_commits():
    """Rotate both origin and orientation around a point."""
    feature = _TestSource()
    feature.axis_system = [2, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    rotate_feature(feature, [1, 0, 0], [0, 0, 1], 90)

    assert feature.axis_system[:3] == pytest.approx([1, 1, 0])
    assert feature.axis_system[3:] == pytest.approx([0, 1, 0, -1, 0, 0, 0, 0, 1])
    assert feature.commit_count == 1


def test_axis_to_axis_maps_origin_and_orientation():
    """Map feature pose from the reference frame into the target frame."""
    feature = _TestSource()
    reference = [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    target = [0, 2, 0, 0, 1, 0, -1, 0, 0, 0, 0, 1]

    axis_to_axis_feature(feature, reference, target)

    assert feature.axis_system[:3] == pytest.approx([0, 1, 0])
    assert feature.axis_system[3:] == pytest.approx([0, 1, 0, -1, 0, 0, 0, 0, 1])


def test_body_copy_transforms_mesh_without_modifying_original(monkeypatch):
    """Transform copied body vertices and preserve its original mesh."""
    monkeypatch.setattr(body_module.Body, "commit", lambda self: self)
    original, original_face = _make_body()

    copied = move_feature(original, [1, 0, 0], 2, copy=True)

    assert copied is not original
    assert copied._name == "mesh_copy"
    assert copied.faces[0].vertices == pytest.approx([2, 0, 0, 3, 0, 0, 2, 1, 0])
    assert copied.faces[0].normals == pytest.approx(original_face.normals)
    assert copied.faces[0].facets == original_face.facets
    assert original_face.vertices == [0, 0, 0, 1, 0, 0, 0, 1, 0]


@pytest.mark.parametrize(
    ("args", "error"),
    [
        (([], 1), ValueError),
        (([0, 0, 0], 1), ValueError),
        (([1, 0], 1), ValueError),
        (([1, 0, 0], float("inf")), ValueError),
    ],
)
def test_move_feature_rejects_invalid_inputs(args, error):
    """Reject malformed, zero-length, and non-finite movement arguments."""
    with pytest.raises(error):
        move_feature(_TestSource(), *args)


def test_rotate_feature_rejects_zero_axis():
    """Reject a zero-length rotation axis."""
    with pytest.raises(ValueError, match="zero vector"):
        rotate_feature(_TestSource(), [0, 0, 0], [0, 0, 0], 45)


def test_axis_to_axis_rejects_invalid_frames():
    """Reject malformed or non-rigid coordinate frames."""
    with pytest.raises(ValueError, match="twelve values"):
        axis_to_axis_feature(_TestSource(), [0, 0, 0], [0, 0, 0])

    non_rigid = [0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 1]
    identity = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    with pytest.raises(ValueError, match="orthonormal"):
        axis_to_axis_feature(_TestSource(), non_rigid, identity)


def test_face_and_unknown_feature_are_rejected():
    """Reject standalone faces and unsupported feature types."""
    body, face = _make_body()
    with pytest.raises(ValueError, match="standalone Face"):
        move_feature(face, [1, 0, 0], 1)

    with pytest.raises(TypeError, match="Unsupported feature type"):
        move_feature(object(), [1, 0, 0], 1)


@pytest.mark.parametrize(
    ("value", "name", "error"),
    [
        pytest.param("1,2,3", "direction", TypeError, id="wrong-vector-type"),
        pytest.param([1, "2", 3], "point", TypeError, id="wrong-vector-values"),
        pytest.param([1, float("nan"), 3], "point", ValueError, id="nan-vector"),
        pytest.param([10**1000, 0, 0], "direction", ValueError, id="overflow-vector"),
        pytest.param([1, 2, float("nan")], "reference_axis", ValueError, id="nan-axis-system"),
        pytest.param([1, 2, 3, 4], "axis", ValueError, id="short-axis-system"),
        pytest.param("axis", "reference_axis", TypeError, id="wrong-axis-system-type"),
        pytest.param(
            [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, "x"],
            "reference_axis",
            TypeError,
            id="wrong-axis-system-values",
        ),
        pytest.param(
            [10**1000, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            "reference_axis",
            ValueError,
            id="overflow-axis-system",
        ),
    ],
)
def test_vector_and_axis_validators_reject_invalid_values(value, name, error):
    """Cover validator branches for malformed types, lengths, and non-finite values."""
    validator = _validate_axis_system12 if name == "reference_axis" else _validate_vector3
    with pytest.raises(error):
        validator(value, name)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(None, id="none"),
        pytest.param(True, id="bool"),
        pytest.param("1", id="string"),
        pytest.param(float("inf"), id="infinity"),
        pytest.param(float("nan"), id="nan"),
        pytest.param(10**1000, id="overflow"),
    ],
)
def test_scalar_validator_rejects_non_finite_or_non_numeric_values(value):
    """Reject scalar values that cannot safely represent a finite number."""
    expected_error = TypeError if value is None or isinstance(value, (bool, str)) else ValueError
    with pytest.raises(expected_error):
        _validate_scalar(value, "angle")


def test_axis_frame_rejects_left_handed_basis():
    """Reject an axis system whose basis has a negative determinant."""
    left_handed = _validate_axis_system12([0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, -1], "frame")
    with pytest.raises(ValueError, match="right-handed"):
        _axis_frame(left_handed, "frame")


def test_transform_math_rejects_zero_norm_and_builds_rotation():
    """Exercise normalized vectors and a basic Rodrigues rotation."""
    with pytest.raises(ValueError, match="zero vector"):
        _normalize(_validate_vector3([0, 0, 0], "vector"), "vector")
    np.testing.assert_allclose(
        _rotation_matrix(_validate_vector3([0, 0, 2], "axis"), 90),
        [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
        atol=1e-12,
    )


def test_axis_feature_copy_preserves_properties_but_not_instance_identity():
    """Copy and transform a source without mutating the original."""
    project = SimpleNamespace(_features=[])
    feature = _TestSource(project=project, metadata={"tag": "kept"})
    project._features.append(feature)
    feature.axis_system = [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]

    copied = move_feature(feature, [0, 1, 0], 2, copy=True, name="copy")

    assert copied is project._features[-1]
    assert copied._name == "copy"
    assert copied.axis_system[:3] == pytest.approx([1, 2, 0])
    assert copied._source_template.metadata["tag"] == "kept"
    assert copied._unique_id is None
    assert feature.axis_system[:3] == [1, 0, 0]
    assert copied.commit_count == 1


def test_sensor_copy_and_auto_name_are_independent():
    """Copy and transform a sensor with a generated unique name."""
    project = SimpleNamespace(_features=[])
    feature = _TestSensor(project=project)
    project._features.extend([feature, _TestSensor(project=project, name="test_sensor_copy")])

    copied = rotate_feature(feature, [0, 0, 0], [0, 0, 1], 90, copy=True)

    assert copied._name == "test_sensor_copy_2"
    assert copied.axis_system[3:] == pytest.approx([0, 1, 0, -1, 0, 0, 0, 0, 1])
    assert copied._sensor_template.name == copied._name
    assert feature.axis_system[3:] == [1, 0, 0, 0, 1, 0, 0, 0, 1]


@pytest.mark.parametrize(
    ("name", "expected_error"),
    [
        ("", ValueError),
        (None, None),
        (12, ValueError),
    ],
)
def test_copy_name_validation(name, expected_error):
    """Validate explicit copy names and exercise the unowned feature collection."""
    feature = _TestSource()
    assert _feature_siblings(feature) == []
    assert _feature_siblings(object()) == []
    if expected_error is None:
        assert _copy_name(feature, name) == "test_source_copy"
    else:
        with pytest.raises(expected_error):
            _copy_name(feature, name)


def test_copy_name_rejects_existing_names_and_in_place_name():
    """Reject name collisions and disallow names for in-place transforms."""
    project = SimpleNamespace(_features=[])
    feature = _TestSource(project=project)
    project._features.append(feature)
    with pytest.raises(ValueError, match="already exists"):
        move_feature(feature, [1, 0, 0], 1, copy=True, name=feature._name)
    with pytest.raises(ValueError, match="only be provided"):
        move_feature(feature, [1, 0, 0], 1, name="ignored")


def test_subpart_copy_keeps_part_link_and_transforms_axis(monkeypatch):
    """Copy a SubPart instance while sharing its underlying immutable part."""
    parent = SimpleNamespace(_geom_features=[])
    original = _make_subpart(parent)
    parent._geom_features.append(original)
    copied_subparts = []

    def create_sub_part(name, description=""):
        copied = _make_subpart(parent, name)
        copied_subparts.append(copied)
        return copied

    parent.create_sub_part = create_sub_part
    monkeypatch.setattr(part.Part.SubPart, "commit", lambda self: self)
    original.part_link = SimpleNamespace(key="part-guid")
    original._part_instance.part_guid = "part-guid"
    copied = axis_to_axis_feature(
        original,
        [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        [1, 2, 3, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        copy=True,
    )

    assert copied is copied_subparts[0]
    assert copied.axis_system[:3] == pytest.approx([1, 2, 3])
    assert copied.part_link is original.part_link
    assert copied._part_instance.part_guid == "part-guid"
    assert copied._unique_id is None
    assert original.axis_system[:3] == [0, 0, 0]


def test_lightbox_copy_preserves_scene_content_and_transforms(monkeypatch):
    """Copy a LightBox instance while preserving its nested scene reference."""
    parent = SimpleNamespace(_features=[])
    original = _make_lightbox(parent)
    parent._features.append(original)

    def initialize_lightbox(self, name, parent_project, instance=None):
        self._name = name
        self._parent_project = parent_project
        self._scene_instance = instance
        self._unique_id = instance.metadata["UniqueId"]

    monkeypatch.setattr(component.LightBox, "__init__", initialize_lightbox)
    monkeypatch.setattr(component.LightBox, "commit", lambda self: self)

    copied = move_feature(original, [1, 0, 0], 5, copy=True)

    assert copied._name == "test_lightbox_copy"
    assert copied.axis_system[:3] == pytest.approx([5, 0, 0])
    assert copied._scene_instance.scene_guid == "nested-scene"
    assert copied._scene_instance.metadata["custom"] == "value"
    assert "UniqueId" not in copied._scene_instance.metadata
    assert copied._unique_id is None
    assert original.axis_system[:3] == [0, 0, 0]


def test_body_in_place_axis_to_axis_transforms_vertices_and_normals(monkeypatch):
    """Transform all face vertices and normals when mutating a body."""
    monkeypatch.setattr(body_module.Body, "commit", lambda self: self)
    body, face = _make_body()
    reference = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    target = [1, 0, 0, 0, 1, 0, -1, 0, 0, 0, 0, 1]

    result = axis_to_axis_feature(body, reference, target)

    assert result is body
    assert face.vertices == pytest.approx([1, 0, 0, 1, 1, 0, 0, 0, 0])
    assert face.normals == pytest.approx([0, 0, 1] * 3)
    assert face.facets == [0, 1, 2]


def test_body_copy_empty_mesh_and_metadata(monkeypatch):
    """Copy empty faces and preserve body metadata without changing topology."""
    monkeypatch.setattr(body_module.Body, "commit", lambda self: self)
    parent = SimpleNamespace(_geom_features=[])
    original, face = _make_body(parent)
    parent._geom_features.append(original)
    face._face.ClearField("vertices")
    face._face.ClearField("normals")
    original._body.description = "body description"
    original._body.metadata["key"] = "value"

    copied = rotate_feature(original, [0, 0, 0], [1, 0, 0], 30, copy=True)

    assert copied._name == "mesh_copy"
    assert copied._body.description == "body description"
    assert copied._body.metadata["key"] == "value"
    assert copied.faces[0].vertices == []
    assert copied.faces[0].normals == []
    assert copied.faces[0].facets == [0, 1, 2]
    assert copied in parent._geom_features
    assert face.vertices == []


def test_unsupported_source_without_axis_system_is_rejected():
    """Reject source base-class instances without a supported axis system."""
    feature = object.__new__(source.BaseSource)
    feature._name = "unsupported"
    feature._project = None
    with pytest.raises(TypeError, match="does not expose an axis_system"):
        _prepare_transform(feature, copy_feature=False, name=None)


@pytest.mark.parametrize(
    ("function", "args"),
    [
        (move_feature, ("bad", 1)),
        (move_feature, ([1, 0, 0], "bad")),
        (rotate_feature, ([0, 0, 0], [1, 0], 20)),
        (rotate_feature, ([0, 0, 0], [1, 0, 0], float("nan"))),
        (
            axis_to_axis_feature,
            (
                [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, float("inf")],
            ),
        ),
    ],
)
def test_public_transform_functions_reject_invalid_arguments(function, args):
    """Cover invalid parameter branches through each public helper."""
    with pytest.raises((TypeError, ValueError)):
        function(_TestSource(), *args)
