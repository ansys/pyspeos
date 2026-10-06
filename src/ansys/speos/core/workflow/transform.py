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

"""Workflow helpers for transforming Speos features."""

from __future__ import annotations

from copy import copy
import math
from typing import Union

import numpy as np

from ansys.speos.core import body as body_module
from ansys.speos.core import component, face as face_module, part, sensor, source
from ansys.speos.core.kernel.scene import ProtoScene

TransformableFeature = Union[
    source.BaseSource,
    sensor.BaseSensor,
    component.LightBox,
    part.Part.SubPart,
    body_module.Body,
]


def _validate_vector3(value: list[float], name: str) -> np.ndarray:
    """Validate and convert a three-dimensional vector."""
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{name} must be a list or tuple of three finite numbers.")
    if len(value) != 3:
        raise ValueError(f"{name} must contain exactly three values.")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise TypeError(f"{name} values must be numeric.")
    vector = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} values must be finite.")
    return vector


def _validate_axis_system12(value: list[float], name: str) -> np.ndarray:
    """Validate and convert a twelve-value axis system."""
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{name} must be a list or tuple of twelve finite numbers.")
    if len(value) != 12:
        raise ValueError(f"{name} must contain exactly twelve values.")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise TypeError(f"{name} values must be numeric.")
    axis_system = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(axis_system)):
        raise ValueError(f"{name} values must be finite.")
    return axis_system


def _validate_scalar(value: float, name: str) -> float:
    """Validate and convert a finite scalar."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite number.")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return float(value)


def _normalize(vector: np.ndarray, name: str) -> np.ndarray:
    """Return a normalized vector, rejecting zero-length input."""
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise ValueError(f"{name} must not be a zero vector.")
    return vector / norm


def _rotation_matrix(axis: np.ndarray, angle_deg: float) -> np.ndarray:
    """Return the rotation matrix for a right-handed rotation in degrees."""
    x, y, z = _normalize(axis, "axis")
    angle = math.radians(angle_deg)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return np.array(
        [
            [cosine + x * x * (1 - cosine), x * y * (1 - cosine) - z * sine,
             x * z * (1 - cosine) + y * sine],
            [y * x * (1 - cosine) + z * sine, cosine + y * y * (1 - cosine),
             y * z * (1 - cosine) - x * sine],
            [z * x * (1 - cosine) - y * sine, z * y * (1 - cosine) + x * sine,
             cosine + z * z * (1 - cosine)],
        ]
    )


def _axis_frame(axis_system: np.ndarray, name: str) -> tuple[np.ndarray, np.ndarray]:
    """Return origin and rotation matrix from a rigid axis system."""
    origin = axis_system[:3]
    rotation = axis_system[3:].reshape(3, 3).T
    if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6) or not np.isclose(
        np.linalg.det(rotation), 1.0, atol=1e-6
    ):
        raise ValueError(f"{name} must contain an orthonormal, right-handed coordinate frame.")
    return origin, rotation


def _get_parent(feature: TransformableFeature):
    """Get the project or geometry parent that owns a feature."""
    if isinstance(feature, component.LightBox):
        return feature._parent_project
    if isinstance(feature, (source.BaseSource, sensor.BaseSensor)):
        return feature._project
    if isinstance(feature, (part.Part.SubPart, body_module.Body)):
        return feature._parent_part
    return None


def _get_name(feature: TransformableFeature) -> str:
    """Get a feature's local name."""
    return feature._name


def _feature_siblings(feature: TransformableFeature) -> list:
    """Return the collection in which a copied feature name must be unique."""
    parent = _get_parent(feature)
    if parent is None:
        return []
    return parent._features if isinstance(feature, (component.LightBox, source.BaseSource, sensor.BaseSensor)) else parent._geom_features


def _copy_name(feature: TransformableFeature, name: str | None) -> str:
    """Choose and validate a unique name for a copied feature."""
    siblings = _feature_siblings(feature)
    names = {_get_name(item) for item in siblings}
    original_name = _get_name(feature)
    if name is not None:
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string.")
        if name in names:
            raise ValueError(f"A feature named {name!r} already exists.")
        return name
    candidate = f"{original_name}_copy"
    suffix = 2
    while candidate in names:
        candidate = f"{original_name}_copy_{suffix}"
        suffix += 1
    return candidate


def _copy_axis_feature(feature: TransformableFeature, name: str) -> TransformableFeature:
    """Duplicate an axis-system feature and add it to its owning project."""
    copied = copy(feature)
    copied._name = name
    if isinstance(feature, source.BaseSource):
        copied._source_instance = ProtoScene.SourceInstance()
        copied._source_instance.CopyFrom(feature._source_instance)
        copied._source_instance.name = name
        copied._source_instance.metadata.pop("UniqueId", None)
        copied._source_instance.source_guid = ""
        copied._source_template = type(feature._source_template)()
        copied._source_template.CopyFrom(feature._source_template)
        copied._source_template.name = name
        copied.source_template_link = None
        copied._unique_id = None
        copied._fill_parameters(default_parameters=None)
        feature._project._features.append(copied)
    elif isinstance(feature, sensor.BaseSensor):
        copied._sensor_instance = ProtoScene.SensorInstance()
        copied._sensor_instance.CopyFrom(feature._sensor_instance)
        copied._sensor_instance.name = name
        copied._sensor_instance.metadata.pop("UniqueId", None)
        copied._sensor_instance.sensor_guid = ""
        copied._sensor_template = type(feature._sensor_template)()
        copied._sensor_template.CopyFrom(feature._sensor_template)
        copied._sensor_template.name = name
        copied.sensor_template_link = None
        copied._unique_id = None
        copied._fill_parameters(default_parameters=None)
        feature._project._features.append(copied)
    elif isinstance(feature, part.Part.SubPart):
        parent = feature._parent_part
        copied = parent.create_sub_part(name=name, description=feature._part_instance.description)
        copied._part.CopyFrom(feature._part)
        if feature.part_link is not None:
            copied.part_link = feature.part_link
            copied._part_instance.part_guid = feature.part_link.key
        copied._part_instance.CopyFrom(feature._part_instance)
        copied._part_instance.name = name
        copied._part_instance.description = ""
        copied._part_instance.metadata.pop("UniqueId", None)
        copied._unique_id = None
    elif isinstance(feature, component.LightBox):
        instance = ProtoScene.SceneInstance()
        instance.CopyFrom(feature._scene_instance)
        instance.name = name
        instance.metadata.pop("UniqueId", None)
        instance.metadata["UniqueId"] = "pending"
        copied = component.LightBox(name=name, parent_project=feature._parent_project, instance=instance)
        copied._scene_instance.name = name
        copied._scene_instance.metadata.pop("UniqueId", None)
        copied._unique_id = None
        feature._parent_project._features.append(copied)
    return copied


def _copy_body(feature: body_module.Body, name: str) -> body_module.Body:
    """Duplicate a body and its faces."""
    parent = feature._parent_part
    copied = body_module.Body(
        speos_client=feature._speos_client,
        name=name,
        description=feature._body.description,
        metadata=feature._body.metadata,
        parent_part=parent,
    )
    if parent is not None:
        parent._geom_features.append(copied)
    for face in feature.faces:
        face_copy = copied.create_face(
            name=face._name,
            description=face._face.description,
            metadata=face._face.metadata,
        )
        face_copy._face.CopyFrom(face._face)
    return copied


def _copy_feature(feature: TransformableFeature, name: str) -> TransformableFeature:
    """Return a copy of a supported feature."""
    if isinstance(feature, body_module.Body):
        return _copy_body(feature, name)
    return _copy_axis_feature(feature, name)


def _transform_mesh(body: body_module.Body, rotation: np.ndarray, translation: np.ndarray) -> None:
    """Transform all mesh vertices and normals in a body."""
    for face in body.faces:
        vertices = np.asarray(face._face.vertices, dtype=float).reshape(-1, 3)
        if vertices.size:
            transformed = (rotation @ vertices.T).T + translation
            face._face.vertices[:] = transformed.reshape(-1).tolist()
        normals = np.asarray(face._face.normals, dtype=float).reshape(-1, 3)
        if normals.size:
            transformed_normals = (rotation @ normals.T).T
            face._face.normals[:] = transformed_normals.reshape(-1).tolist()


def _apply_transform(
    feature: TransformableFeature, rotation: np.ndarray, translation: np.ndarray
) -> TransformableFeature:
    """Apply a rigid transform to a feature and commit it."""
    if isinstance(feature, body_module.Body):
        _transform_mesh(feature, rotation, translation)
    else:
        axis_system = _validate_axis_system12(feature.axis_system, "feature.axis_system")
        origin = rotation @ axis_system[:3] + translation
        axes = (rotation @ axis_system[3:].reshape(3, 3).T).T.reshape(-1)
        feature.axis_system = np.concatenate((origin, axes)).tolist()
    feature.commit()
    return feature


def _prepare_transform(
    feature: TransformableFeature, copy_feature: bool, name: str | None
) -> TransformableFeature:
    """Validate a target feature and optionally duplicate it."""
    if isinstance(feature, face_module.Face):
        raise ValueError("Transforming a standalone Face is not supported; transform its Body.")
    if not isinstance(
        feature,
        (source.BaseSource, sensor.BaseSensor, component.LightBox, part.Part.SubPart, body_module.Body),
    ):
        raise TypeError(f"Unsupported feature type: {type(feature).__name__}.")
    if not copy_feature and name is not None:
        raise ValueError("name can only be provided when copy=True.")
    if not copy_feature:
        return feature
    copied_name = _copy_name(feature, name)
    return _copy_feature(feature, copied_name)


def move_feature(
    feature: TransformableFeature,
    direction: list[float],
    distance: float,
    *,
    copy: bool = False,
    name: str | None = None,
) -> TransformableFeature:
    """Translate a source, sensor, LightBox, SubPart, or Body.

    Parameters
    ----------
    feature : TransformableFeature
        Feature to translate.
    direction : list[float]
        Direction of translation. The vector is normalized before use.
    distance : float
        Translation distance.
    copy : bool, optional
        If ``True``, return a transformed duplicate instead of changing the input.
    name : str, optional
        Name for the duplicate. Only valid when ``copy=True``.

    Returns
    -------
    TransformableFeature
        The modified feature or its transformed duplicate.

    Raises
    ------
    TypeError
        If the feature or an input vector has an unsupported type.
    ValueError
        If an input is invalid or a standalone Face is provided.
    """
    unit_direction = _normalize(_validate_vector3(direction, "direction"), "direction")
    displacement = unit_direction * _validate_scalar(distance, "distance")
    target = _prepare_transform(feature, copy, name)
    return _apply_transform(target, np.eye(3), displacement)


def rotate_feature(
    feature: TransformableFeature,
    point: list[float],
    axis: list[float],
    angle: float,
    *,
    copy: bool = False,
    name: str | None = None,
) -> TransformableFeature:
    """Rotate a source, sensor, LightBox, SubPart, or Body around an axis.

    Parameters
    ----------
    feature : TransformableFeature
        Feature to rotate.
    point : list[float]
        A point on the rotation axis.
    axis : list[float]
        Rotation axis.
    angle : float
        Rotation angle in degrees.
    copy : bool, optional
        If ``True``, return a transformed duplicate instead of changing the input.
    name : str, optional
        Name for the duplicate. Only valid when ``copy=True``.

    Returns
    -------
    TransformableFeature
        The modified feature or its transformed duplicate.

    Raises
    ------
    TypeError
        If the feature or an input vector has an unsupported type.
    ValueError
        If an input is invalid or a standalone Face is provided.
    """
    rotation_point = _validate_vector3(point, "point")
    rotation = _rotation_matrix(
        _validate_vector3(axis, "axis"), _validate_scalar(angle, "angle")
    )
    translation = rotation_point - rotation @ rotation_point
    target = _prepare_transform(feature, copy, name)
    return _apply_transform(target, rotation, translation)


def axis_to_axis_feature(
    feature: TransformableFeature,
    reference_axis: list[float],
    target_axis: list[float],
    *,
    copy: bool = False,
    name: str | None = None,
) -> TransformableFeature:
    """Move and rotate a feature by mapping one rigid coordinate frame onto another.

    Parameters
    ----------
    feature : TransformableFeature
        Feature to transform.
    reference_axis : list[float]
        Source frame in twelve-value ``[O, X, Y, Z]`` representation.
    target_axis : list[float]
        Destination frame in twelve-value ``[O, X, Y, Z]`` representation.
    copy : bool, optional
        If ``True``, return a transformed duplicate instead of changing the input.
    name : str, optional
        Name for the duplicate. Only valid when ``copy=True``.

    Returns
    -------
    TransformableFeature
        The modified feature or its transformed duplicate.

    Raises
    ------
    TypeError
        If the feature or axis-system input has an unsupported type.
    ValueError
        If an axis system is invalid or a standalone Face is provided.
    """
    reference_origin, reference_rotation = _axis_frame(
        _validate_axis_system12(reference_axis, "reference_axis"), "reference_axis"
    )
    target_origin, target_rotation = _axis_frame(
        _validate_axis_system12(target_axis, "target_axis"), "target_axis"
    )
    rotation = target_rotation @ reference_rotation.T
    translation = target_origin - rotation @ reference_origin
    target = _prepare_transform(feature, copy, name)
    return _apply_transform(target, rotation, translation)
