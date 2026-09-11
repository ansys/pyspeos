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

"""Provides the Speos ``*.simplescattering`` input file format."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, List, Optional

from ansys.speos.core.input_files._base import (
    LineReader,
    SpeosTextFileFormat,
    check_percentage,
    format_number,
)


@dataclass
class SimpleScatteringSurfaceFile(SpeosTextFileFormat):
    """Speos ``*.simplescattering`` file, a scattering surface with no spectral dependency.

    The incident light is split into an absorbed part and, on each active side of the
    surface, a Lambertian, a Gaussian and a specular part. The specular part is the
    complement to 100 percent of the Lambertian and Gaussian ones.

    Parameters
    ----------
    mode : str, optional
        Sides of the surface that scatter the light: ``"Reflection"``,
        ``"Transmission"`` or ``"Both"``. By default, ``"Reflection"``.
    absorption : float, optional
        Absorbed part of the incident light, in percent. By default, ``0.0``.
    lambertian : float, optional
        Lambertian part in percent. In ``"Both"`` mode this is the reflection side.
        By default, ``0.0``.
    gaussian : float, optional
        Gaussian part in percent. In ``"Both"`` mode this is the reflection side.
        By default, ``0.0``.
    gaussian_fwhm : float, optional
        Full width at half maximum of the Gaussian lobe, in degrees. In ``"Both"`` mode
        this is the reflection side. By default, ``0.0``.
    lambertian_transmission : float, optional
        Lambertian part of the transmission side, in percent. ``"Both"`` mode only.
        By default, ``0.0``.
    gaussian_transmission : float, optional
        Gaussian part of the transmission side, in percent. ``"Both"`` mode only.
        By default, ``0.0``.
    gaussian_fwhm_transmission : float, optional
        Full width at half maximum of the transmission Gaussian lobe, in degrees.
        ``"Both"`` mode only. By default, ``0.0``.
    reflection : Optional[float], optional
        Reflected part in percent, the transmitted part being its complement to 100.
        ``"Both"`` mode only. By default, ``None``, which makes the split follow the
        Fresnel laws.
    description : str, optional
        Free text written on the second line of the file. By default,
        ``"Scattering surface"``.

    Examples
    --------
    >>> from ansys.speos.core.input_files.simple_scattering_surface import (
    ...     SimpleScatteringSurfaceFile,
    ... )
    >>> diffuser = SimpleScatteringSurfaceFile(mode="Reflection", lambertian=100.0)
    >>> diffuser.save("white_diffuser.simplescattering")
    """

    mode: str = "Reflection"
    absorption: float = 0.0
    lambertian: float = 0.0
    gaussian: float = 0.0
    gaussian_fwhm: float = 0.0
    lambertian_transmission: float = 0.0
    gaussian_transmission: float = 0.0
    gaussian_fwhm_transmission: float = 0.0
    reflection: Optional[float] = None
    description: str = "Scattering surface"

    EXTENSION = ".simplescattering"
    HEADER = "OPTIS - Simple scattering surface file v2.0"
    HEADER_PREFIX = "OPTIS - Simple scattering surface file"

    MODES: ClassVar[tuple] = ("Reflection", "Transmission", "Both")
    """Accepted values of :attr:`mode`."""

    @property
    def fresnel(self) -> bool:
        """Whether the reflection and transmission split follows the Fresnel laws.

        Returns
        -------
        bool
            ``True`` when :attr:`reflection` is ``None``.
        """
        return self.reflection is None

    def validate(self) -> None:
        """Check the surface against the constraints of the ``*.simplescattering`` format.

        Raises
        ------
        ValueError
            If :attr:`mode` is unknown, a percentage is outside the 0 to 100 range, or the
            Lambertian and Gaussian parts of a side sum to more than 100 percent.
        """
        if self.mode not in self.MODES:
            raise ValueError(f"mode must be one of {self.MODES}, got {self.mode!r}.")
        check_percentage("absorption", self.absorption)
        self._check_side("", self.lambertian, self.gaussian)
        if self.mode != "Both":
            return
        self._check_side("_transmission", self.lambertian_transmission, self.gaussian_transmission)
        if self.reflection is not None:
            check_percentage("reflection", self.reflection)

    @staticmethod
    def _check_side(suffix: str, lambertian: float, gaussian: float) -> None:
        check_percentage(f"lambertian{suffix}", lambertian)
        check_percentage(f"gaussian{suffix}", gaussian)
        if lambertian + gaussian > 100.0:
            raise ValueError(
                f"lambertian{suffix} and gaussian{suffix} must not sum to more than 100, "
                f"got {lambertian + gaussian}."
            )

    def _to_lines(self) -> List[str]:
        lines = [self.description, self.mode]
        if self.mode != "Both":
            lines.append(
                " ".join(
                    format_number(value)
                    for value in (
                        self.absorption,
                        self.lambertian,
                        self.gaussian,
                        self.gaussian_fwhm,
                    )
                )
            )
            return lines

        lines.append("")
        lines.append(
            " ".join(
                format_number(value)
                for value in (
                    self.absorption,
                    self.lambertian,
                    self.lambertian_transmission,
                    self.gaussian,
                    self.gaussian_transmission,
                )
            )
        )
        lines.append(
            f"{format_number(self.gaussian_fwhm)} {format_number(self.gaussian_fwhm_transmission)}"
        )
        lines.append("1" if self.fresnel else "0")
        if not self.fresnel:
            lines.append(format_number(self.reflection))
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> SimpleScatteringSurfaceFile:
        description = reader.next_line()
        mode = reader.next_data_line()
        if mode not in cls.MODES:
            raise reader.error(f"expected one of {cls.MODES}, got {mode!r}.")

        if mode != "Both":
            absorption, lambertian, gaussian, fwhm = reader.next_floats(count=4)
            return cls(
                mode=mode,
                absorption=absorption,
                lambertian=lambertian,
                gaussian=gaussian,
                gaussian_fwhm=fwhm,
                description=description,
            )

        absorption, lamb_r, lamb_t, gauss_r, gauss_t = reader.next_floats(count=5)
        fwhm_r, fwhm_t = reader.next_floats(count=2)
        reflection = None if reader.next_int() else reader.next_floats(count=1)[0]
        return cls(
            mode=mode,
            absorption=absorption,
            lambertian=lamb_r,
            gaussian=gauss_r,
            gaussian_fwhm=fwhm_r,
            lambertian_transmission=lamb_t,
            gaussian_transmission=gauss_t,
            gaussian_fwhm_transmission=fwhm_t,
            reflection=reflection,
            description=description,
        )
