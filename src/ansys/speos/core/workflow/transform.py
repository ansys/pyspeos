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

from collections.abc import Iterator
from typing import TYPE_CHECKING, Union
import uuid

from google.protobuf.message import Message
import numpy as np

from ansys.speos.core import (
    body as body_module,
    component,
    face as face_module,
    opt_prop,
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
from ansys.speos.core.kernel import ProtoScene

if TYPE_CHECKING:
    from ansys.speos.core.project import Project

TransformableFeature = Union[
    source.BaseSource,
    sensor.BaseSensor,
    component.LightBox,
    part.Part.SubPart,
    body_module.Body,
]


def _owner_project(feature: TransformableFeature) -> Project:
    """Resolve the owning project, including through nested geometry parents."""
    if isinstance(feature, component.LightBox):
        return feature._parent_project
    if isinstance(feature, (source.BaseSource, sensor.BaseSensor)):
        return feature._project
    parent = feature._parent_part
    while isinstance(parent, part.Part.SubPart):
        parent = parent._parent_part
    if not isinstance(parent, part.Part):
        raise ValueError("Cannot resolve the owning project without a root part.")
    return parent._project


def _feature_siblings(feature: TransformableFeature) -> list:
    """Return the collection in which a copied feature name must be unique."""
    if isinstance(feature, (component.LightBox, source.BaseSource, sensor.BaseSensor)):
        return _owner_project(feature)._features
    return feature._parent_part._geom_features


def _copy_name(feature: TransformableFeature, name: str | None) -> str:
    """Choose and validate a unique name for a copied feature."""
    siblings = _feature_siblings(feature)
    names = {item._name for item in siblings}
    original_name = feature._name
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


def _copy_source_or_sensor(
    feature: source.BaseSource | sensor.BaseSensor, name: str
) -> source.BaseSource | sensor.BaseSensor:
    """Copy a source or sensor instance while sharing its templates."""
    project = _owner_project(feature)
    if isinstance(feature, source.BaseSource):
        new_instance = ProtoScene.SourceInstance()
        new_instance.CopyFrom(feature._source_instance)
        new_instance.metadata["UniqueId"] = str(uuid.uuid4())
        new_instance.name = name
        copied = type(feature)(
            project=project,
            name=name,
            source_instance=new_instance,
            default_parameters=None,
        )
    else:
        new_instance = ProtoScene.SensorInstance()
        new_instance.CopyFrom(feature._sensor_instance)
        new_instance.metadata["UniqueId"] = str(uuid.uuid4())
        new_instance.name = name
        copied = type(feature)(
            project=project,
            name=name,
            sensor_instance=new_instance,
            default_parameters=None,
        )
    project._features.append(copied)
    return copied


def _copy_subpart(feature: part.Part.SubPart, name: str) -> part.Part.SubPart:
    """Copy a SubPart instance and hydrate wrappers for its shared contents."""
    project = _owner_project(feature)
    copied = feature._parent_part.create_sub_part(
        name=name, description=feature._part_instance.description
    )
    copied._part.CopyFrom(feature._part)
    copied.part_link = feature.part_link
    copied._part_instance.CopyFrom(feature._part_instance)
    copied._part_instance.name = name
    copied._part_instance.metadata["UniqueId"] = str(uuid.uuid4())
    copied._unique_id = copied._part_instance.metadata["UniqueId"]
    copied._part_instance.description = "UniqueId_" + copied._unique_id
    project._fill_bodies(body_guids=copied._part.body_guids, feat_host=copied)
    project._fill_subparts(sub_parts=copied._part.parts, feat_host=copied)
    _copy_geometry_material_assignments(feature, copied)
    return copied


def _copy_lightbox(feature: component.LightBox, name: str) -> component.LightBox:
    """Copy a LightBox instance while sharing its scene contents."""
    project = _owner_project(feature)
    new_instance = ProtoScene.SceneInstance()
    new_instance.CopyFrom(feature._scene_instance)
    new_instance.name = name
    new_instance.metadata["UniqueId"] = str(uuid.uuid4())
    copied = component.LightBox(name=name, parent_project=project, instance=new_instance)
    project._features.append(copied)
    return copied


def _copy_geometry_material_assignments(
    original: body_module.Body | part.Part.SubPart,
    copied: body_module.Body | part.Part.SubPart,
) -> None:
    """Reuse material assignments on copied geometry and its descendants.

    Explicit body, face, and SubPart paths are remapped to the copied geometry.
    Ancestor and all-geometry assignments already cover the copy. Geometry must
    exist on the server before new material paths can be assigned.
    """
    project = _owner_project(original)
    if project.scene_link is None:
        return

    original_path = original.geo_path.to_native_link()
    copied_path = copied.geo_path.to_native_link()
    scene_data = project.scene_link.get()
    updated_materials = {}
    for material in scene_data.materials:
        if not material.HasField("geometries"):
            continue
        paths = list(material.geometries.geo_paths)
        additions = _remap_geometry_paths(paths, original_path, copied_path)
        additions = [path for path in additions if path not in paths]
        if additions:
            material.geometries.geo_paths.extend(additions)
            updated_materials[material.metadata["UniqueId"]] = material
    if updated_materials:
        copied.commit()
        project.scene_link.set(data=scene_data)
        for feature in project._features:
            if isinstance(feature, opt_prop.OptProp):
                instance = feature._material_instance
                material = updated_materials.get(instance.metadata.get("UniqueId"))
                if material is not None:
                    instance.geometries.CopyFrom(material.geometries)


def _remap_geometry_paths(paths: list[str], original: str, copied: str) -> list[str]:
    """Map explicit geometry and descendant paths without matching name prefixes."""
    return [
        copied + path[len(original) :]
        for path in paths
        if path == original or path.startswith(original + "/")
    ]


def _copy_body(feature: body_module.Body, name: str) -> body_module.Body:
    """Duplicate a body and its faces."""
    parent = feature._parent_part
    copied = parent.create_body(
        name=name, description=feature._body.description, metadata=feature._body.metadata
    )
    copied._body.metadata["UniqueId"] = str(uuid.uuid4())
    copied._body.metadata.pop("Internal_From_Speos_File", None)

    for face in feature.faces:
        face_copy = copied.create_face(
            name=face._name,
            description=face._face.description,
            metadata=face._face.metadata,
        )
        face_copy._face.CopyFrom(face._face)
        face_copy._face.metadata["UniqueId"] = str(uuid.uuid4())
    _copy_geometry_material_assignments(feature, copied)
    return copied


def _copy_feature(feature: TransformableFeature, name: str) -> TransformableFeature:
    """Return a copy of a supported feature."""
    if isinstance(feature, body_module.Body):
        return _copy_body(feature, name)
    if isinstance(feature, source.SourceSurface):
        return _copy_surface_source(feature, name)
    if isinstance(feature, (source.BaseSource, sensor.BaseSensor)):
        return _copy_source_or_sensor(feature, name)
    if isinstance(feature, part.Part.SubPart):
        return _copy_subpart(feature, name)
    if isinstance(feature, component.LightBox):
        return _copy_lightbox(feature, name)
    raise TypeError(f"Unsupported feature type: {type(feature).__name__}.")


def _transform_frame(
    frame: np.ndarray, rotation: np.ndarray, translation: np.ndarray
) -> list[float]:
    """Transform an origin and any number of basis vectors."""
    transformed = frame.reshape(-1, 3) @ rotation.T
    transformed[0] += translation
    return transformed.reshape(-1).tolist()


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
        if feature._source_template.surface.HasField("exitance_variable"):
            exitance = feature.set_exitance_variable()
            exitance.axis_plane = _transform_frame(
                np.asarray(exitance.axis_plane, dtype=float), rotation, translation
            )
        else:
            target_body = _surface_source_body(feature)
            _transform_mesh(target_body, rotation, translation)
            target_body.commit()
        feature.commit()
        return feature
    if isinstance(feature, body_module.Body):
        _transform_mesh(feature, rotation, translation)
    else:
        axis_system = _validate_axis_system12(feature.axis_system)
        feature.axis_system = _transform_frame(axis_system, rotation, translation)
    feature.commit()
    return feature


def _iter_geo_path_links(message: Message) -> Iterator[tuple[str, bool]]:
    """Yield ``(geo_path, reverse_normal)`` tuples from a protobuf geometry reference tree."""
    for field, value in message.ListFields():
        if field.name == "geo_path":
            if value:
                yield value, bool(getattr(message, "reverse_normal", False))
        elif field.name == "geo_paths":
            if field.message_type is None:
                for path in value:
                    if path:
                        yield path, False
            else:
                for item in value:
                    yield from _iter_geo_path_links(item)
        elif field.message_type is not None and not field.message_type.GetOptions().map_entry:
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


def _surface_source_body(feature: source.SourceSurface) -> body_module.Body:
    """Resolve a full surface source to its single referenced body."""
    project = feature._project
    root_part = project.root_part
    geometry_paths = tuple(path for path, _ in _iter_geo_path_links(feature._source_instance))
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
    body_path = target_body.geo_path.to_native_link()
    for other_source in project.sources:
        if other_source is feature:
            continue
        other_paths = tuple(path for path, _ in _iter_geo_path_links(other_source._source_instance))
        if set(other_paths) == set(geometry_paths):
            continue
        if any(_paths_share_geometry(geopath, body_path) for geopath in other_paths):
            raise ValueError(
                f"Cannot transform body {target_body._name!r}:another source is applied to it."
            )
    return target_body


def _copy_surface_geometry(
    feature: source.SourceSurface, original_body: body_module.Body, body_copy: body_module.Body
) -> list[tuple[body_module.Body | face_module.Face, bool]]:
    """Map a copied surface source back to the corresponding copied face(s)."""
    targets = {original_body.geo_path.to_native_link(): body_copy}
    copied_faces = {face._name: face for face in body_copy.faces}
    targets.update(
        (face.geo_path.to_native_link(), copied_faces[face._name])
        for face in original_body.faces
        if face._name in copied_faces
    )
    copied_geometries = []
    for geopath, reverse_normal in _iter_geo_path_links(feature._source_instance):
        if geopath not in targets:
            raise ValueError(f"Cannot map surface source geometry path {geopath!r} to its copy.")
        copied_geometries.append((targets[geopath], reverse_normal))
    if not copied_geometries:
        raise ValueError("The surface source does not reference any geometry.")
    return copied_geometries


def _copy_surface_source(feature: source.SourceSurface, name: str) -> source.SourceSurface:
    """Duplicate a surface source and any referenced body for a transform copy."""
    if feature._source_template.surface.HasField("exitance_variable"):
        return _copy_source_or_sensor(feature, name)
    body_target = _surface_source_body(feature)
    body_copy = _copy_body(body_target, _copy_name(body_target, None))
    geometries = _copy_surface_geometry(feature, body_target, body_copy)
    source_copy = _copy_source_or_sensor(feature, name)
    source_copy.set_exitance_constant().geometries = geometries
    return source_copy


def _prepare_transform(
    feature: TransformableFeature, copy_feature: bool, name: str | None
) -> TransformableFeature:
    """Validate a target feature and optionally duplicate it."""
    if isinstance(feature, face_module.Face):
        raise ValueError("Transforming a standalone Face is not supported; transform its Body.")
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
    if (
        isinstance(feature, (source.BaseSource, sensor.BaseSensor))
        and not isinstance(feature, source.SourceSurface)
        and not hasattr(feature, "axis_system")
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
        The original feature when ``copy=False``, or its transformed duplicate.
        For a surface source, the referenced body geometry (constant exitance)
        or XMP map plane (variable exitance) is transformed.

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
        The original feature when ``copy=False``, or its transformed duplicate.
        For a surface source, the referenced body geometry (constant exitance)
        or XMP map plane (variable exitance) is transformed.

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
        The original feature when ``copy=False``, or its transformed duplicate.
        For a surface source, the referenced body geometry (constant exitance)
        or XMP map plane (variable exitance) is transformed.

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
