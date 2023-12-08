"""Provides some classes needed for geometry."""
from typing import List


class AxisSystem:
    def __init__(
        self,
        origin: List[float] = [0, 0, 0],
        x_vect: List[float] = [1, 0, 0],
        y_vect: List[float] = [0, 1, 0],
        z_vect: List[float] = [0, 0, 1],
    ) -> None:
        self.origin = origin
        self.x_vect = x_vect
        self.y_vect = y_vect
        self.z_vect = z_vect


class AxisPlane:
    def __init__(
        self,
        origin: List[float] = [0, 0, 0],
        x_vect: List[float] = [1, 0, 0],
        y_vect: List[float] = [0, 1, 0],
    ) -> None:
        self.origin = origin
        self.x_vect = x_vect
        self.y_vect = y_vect


class GeoPaths:
    def __init__(self, geo_paths: List[str] = []) -> None:
        self.geo_paths = geo_paths


class GeoPathWithReverseNormal:
    def __init__(self, geo_path: str, reverse_normal: bool = False) -> None:
        self.geo_path = geo_path
        self.reverse_normal = reverse_normal
