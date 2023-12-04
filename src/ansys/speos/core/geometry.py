"""Provides some classes needed for geometry."""


class AxisSystem:
    def __init__(
        self,
        origin: list[float] = [0, 0, 0],
        x_vect: list[float] = [1, 0, 0],
        y_vect: list[float] = [0, 1, 0],
        z_vect: list[float] = [0, 0, 1],
    ) -> None:
        self.origin = origin
        self.x_vect = x_vect
        self.y_vect = y_vect
        self.z_vect = z_vect


class AxisPlane:
    def __init__(
        self,
        origin: list[float] = [0, 0, 0],
        x_vect: list[float] = [1, 0, 0],
        y_vect: list[float] = [0, 1, 0],
    ) -> None:
        self.origin = origin
        self.x_vect = x_vect
        self.y_vect = y_vect


class GeoPaths:
    def __init__(self, geo_paths: list[str]) -> None:
        self.geo_paths = geo_paths


class GeoPathReverseNormal:
    def __init__(self, geo_path: str, reverse_normal: bool = False) -> None:
        self.geo_path = geo_path
        self.reverse_normal = reverse_normal
