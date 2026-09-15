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

"""Provides a way to interact with the Speos 3D Texture mapping files.

A Speos 3D Texture is made of a mesh, simulated by Speos, and of a ``*.OPT3DMapping``
file, which lays out where each pattern sits on the support. That mapping file is the
recipe handed over to manufacture the physical part, so it is often produced or
post-processed outside of Speos. It is read and written locally, no Speos server is
needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, List, Tuple

from ansys.speos.core.input_files._base import LineReader, SpeosTextFileFormat, format_number


@dataclass
class TexturePattern:
    """Placement of one pattern of a Speos 3D Texture.

    Parameters
    ----------
    position : Tuple[float, float, float], optional
        Origin of the pattern, in the axis system of the 3D Texture.
        By default, ``(0.0, 0.0, 0.0)``.
    x_direction : Tuple[float, float, float], optional
        Orientation of the pattern along the X direction of the axis system.
        By default, ``(1.0, 0.0, 0.0)``.
    y_direction : Tuple[float, float, float], optional
        Orientation of the pattern along the Y direction of the axis system.
        By default, ``(0.0, 1.0, 0.0)``.
    scale : Tuple[float, float, float], optional
        Scale factors along the X, Y and Z directions, ``1`` meaning 100 percent of the
        original pattern size. By default, ``(1.0, 1.0, 1.0)``.
    """

    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    x_direction: Tuple[float, float, float] = (1.0, 0.0, 0.0)
    y_direction: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass
class Texture3DMappingFile(SpeosTextFileFormat):
    """Speos ``*.OPT3DMapping`` file, laying out the patterns of a 3D Texture.

    The pattern count opens the file, then each pattern takes one line,
    ``x y z ix iy iz jx jy jz kx ky kz``.

    Parameters
    ----------
    patterns : List[TexturePattern], optional
        Patterns of the texture. By default, ``[]``.
    uniform_scale : bool, optional
        Whether to write a single scale factor per pattern instead of one per direction.
        By default, ``False``. Reading a file sets this from the number of columns found.

    Examples
    --------
    >>> from ansys.speos.core.input_files.texture_3d import (
    ...     Texture3DMappingFile,
    ...     TexturePattern,
    ... )
    >>> patterns = [TexturePattern(position=(x * 0.5, 0.0, 0.0)) for x in range(10)]
    >>> Texture3DMappingFile(patterns=patterns).save("prisms.OPT3DMapping")
    """

    patterns: List[TexturePattern] = field(default_factory=list)
    uniform_scale: bool = False

    EXTENSION = ".OPT3DMapping"

    _UNIFORM_COLUMN_COUNT: ClassVar[int] = 10
    _COLUMN_COUNT: ClassVar[int] = 12

    def validate(self) -> None:
        """Check the mapping against the constraints of the ``*.OPT3DMapping`` format.

        Raises
        ------
        ValueError
            If the mapping holds no pattern, or if :attr:`uniform_scale` is set while a
            pattern scales differently along X, Y and Z.
        """
        if not self.patterns:
            raise ValueError("A 3D Texture mapping must hold at least one pattern.")
        if not self.uniform_scale:
            return
        for index, pattern in enumerate(self.patterns):
            if len(set(pattern.scale)) != 1:
                raise ValueError(
                    f"Pattern {index + 1}: uniform_scale needs the same scale factor along "
                    f"X, Y and Z, got {pattern.scale}."
                )

    def _to_lines(self) -> List[str]:
        lines = [str(len(self.patterns))]
        for pattern in self.patterns:
            scale = pattern.scale[:1] if self.uniform_scale else pattern.scale
            values = (*pattern.position, *pattern.x_direction, *pattern.y_direction, *scale)
            lines.append("\t".join(format_number(value) for value in values))
        return lines

    @classmethod
    def _from_lines(cls, reader: LineReader) -> Texture3DMappingFile:
        pattern_count = reader.next_int()
        patterns, uniform_scale = [], False
        for _ in range(pattern_count):
            values = reader.next_floats()
            if len(values) == cls._UNIFORM_COLUMN_COUNT:
                uniform_scale = True
                scale = (values[9], values[9], values[9])
            elif len(values) == cls._COLUMN_COUNT:
                scale = (values[9], values[10], values[11])
            else:
                raise reader.error(
                    f"expected {cls._UNIFORM_COLUMN_COUNT} or {cls._COLUMN_COUNT} values per "
                    f"pattern, got {len(values)}."
                )
            x, y, z, ix, iy, iz, jx, jy, jz = values[:9]
            patterns.append(
                TexturePattern(
                    position=(x, y, z),
                    x_direction=(ix, iy, iz),
                    y_direction=(jx, jy, jz),
                    scale=scale,
                )
            )
        return cls(patterns=patterns, uniform_scale=uniform_scale)
