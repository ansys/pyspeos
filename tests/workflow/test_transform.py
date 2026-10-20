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

from pathlib import Path
from typing import Callable, cast

import numpy as np
import pytest

from ansys.speos.core import Project, Speos, source
from ansys.speos.core.generic.general_methods import (
    _axis_frame,
    _validate_axis_system12,
    _validate_scalar,
    _validate_vector3,
    normalize_vector,
)
from ansys.speos.core.workflow import axis_to_axis_feature, move_feature, rotate_feature
from ansys.speos.core.workflow.transform import (
    _rotation_matrix,
)
from tests.conftest import test_path


@pytest.mark.parametrize(
    ("validator", "value", "error", "message"),
    [
        pytest.param(
            _validate_vector3,
            "1,2,3",
            TypeError,
            "A vector must be a list or tuple of three finite numbers.",
            id="wrong-vector-type",
        ),
        pytest.param(
            _validate_vector3,
            [1, "2", 3],
            TypeError,
            "Vector values must be numeric.",
            id="wrong-vector-values",
        ),
        pytest.param(
            _validate_vector3,
            [1, float("nan"), 3],
            ValueError,
            "Vector values must be finite.",
            id="nan-vector",
        ),
        pytest.param(
            _validate_vector3,
            [10**1000, 0, 0],
            ValueError,
            "Vector values must be finite.",
            id="overflow-vector",
        ),
        pytest.param(
            _validate_axis_system12,
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, float("nan")],
            ValueError,
            "Axis system values must be finite.",
            id="nan-axis-system",
        ),
        pytest.param(
            _validate_axis_system12,
            [1, 2, 3, 4],
            ValueError,
            "An axis system must contain exactly twelve values.",
            id="short-axis-system",
        ),
        pytest.param(
            _validate_axis_system12,
            "axis",
            TypeError,
            "An axis system must be a list or tuple of twelve finite numbers.",
            id="wrong-axis-system-type",
        ),
        pytest.param(
            _validate_axis_system12,
            [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, "x"],
            TypeError,
            "Axis system values must be numeric.",
            id="wrong-axis-system-values",
        ),
        pytest.param(
            _validate_axis_system12,
            [10**1000, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            ValueError,
            "Axis system values must be finite.",
            id="overflow-axis-system",
        ),
    ],
)
def test_vector_and_axis_validators_reject_invalid_values(
    validator: Callable[..., np.ndarray], value, error, message
):
    """Cover validator branches for malformed types, lengths, and non-finite values."""
    with pytest.raises(error, match=message):
        validator(value)


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
    match = (
        "A scalar must be a finite number."
        if expected_error is TypeError
        else "A scalar must be finite."
    )
    with pytest.raises(expected_error, match=match):
        _validate_scalar(cast(float, value))


def test_axis_frame_rejects_left_handed_basis():
    """Reject an axis system whose basis has a negative determinant."""
    left_handed = _validate_axis_system12([0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, -1])
    with pytest.raises(
        ValueError,
        match="An axis system must contain an orthonormal, right-handed coordinate frame.",
    ):
        _axis_frame(left_handed)


def test_transform_math_rejects_zero_norm_and_builds_rotation():
    """Exercise normalized vectors and a basic Rodrigues rotation."""
    with pytest.raises(ValueError, match="A vector must not be a zero vector."):
        normalize_vector(_validate_vector3([0, 0, 0]))
    np.testing.assert_allclose(
        _rotation_matrix(_validate_vector3([0, 0, 2]), 90),
        [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
        atol=1e-12,
    )


def _load_workflow_transform_project(speos: Speos):
    """Load the real workflow transform asset used to validate feature transforms."""
    return Project(
        speos=speos,
        path=Path(test_path) / "Workflow_transforms.1.speos" / "Workflow_transforms.1.speos",
    )


@pytest.mark.supported_speos_versions(min=251)
def test_move_feature_matches_loaded_body_translation(speos: Speos):
    """Translate a real body from the workflow file without mutating the original."""
    project = _load_workflow_transform_project(speos)
    original = project.root_part._geom_features[0]

    moved = move_feature(original, [1, 0, 0], 5, copy=True)

    assert moved is not original
    assert moved.faces[0].vertices[0] == pytest.approx(original.faces[0].vertices[0] + 5.0)
    assert original.faces[0].vertices[0] == pytest.approx(original.faces[0].vertices[0])


@pytest.mark.supported_speos_versions(min=251)
def test_rotate_feature_matches_loaded_rayfile_rotation(speos: Speos):
    """Rotate a real rayfile source to the same pose as the reference workflow asset."""
    project = _load_workflow_transform_project(speos)
    reference = next(
        feature for feature in project.sources if feature._name.startswith("Ray-file.2")
    )
    target = next(feature for feature in project.sources if feature._name.startswith("Ray-file.3"))

    rotated = rotate_feature(reference, [0, 0, 0], [1, 0, 0], -30, copy=True)

    assert rotated is not reference
    np.testing.assert_allclose(rotated.axis_system, target.axis_system, atol=1e-9)
    np.testing.assert_allclose(
        reference.axis_system,
        [5.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        atol=1e-9,
    )


@pytest.mark.supported_speos_versions(min=251)
def test_axis_to_axis_matches_loaded_reference_frames(speos: Speos):
    """Map a real source pose between the workflow file's reference frames."""
    project = _load_workflow_transform_project(speos)
    source1 = next(feature for feature in project.sources if feature._name.startswith("Ray-file.1"))
    source2 = next(feature for feature in project.sources if feature._name.startswith("Ray-file.2"))

    mapped = axis_to_axis_feature(source1, source1.axis_system, source2.axis_system, copy=True)

    assert mapped is not source1
    np.testing.assert_allclose(mapped.axis_system, source2.axis_system, atol=1e-9)
    np.testing.assert_allclose(
        source1.axis_system, [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0], atol=1e-9
    )


@pytest.mark.supported_speos_versions(min=251)
def test_move_surface_source(speos: Speos):
    """Translate a real body from the workflow file without mutating the original."""
    project = _load_workflow_transform_project(speos)
    source1 = next(feature for feature in project.sources if feature._name.startswith("Surface.1"))

    moved = move_feature(source1, [1, 0, 0], 5, copy=True)

    assert moved is not source1
    assert isinstance(moved, source.SourceSurface)
    project.preview()
