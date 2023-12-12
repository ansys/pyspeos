"""Provides some classes needed for geometry."""
from typing import List, Optional


class AxisSystem:
    """
    Represents an axis system.

    Parameters
    ----------
    origin : List[float], optional
        Origin of the axis system.
        By default, ``[0, 0, 0]``.
    x_vect : List[float], optional
        X vector of the axis system.
        By default, ``[1, 0, 0]``.
    y_vect : List[float], optional
        Y vector of the axis system.
        By default, ``[0, 1, 0]``.
    z_vect : List[float], optional
        Z vector of the axis system.
        By default, ``[0, 0, 1]``.
    """

    def __init__(
        self,
        origin: Optional[List[float]] = [0, 0, 0],
        x_vect: Optional[List[float]] = [1, 0, 0],
        y_vect: Optional[List[float]] = [0, 1, 0],
        z_vect: Optional[List[float]] = [0, 0, 1],
    ) -> None:
        self.origin = origin
        self.x_vect = x_vect
        self.y_vect = y_vect
        self.z_vect = z_vect


class AxisPlane:
    """
    Represents an axis plane.

    Parameters
    ----------
    origin : List[float], optional
        Origin of the axis plane.
        By default, ``[0, 0, 0]``.
    x_vect : List[float], optional
        X vector of the axis plane.
        By default, ``[1, 0, 0]``.
    y_vect : List[float], optional
        Y vector of the axis plane.
        By default, ``[0, 1, 0]``.
    """

    def __init__(
        self,
        origin: Optional[List[float]] = [0, 0, 0],
        x_vect: Optional[List[float]] = [1, 0, 0],
        y_vect: Optional[List[float]] = [0, 1, 0],
    ) -> None:
        self.origin = origin
        self.x_vect = x_vect
        self.y_vect = y_vect


class GeoPaths:
    """
    GeoPaths allows to point to geometries (parts, bodies, faces).

    A geometry path:
    In the format : <sub-scene name>/<sub-part name>/<body name>/<face name> (no name by default for root scene and root part).
    "body1/face1" -> face1 in body1 of the root part in the root scene
    "subPart1" -> subPart1 of the root part in the root scene
    "subScene1" -> root part in the subScene1
    "subScene1/subPart2" -> subPart2 of the root part in the subScene1

    Parameters
    ----------
    geo_paths : List[str], optional
        List of geometry paths.
        By default, ``[]``, equivalent to "All geometries".
    """

    def __init__(self, geo_paths: Optional[List[str]] = []) -> None:
        self.geo_paths = geo_paths


class GeoPathWithReverseNormal:
    """
    GeoPathWithReverseNormal allows to point to geometry (part, body, face), with precising reverse to normal.
    Used for example in Surface Source Instance.
    Reverse to normal precise then if the ray's propagation direction is on the side following the normal, or if we want to reverse.

    A geometry path:
    In the format : <sub-scene name>/<sub-part name>/<body name>/<face name> (no name by default for root scene and root part).
    "body1/face1" -> face1 in body1 of the root part in the root scene
    "subPart1" -> subPart1 of the root part in the root scene
    "subScene1" -> root part in the subScene1
    "subScene1/subPart2" -> subPart2 of the root part in the subScene1

    Parameters
    ----------
    geo_path : List[str], optional
        geometry path.
        By default, ``""``, equivalent to "All geometries".
    reverse_normal : bool, optional
        Ray's propagation direction on the side following the normal (False), or reversed (True).
        By default, ``False``.
    """

    def __init__(self, geo_path: Optional[str] = "", reverse_normal: Optional[bool] = False) -> None:
        self.geo_path = geo_path
        self.reverse_normal = reverse_normal
