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
    LineReader,
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

        Parameters
        ----------
        values : Tuple[float, float, float]
            New Cartesian coordinates the ray starts from, in mm.

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

        Parameters
        ----------
        values : Tuple[float, float, float]
            New direction cosines ``(l, m, n)`` of the ray, which must be a unit vector.
            The norm must be within 1e-3 of one; the vector is not normalized automatically.

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

        Parameters
        ----------
        value : float
            New wavelength of the ray, in nm.

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

        Parameters
        ----------
        value : float
            New relative radiometric energy of the ray, between 0 and 1. The absolute flux of
            the ray is its share of the total flux of the file.

        Returns
        -------
        float
            Finite relative energy.
        """
        return self._energy

    @energy.setter
    def energy(self, value: float) -> None:
        value = _finite_number(_property_name(Ray.energy), value)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"energy must be between 0 and 1, got {value}.")
        self._energy = value

    @property
    def polarization(self) -> Optional[Tuple[float, ...]]:
        """Polarization ellipse parameters.

        Parameters
        ----------
        values : Optional[Tuple[float, float, float, float, float]]
            New polarization ``(o, p, q, r, s)``, where ``(o, p, q)`` is the normalized big axis
            of the polarization ellipse, ``r`` the ratio of its small axis over its big axis and
            ``s`` the handedness, ``0`` for right and ``1`` for left.
            Use ``None`` for an unpolarized ray.

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
    editors also accept. :meth:`save_sdf` and :meth:`load_sdf` handle Zemax spectral
    binary source files.

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
    Binary :meth:`save` rejects polarized rays; use :meth:`save_text` to retain polarization.

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

        Parameters
        ----------
        values : List[Ray]
            New rays of the file.

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

        Parameters
        ----------
        value : float
            New total radiant flux of the file, in W.

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

        Parameters
        ----------
        value : float
            New total luminous flux of the file, in lm.

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
    _SDF_HEADER: ClassVar[struct.Struct] = struct.Struct("<II100s7fI13f4I")

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
        if any(ray.polarization is not None for ray in self._rays):
            raise ValueError("Binary ray files do not support polarization; use save_text().")
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
        if header[1:6] != cls._HEADER_MARKERS:
            raise ValueError(f"{path} is not a binary Speos ray file: invalid header markers.")
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

    def save_sdf(self, file_path: Union[str, Path]) -> Path:
        """Write an unpolarized Zemax spectral binary source file.

        Parameters
        ----------
        file_path : Union[str, pathlib.Path]
            Path of the file to write. An existing file is overwritten after validation.

        Returns
        -------
        pathlib.Path
            Path of the written file.

        Raises
        ------
        ValueError
            If the rays are invalid or polarized, the radiant flux is negative, wavelengths
            are not positive, positive power has no nonzero weights, or data cannot be
            represented by the format's 32-bit floats.

        Notes
        -----
        The 208-byte little-endian header identifies spectral records in watts with
        millimeter coordinates. Each 32-byte record holds ``x y z l m n flux wavelength``.
        Wavelengths are converted from nm to micrometers. Ray energies are relative weights:
        each output flux is ``radiant_flux * energy / sum(energies)``. Zero total power
        writes zero ray fluxes. Neither the model nor its energy weights are modified.
        Luminous flux and polarization are not stored; use :meth:`save_text` for polarization.

        References
        ----------
        .. [1] `Speos and Zemax Source file converter
           <https://optics.ansys.com/hc/en-us/articles/43071106808595>`_.
        """
        self.validate()
        if any(ray.polarization is not None for ray in self._rays):
            raise ValueError("SDF files do not support polarization; use save_text().")
        flux = self.radiant_flux
        if flux < 0.0:
            raise ValueError("SDF radiant flux must be nonnegative.")
        total_weight = math.fsum(ray.energy for ray in self._rays)
        if flux > 0.0 and total_weight == 0.0:
            raise ValueError("Positive SDF radiant flux requires nonzero ray energy weights.")
        rows = []
        for ray in self._rays:
            if ray.wavelength <= 0.0:
                raise ValueError("SDF wavelengths must be positive.")
            ray_flux = flux * (ray.energy / total_weight) if total_weight else 0.0
            rows.append((*ray.position, *ray.direction, ray_flux, ray.wavelength / 1000.0))
        try:
            with np.errstate(over="raise", invalid="raise"):
                values = np.asarray(rows, dtype="<f4")
            header = self._SDF_HEADER.pack(
                1010,
                len(self._rays),
                b"Converted from Speos by PySpeos.".ljust(100, b" "),
                flux,
                flux,
                *([0.0] * 5),
                4,
                *([0.0] * 13),
                2,
                0,
                0,
                0,
            )
        except (FloatingPointError, OverflowError, struct.error) as error:
            raise ValueError("SDF data must fit finite 32-bit floats and ray counts.") from error
        if np.any(values[:, 7] <= 0.0) or (flux > 0.0 and not np.any(values[:, 6] > 0.0)):
            raise ValueError("SDF wavelengths and positive power must not underflow to zero.")
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as stream:
            stream.write(header)
            stream.write(values.tobytes())
        return path

    @classmethod
    def load_sdf(cls, file_path: Union[str, Path], *, luminous_flux: float = 683.0) -> RayFile:
        """Read a Zemax spectral binary source file in millimeter coordinates.

        Parameters
        ----------
        file_path : Union[str, pathlib.Path]
            Path of the file to read.
        luminous_flux : float, optional
            Known photometric flux in lm. By default, ``683.0``, the model's default,
            not a value inferred from the SDF spectrum.

        Returns
        -------
        ansys.speos.core.input_files.ray_file.RayFile
            Unpolarized rays with wavelengths in nm, normalized relative energy weights,
            and radiant flux from the header's ``RaySetFlux``.

        Raises
        ------
        FileNotFoundError
            If ``file_path`` does not point to an existing file.
        ValueError
            If the header, record count or ray data are invalid, coordinates are not in mm,
            the source has a nonneutral transform, or the file is not spectral radiometric SDF.

        Notes
        -----
        Identifiers ``1010`` and ``8675309`` are accepted. Monochromatic DAT and photometric
        formats are not supported. Wavelengths in micrometers are converted to nm. Record
        fluxes are normalized to relative weights; their sum need not equal ``RaySetFlux``.
        Positive ray-set power requires a positive sum of record fluxes. An all-zero set
        is represented by zero energies without dividing by zero.
        Original luminous flux, description, angular limits and ``SourceFlux`` metadata
        are not reconstructed. Re-export preserves the ray-set power and distribution,
        not arbitrary original energy scaling or header-only metadata.

        References
        ----------
        .. [1] `Converting a binary Source File into ASCII
           <https://optics.ansys.com/hc/en-us/articles/43071069319443>`_.
        """
        path = Path(file_path)
        content = path.read_bytes()
        header_size = cls._SDF_HEADER.size
        if len(content) < header_size:
            raise ValueError(f"{path}: truncated SDF header.")
        header = cls._SDF_HEADER.unpack_from(content)
        identifier, count = header[:2]
        if identifier not in (1010, 8675309):
            raise ValueError(f"{path}: invalid SDF identifier {identifier}.")
        if header[24:26] != (2, 0):
            raise ValueError(f"{path}: only spectral SDF records in watts are supported.")
        if header[10] != 4:
            raise ValueError(f"{path}: SDF coordinates must be in millimeters.")
        if not all(math.isfinite(value) for value in (*header[3:10], *header[11:24])):
            raise ValueError(f"{path}: SDF header values must be finite.")
        if any(header[11:17]) or header[17:20] not in ((0.0,) * 3, (1.0,) * 3):
            raise ValueError(f"{path}: SDF source transforms are not supported.")
        if count < 1 or len(content) != header_size + count * 32:
            raise ValueError(f"{path}: SDF ray count must be positive and match the file size.")
        if header[3] < 0.0 or header[4] < 0.0:
            raise ValueError(f"{path}: SDF header fluxes must be nonnegative.")
        values = np.frombuffer(content, dtype="<f4", offset=header_size).reshape(count, 8)
        if not np.all(np.isfinite(values)):
            raise ValueError(f"{path}: SDF ray values must be finite.")
        if np.any(values[:, 6] < 0.0) or np.any(values[:, 7] <= 0.0):
            raise ValueError(
                f"{path}: SDF ray fluxes must be nonnegative and wavelengths positive."
            )
        total_weight = math.fsum(float(value) for value in values[:, 6])
        if header[4] > 0.0 and total_weight == 0.0:
            raise ValueError(f"{path}: positive SDF ray-set flux requires nonzero record fluxes.")
        rays = []
        for number, row in enumerate(values, start=1):
            try:
                rays.append(
                    Ray(
                        position=(float(row[0]), float(row[1]), float(row[2])),
                        direction=(float(row[3]), float(row[4]), float(row[5])),
                        wavelength=float(row[7]) * 1000.0,
                        energy=float(row[6]) / total_weight if total_weight else 0.0,
                    )
                )
            except ValueError as error:
                raise ValueError(f"{path}, ray {number}: {error}") from None
        model = cls(rays=rays, radiant_flux=header[4], luminous_flux=luminous_flux)
        model.validate()
        return model

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
            If the count is not a positive integer, does not match the file content,
            or a ray line is invalid or does not hold 9 values, or 14 when polarized.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"No such file: {path}")

        lines = path.read_text(encoding=ENCODING).splitlines()
        data_line_count = sum(bool(line.strip()) for line in lines)
        if not data_line_count:
            raise ValueError(f"{path} is empty.")

        reader = LineReader(lines, path)
        ray_count = reader.next_int(minimum=1)
        if data_line_count - 1 != ray_count:
            raise ValueError(
                f"{path} declares {ray_count} rays but holds {data_line_count - 1} ray lines."
            )

        rays = []
        for number in range(1, ray_count + 1):
            values = reader.next_floats()
            if len(values) not in (9, 14):
                raise reader.error(
                    f"ray {number}: expected 9 values, or 14 when polarized, got {len(values)}."
                )
            try:
                ray = Ray(
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
            except ValueError as error:
                raise reader.error(f"ray {number}: {error}") from None
            rays.append(ray)
        model = cls(rays=rays)
        model.validate()
        return model
