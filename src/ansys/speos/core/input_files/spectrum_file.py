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

"""Provides the Speos ``*.spectrum`` input file format."""

from __future__ import annotations

from typing import ClassVar, List

from ansys.speos.core.input_files._base import (
    LineReader,
    SpeosTextFileFormat,
    _finite_values,
    _property_name,
    _single_line,
    check_percentage,
    format_number,
)
from ansys.speos.core.spectrum import Spectrum

MAX_SPECTRUM_SAMPLES = 32767
"""Maximum number of wavelength samples accepted by Speos in a ``*.spectrum`` file."""


class SpectrumFile(SpeosTextFileFormat):
    """Speos ``*.spectrum`` file, holding a sampled spectral distribution.

    The file is the text (``v1``) flavor of the format: a header line, a description, the
    number of samples, then one ``wavelength<TAB>value`` line per sample. Files are read
    and written locally, no Speos server is needed.

    Parameters
    ----------
    wavelengths : List[float], optional
        Wavelengths of the samples, in nm. By default, ``[]``.
    values : List[float], optional
        Relative spectral values of the samples, in percent (0 to 100). By default, ``[]``.
    description : str, optional
        Free text written on the second line of the file. By default, ``""``.

    Notes
    -----
    Construction and setters validate numeric data before storing it. List getters return
    copies; assign an edited list back to change the model. Empty columns permit staged
    construction, while :meth:`validate` and :meth:`save` require complete matching columns.
    To resize a populated spectrum, clear :attr:`values`, replace :attr:`wavelengths`, then
    assign the new values.

    Examples
    --------
    >>> from ansys.speos.core.input_files.spectrum_file import SpectrumFile
    >>> SpectrumFile(wavelengths=[400.0, 700.0], values=[100.0, 50.0]).save("led.spectrum")
    """

    def __init__(
        self,
        wavelengths: List[float] | None = None,
        values: List[float] | None = None,
        description: str = "",
    ) -> None:
        self._wavelengths: List[float] = []
        self._values: List[float] = []
        self.wavelengths = wavelengths if wavelengths is not None else []
        self.values = values if values is not None else []
        self.description = description

    @property
    def wavelengths(self) -> List[float]:
        """Wavelengths in nm, returned as a copy.

        Parameters
        ----------
        values : List[float]
            New wavelengths of the samples, in nm.

        Returns
        -------
        List[float]
            Finite sample wavelengths.
        """
        return self._wavelengths.copy()

    @wavelengths.setter
    def wavelengths(self, values: List[float]) -> None:
        values = _finite_values(_property_name(SpectrumFile.wavelengths), values)
        self._check_columns(values, self._values)
        self._wavelengths = values

    @property
    def values(self) -> List[float]:
        """Spectral values in percent, returned as a copy.

        Parameters
        ----------
        values : List[float]
            New relative spectral values of the samples, in percent (0 to 100).

        Returns
        -------
        List[float]
            Values between 0 and 100.
        """
        return self._values.copy()

    @values.setter
    def values(self, values: List[float]) -> None:
        name = _property_name(SpectrumFile.values)
        values = _finite_values(name, values)
        for value in values:
            check_percentage(name, value)
        self._check_columns(self._wavelengths, values)
        self._values = values

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
        _property_name(wavelengths),
        _property_name(values),
        _property_name(description),
    )

    @staticmethod
    def _check_columns(wavelengths: List[float], values: List[float]) -> None:
        if wavelengths and values and len(wavelengths) != len(values):
            raise ValueError(
                f"wavelengths and values must have the same length, got "
                f"{len(wavelengths)} and {len(values)}."
            )
        count = max(len(wavelengths), len(values))
        if count > MAX_SPECTRUM_SAMPLES:
            raise ValueError(
                f"A spectrum cannot hold more than {MAX_SPECTRUM_SAMPLES} samples, got {count}."
            )

    EXTENSION = ".spectrum"
    HEADER = "OPTIS - Spectrum file v1"
    # Kept loose on purpose: some files shipped by Ansys misspell the header as
    # "OPTIS - Spectrum fie v1.0", and Speos reads them.
    HEADER_PREFIX = "OPTIS - Spectrum"

    def validate(self) -> None:
        """Check the spectrum against the constraints of the ``*.spectrum`` format.

        Raises
        ------
        ValueError
            If the sample lists are empty, do not have the same length, hold more than
            32767 samples, or if a value is outside the 0 to 100 percent range.
        """
        if len(self.wavelengths) != len(self.values):
            raise ValueError(
                f"wavelengths and values must have the same length, got "
                f"{len(self.wavelengths)} and {len(self.values)}."
            )
        if not self.wavelengths:
            raise ValueError("A spectrum must hold at least one sample.")
        if len(self.wavelengths) > MAX_SPECTRUM_SAMPLES:
            raise ValueError(
                f"A spectrum cannot hold more than {MAX_SPECTRUM_SAMPLES} samples, "
                f"got {len(self.wavelengths)}."
            )
        for wavelength, value in zip(self.wavelengths, self.values):
            check_percentage(f"The value at {wavelength} nm", value)

    def _to_lines(self) -> List[str]:
        lines = [self.description, str(len(self.wavelengths))]
        lines.extend(
            f"{format_number(wavelength)}\t{format_number(value)}"
            for wavelength, value in zip(self.wavelengths, self.values)
        )
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> SpectrumFile:
        description = reader.next_line()
        sample_count = reader.next_int(minimum=1)
        wavelengths, values = [], []
        for _ in range(sample_count):
            wavelength, value = reader.next_floats(count=2)
            wavelengths.append(wavelength)
            values.append(value)
        return cls(wavelengths=wavelengths, values=values, description=description)

    @classmethod
    def from_sampled(cls, spectrum: Spectrum, description: str = "") -> SpectrumFile:
        """Build a spectrum file from a sampled :class:`Spectrum` feature.

        Parameters
        ----------
        spectrum : ansys.speos.core.spectrum.Spectrum
            Spectrum feature configured with :meth:`Spectrum.set_sampled`.
        description : str, optional
            Free text written on the second line of the file. By default, ``""``, which
            uses the name of the spectrum feature.

        Returns
        -------
        ansys.speos.core.input_files.spectrum_file.SpectrumFile
            Spectrum file model.

        Raises
        ------
        ValueError
            If ``spectrum`` is not of sampled type.
        """
        sampled = spectrum._type
        if not isinstance(sampled, Spectrum.Sampled):
            raise ValueError("from_sampled expects a spectrum set with set_sampled().")
        return cls(
            wavelengths=list(sampled.wavelengths),
            values=list(sampled.values),
            description=description or spectrum._spectrum.name,
        )
