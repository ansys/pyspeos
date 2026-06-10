# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
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

"""Test map actions."""

from ansys.speos.core.speos import Speos
from tests.conftest import test_path
import tests.helper as helper


def test_export_xmp_to_image(speos: Speos):
    """Test the export of XMP to PNG."""
    assert speos.client.healthy is True

    xmp_path = test_path / "Source.speos" / "PROJECT.Direct-no-Ray.Irradiance Ray Spectral.xmp"
    png_exported = test_path / "testExported.png"

    map_stub = speos.client.maps()
    map_stub.export_xmp_to_image(xmp_file_uri=xmp_path, image_file_uri=png_exported)

    assert helper.does_file_exist(png_exported) is True
    helper.remove_file(png_exported)
