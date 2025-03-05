# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
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

"""Provides interface to link Speos Objects to Geometries."""

from __future__ import annotations

from typing import Mapping


class GeoRef:
    """Represent a CAD object."""

    def __init__(self, name: str, description: str, metadata: Mapping[str, str]):
        self.name = name
        self.description = description
        self.metadata = metadata
        return

    @staticmethod
    def from_native_link(geopath: str) -> GeoRef:
        """
        Convert a native link to a GeoRef.

        Parameters
        ----------
        geopath : str
            Geometry path.

        Returns
        -------
        GeoRef
        """
        return GeoRef("", "", {"GeoPath": geopath})

    def to_native_link(self) -> str:
        """
        Convert to a native link.

        Returns
        -------
        str
            Geometry path.
        """
        return self.metadata["GeoPath"]
