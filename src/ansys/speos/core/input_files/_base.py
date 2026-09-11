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

"""Common building blocks shared by the modules of :mod:`ansys.speos.core.input_files`.

The classes and helpers here back every ``*File`` dataclass of the package (for example
:class:`ansys.speos.core.input_files.material.MaterialFile` or
:class:`ansys.speos.core.input_files.spectrum_file.SpectrumFile`). They describe files
that Speos reads as inputs, so they are parsed and written locally and never require a
connection to a Speos gRPC server.

Every format class exposes the same three entry points:

* :meth:`SpeosFileFormat.load` - build a model from an existing file.
* :meth:`SpeosFileFormat.save` - write the model to a file.
* :meth:`SpeosFileFormat.validate` - check the model against the format constraints.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import fields
import math
from pathlib import Path
from typing import ClassVar, List, Mapping, Optional, Sequence, Union

NEWLINE = "\r\n"
"""Line separator used by the Speos text input files."""

ENCODING = "utf-8"
"""Encoding used by the Speos text input files."""


def format_number(value: float) -> str:
    """Format a number the way the Speos editors do.

    Parameters
    ----------
    value : float
        Value to format.

    Returns
    -------
    str
        ``value`` without a decimal part when it is a whole number, and with the shortest
        representation that reads back to the same number otherwise. Negative zero keeps
        its sign, as Speos writes it that way.
    """
    value = float(value)
    if value.is_integer() and abs(value) < 1e15:
        sign = "-" if value == 0.0 and math.copysign(1.0, value) < 0 else ""
        return sign + str(int(value))
    return repr(value)


def check_percentage(name: str, value: float) -> None:
    """Check that a value is a percentage expressed between 0 and 100.

    Parameters
    ----------
    name : str
        Name of the checked value, used in the error message.
    value : float
        Value to check.

    Raises
    ------
    ValueError
        If ``value`` is not within ``[0, 100]``.
    """
    if not 0.0 <= value <= 100.0:
        raise ValueError(f"{name} must be between 0 and 100, got {value}.")


class LineReader:
    """Cursor over the lines of a Speos text input file.

    Parameters
    ----------
    lines : List[str]
        Lines of the file, without their line separator.
    file_path : Union[str, pathlib.Path]
        Path the lines were read from. Only used to build error messages.
    """

    def __init__(self, lines: List[str], file_path: Union[str, Path] = "") -> None:
        self._lines = lines
        self._file_path = file_path
        self._index = 0

    @property
    def exhausted(self) -> bool:
        """Whether every line has been consumed.

        Returns
        -------
        bool
            ``True`` when no line is left to read.
        """
        return self._index >= len(self._lines)

    def error(self, message: str) -> ValueError:
        """Build an error mentioning the file and the current line.

        Parameters
        ----------
        message : str
            Description of the problem.

        Returns
        -------
        ValueError
            Error to raise by the caller.
        """
        return ValueError(f"{self._file_path}, line {self._index}: {message}")

    def next_line(self) -> str:
        """Read the next line, blank lines included.

        Returns
        -------
        str
            The line, stripped from its trailing whitespace.

        Raises
        ------
        ValueError
            If the end of the file is reached.
        """
        if self.exhausted:
            raise self.error("unexpected end of file.")
        line = self._lines[self._index].rstrip()
        self._index += 1
        return line

    def next_data_line(self) -> str:
        """Read the next non-blank line.

        Returns
        -------
        str
            The line, stripped from its surrounding whitespace.

        Raises
        ------
        ValueError
            If the end of the file is reached.
        """
        while True:
            line = self.next_line().strip()
            if line:
                return line

    def next_int(self) -> int:
        """Read the next non-blank line as a single integer.

        Returns
        -------
        int
            Parsed value.

        Raises
        ------
        ValueError
            If the line does not hold a single integer.
        """
        line = self.next_data_line()
        try:
            return int(float(line))
        except ValueError:
            raise self.error(f"expected an integer, got {line!r}.") from None

    def next_floats(self, count: int = -1) -> List[float]:
        """Read the next non-blank line as a list of floats.

        Parameters
        ----------
        count : int, optional
            Expected number of values. By default, ``-1``, which accepts any number.

        Returns
        -------
        List[float]
            Parsed values.

        Raises
        ------
        ValueError
            If the line does not hold ``count`` floats.
        """
        line = self.next_data_line()
        try:
            values = [float(token) for token in line.split()]
        except ValueError:
            raise self.error(f"expected numbers, got {line!r}.") from None
        if count >= 0 and len(values) != count:
            raise self.error(f"expected {count} values, got {len(values)}.")
        return values


class SpeosFileFormat(ABC):
    """Base class for the Speos input files that PySpeos reads and writes locally.

    Notes
    -----
    This is a superclass and is not intended to be instantiated directly.
    """

    EXTENSION: ClassVar[str] = ""
    """Usual file extension of the format."""

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "SpeosFileFormat":
        """Read a file and return the corresponding model.

        Parameters
        ----------
        file_path : Union[str, pathlib.Path]
            Path of the file to read.

        Returns
        -------
        ansys.speos.core.input_files._base.SpeosFileFormat
            Model holding the file content.

        Raises
        ------
        FileNotFoundError
            If ``file_path`` does not point to an existing file.
        ValueError
            If the file content does not match the format.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"No such file: {path}")
        return cls._decode(path)

    def save(self, file_path: Union[str, Path]) -> Path:
        """Write the model to a file, creating the parent directories if needed.

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
            If the model does not satisfy the format constraints.
        """
        self.validate()
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._encode(path)
        return path

    def validate(self) -> None:
        """Check the model against the format constraints.

        Raises
        ------
        ValueError
            If the model cannot be written as a valid file.
        """

    @classmethod
    @abstractmethod
    def _decode(cls, path: Path) -> "SpeosFileFormat":
        """Build a model from an existing file."""

    @abstractmethod
    def _encode(self, path: Path) -> None:
        """Write the model to a file."""


class SpeosTextFileFormat(SpeosFileFormat, ABC):
    """Base class for the line-oriented text formats of Speos.

    Notes
    -----
    This is a superclass and is not intended to be instantiated directly.
    """

    HEADER: ClassVar[str] = ""
    """First line of the file. Empty when the format has no header line."""

    HEADER_PREFIX: ClassVar[str] = ""
    """Version-agnostic start of :attr:`HEADER`, used to validate a file being read."""

    @classmethod
    def _decode(cls, path: Path) -> "SpeosTextFileFormat":
        lines = path.read_text(encoding=ENCODING, errors="replace").splitlines()
        reader = LineReader(lines, path)
        if cls.HEADER:
            header = reader.next_line().strip()
            if not header.lower().startswith(cls.HEADER_PREFIX.lower()):
                raise reader.error(f"expected a header starting with {cls.HEADER_PREFIX!r}.")
        return cls._from_lines(reader)

    def _encode(self, path: Path) -> None:
        lines = ([self.HEADER] if self.HEADER else []) + self._to_lines()
        path.write_text(NEWLINE.join(lines) + NEWLINE, encoding=ENCODING, newline="")

    @classmethod
    @abstractmethod
    def _from_lines(cls, reader: LineReader) -> "SpeosTextFileFormat":
        """Build a model from a reader positioned after the header line."""

    @abstractmethod
    def _to_lines(self) -> List[str]:
        """Return the lines of the file that follow the header line."""

    @staticmethod
    def _tabulated(values: Sequence[float]) -> str:
        """Join values with a tabulation, after a leading tabulation."""
        return "\t" + "\t".join(format_number(value) for value in values)


_PERCENT = {"unit": "percent"}
"""Field metadata of a value expressed as a percentage of the incident light."""

_DEGREES = {"unit": "degrees"}
"""Field metadata of a value expressed as an angle in degrees."""


def _tagged_names(model, tag: Mapping[str, str]) -> List[str]:
    """Return the names of the dataclass fields carrying exactly the given metadata.

    ``model`` is either a dataclass or an instance of one, and the names come back in
    declaration order, which every format here also uses as its file order.
    """
    return [entry.name for entry in fields(model) if entry.metadata == tag]


def _tagged(model, tag: Mapping[str, str]) -> dict:
    """Return the values of the dataclass fields carrying exactly the given metadata."""
    return {name: getattr(model, name) for name in _tagged_names(model, tag)}


def _wavelength_line(wavelengths: Sequence[float], values_per_wavelength: int) -> str:
    """Build the wavelength header row of a tabulated surface property file.

    Each wavelength labels a group of ``values_per_wavelength`` data columns, so it is
    followed by that many empty cells minus one. Speos closes every row with a tabulation.
    """
    cells: List[str] = []
    for wavelength in wavelengths:
        cells.append(format_number(wavelength))
        cells.extend([""] * (values_per_wavelength - 1))
    return "\t" + "\t".join(cells) + "\t"


def _data_line(values: Sequence[float], incidence: Optional[float] = None) -> str:
    """Build a data row of a tabulated surface property file.

    The first row of an incidence block starts with the angle of incidence, the following
    ones start with an empty cell. Speos closes every row with a tabulation.
    """
    head = format_number(incidence) if incidence is not None else ""
    return "\t".join([head, *(format_number(value) for value in values)]) + "\t"


def _read_grid(
    reader: LineReader, incidence_count: int, row_count: int, value_count: int
) -> List[List[List[float]]]:
    """Read ``incidence_count`` blocks of ``row_count`` rows holding ``value_count`` values.

    Returns the angles of incidence interleaved with the rows: each block is returned as
    ``[[incidence], row_1, ..., row_n]``.
    """
    blocks = []
    for _ in range(incidence_count):
        first = reader.next_floats(count=value_count + 1)
        rows = [first[1:]]
        rows.extend(reader.next_floats(count=value_count) for _ in range(row_count - 1))
        blocks.append([[first[0]], *rows])
    return blocks
