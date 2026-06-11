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

"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""

from pathlib import Path

from ansys.api.speos.results.v1 import (
    map_pb2 as messages,
    map_pb2_grpc as service,
)

from ansys.speos.core.generic.version_checker import server_version_checker


class MapStub:
    """
    Database interactions for map actions.

    Parameters
    ----------
    channel : grpc.Channel
        Channel to use for the stub.

    Examples
    --------
    The best way to get a MapStub is to retrieve it from SpeosClient via
    maps() method. Like in the following example:

    >>> from ansys.speos.core.speos import Speos
    >>> speos = Speos()
    >>> map_db = speos.client.maps()

    """

    def __init__(self, channel):
        if not server_version_checker.is_version_supported(2026, 1, 2):
            raise NotImplementedError(
                "Map actions are only supported with Speos 2026 R1.2 or higher."
            )
        self._actions_stub = service.MapActionsStub(channel=channel)

    # Actions
    def export_xmp_to_image(self, xmp_file_uri: Path | str, image_file_uri: Path | str) -> None:
        """
        Export XMP file to PNG file.

        Parameters
        ----------
        xmp_file_uri : Path | str
            XMP file to be exported.
        image_file_uri : Path | str
            PNG file to be created.
        """
        self._actions_stub.ExportXMPToImage(
            messages.ExportXMPToImage_Request(
                xmp_file_uri=str(xmp_file_uri), image_file_uri=str(image_file_uri)
            )
        )
