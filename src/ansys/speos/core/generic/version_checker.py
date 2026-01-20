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
"""Module to ease version checks."""


def check_version(input_version: str, major: int, minor: int, patch: int) -> bool:
    """Check that the input version is greater than or equal to the major.minor.patch.

    Parameters
    ----------
    input_version: str
        Input version written as "major.minor.patch", e.g. "2026.1.0"
    major : int
        Major release version, e.g. 2025
    minor : int
        Minor release version e.g. 2
    patch : int
        Service Pack version e.g. 3

    Returns
    -------
    bool
        True if the input version is >= to the major.minor.patch
    """
    input_major, input_minor, input_patch = input_version.split(".")
    if "-" in input_patch:
        input_patch = input_patch.split("-")[0]
    if int(input_major) > major:
        return True
    elif int(input_major) == major:
        if int(input_minor) > minor:
            return True
        elif int(input_minor) == minor:
            if int(input_patch) >= patch:
                return True

    return False


class VersionChecker:
    """Class to check version."""

    def __init__(self):
        self._version = None

    def set_version(self, input_version: str):
        """Set version.

        Parameters
        ----------
        input_version: str
            Input version written as "major.minor.patch", e.g. "2026.1.0"
        """
        self._version = input_version

    def is_version_supported(self, major: int, minor: int, patch: int) -> bool:
        """Check that the version is greater than or equal to the major.minor.patch.

        Parameters
        ----------
        major : int
            Major release version, e.g. 2025
        minor : int
            Minor release version e.g. 2
        patch : int
            Service Pack version e.g. 3

        Returns
        -------
        bool
            True if the input version is >= to the major.minor.patch
        """
        if self._version is not None:
            return check_version(self._version, major, minor, patch)
        return False


# server_version_checker.set_version() is called during SpeosClient initialization.
server_version_checker = VersionChecker()
