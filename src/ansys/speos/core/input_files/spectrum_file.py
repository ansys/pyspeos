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

from dataclasses import dataclass, field
from typing import List

from ansys.speos.core.input_files._base import (
    LineReader,
    SpeosTextFileFormat,
    check_percentage,
    format_number,
)
from ansys.speos.core.spectrum import Spectrum

MAX_SPECTRUM_SAMPLES = 32767
"""Maximum number of wavelength samples accepted by Speos in a ``*.spectrum`` file."""


@dataclass
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

    Examples
    --------
    >>> from ansys.speos.core.input_files.spectrum_file import SpectrumFile
    >>> SpectrumFile(wavelengths=[400.0, 700.0], values=[100.0, 50.0]).save("led.spectrum")
    """

    wavelengths: List[float] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    description: str = ""

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
        sample_count = reader.next_int()
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
