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

from typing import Union

import numpy as np

from ansys.speos.core import (
    body as body_module,
    component,
    face as face_module,
    part,
    sensor,
    source,
)
from ansys.speos.core.generic.general_methods import (
    _axis_frame,
    _rotation_matrix,
    _validate_axis_system12,
    _validate_scalar,
    _validate_vector3,
    normalize_vector,
)

TransformableFeature = Union[
    source.BaseSource,
    sensor.BaseSensor,
    component.LightBox,
    part.Part.SubPart,
    body_module.Body,
]


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
    if isinstance(feature, (component.LightBox, source.BaseSource, sensor.BaseSensor)):
        return parent._features
    return parent._geom_features


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
    if isinstance(feature, source.BaseSource):
        p = feature._project
        copied = p.create_source(
            name=name, description=feature._source_instance.description, feature_type=type(feature)
        )
        copied._source_template.CopyFrom(feature._source_template)
        copied._source_template.name = name
        copied._source_instance.CopyFrom(feature._source_instance)
        copied._source_instance.name = name
        copied._unique_id = None
        copied._fill_parameters(default_parameters=None)
    elif isinstance(feature, sensor.BaseSensor):
        p = feature._project
        copied = p.create_sensor(
            name=name, description=feature._source_instance.description, feature_type=type(feature)
        )
        copied._sensor_instance.CopyFrom(feature._sensor_instance)
        copied._sensor_instance.name = name
        copied._sensor_template.CopyFrom(feature._sensor_template)
        copied._sensor_template.name = name
        copied._unique_id = None
        copied._fill_parameters(default_parameters=None)
    elif isinstance(feature, part.Part.SubPart):
        parent = feature._parent_part
        copied = parent.create_sub_part(name=name, description=feature._part_instance.description)
        copied._part.CopyFrom(feature._part)
        if feature.part_link is not None:
            copied.part_link = feature.part_link
            copied._part_instance.part_guid = feature.part_link.key
        copied._part_instance.CopyFrom(feature._part_instance)
        copied._part_instance.name = name
        copied._unique_id = None
    elif isinstance(feature, component.LightBox):
        p = feature.project
        copied = p.create_light_box(name=name, description=feature._scene_instance.description)
        copied._scene_instance.CopyFrom(feature._scene_instance)
        copied._scene_instance.name = name
        copied._scene_instance.metadata.pop("UniqueId", None)
        copied._unique_id = None
        copied.project._fill_features(context=copied._scene_instance.name + "/")
    return copied


def _copy_body_material_assignments(original: body_module.Body, copied: body_module.Body) -> None:
    """Reuse the original body material assignments on the copied body.

    The copied body receives a new geometry path, so any material instances that apply
    to the original body must also include the new path. This keeps the same material
    assignments without creating a fresh material instance.
    """
    parent = original._parent_part
    while parent is not None and not hasattr(parent, "_project"):
        parent = getattr(parent, "_parent_part", None)
    project = getattr(parent, "_project", None)
    if project is None or project.scene_link is None:
        return

    original_path = original.geo_path.to_native_link()
    copied_path = copied.geo_path.to_native_link()
    scene_data = project.scene_link.get()
    for material in scene_data.materials:
        if not material.HasField("geometries"):
            continue
        paths = list(material.geometries.geo_paths)
        if original_path not in paths or copied_path in paths:
            continue
        paths.append(copied_path)
        material.geometries.geo_paths[:] = paths
    project.scene_link.set(data=scene_data)


def _copy_body(feature: body_module.Body, name: str) -> body_module.Body:
    """Duplicate a body and its faces."""
    parent = feature._parent_part
    copied = parent.create_body(name=name, description=feature._body.description)
    for face in feature.faces:
        face_copy = copied.create_face(
            name=face._name,
            description=face._face.description,
            metadata=face._face.metadata,
        )
        face_copy._face.CopyFrom(face._face)
    _copy_body_material_assignments(feature, copied)
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
    if isinstance(feature, source.SourceSurface):
        target_body = _surface_source_body(feature)
        _transform_mesh(target_body, rotation, translation)
        target_body.commit()
        feature.commit()
        return feature
    if isinstance(feature, body_module.Body):
        _transform_mesh(feature, rotation, translation)
    else:
        axis_system = _validate_axis_system12(feature.axis_system)
        origin = rotation @ axis_system[:3] + translation
        axes = (rotation @ axis_system[3:].reshape(3, 3).T).T.reshape(-1)
        feature.axis_system = np.concatenate((origin, axes)).tolist()
    feature.commit()
    return feature


def _iter_geopaths(message):
    """Yield geometry paths from a protobuf message and its nested fields."""
    if not hasattr(message, "ListFields"):
        return
    for field, value in message.ListFields():
        if field.name == "geo_path":
            if value:
                yield value
        elif field.name == "geo_paths":
            if field.message_type is None:
                yield from (path for path in value if path)
            else:
                for item in value:
                    yield from _iter_geopaths(item)
        elif field.message_type is not None:
            values = value if field.is_repeated else (value,)
            for item in values:
                yield from _iter_geopaths(item)


def _iter_geo_path_links(message):
    """Yield ``(geo_path, reverse_normal)`` tuples from a protobuf geometry reference tree."""
    if not hasattr(message, "ListFields"):
        return
    for field, value in message.ListFields():
        if field.name == "geo_path":
            if hasattr(value, "geo_path"):
                yield value.geo_path, bool(getattr(value, "reverse_normal", False))
            elif value:
                yield value, False
        elif field.name == "geo_paths":
            if field.message_type is None:
                for path in value:
                    if path:
                        yield path, False
            else:
                for item in value:
                    yield from _iter_geo_path_links(item)
        elif field.message_type is not None:
            values = value if field.is_repeated else (value,)
            for item in values:
                yield from _iter_geo_path_links(item)


def _find_body_in_geometry_tree(parent, path_segments: list[str]) -> body_module.Body | None:
    """Find the body named by a geometry path within a part hierarchy."""
    if not path_segments:
        return None
    segment, *remaining = path_segments
    for feature in parent._geom_features:
        if feature._name != segment:
            continue
        if isinstance(feature, body_module.Body):
            if not remaining:
                return feature
            if len(remaining) == 1 and any(face._name == remaining[0] for face in feature.faces):
                return feature
        elif isinstance(feature, part.Part.SubPart):
            result = _find_body_in_geometry_tree(feature, remaining)
            if result is not None:
                return result
    return None


def _paths_share_geometry(path: str, body_path: str) -> bool:
    """Return whether a geometry path targets a body, its face, or an ancestor."""
    path_parts = tuple(segment for segment in path.split("/") if segment)
    body_parts = tuple(segment for segment in body_path.split("/") if segment)
    common_length = min(len(path_parts), len(body_parts))
    return path_parts[:common_length] == body_parts[:common_length]


def _surface_source_body(feature: source.SourceSurface, unsafe=False) -> body_module.Body:
    """Resolve a full surface source to its single referenced body."""
    project = feature._project
    root_part = project.root_part
    geometry_paths = list(_iter_geopaths(feature._source_instance))
    if not geometry_paths:
        raise ValueError("The surface source does not reference any geometry.")
    if root_part is None:
        raise ValueError("Cannot resolve the surface source geometry without a project root part.")

    bodies = []
    for geopath in geometry_paths:
        segments = [segment for segment in geopath.split("/") if segment]
        resolved_body = _find_body_in_geometry_tree(root_part, segments)
        if resolved_body is None:
            raise ValueError(f"Cannot resolve surface source geometry path {geopath!r}.")
        if resolved_body not in bodies:
            bodies.append(resolved_body)
    if len(bodies) != 1:
        raise ValueError("A full surface source must reference geometry from exactly one body.")

    target_body = bodies[0]
    # if not unsafe:
    #     body_path = target_body.geo_path.to_native_link()
    #     for other_source in project.sources:
    #         if other_source is feature:
    #             continue
    #         if any(
    #             _paths_share_geometry(geopath, body_path)
    #             for geopath in _iter_geopaths(other_source._source_instance)
    #         ):
    #             raise ValueError(
    #                 f"Cannot transform body {target_body._name!r}:
    #                 another source is applied to it."
    #             )
    return target_body


def _copy_surface_geometry(feature: source.SourceSurface, body_copy: body_module.Body):
    """Map a copied surface source back to the corresponding copied face(s)."""
    target_body = _surface_source_body(feature, True)
    geometry_links = list(_iter_geo_path_links(feature._source_instance))
    if not geometry_links:
        return [(body_copy, False)]

    copied_geometries = []
    for geopath, reverse_normal in geometry_links:
        if not geopath:
            continue
        final_segment = next((segment for segment in reversed(geopath.split("/")) if segment), None)
        if final_segment == target_body._name:
            copied_target = body_copy
        else:
            copied_target = next(
                (face for face in body_copy.faces if face._name == final_segment),
                body_copy,
            )
        copied_geometries.append((copied_target, reverse_normal))
    return copied_geometries or [(body_copy, False)]


def _copy_surface_source(feature: source.SourceSurface, name: str) -> source.SourceSurface:
    """Duplicate a surface source and its referenced body for a transform copy."""
    body_target = _surface_source_body(feature)
    body_copy = _copy_body(body_target, _copy_name(body_target, None))
    source_copy = _copy_axis_feature(feature, name)
    source_copy.set_exitance_constant().geometries = _copy_surface_geometry(feature, body_copy)
    return source_copy


def _prepare_transform(
    feature: TransformableFeature, copy_feature: bool, name: str | None
) -> TransformableFeature:
    """Validate a target feature and optionally duplicate it."""
    if isinstance(feature, face_module.Face):
        raise ValueError("Transforming a standalone Face is not supported; transform its Body.")
    if isinstance(feature, source.SourceSurface):
        if copy_feature:
            copied_name = _copy_name(feature, name)
            return _copy_surface_source(feature, copied_name)
        return _surface_source_body(feature)
    if not isinstance(
        feature,
        (
            source.BaseSource,
            sensor.BaseSensor,
            component.LightBox,
            part.Part.SubPart,
            body_module.Body,
        ),
    ):
        raise TypeError(f"Unsupported feature type: {type(feature).__name__}.")
    if isinstance(feature, (source.BaseSource, sensor.BaseSensor)) and not hasattr(
        feature, "axis_system"
    ):
        raise TypeError(f"{type(feature).__name__} does not expose an axis_system to transform.")
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
    unit_direction = np.asarray(normalize_vector(_validate_vector3(direction)), dtype=float)
    displacement = unit_direction * _validate_scalar(distance)
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
    rotation_point = _validate_vector3(point)
    rotation = _rotation_matrix(_validate_vector3(axis), _validate_scalar(angle))
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
    reference_origin, reference_rotation = _axis_frame(_validate_axis_system12(reference_axis))
    target_origin, target_rotation = _axis_frame(_validate_axis_system12(target_axis))
    rotation = target_rotation @ reference_rotation.T
    translation = target_origin - rotation @ reference_origin
    target = _prepare_transform(feature, copy, name)
    return _apply_transform(target, rotation, translation)
