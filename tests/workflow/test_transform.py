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

import pytest

from ansys.speos.core import body as body_module, source
from ansys.speos.core.kernel.body import ProtoBody
from ansys.speos.core.kernel.face import ProtoFace
from ansys.speos.core.workflow import axis_to_axis_feature, move_feature, rotate_feature


class _TestSource(source.BaseSource):
    """Minimal source wrapper for exercising axis-system transforms."""

    def __init__(self, axis_system=None):
        """Initialize a source-like feature."""
        self._name = "test_source"
        self._project = None
        self.axis_system = (
            [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1] if axis_system is None else axis_system
        )
        self.commit_count = 0

    def commit(self):
        self.commit_count += 1
        return self


def _make_body():
    body = object.__new__(body_module.Body)
    body._name = "mesh"
    body._speos_client = None
    body._parent_part = None
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
    feature = _TestSource(axis_system=[2, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1])

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
