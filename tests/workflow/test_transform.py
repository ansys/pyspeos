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

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, cast
from uuid import UUID, uuid4

import numpy as np
import pytest

from ansys.speos.core import Project, Speos, body, component, face, part, sensor, source
from ansys.speos.core.generic.general_methods import (
    _axis_frame,
    _validate_axis_system12,
    _validate_scalar,
    _validate_vector3,
    normalize_vector,
)
from ansys.speos.core.workflow import axis_to_axis_feature, move_feature, rotate_feature
from ansys.speos.core.workflow.transform import (
    _copy_feature,
    _copy_name,
    _copy_surface_geometry,
    _owner_project,
    _prepare_transform,
    _rotation_matrix,
    _surface_source_body,
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
    original_vertices = list(original.faces[0].vertices)

    moved = move_feature(original, [1, 0, 0], 5, copy=True)

    assert moved is not original
    assert moved.faces[0].vertices[0] == pytest.approx(original.faces[0].vertices[0] + 5.0)
    assert list(original.faces[0].vertices) == original_vertices


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
    assert moved._source_template == source1._source_template
    assert (
        moved.set_exitance_constant().geometries[0].geo_path
        != source1.set_exitance_constant().geometries[0].geo_path
    )

    moved = move_feature(source1, [1, 0, 0], 5)

    assert isinstance(moved, source.SourceSurface)
    assert moved is source1


@pytest.mark.supported_speos_versions(min=251)
@pytest.mark.parametrize(
    ("transform", "args", "rotation", "translation"),
    [
        pytest.param(move_feature, ([1, 0, 0], 5), np.eye(3), [5, 0, 0], id="move"),
        pytest.param(
            rotate_feature,
            ([0, 0, 0], [0, 0, 1], 90),
            [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
            [0, 0, 0],
            id="rotate",
        ),
        pytest.param(
            axis_to_axis_feature,
            (
                [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                [5, 0, 0, 0, 1, 0, -1, 0, 0, 0, 0, 1],
            ),
            [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
            [5, 0, 0],
            id="axis-to-axis",
        ),
    ],
)
def test_surface_source_transform_in_place(speos: Speos, transform, args, rotation, translation):
    """Return the original surface source while transforming its referenced geometry."""
    project = _load_workflow_transform_project(speos)
    original = next(feature for feature in project.sources if feature._name.startswith("Surface.1"))
    body = _surface_source_body(original)
    vertices = np.asarray(body.faces[0].vertices).reshape(-1, 3).copy()
    geometry_path = body.geo_path.to_native_link()

    transformed = transform(original, *args, copy=False)

    assert transformed is original
    assert _surface_source_body(transformed) is body
    assert body.geo_path.to_native_link() == geometry_path
    np.testing.assert_allclose(
        np.asarray(body.faces[0].vertices).reshape(-1, 3),
        (np.asarray(rotation) @ vertices.T).T + translation,
        atol=1e-9,
    )


@pytest.mark.supported_speos_versions(min=251)
@pytest.mark.parametrize("copy", [False, True])
@pytest.mark.parametrize(
    ("transform", "args", "rotation", "translation"),
    [
        pytest.param(move_feature, ([1, 0, 0], 5), np.eye(3), [5, 0, 0], id="move"),
        pytest.param(
            rotate_feature,
            ([1, 2, 3], [0, 0, 1], 90),
            [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
            [3, 1, 0],
            id="rotate",
        ),
        pytest.param(
            axis_to_axis_feature,
            (
                [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                [5, 0, 0, 0, 1, 0, -1, 0, 0, 0, 0, 1],
            ),
            [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
            [5, 0, 0],
            id="axis-to-axis",
        ),
    ],
)
def test_transform_variable_exitance_surface_source(
    speos: Speos, copy: bool, transform, args, rotation, translation
):
    """Transform and persist the XMP plane while preserving variable exitance settings."""
    project = Project(speos, path=Path(test_path) / "Source.speos" / "SourceSurfaceTests.speos")
    original = project.find(name="Surface.4", name_regex=True, feature_type=source.SourceSurface)[0]
    exitance = original.set_exitance_variable()
    original_plane = np.asarray(exitance.axis_plane).copy()
    original_template = original._source_template.SerializeToString()
    original_instance = deepcopy(original._source_instance)

    moved = transform(original, *args, copy=copy)

    assert isinstance(moved, source.SourceSurface)
    assert (moved is original) is not copy
    assert moved._source_template.SerializeToString() == original_template
    expected_plane = original_plane.reshape(3, 3) @ np.asarray(rotation).T
    expected_plane[0] += translation
    expected_plane = expected_plane.reshape(-1)
    np.testing.assert_allclose(moved.set_exitance_variable().axis_plane, expected_plane, atol=1e-9)
    if copy:
        np.testing.assert_allclose(exitance.axis_plane, original_plane, atol=1e-9)
    moved.reset()
    assert moved._source_template.SerializeToString() == original_template
    np.testing.assert_allclose(moved.set_exitance_variable().axis_plane, expected_plane, atol=1e-9)
    assert _without_pose_and_identity(moved._source_instance) == _without_pose_and_identity(
        original_instance
    )
    _assert_metadata_identity(moved._source_instance, original_instance, copy)
    if copy:
        original.reset()
        assert original._source_instance == original_instance
        assert moved._unique_id != original._unique_id


@pytest.fixture(
    params=[
        pytest.param((move_feature, ([2, -1, 2], 9), np.eye(3), [6, -3, 6]), id="move"),
        pytest.param(
            (
                rotate_feature,
                ([1, 2, 3], [0, 0, 2], 90),
                [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
                [3, 1, 0],
            ),
            id="rotate",
        ),
        pytest.param(
            (
                axis_to_axis_feature,
                (
                    [1, 2, 3, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                    [7, 5, 4, 0, 1, 0, -1, 0, 0, 0, 0, 1],
                ),
                [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
                [9, 4, 1],
            ),
            id="axis-to-axis",
        ),
    ]
)
def rigid_transform(request):
    """Provide transforms with independently calculated expected matrices and offsets."""
    transform, args, rotation, translation = request.param
    return transform, args, np.asarray(rotation), np.asarray(translation)


def _without_pose_and_identity(message):
    """Snapshot all protobuf configuration except the transform and instance identity."""
    result = deepcopy(message)
    for field in ("name", "axis_system", "axis_plane"):
        if field in result.DESCRIPTOR.fields_by_name:
            result.ClearField(field)
    if "metadata" in result.DESCRIPTOR.fields_by_name:
        result.metadata.pop("UniqueId", None)
    for field, value in result.ListFields():
        if field.message_type is not None and not field.message_type.GetOptions().map_entry:
            if field.is_repeated:
                for item in value:
                    item.CopyFrom(_without_pose_and_identity(item))
            else:
                value.CopyFrom(_without_pose_and_identity(value))
    return result


def _assert_metadata_identity(actual, original, copied: bool):
    """Verify persisted UUIDs change only on copied objects and preserve other metadata."""
    actual_metadata = dict(actual.metadata)
    original_metadata = dict(original.metadata)
    if copied:
        assert str(UUID(actual_metadata["UniqueId"])) == actual_metadata["UniqueId"]
        assert actual_metadata["UniqueId"] != original_metadata.get("UniqueId")
        actual_metadata.pop("UniqueId")
        original_metadata.pop("UniqueId", None)
    assert actual_metadata == original_metadata


def _geometry_snapshot(feature):
    """Capture every body, face, mesh, and nested part through the Python API."""
    if isinstance(feature, body.Body):
        feature.reset()
        message = deepcopy(feature._body)
        message.ClearField("face_guids")
        for face in feature.faces:
            face.reset()
        return message, [deepcopy(face._face) for face in feature.faces]
    return [
        (
            child._name,
            deepcopy(child._part_instance) if isinstance(child, part.Part.SubPart) else None,
            _geometry_snapshot(child),
        )
        for child in feature._geom_features
    ]


def _create_mesh(parent, name):
    """Create a nonempty body with two distinct faces and non-default metadata."""
    mesh = parent.create_body(
        name=name,
        description="Transform body",
        metadata={"purpose": "transform", "UniqueId": str(uuid4())},
    )
    for index in range(2):
        face = mesh.create_face(
            name=f"Face{index}",
            description="Transform face",
            metadata={"index": str(index), "UniqueId": str(uuid4())},
        )
        face.vertices = [index, 2, 3, index, 4, 3, index, 2, 5]
        face.facets = [0, 1, 2]
        face.normals = [1, 0, 0] * 3
    return mesh


@pytest.mark.parametrize("copy", [False, True], ids=["in-place", "copy"])
@pytest.mark.parametrize(
    "feature_type",
    [
        pytest.param(source.SourceLuminaire, marks=pytest.mark.supported_speos_versions(min=252)),
        pytest.param(source.SourceRayFile, marks=pytest.mark.supported_speos_versions(min=252)),
        pytest.param(source.SourceDisplay, marks=pytest.mark.supported_speos_versions(min=252)),
        pytest.param(sensor.SensorCamera, marks=pytest.mark.supported_speos_versions(min=252)),
        pytest.param(sensor.SensorIrradiance, marks=pytest.mark.supported_speos_versions(min=251)),
        pytest.param(sensor.SensorRadiance, marks=pytest.mark.supported_speos_versions(min=251)),
        pytest.param(
            sensor.SensorXMPIntensity, marks=pytest.mark.supported_speos_versions(min=252)
        ),
        pytest.param(
            sensor.SensorPolarIntensity, marks=pytest.mark.supported_speos_versions(min=252)
        ),
        pytest.param(sensor.SensorImmersive, marks=pytest.mark.supported_speos_versions(min=261)),
        pytest.param(sensor.SensorObserver, marks=pytest.mark.supported_speos_versions(min=261)),
        pytest.param(part.Part.SubPart, marks=pytest.mark.supported_speos_versions(min=251)),
        pytest.param(component.LightBox, marks=pytest.mark.supported_speos_versions(min=261)),
    ],
    ids=lambda feature_type: feature_type.__name__,
)
def test_transform_axis_feature_preserves_contents(
    speos: Speos, feature_type, rigid_transform, copy: bool
):
    """Transform real features and preserve all configuration and nested geometry on the server."""
    project = Project(speos)
    if issubclass(feature_type, source.BaseSource):
        original = project.create_source(name="Original", feature_type=feature_type)
        if feature_type is source.SourceLuminaire:
            original.intensity_file_uri = Path(test_path) / "IES_C_DETECTOR.ies"
        elif feature_type is source.SourceRayFile:
            original.ray_file_uri = Path(test_path) / "RaysWithoutSpectralData.RAY"
            original.spectrum.set_monochromatic().wavelength = 555
        else:
            original.image_file_uri = Path(test_path) / "stars.exr"
            original.luminance = 200
    elif issubclass(feature_type, sensor.BaseSensor):
        original = project.create_sensor(name="Original", feature_type=feature_type)
        if feature_type is sensor.SensorCamera:
            original.set_mode_geometric()
    elif feature_type is part.Part.SubPart:
        root = project.create_root_part()
        original = root.create_sub_part(name="Original", description="Nested geometry")
        original.axis_system = [2, 3, 4, 0, 1, 0, 0, 0, 1, 1, 0, 0]
        _create_mesh(original, "Body1")
        _create_mesh(original, "Body2")
        nested = original.create_sub_part(name="Nested")
        nested.axis_system = [1, 2, 3, 1, 0, 0, 0, 1, 0, 0, 0, 1]
        _create_mesh(nested, "NestedBody")
        root.commit()
    else:
        original = project.create_lightbox(
            name="Original",
            lightbox=component.LightBoxFileInstance(
                file=Path(test_path) / "lightbox" / "Light Box Export.2.SPEOSLightBox"
            ),
        )

    original.axis_system = [2, 3, 4, 0, 1, 0, 0, 0, 1, 1, 0, 0]
    original.commit()
    original.reset()
    if isinstance(original, part.Part.SubPart):
        original._part_instance.metadata["UniqueId"] = original._unique_id
        original.commit()
    initial_pose = np.asarray(original.axis_system).reshape(4, 3).copy()
    if isinstance(original, source.BaseSource):
        instance = original._source_instance
        template = original.source_template_link.get()
    elif isinstance(original, sensor.BaseSensor):
        instance = original._sensor_instance
        template = original.sensor_template_link.get()
    elif isinstance(original, part.Part.SubPart):
        instance = original._part_instance
        template = original.part_link.get()
    else:
        instance = original._scene_instance
        template = original.project.scene_link.get()
    initial_instance = deepcopy(instance)
    initial_contents = (
        _geometry_snapshot(original)
        if isinstance(original, part.Part.SubPart)
        else _geometry_snapshot(original.project.root_part)
        if isinstance(original, component.LightBox)
        else None
    )

    transform, args, rotation, translation = rigid_transform
    transformed = transform(original, *args, copy=copy, **({"name": "Transformed"} if copy else {}))

    assert type(transformed) is feature_type
    assert (transformed is original) is not copy
    expected_pose = initial_pose @ rotation.T
    expected_pose[0] += translation
    np.testing.assert_allclose(transformed.axis_system, expected_pose.reshape(-1), atol=1e-9)
    transformed.reset()
    np.testing.assert_allclose(transformed.axis_system, expected_pose.reshape(-1), atol=1e-9)
    if isinstance(transformed, source.BaseSource):
        actual_instance = transformed._source_instance
        assert transformed.source_template_link.get() == template
    elif isinstance(transformed, sensor.BaseSensor):
        actual_instance = transformed._sensor_instance
        assert transformed.sensor_template_link.get() == template
    elif isinstance(transformed, part.Part.SubPart):
        actual_instance = transformed._part_instance
        assert transformed.part_link.get() == template
        assert _geometry_snapshot(transformed) == initial_contents
    else:
        actual_instance = transformed._scene_instance
        assert transformed.project.scene_link.get() == template
        assert _geometry_snapshot(transformed.project.root_part) == initial_contents
        assert len(transformed.project._features) == len(original.project._features)
    expected_instance = deepcopy(initial_instance)
    if isinstance(transformed, part.Part.SubPart):
        expected_instance.description = actual_instance.description
    assert _without_pose_and_identity(actual_instance) == _without_pose_and_identity(
        expected_instance
    )
    _assert_metadata_identity(actual_instance, initial_instance, copy)
    assert actual_instance.metadata["UniqueId"] == transformed._unique_id
    if isinstance(transformed, part.Part.SubPart):
        assert actual_instance.description == "UniqueId_" + transformed._unique_id
    if copy:
        assert transformed._unique_id != original._unique_id
        assert transformed._name == "Transformed"
        original.reset()
        np.testing.assert_allclose(original.axis_system, initial_pose.reshape(-1), atol=1e-9)
        if isinstance(original, source.BaseSource):
            assert original._source_instance == initial_instance
        elif isinstance(original, sensor.BaseSensor):
            assert original._sensor_instance == initial_instance
        elif isinstance(original, part.Part.SubPart):
            assert original._part_instance == initial_instance
            assert _geometry_snapshot(original) == initial_contents
        else:
            assert original._scene_instance == initial_instance


@pytest.mark.supported_speos_versions(min=251)
@pytest.mark.parametrize("copy", [False, True], ids=["in-place", "copy"])
@pytest.mark.parametrize("surface_source", [False, True], ids=["body", "constant-surface"])
def test_transform_mesh_feature_preserves_faces(
    speos: Speos, rigid_transform, copy: bool, surface_source: bool
):
    """Persist transformed vertices and normals while preserving every face and body property."""
    project = Project(speos)
    root = project.create_root_part()
    original = _create_mesh(root, "Original")
    root.commit()
    feature = original
    if surface_source:
        feature = project.create_source(name="Surface", feature_type=source.SourceSurface)
        feature.set_exitance_constant().geometries = [
            (original.faces[0], False),
            (original.faces[1], True),
        ]
        feature.commit()
        initial_template = feature.source_template_link.get()
        initial_instance = deepcopy(feature._source_instance)
    initial_body, initial_faces = _geometry_snapshot(original)
    transform, args, rotation, translation = rigid_transform

    result = transform(feature, *args, copy=copy)

    assert (result is feature) is not copy
    result.reset()
    if surface_source:
        assert isinstance(result, source.SourceSurface)
        assert result.source_template_link.get() == initial_template
        transformed = _surface_source_body(result)
        expected_instance = deepcopy(initial_instance)
        expected_geometries = expected_instance.surface_properties.exitance_constant_properties
        for path, face in zip(expected_geometries.geo_paths, transformed.faces, strict=True):
            path.geo_path = face.geo_path.to_native_link()
        assert _without_pose_and_identity(result._source_instance) == _without_pose_and_identity(
            expected_instance
        )
        _assert_metadata_identity(result._source_instance, initial_instance, copy)
        if copy:
            feature.reset()
            assert feature._source_instance == initial_instance
            assert result._unique_id != feature._unique_id
    else:
        transformed = result
    assert len(transformed.faces) == len(initial_faces) == 2
    transformed.reset()
    actual_body, actual_faces = _geometry_snapshot(transformed)
    expected_body = deepcopy(initial_body)
    expected_body.name = actual_body.name
    _assert_metadata_identity(actual_body, initial_body, copy)
    expected_body.metadata["UniqueId"] = actual_body.metadata["UniqueId"]
    assert actual_body == expected_body
    for actual, before in zip(actual_faces, initial_faces, strict=True):
        expected = deepcopy(before)
        _assert_metadata_identity(actual, before, copy)
        expected.metadata["UniqueId"] = actual.metadata["UniqueId"]
        vertices = np.asarray(before.vertices).reshape(-1, 3) @ rotation.T + translation
        normals = np.asarray(before.normals).reshape(-1, 3) @ rotation.T
        expected.vertices[:] = vertices.reshape(-1).tolist()
        expected.normals[:] = normals.reshape(-1).tolist()
        np.testing.assert_allclose(actual.vertices, expected.vertices, atol=1e-9)
        np.testing.assert_allclose(actual.normals, expected.normals, atol=1e-9)
        actual.ClearField("vertices")
        actual.ClearField("normals")
        expected.ClearField("vertices")
        expected.ClearField("normals")
        assert actual == expected
    copied_ids = [actual_body.metadata["UniqueId"]] + [
        face.metadata["UniqueId"] for face in actual_faces
    ]
    assert len(set(copied_ids)) == len(copied_ids)
    if copy:
        original.reset()
        assert _geometry_snapshot(original) == (initial_body, initial_faces)
        assert transformed.body_link.key != original.body_link.key
        assert all(
            new.face_link.key != old.face_link.key
            for new, old in zip(transformed.faces, original.faces, strict=True)
        )


@pytest.mark.supported_speos_versions(min=252)
@pytest.mark.parametrize("copy", [False, True], ids=["in-place", "copy"])
@pytest.mark.parametrize("feature_kind", ["body", "surface", "subpart"])
@pytest.mark.parametrize("assignment", ["body", "face", "parent", "all", "none"])
def test_transform_preserves_material_assignments(
    speos: Speos, rigid_transform, copy: bool, feature_kind: str, assignment: str
):
    """Keep material references, templates, and original assignments through real transforms."""
    project = Project(speos)
    root = project.create_root_part()
    parent = root.create_sub_part(name="Assembly")
    parent.axis_system = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    original = _create_mesh(parent, "Original")
    unrelated = _create_mesh(root, "Unrelated")
    root.commit()
    material = project.create_optical_property(name="Assigned")
    material.set_surface_mirror().reflectance = 73
    material.set_volume_opaque()
    targets = {
        "body": [original],
        "face": [original.faces[1]],
        "parent": [parent],
        "all": [],
        "none": None,
    }
    material.geometries = targets[assignment]
    material.commit()
    other_material = project.create_optical_property(name="UnrelatedMaterial")
    other_material.geometries = [unrelated]
    other_material.commit()
    initial_materials = deepcopy(project.scene_link.get().materials)
    sop = material.sop_template_link.get()
    vop = material.vop_template_link.get()
    feature = original
    if feature_kind == "surface":
        feature = project.create_source(name="Surface", feature_type=source.SourceSurface)
        feature.set_exitance_constant().geometries = [(original, False)]
        feature.commit()
    elif feature_kind == "subpart":
        feature = parent
    original_path = (
        feature.geo_path.to_native_link()
        if feature_kind == "subpart"
        else original.geo_path.to_native_link()
    )
    transform, args, _, _ = rigid_transform

    transformed = transform(feature, *args, copy=copy)

    result_body = _surface_source_body(transformed) if feature_kind == "surface" else transformed
    result_path = result_body.geo_path.to_native_link()
    expected = deepcopy(initial_materials)
    if copy and (
        assignment in ("body", "face") or (feature_kind == "subpart" and assignment == "parent")
    ):
        old_path = targets[assignment][0].geo_path.to_native_link()
        expected[0].geometries.geo_paths.append(result_path + old_path[len(original_path) :])
    assert project.scene_link.get().materials == expected
    assert material._material_instance == expected[0]
    material.commit()
    assert project.scene_link.get().materials == expected
    material.reset()
    assert material._material_instance == expected[0]
    assert material.sop_template_link.get() == sop
    assert material.vop_template_link.get() == vop
    assert len(project.scene_link.get().materials) == len(initial_materials)
    if assignment == "parent" and feature_kind != "subpart":
        assert result_path.startswith(parent.geo_path.to_native_link() + "/")
    if copy:
        assert result_path != original_path
    material.commit()
    assert project.scene_link.get().materials == expected


@pytest.mark.supported_speos_versions(min=261)
@pytest.mark.parametrize("copy", [False, True], ids=["in-place", "copy"])
def test_transform_lightbox_preserves_material_assignments(
    speos: Speos, rigid_transform, copy: bool
):
    """Keep LightBox material assignments and optical templates in its shared scene."""
    project = Project(speos)
    original = project.create_lightbox(
        name="Original",
        lightbox=component.LightBoxFileInstance(
            file=Path(test_path) / "lightbox" / "Light Box Export.2.SPEOSLightBox"
        ),
    )
    original.commit()
    initial_materials = deepcopy(original.project.scene_link.get().materials)
    assert initial_materials
    assert any(material.HasField("geometries") for material in initial_materials)
    templates = {
        guid: project.client[guid].get()
        for material in initial_materials
        for guid in (material.sop_guid, material.vop_guid)
        if guid
    }
    assert templates
    transform, args, _, _ = rigid_transform

    transformed = transform(original, *args, copy=copy)

    transformed.reset()
    assert transformed.project.scene_link.key == original.project.scene_link.key
    assert transformed.project.scene_link.get().materials == initial_materials
    for guid, template in templates.items():
        assert project.client[guid].get() == template


@pytest.mark.supported_speos_versions(min=252)
@pytest.mark.parametrize("variable", [False, True], ids=["constant", "variable"])
def test_surface_transform_rejects_name_without_copy(speos: Speos, rigid_transform, variable: bool):
    """Reject copy-only naming before modifying either surface source configuration."""
    project = Project(speos)
    original = project.create_source(name="Surface", feature_type=source.SourceSurface)
    if variable:
        original.set_exitance_variable()
    instance = deepcopy(original._source_instance)
    template = deepcopy(original._source_template)
    transform, args, _, _ = rigid_transform

    with pytest.raises(ValueError, match="name can only be provided when copy=True"):
        transform(original, *args, copy=False, name="Unexpected")

    assert original._source_instance == instance
    assert original._source_template == template


@pytest.mark.supported_speos_versions(min=252)
def test_surface_copy_rejects_missing_face(speos: Speos):
    """Never replace an unmapped emissive face with the entire copied body."""
    project = Project(speos)
    root = project.create_root_part()
    original = _create_mesh(root, "Original")
    incomplete = root.create_body(name="Incomplete")
    feature = project.create_source(name="Surface", feature_type=source.SourceSurface)
    feature.set_exitance_constant().geometries = [(original.faces[1], True)]

    with pytest.raises(ValueError, match="Cannot map surface source geometry path"):
        _copy_surface_geometry(feature, original, incomplete)


def test_owner_project_rejects_geometry_without_root_part():
    """Reject geometry whose parent chain does not lead to a root Part."""
    feature = SimpleNamespace(_parent_part=None)

    with pytest.raises(ValueError, match="Cannot resolve the owning project without a root part"):
        _owner_project(feature)


@pytest.mark.parametrize("name", ["", 1], ids=["empty", "not-string"])
def test_copy_name_rejects_invalid_name(monkeypatch, name):
    """Require an explicit copy name to be a non-empty string."""
    feature = SimpleNamespace(_name="Original")
    monkeypatch.setattr("ansys.speos.core.workflow.transform._feature_siblings", lambda _: [])

    with pytest.raises(ValueError, match="name must be a non-empty string"):
        _copy_name(feature, name)


def test_copy_name_rejects_duplicate_name(monkeypatch):
    """Prevent copied features from colliding with an existing sibling."""
    feature = SimpleNamespace(_name="Original")
    monkeypatch.setattr(
        "ansys.speos.core.workflow.transform._feature_siblings",
        lambda _: [SimpleNamespace(_name="Existing")],
    )

    with pytest.raises(ValueError, match="A feature named 'Existing' already exists"):
        _copy_name(feature, "Existing")


@pytest.mark.parametrize(
    ("feature", "error", "message"),
    [
        pytest.param(
            "unsupported",
            TypeError,
            "Unsupported feature type: str",
            id="unsupported-feature",
        ),
        pytest.param(
            face.Face(speos_client=None, name="Standalone"),
            ValueError,
            "Transforming a standalone Face is not supported",
            id="standalone-face",
        ),
        pytest.param(
            object.__new__(source.BaseSource),
            TypeError,
            "BaseSource does not expose an axis_system to transform",
            id="source-without-axis-system",
        ),
    ],
)
def test_prepare_transform_rejects_unsupported_feature(feature, error, message):
    """Reject feature types that cannot be transformed before touching their state."""
    with pytest.raises(error, match=message):
        _prepare_transform(feature, copy_feature=False, name=None)


def test_copy_feature_rejects_unsupported_feature():
    """Reject unsupported feature types at the copy-dispatch boundary."""
    with pytest.raises(TypeError, match="Unsupported feature type: object"):
        _copy_feature(object(), "Copy")


def test_prepare_transform_rejects_name_without_copy():
    """Only accept explicit names for copied features."""
    feature = object.__new__(source.SourceLuminaire)
    feature._source_instance = SimpleNamespace(luminaire_properties=SimpleNamespace(axis_system=[]))

    with pytest.raises(ValueError, match="name can only be provided when copy=True"):
        _prepare_transform(feature, copy_feature=False, name="Unexpected")


def test_prepare_transform_rejects_duplicate_copy_name(monkeypatch):
    """Reject duplicate names before attempting to construct the copied feature."""
    feature = object.__new__(source.SourceLuminaire)
    feature._name = "Original"
    feature._source_instance = SimpleNamespace(luminaire_properties=SimpleNamespace(axis_system=[]))
    monkeypatch.setattr(
        "ansys.speos.core.workflow.transform._feature_siblings",
        lambda _: [SimpleNamespace(_name="Duplicate")],
    )

    with pytest.raises(ValueError, match="A feature named 'Duplicate' already exists"):
        _prepare_transform(feature, copy_feature=True, name="Duplicate")


def test_surface_source_body_rejects_missing_geometry(monkeypatch):
    """Reject a surface source without any geometry references."""
    feature = SimpleNamespace(
        _project=SimpleNamespace(root_part=object()),
        _source_instance=object(),
    )
    monkeypatch.setattr(
        "ansys.speos.core.workflow.transform._iter_geo_path_links", lambda _: iter(())
    )

    with pytest.raises(ValueError, match="The surface source does not reference any geometry"):
        _surface_source_body(feature)


def test_surface_source_body_rejects_missing_root_part(monkeypatch):
    """Require a project root part before resolving referenced geometry paths."""
    feature = SimpleNamespace(
        _project=SimpleNamespace(root_part=None),
        _source_instance=object(),
    )
    monkeypatch.setattr(
        "ansys.speos.core.workflow.transform._iter_geo_path_links",
        lambda _: iter([("/Body/Face", False)]),
    )

    with pytest.raises(
        ValueError, match="Cannot resolve the surface source geometry without a project root part"
    ):
        _surface_source_body(feature)


def test_surface_source_body_rejects_unresolved_path(monkeypatch):
    """Reject referenced geometry paths that are absent from the project tree."""
    feature = SimpleNamespace(
        _project=SimpleNamespace(root_part=SimpleNamespace(_geom_features=[])),
        _source_instance=object(),
    )
    monkeypatch.setattr(
        "ansys.speos.core.workflow.transform._iter_geo_path_links",
        lambda _: iter([("/Missing/Face", False)]),
    )

    with pytest.raises(ValueError, match="Cannot resolve surface source geometry path"):
        _surface_source_body(feature)


def test_surface_source_body_rejects_references_to_multiple_bodies(monkeypatch):
    """Require a full surface source to target geometry from exactly one body."""
    feature = SimpleNamespace(
        _project=SimpleNamespace(root_part=object()),
        _source_instance=object(),
    )
    bodies = iter([object(), object()])
    monkeypatch.setattr(
        "ansys.speos.core.workflow.transform._iter_geo_path_links",
        lambda _: iter([("/Body1/Face", False), ("/Body2/Face", False)]),
    )
    monkeypatch.setattr(
        "ansys.speos.core.workflow.transform._find_body_in_geometry_tree",
        lambda *_: next(bodies),
    )

    with pytest.raises(
        ValueError, match="A full surface source must reference geometry from exactly one body"
    ):
        _surface_source_body(feature)


def test_surface_source_body_rejects_another_source_on_target_body(monkeypatch):
    """Prevent transforming geometry also referenced by a different source."""
    source_instance = object()
    other_instance = object()
    feature = SimpleNamespace(
        _project=None,
        _source_instance=source_instance,
    )
    other_source = SimpleNamespace(_source_instance=other_instance)
    body_feature = SimpleNamespace(
        _name="Body",
        geo_path=SimpleNamespace(to_native_link=lambda: "/Body"),
    )
    feature._project = SimpleNamespace(root_part=object(), sources=[feature, other_source])

    def geometry_paths(message):
        if message is source_instance:
            return iter([("/Body/Face", False)])
        if message is other_instance:
            return iter([("/Body/OtherFace", False)])
        return iter(())

    monkeypatch.setattr("ansys.speos.core.workflow.transform._iter_geo_path_links", geometry_paths)
    monkeypatch.setattr(
        "ansys.speos.core.workflow.transform._find_body_in_geometry_tree",
        lambda *_: body_feature,
    )

    with pytest.raises(
        ValueError, match="Cannot transform body 'Body':another source is applied to it"
    ):
        _surface_source_body(feature)


def test_copy_surface_geometry_rejects_missing_geometry(monkeypatch):
    """Reject copying a surface source that has no referenced geometry."""
    feature = SimpleNamespace(_source_instance=object())
    original_body = SimpleNamespace(
        geo_path=SimpleNamespace(to_native_link=lambda: "/Body"),
        faces=[],
    )
    body_copy = SimpleNamespace(
        geo_path=SimpleNamespace(to_native_link=lambda: "/Body_copy"),
        faces=[],
    )
    monkeypatch.setattr(
        "ansys.speos.core.workflow.transform._iter_geo_path_links", lambda _: iter(())
    )

    with pytest.raises(ValueError, match="The surface source does not reference any geometry"):
        _copy_surface_geometry(feature, original_body, body_copy)
