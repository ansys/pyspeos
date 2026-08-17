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

"""Test basic using version checker."""

import pytest

from ansys.speos.core.generic.version_checker import check_version


@pytest.mark.parametrize(
    "input_version, major, minor, patch, expected",
    [
        # Major comparison
        ("2027.1.0", 2026, 1, 0, True),
        ("2025.1.0", 2026, 1, 0, False),
        ("0.10.0", 1, 0, 0, False),
        ("1.0.0", 0, 10, 0, True),
        # Minor comparison (same major)
        ("2026.2.0", 2026, 1, 3, True),
        ("2026.1.0", 2026, 2, 0, False),
        ("0.10.0", 0, 8, 0, True),
        ("0.6.3", 0, 8, 0, False),
        # Patch comparison (same major and minor)
        ("2026.1.3", 2026, 1, 3, True),
        ("2026.1.4", 2026, 1, 3, True),
        ("2026.1.2", 2026, 1, 3, False),
        ("0.10.0", 0, 10, 0, True),
        ("0.6.3", 0, 6, 3, True),
        # Four-part versions: the fourth part is ignored
        ("2026.1.3.5214", 2026, 1, 3, True),
        ("2026.1.3.5214", 2026, 1, 4, False),
        ("2027.1.0.42487-beta", 2027, 1, 0, True),
        ("2027.1.0.42487-beta", 2027, 1, 1, False),
        # Patch carrying a suffix: only the leading number is used
        ("2026.1.3-suffix", 2026, 1, 3, True),
        ("2026.1.3-suffix", 2026, 1, 4, False),
        ("2026.1.3-suffix", 2026, 0, 0, True),
        # Development patch is always lower than any numbered patch
        ("0.8.dev0", 0, 8, 0, False),
        ("0.8.dev1", 0, 8, 0, False),
        ("0.8.dev0", 0, 7, 0, True),
        ("0.8.dev0", 0, 9, 0, False),
        ("0.8.dev0", 1, 0, 0, False),
        # Patch not provided: only major and minor are compared
        ("2026.1.3.5214", 2026, 1, None, True),
        ("0.8.dev0", 0, 8, None, True),
        ("0.10.0", 0, 10, None, True),
        ("0.6.3", 0, 8, None, False),
        ("0.10.0", 1, 0, None, False),
        ("1.0.0", 0, 10, None, True),
    ],
)
def test_check_version(input_version: str, major: int, minor: int, patch, expected: bool):
    """Test check_version with the different supported version patterns."""
    assert check_version(input_version, major, minor, patch) is expected


def test_check_version_default_patch():
    """Test check_version when the patch argument is omitted."""
    assert check_version("0.17.dev0", 0, 17) is True
    assert check_version("0.17.dev0", 0, 18) is False
