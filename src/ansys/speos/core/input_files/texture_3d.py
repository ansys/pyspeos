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

from typing import ClassVar, List, Tuple

from ansys.speos.core.input_files._base import (
    LineReader,
    SpeosTextFileFormat,
    _numeric_tuple,
    _property_name,
    _ValueComparable,
    format_number,
)


class TexturePattern(_ValueComparable):
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

    Notes
    -----
    Construction and setters validate finite three-component vectors before storing them
    as immutable tuples. Editing a pattern shared with a mapping does not notify the
    mapping; its uniform-scale constraint is rechecked when validating or saving it.
    """

    def __init__(
        self,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        x_direction: Tuple[float, float, float] = (1.0, 0.0, 0.0),
        y_direction: Tuple[float, float, float] = (0.0, 1.0, 0.0),
        scale: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> None:
        self.position = position
        self.x_direction = x_direction
        self.y_direction = y_direction
        self.scale = scale

    @property
    def position(self) -> Tuple[float, ...]:
        """Pattern origin.

        Returns
        -------
        Tuple[float, ...]
            Three finite Cartesian coordinates.
        """
        return self._position

    @position.setter
    def position(self, values: Tuple[float, float, float]) -> None:
        self._position = _numeric_tuple(_property_name(TexturePattern.position), values)

    @property
    def x_direction(self) -> Tuple[float, ...]:
        """Pattern X direction.

        Returns
        -------
        Tuple[float, ...]
            Three finite direction coordinates.
        """
        return self._x_direction

    @x_direction.setter
    def x_direction(self, values: Tuple[float, float, float]) -> None:
        self._x_direction = _numeric_tuple(_property_name(TexturePattern.x_direction), values)

    @property
    def y_direction(self) -> Tuple[float, ...]:
        """Pattern Y direction.

        Returns
        -------
        Tuple[float, ...]
            Three finite direction coordinates.
        """
        return self._y_direction

    @y_direction.setter
    def y_direction(self, values: Tuple[float, float, float]) -> None:
        self._y_direction = _numeric_tuple(_property_name(TexturePattern.y_direction), values)

    @property
    def scale(self) -> Tuple[float, ...]:
        """Pattern scale factors.

        Returns
        -------
        Tuple[float, ...]
            Three finite scale factors.
        """
        return self._scale

    @scale.setter
    def scale(self, values: Tuple[float, float, float]) -> None:
        self._scale = _numeric_tuple(_property_name(TexturePattern.scale), values)

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(position),
        _property_name(x_direction),
        _property_name(y_direction),
        _property_name(scale),
    )

    def validate(self) -> None:
        """Check vector dimensions and finite coordinates.

        Raises
        ------
        ValueError
            If a vector is not a finite three-component vector.
        """
        for name in self._EQUALITY_FIELDS:
            _numeric_tuple(name, getattr(self, name))


_PATTERN_FIELDS = TexturePattern._EQUALITY_FIELDS


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

    Notes
    -----
    The pattern list is copied on assignment and access, while pattern objects stay shared.
    Setters check the current uniform-scale constraint before storing values, and
    :meth:`validate` rechecks it after child edits. Empty lists permit drafts, not saved files.

    Examples
    --------
    >>> from ansys.speos.core.input_files.texture_3d import (
    ...     Texture3DMappingFile,
    ...     TexturePattern,
    ... )
    >>> patterns = [TexturePattern(position=(x * 0.5, 0.0, 0.0)) for x in range(10)]
    >>> Texture3DMappingFile(patterns=patterns).save("prisms.OPT3DMapping")
    """

    def __init__(
        self, patterns: List[TexturePattern] | None = None, uniform_scale: bool = False
    ) -> None:
        self._patterns: List[TexturePattern] = []
        self._uniform_scale = False
        self.patterns = patterns if patterns is not None else []
        self.uniform_scale = uniform_scale

    @property
    def patterns(self) -> List[TexturePattern]:
        """Pattern collection with a copied container and shared patterns.

        Returns
        -------
        List[TexturePattern]
            Validated pattern objects.
        """
        return self._patterns.copy()

    @patterns.setter
    def patterns(self, values: List[TexturePattern]) -> None:
        values = list(values)
        for pattern in values:
            if not isinstance(pattern, TexturePattern):
                raise TypeError("patterns must contain TexturePattern objects.")
            pattern.validate()
        self._check_uniform(values, self._uniform_scale)
        self._patterns = values

    @property
    def uniform_scale(self) -> bool:
        """Whether the mapping writes one scale factor per pattern.

        Returns
        -------
        bool
            True when each pattern must have equal scale factors.
        """
        return self._uniform_scale

    @uniform_scale.setter
    def uniform_scale(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("uniform_scale must be a bool.")
        self._check_uniform(self._patterns, value)
        self._uniform_scale = value

    _EQUALITY_FIELDS: ClassVar[tuple[str, ...]] = (
        _property_name(patterns),
        _property_name(uniform_scale),
    )

    @staticmethod
    def _check_uniform(patterns: List[TexturePattern], uniform: bool) -> None:
        if uniform:
            for index, pattern in enumerate(patterns):
                if len(set(pattern.scale)) != 1:
                    raise ValueError(
                        f"Pattern {index + 1}: uniform_scale needs the same scale factor along "
                        f"X, Y and Z, got {pattern.scale}."
                    )

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
        if not self._patterns:
            raise ValueError("A 3D Texture mapping must hold at least one pattern.")
        for pattern in self._patterns:
            pattern.validate()
        self._check_uniform(self._patterns, self._uniform_scale)

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
