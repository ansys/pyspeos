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

from dataclasses import dataclass, field
from pathlib import Path
import struct
from typing import ClassVar, List, Optional, Tuple, Union

import numpy as np

from ansys.speos.core.input_files._base import ENCODING, NEWLINE, SpeosFileFormat, format_number


@dataclass
class Ray:
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
    """

    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    direction: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    wavelength: float = 555.0
    energy: float = 1.0
    polarization: Optional[Tuple[float, float, float, float, float]] = None


@dataclass
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

    Examples
    --------
    >>> from ansys.speos.core.input_files.ray_file import Ray, RayFile
    >>> rays = [Ray(position=(0.0, 0.0, 0.0), direction=(0.0, 0.0, 1.0), wavelength=633.0)]
    >>> RayFile(rays=rays, radiant_flux=1.0, luminous_flux=112.0).save("laser.ray")
    """

    rays: List[Ray] = field(default_factory=list)
    radiant_flux: float = 1.0
    luminous_flux: float = 683.0

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
        if not self.rays:
            raise ValueError("A ray file must hold at least one ray.")
        for index, ray in enumerate(self.rays):
            norm = float(np.linalg.norm(ray.direction))
            if abs(norm - 1.0) > 1e-3:
                raise ValueError(
                    f"Ray {index + 1}: direction must be a unit vector of direction cosines, "
                    f"got a norm of {norm}."
                )

    def _encode(self, path: Path) -> None:
        values = np.empty((len(self.rays), self._RAY_VALUE_COUNT), dtype="<f4")
        for index, ray in enumerate(self.rays):
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
        polarized = [ray.polarization is not None for ray in self.rays]
        if any(polarized) and not all(polarized):
            raise ValueError("Either every ray or no ray at all must carry a polarization.")

        lines = [str(len(self.rays))]
        for index, ray in enumerate(self.rays):
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
