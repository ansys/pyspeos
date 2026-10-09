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

from typing import ClassVar, List, Optional

from ansys.speos.core.input_files._base import (
    LineReader,
    SpeosTextFileFormat,
    _finite_number,
    _percentage,
    _property_name,
    _single_line,
    check_percentage,
    format_number,
)


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

    Notes
    -----
    Setters reject invalid values before changing the model. Lower an outgoing contribution
    before increasing another in a fully allocated side budget. Transmission-side values
    remain stored outside Both mode; enabling Both validates their combined budget.

    Examples
    --------
    >>> from ansys.speos.core.input_files.simple_scattering_surface import (
    ...     SimpleScatteringSurfaceFile,
    ... )
    >>> diffuser = SimpleScatteringSurfaceFile(mode="Reflection", lambertian=100.0)
    >>> diffuser.save("white_diffuser.simplescattering")
    """

    def __init__(
        self,
        mode: str = "Reflection",
        absorption: float = 0.0,
        lambertian: float = 0.0,
        gaussian: float = 0.0,
        gaussian_fwhm: float = 0.0,
        lambertian_transmission: float = 0.0,
        gaussian_transmission: float = 0.0,
        gaussian_fwhm_transmission: float = 0.0,
        reflection: Optional[float] = None,
        description: str = "Scattering surface",
    ) -> None:
        self._lambertian = self._gaussian = 0.0
        self._lambertian_transmission = self._gaussian_transmission = 0.0
        self.mode = mode
        self.absorption = absorption
        self.lambertian = lambertian
        self.gaussian = gaussian
        self.gaussian_fwhm = gaussian_fwhm
        self.lambertian_transmission = lambertian_transmission
        self.gaussian_transmission = gaussian_transmission
        self.gaussian_fwhm_transmission = gaussian_fwhm_transmission
        self.reflection = reflection
        self.description = description

    @property
    def mode(self) -> str:
        """Active sides of the surface.

        Parameters
        ----------
        value : str
            New sides of the surface that scatter the light: ``"Reflection"``,
            ``"Transmission"`` or ``"Both"``.

        Returns
        -------
        str
            Reflection, Transmission, or Both.
        """
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        if value not in self.MODES:
            raise ValueError(f"mode must be one of {self.MODES}, got {value!r}.")
        if value == "Both":
            self._check_side(
                "_transmission", self._lambertian_transmission, self._gaussian_transmission
            )
        self._mode = value

    @property
    def absorption(self) -> float:
        """Absorbed contribution, in percent.

        Parameters
        ----------
        value : float
            New absorbed part of the incident light, in percent.

        Returns
        -------
        float
            Percentage between 0 and 100.
        """
        return self._absorption

    @absorption.setter
    def absorption(self, value: float) -> None:
        self._absorption = _percentage(
            _property_name(SimpleScatteringSurfaceFile.absorption), value
        )

    @property
    def lambertian(self) -> float:
        """Lambertian contribution of the first side, in percent.

        Parameters
        ----------
        value : float
            New lambertian part in percent. In ``"Both"`` mode this is the reflection side.

        Returns
        -------
        float
            Percentage within the side's light budget.
        """
        return self._lambertian

    @lambertian.setter
    def lambertian(self, value: float) -> None:
        value = _percentage(_property_name(SimpleScatteringSurfaceFile.lambertian), value)
        self._check_side("", value, self._gaussian)
        self._lambertian = value

    @property
    def gaussian(self) -> float:
        """Gaussian contribution of the first side, in percent.

        Parameters
        ----------
        value : float
            New gaussian part in percent. In ``"Both"`` mode this is the reflection side.

        Returns
        -------
        float
            Percentage within the side's light budget.
        """
        return self._gaussian

    @gaussian.setter
    def gaussian(self, value: float) -> None:
        value = _percentage(_property_name(SimpleScatteringSurfaceFile.gaussian), value)
        self._check_side("", self._lambertian, value)
        self._gaussian = value

    @property
    def gaussian_fwhm(self) -> float:
        """Gaussian width of the first side, in degrees.

        Parameters
        ----------
        value : float
            New full width at half maximum of the Gaussian lobe, in degrees. In ``"Both"`` mode
            this is the reflection side.

        Returns
        -------
        float
            Finite full width at half maximum.
        """
        return self._gaussian_fwhm

    @gaussian_fwhm.setter
    def gaussian_fwhm(self, value: float) -> None:
        self._gaussian_fwhm = _finite_number(
            _property_name(SimpleScatteringSurfaceFile.gaussian_fwhm), value
        )

    @property
    def lambertian_transmission(self) -> float:
        """Lambertian contribution of the second side, in percent.

        Parameters
        ----------
        value : float
            New lambertian part of the transmission side, in percent. ``"Both"`` mode only.

        Returns
        -------
        float
            Percentage used in Both mode.
        """
        return self._lambertian_transmission

    @lambertian_transmission.setter
    def lambertian_transmission(self, value: float) -> None:
        value = _percentage(
            _property_name(SimpleScatteringSurfaceFile.lambertian_transmission), value
        )
        if self._mode == "Both":
            self._check_side("_transmission", value, self._gaussian_transmission)
        self._lambertian_transmission = value

    @property
    def gaussian_transmission(self) -> float:
        """Gaussian contribution of the second side, in percent.

        Parameters
        ----------
        value : float
            New gaussian part of the transmission side, in percent. ``"Both"`` mode only.

        Returns
        -------
        float
            Percentage used in Both mode.
        """
        return self._gaussian_transmission

    @gaussian_transmission.setter
    def gaussian_transmission(self, value: float) -> None:
        value = _percentage(
            _property_name(SimpleScatteringSurfaceFile.gaussian_transmission), value
        )
        if self._mode == "Both":
            self._check_side("_transmission", self._lambertian_transmission, value)
        self._gaussian_transmission = value

    @property
    def gaussian_fwhm_transmission(self) -> float:
        """Gaussian width of the second side, in degrees.

        Parameters
        ----------
        value : float
            New full width at half maximum of the transmission Gaussian lobe, in degrees.
            ``"Both"`` mode only.

        Returns
        -------
        float
            Finite full width at half maximum.
        """
        return self._gaussian_fwhm_transmission

    @gaussian_fwhm_transmission.setter
    def gaussian_fwhm_transmission(self, value: float) -> None:
        self._gaussian_fwhm_transmission = _finite_number(
            _property_name(SimpleScatteringSurfaceFile.gaussian_fwhm_transmission), value
        )

    @property
    def reflection(self) -> Optional[float]:
        """Explicit reflection share or Fresnel splitting.

        Parameters
        ----------
        value : Optional[float]
            New reflected part in percent, the transmitted part being its complement to 100.
            ``"Both"`` mode only. Use ``None`` to follow the Fresnel laws.

        Returns
        -------
        Optional[float]
            Percentage, or None to use Fresnel laws.
        """
        return self._reflection

    @reflection.setter
    def reflection(self, value: Optional[float]) -> None:
        self._reflection = (
            None
            if value is None
            else _percentage(_property_name(SimpleScatteringSurfaceFile.reflection), value)
        )

    @property
    def description(self) -> str:
        """Single-line description.

        Parameters
        ----------
        value : str
            New free text written on the second line of the file.

        Returns
        -------
        str
            Free text written after the header.
        """
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = _single_line(value)

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(mode),
        _property_name(absorption),
        _property_name(lambertian),
        _property_name(gaussian),
        _property_name(gaussian_fwhm),
        _property_name(lambertian_transmission),
        _property_name(gaussian_transmission),
        _property_name(gaussian_fwhm_transmission),
        _property_name(reflection),
        _property_name(description),
    )

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

        Notes
        -----
        This property is read-only.
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
            if self.reflection is None:
                raise ValueError("reflection is required when fresnel is disabled.")
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
