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

"""Provides the Speos ``*.ray`` input file format."""

from __future__ import annotations

import math
from pathlib import Path
import struct
from typing import ClassVar, List, Optional, Tuple, Union

import numpy as np

from ansys.speos.core.input_files._base import (
    ENCODING,
    NEWLINE,
    SpeosFileFormat,
    _finite_number,
    _numeric_tuple,
    _property_name,
    _ValueComparable,
    format_number,
)


class Ray(_ValueComparable):
    """Single ray of a Speos ray file.

    Parameters
    ----------
    position : Tuple[float, float, float], optional
        Cartesian coordinates the ray starts from, in mm. By default, ``(0.0, 0.0, 0.0)``.
    direction : Tuple[float, float, float], optional
        Direction cosines ``(l, m, n)`` of the ray, which must be a unit vector.
        By default, ``(0.0, 0.0, 1.0)``.
    wavelength : float, optional
        Wavelength of the ray, in nm. By default, ``555.0``.
    energy : float, optional
        Relative radiometric energy of the ray, between 0 and 1. The absolute flux of the
        ray is its share of the total flux of the file. By default, ``1.0``.
    polarization : Optional[Tuple[float, float, float, float, float]], optional
        Polarization ``(o, p, q, r, s)``, where ``(o, p, q)`` is the normalized big axis
        of the polarization ellipse, ``r`` the ratio of its small axis over its big axis
        and ``s`` the handedness, ``0`` for right and ``1`` for left. By default,
        ``None``, for an unpolarized ray.

    Notes
    -----
    The direction cosines relate to the zenith angle theta and the azimuth angle phi
    through ``l = sin(theta) * cos(phi)``, ``m = sin(theta) * sin(phi)`` and
    ``n = cos(theta)``.
    Vector setters store finite immutable tuples. The direction must already be normalized
    within a tolerance of 1e-3 when constructing or updating a ray; it is not normalized
    automatically.
    """

    def __init__(
        self,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        direction: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        wavelength: float = 555.0,
        energy: float = 1.0,
        polarization: Optional[Tuple[float, float, float, float, float]] = None,
    ) -> None:
        self.position = position
        self.direction = direction
        self.wavelength = wavelength
        self.energy = energy
        self.polarization = polarization

    @property
    def position(self) -> Tuple[float, ...]:
        """Starting coordinates in mm.

        Returns
        -------
        Tuple[float, ...]
            Three finite Cartesian coordinates.
        """
        return self._position

    @position.setter
    def position(self, values: Tuple[float, float, float]) -> None:
        self._position = _numeric_tuple(_property_name(Ray.position), values)

    @property
    def direction(self) -> Tuple[float, ...]:
        """Direction cosines of the ray.

        Returns
        -------
        Tuple[float, ...]
            Three finite coordinates with unit norm within 1e-3.
        """
        return self._direction

    @direction.setter
    def direction(self, values: Tuple[float, float, float]) -> None:
        direction = _numeric_tuple(_property_name(Ray.direction), values)
        self._check_direction(direction)
        self._direction = direction

    @staticmethod
    def _check_direction(values: Tuple[float, ...]) -> None:
        norm = math.hypot(*values)
        if abs(norm - 1.0) > 1e-3:
            raise ValueError(
                f"direction must be a unit vector of direction cosines, got a norm of {norm}."
            )

    @property
    def wavelength(self) -> float:
        """Wavelength of the ray, in nm.

        Returns
        -------
        float
            Finite wavelength.
        """
        return self._wavelength

    @wavelength.setter
    def wavelength(self, value: float) -> None:
        self._wavelength = _finite_number(_property_name(Ray.wavelength), value)

    @property
    def energy(self) -> float:
        """Relative radiometric energy.

        Returns
        -------
        float
            Finite relative energy.
        """
        return self._energy

    @energy.setter
    def energy(self, value: float) -> None:
        self._energy = _finite_number(_property_name(Ray.energy), value)

    @property
    def polarization(self) -> Optional[Tuple[float, ...]]:
        """Polarization ellipse parameters.

        Returns
        -------
        Optional[Tuple[float, ...]]
            Five finite parameters, or None for an unpolarized ray.
        """
        return self._polarization

    @polarization.setter
    def polarization(self, values: Optional[Tuple[float, float, float, float, float]]) -> None:
        self._polarization = (
            None if values is None else _numeric_tuple(_property_name(Ray.polarization), values, 5)
        )

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(position),
        _property_name(direction),
        _property_name(wavelength),
        _property_name(energy),
        _property_name(polarization),
    )

    def validate(self) -> None:
        """Check that the ray direction retains its unit norm.

        Raises
        ------
        ValueError
            If the direction is not a unit vector.
        """
        self._check_direction(self._direction)


class RayFile(SpeosFileFormat):
    """Speos ray file, holding the rays emitted by a measured or simulated source.

    :meth:`save` and :meth:`load` handle the binary ``*.ray`` flavor, while
    :meth:`save_text` and :meth:`load_text` handle the text flavor that the Speos ray file
    editors also accept.

    Parameters
    ----------
    rays : List[Ray], optional
        Rays of the file. By default, ``[]``.
    radiant_flux : float, optional
        Total radiant flux of the file, in W. By default, ``1.0``.
    luminous_flux : float, optional
        Total luminous flux of the file, in lm. By default, ``683.0``.

    Notes
    -----
    The binary layout is 7 little-endian 32-bit floats, the total radiant flux followed by
    5 format markers and the total luminous flux, then 8 floats per ray: the position, the
    direction cosines, the wavelength and the energy. The text flavor does not carry any
    flux, so :meth:`load_text` leaves :attr:`radiant_flux` and :attr:`luminous_flux` at
    their default.
    The :attr:`rays` getter copies the container but keeps ray objects shared. Assign an
    edited list back to replace rays. An empty list permits a draft but cannot be saved.
    Polarization consistency across rays is required by :meth:`save_text` only.

    Examples
    --------
    >>> from ansys.speos.core.input_files.ray_file import Ray, RayFile
    >>> rays = [Ray(position=(0.0, 0.0, 0.0), direction=(0.0, 0.0, 1.0), wavelength=633.0)]
    >>> RayFile(rays=rays, radiant_flux=1.0, luminous_flux=112.0).save("laser.ray")
    """

    def __init__(
        self, rays: List[Ray] | None = None, radiant_flux: float = 1.0, luminous_flux: float = 683.0
    ) -> None:
        self.rays = rays if rays is not None else []
        self.radiant_flux = radiant_flux
        self.luminous_flux = luminous_flux

    @property
    def rays(self) -> List[Ray]:
        """Ray collection with a copied container and shared rays.

        Returns
        -------
        List[Ray]
            Editable validated ray objects.
        """
        return self._rays.copy()

    @rays.setter
    def rays(self, values: List[Ray]) -> None:
        values = list(values)
        for ray in values:
            if not isinstance(ray, Ray):
                raise TypeError("rays must contain Ray objects.")
            ray.validate()
        self._rays = values

    @property
    def radiant_flux(self) -> float:
        """Total radiant flux, in W.

        Returns
        -------
        float
            Finite radiant flux.
        """
        return self._radiant_flux

    @radiant_flux.setter
    def radiant_flux(self, value: float) -> None:
        self._radiant_flux = _finite_number(_property_name(RayFile.radiant_flux), value)

    @property
    def luminous_flux(self) -> float:
        """Total luminous flux, in lm.

        Returns
        -------
        float
            Finite luminous flux.
        """
        return self._luminous_flux

    @luminous_flux.setter
    def luminous_flux(self, value: float) -> None:
        self._luminous_flux = _finite_number(_property_name(RayFile.luminous_flux), value)

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(rays),
        _property_name(radiant_flux),
        _property_name(luminous_flux),
    )

    EXTENSION = ".ray"

    _HEADER_MARKERS: ClassVar[Tuple[float, ...]] = (2.0, 2.0, 2.0, 2.0, 2.0)
    _HEADER_FORMAT: ClassVar[str] = "<7f"
    _RAY_VALUE_COUNT: ClassVar[int] = 8

    def validate(self) -> None:
        """Check the rays against the constraints of the ray file formats.

        Raises
        ------
        ValueError
            If the file holds no ray, or if a ray direction is not a unit vector.
        """
        if not self._rays:
            raise ValueError("A ray file must hold at least one ray.")
        for ray in self._rays:
            ray.validate()

    def _encode(self, path: Path) -> None:
        values = np.empty((len(self._rays), self._RAY_VALUE_COUNT), dtype="<f4")
        for index, ray in enumerate(self._rays):
            values[index] = (*ray.position, *ray.direction, ray.wavelength, ray.energy)
        header = struct.pack(
            self._HEADER_FORMAT, self.radiant_flux, *self._HEADER_MARKERS, self.luminous_flux
        )
        with path.open("wb") as file:
            file.write(header)
            file.write(values.tobytes())

    @classmethod
    def _decode(cls, path: Path) -> RayFile:
        content = path.read_bytes()
        header_size = struct.calcsize(cls._HEADER_FORMAT)
        payload = content[header_size:]
        record_size = 4 * cls._RAY_VALUE_COUNT
        if len(content) < header_size or len(payload) % record_size:
            raise ValueError(f"{path} is not a binary Speos ray file.")

        header = struct.unpack(cls._HEADER_FORMAT, content[:header_size])
        values = np.frombuffer(payload, dtype="<f4").reshape(-1, cls._RAY_VALUE_COUNT)
        rays = [
            Ray(
                position=(float(row[0]), float(row[1]), float(row[2])),
                direction=(float(row[3]), float(row[4]), float(row[5])),
                wavelength=float(row[6]),
                energy=float(row[7]),
            )
            for row in values
        ]
        return cls(rays=rays, radiant_flux=header[0], luminous_flux=header[6])

    def save_text(self, file_path: Union[str, Path]) -> Path:
        """Write the rays to a text ray file.

        Each ray takes one line, ``index x y z l m n wavelength energy``, extended with
        ``o p q r s`` when the rays are polarized. The line count opens the file.

        Parameters
        ----------
        file_path : Union[str, pathlib.Path]
            Path of the file to write. An existing file is overwritten.

        Returns
        -------
        pathlib.Path
            Path of the written file.

        Raises
        ------
        ValueError
            If the rays are invalid, or if only some of them carry a polarization.
        """
        self.validate()
        polarized = [ray.polarization is not None for ray in self._rays]
        if any(polarized) and not all(polarized):
            raise ValueError("Either every ray or no ray at all must carry a polarization.")

        lines = [str(len(self._rays))]
        for index, ray in enumerate(self._rays):
            values = [*ray.position, *ray.direction, ray.wavelength, ray.energy]
            if ray.polarization is not None:
                values.extend(ray.polarization)
            lines.append(" ".join([str(index + 1), *(format_number(value) for value in values)]))

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(NEWLINE.join(lines) + NEWLINE, encoding=ENCODING, newline="")
        return path

    @classmethod
    def load_text(cls, file_path: Union[str, Path]) -> RayFile:
        """Read a text ray file.

        Parameters
        ----------
        file_path : Union[str, pathlib.Path]
            Path of the file to read.

        Returns
        -------
        ansys.speos.core.input_files.ray_file.RayFile
            Ray file model. The flux is not carried by the text flavor, so
            :attr:`radiant_flux` and :attr:`luminous_flux` keep their default value.

        Raises
        ------
        FileNotFoundError
            If ``file_path`` does not point to an existing file.
        ValueError
            If the declared ray count does not match the file content, or a ray line does
            not hold 9 values, or 14 values when polarized.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"No such file: {path}")

        lines = [line for line in path.read_text(encoding=ENCODING).splitlines() if line.strip()]
        if not lines:
            raise ValueError(f"{path} is empty.")

        ray_count = int(float(lines[0].strip()))
        if len(lines) - 1 != ray_count:
            raise ValueError(
                f"{path} declares {ray_count} rays but holds {len(lines) - 1} ray lines."
            )

        rays = []
        for number, line in enumerate(lines[1:], start=1):
            values = [float(token) for token in line.split()]
            if len(values) not in (9, 14):
                raise ValueError(
                    f"{path}, ray {number}: expected 9 values, or 14 when polarized, got "
                    f"{len(values)}."
                )
            rays.append(
                Ray(
                    position=(values[1], values[2], values[3]),
                    direction=(values[4], values[5], values[6]),
                    wavelength=values[7],
                    energy=values[8],
                    polarization=(
                        (values[9], values[10], values[11], values[12], values[13])
                        if len(values) == 14
                        else None
                    ),
                )
            )
        return cls(rays=rays)
