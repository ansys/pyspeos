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

"""Compatibility tests for BSDF import paths."""

from ansys.speos.core import bsdf, input_files
from ansys.speos.core.input_files import bsdf as input_bsdf


def test_bsdf_compatibility_exports():
    """Legacy and input_files imports expose identical BSDF objects."""
    public_names = (
        "AnisotropicBSDF",
        "BaseBSDF",
        "BxdfDatapoint",
        "InterpolationEnhancement",
        "SpectralBRDF",
        "create_anisotropic_bsdf",
        "create_bsdf180",
        "create_spectral_brdf",
    )
    for name in public_names:
        implementation = getattr(input_bsdf, name)
        assert getattr(bsdf, name) is implementation
        assert getattr(input_files, name) is implementation
