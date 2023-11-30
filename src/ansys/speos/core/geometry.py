"""Provides some classes needed for geometry."""


class CoordSys:
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
