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

"""Test basic client connection."""

import platform

from ansys.speos.core.generic.version_checker import server_version_checker
from ansys.speos.core.kernel import (
    BodyLink,
    FaceLink,
    IntensityTemplateLink,
    JobLink,
    PartLink,
    SceneLink,
    SensorTemplateLink,
    SimulationTemplateLink,
    SOPTemplateLink,
    SourceTemplateLink,
    SpectrumLink,
    VOPTemplateLink,
)
from ansys.speos.core.kernel.client import (
    SpeosClient,
    default_docker_channel,
    default_local_channel,
)
from ansys.speos.core.kernel.sensor_template_v2 import SensorTemplateLinkV2
from ansys.speos.core.speos import Speos
from tests.conftest import IS_DOCKER, SERVER_PORT


def test_client_init(speos: Speos):
    """Test the instantiation of a client from the default constructor."""
    assert speos._client.healthy is True


def test_client_through_channel():
    """Test the instantiation of a client from a gRPC channel."""
    if platform.system() == "Linux" and not IS_DOCKER:
        target = "unix:/tmp/speosrpc_sock_" + str(SERVER_PORT)
    else:
        target = "dns:///localhost:" + str(SERVER_PORT)
    if IS_DOCKER:
        channel = default_docker_channel(port=SERVER_PORT)
    else:
        channel = default_local_channel(port=SERVER_PORT)
    client = SpeosClient(channel=channel)
    client_repr = repr(client)
    assert "Target" in client_repr
    assert "Connection" in client_repr
    assert client.healthy is True
    assert client.target() == target
    assert client.channel
    assert client.close()
    assert client.healthy is False


def test_client_datamodels(speos: Speos):
    """Test the instantiation of a client from the default constructor."""
    assert speos._client.healthy is True
    type_links = [
        SOPTemplateLink,
        VOPTemplateLink,
        SpectrumLink,
        IntensityTemplateLink,
        SourceTemplateLink,
        SensorTemplateLink,
        SimulationTemplateLink,
        SceneLink,
        JobLink,
        PartLink,
        BodyLink,
        FaceLink,
    ]
    if server_version_checker.is_version_supported(2027, 1, 0):
        type_links += [SensorTemplateLinkV2]
    for link_type in type_links:
        test = speos._client.get_items("123", link_type)
        assert test == []
    assert speos._client.__getitem__("123") is None
