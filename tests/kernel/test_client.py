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

"""Test basic client connection."""

from grpc import insecure_channel

from ansys.speos.core.kernel.client import SpeosClient
from ansys.speos.core.speos import Speos
from tests.conftest import config


def test_client_init(speos: Speos):
    """Test the instantiation of a client from the default constructor."""
    assert speos._client.healthy is True


def test_client_through_channel():
    """Test the instantiation of a client from a gRPC channel."""
    target = "dns:///localhost:" + str(config.get("SpeosServerPort"))
    channel = insecure_channel(target)
    client = SpeosClient(channel=channel)
    client_repr = repr(client)
    assert "Target" in client_repr
    assert "Connection" in client_repr
    assert client.healthy is True
    assert client.target() == target
    assert client.channel
