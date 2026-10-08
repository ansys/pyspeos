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

The classes and helpers here back every ``*File`` model of the package (for example
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
import math
from pathlib import Path
from types import FunctionType
from typing import ClassVar, List, Mapping, Optional, Sequence, TypeVar, Union, cast

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


_SNIFF_SIZE = 4096
"""Number of bytes read at the start of a file to tell text content from binary content."""


def _check_text_file(path: Path) -> None:
    """Check that a file holds text and not the binary payload of an encrypted file.

    Speos writes its encrypted input files with the very same extension and header line as
    the plain ones, so the only reliable clue is the compressed payload that follows.

    Parameters
    ----------
    path : pathlib.Path
        Path of the file to check.

    Raises
    ------
    ValueError
        If the beginning of the file holds binary content.
    """
    with path.open("rb") as stream:
        head = stream.read(_SNIFF_SIZE)
    if b"\x00" in head:
        raise ValueError(
            f"{path} is not a plain text file. PySpeos cannot read encrypted Speos input "
            "files, save the file without encryption from Speos and read it again."
        )


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


def _finite_number(name: str, value: float) -> float:
    """Convert a numeric value without accepting nonfinite data."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value}.")
    return value


def _percentage(name: str, value: float) -> float:
    """Convert and validate a finite percentage before storing it."""
    value = _finite_number(name, value)
    check_percentage(name, value)
    return value


def _finite_values(name: str, values: Sequence[float]) -> List[float]:
    """Copy a numeric column while validating its entries."""
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be a numeric sequence, not text.")
    return [_finite_number(name, value) for value in values]


def _numeric_tuple(name: str, values: Sequence[float], count: int = 3) -> tuple[float, ...]:
    """Validate a fixed-size numeric vector and store it immutably."""
    values = tuple(_finite_values(name, values))
    if len(values) != count:
        raise ValueError(f"{name} must hold {count} coordinates, got {len(values)}.")
    return values


def _single_line(value: str) -> str:
    """Validate a file description without silently changing it."""
    if not isinstance(value, str):
        raise TypeError("description must be a string.")
    if value and value.splitlines() != [value]:
        raise ValueError("description must be a single line.")
    return value


def _matching_columns(columns: Mapping[str, Sequence[float]], complete: bool = False) -> None:
    """Check populated columns, allowing empty columns only while building a draft."""
    lengths = {name: len(values) for name, values in columns.items()}
    populated = {length for length in lengths.values() if length}
    if len(populated) > 1 or (complete and len(set(lengths.values())) > 1):
        raise ValueError(f"All the columns must have the same length, got {lengths}.")
    if complete and not populated:
        raise ValueError(f"The columns {list(columns)} must not be empty.")


def _matching_grid(
    name: str,
    rows: Sequence[Sequence[object]],
    *,
    row_count: int | None = None,
    column_count: int | None = None,
    row_axis: str = "angle",
    incidences: Sequence[float] | None = None,
) -> None:
    """Check known grid dimensions without imposing a format's completeness policy."""
    if row_count is not None and len(rows) != row_count:
        raise ValueError(
            f"{name} must hold one row per {row_axis}, expected {row_count} rows, got {len(rows)}."
        )
    if column_count is not None:
        for index, row in enumerate(rows):
            if len(row) != column_count:
                location = f"At {incidences[index]} degrees, " if incidences is not None else ""
                raise ValueError(
                    f"{location}{name} must hold one entry per wavelength, "
                    f"expected {column_count}, got {len(row)}."
                )


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
            return int(line)
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


def _property_name(attribute: property) -> str:
    """Retrieve the name of a property defined with a named getter."""
    if not isinstance(attribute, property):
        raise TypeError("Expected a property descriptor.")
    getter = attribute.fget
    if not isinstance(getter, FunctionType):
        raise ValueError("The property must have a getter defined as a function.")
    return getter.__name__


class _ValueComparable:
    """Compare explicitly declared model fields without adding file I/O behavior."""

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]]

    def __eq__(self, other: object) -> bool:
        """Compare declared fields of models with exactly the same concrete type."""
        if type(self) is not type(other):
            return NotImplemented
        return all(getattr(self, name) == getattr(other, name) for name in self._EQUALITY_FIELDS)


_FileFormat = TypeVar("_FileFormat", bound="SpeosFileFormat")


class SpeosFileFormat(_ValueComparable, ABC):
    """Base class for the Speos input files that PySpeos reads and writes locally.

    Notes
    -----
    This is a superclass and is not intended to be instantiated directly.
    """

    EXTENSION: ClassVar[str] = ""
    """Usual file extension of the format."""

    @classmethod
    def load(cls: type[_FileFormat], file_path: Union[str, Path]) -> _FileFormat:
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
        return cast(_FileFormat, cls._decode(path))

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
        _check_text_file(path)
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
