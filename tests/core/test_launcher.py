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

"""Test launcher."""

import psutil
import pytest

from ansys.speos.core.generic.constants import DEFAULT_VERSION
from ansys.speos.core.kernel.grpc.transport_options import (
    InsecureOptions,
    MTLSOptions,
    TransportMode,
    TransportOptions,
    UDSOptions,
    WNUAOptions,
)
from ansys.speos.core.launcher import launch_local_speos_rpc_server, retrieve_speos_install_dir
from tests.conftest import IS_WINDOWS, SERVER_PORT

# Check local installation
try:
    _ = retrieve_speos_install_dir(None, DEFAULT_VERSION)
    HAS_LOCAL_SPEOS_SERVER = True
except FileNotFoundError:
    HAS_LOCAL_SPEOS_SERVER = False


@pytest.mark.skipif(
    not HAS_LOCAL_SPEOS_SERVER, reason="requires Speos server to be installed locally"
)
def test_local_session(*args):
    """Test local session launch and close."""
    port = SERVER_PORT + 1
    if IS_WINDOWS:
        speos_loc = None
        name = "SpeosRPC_Server.exe"
    else:
        speos_loc = None
        name = "SpeosRPC_Server.x"
    p_list = [p.name() for p in psutil.process_iter()]
    nb_process = p_list.count(name)
    test_speos = launch_local_speos_rpc_server(port=port, speos_rpc_path=speos_loc)
    p_list = [p.name() for p in psutil.process_iter()]
    running = p_list.count(name) > nb_process
    assert running is test_speos.client.healthy
    closed = test_speos.close()
    p_list = [p.name() for p in psutil.process_iter()]
    running = p_list.count(name) > nb_process
    assert running is not closed


def test_transport_options():
    """Test transport options."""
    to = TransportOptions()
    assert to.mode == TransportMode.UDS
    assert to.options == UDSOptions()
    to_uds = UDSOptions(uds_service="test_service", uds_dir="/uds", uds_id="1234")
    kwargs_uds = to_uds._to_cyberchannel_kwargs()
    assert kwargs_uds["uds_service"] == "test_service"
    assert kwargs_uds["uds_dir"] == "/uds"
    assert kwargs_uds["uds_id"] == "1234"
    to_mtls = MTLSOptions(certs_dir="/certs", host="localhost", port=50051)
    kwargs_mtls = to_mtls._to_cyberchannel_kwargs()
    assert kwargs_mtls["certs_dir"] == "/certs"
    assert kwargs_mtls["host"] == "localhost"
    assert kwargs_mtls["port"] == 50051
    to_insecure = InsecureOptions(host="localhost", port=50051)
    kwargs_insecure = to_insecure._to_cyberchannel_kwargs()
    assert kwargs_insecure["host"] == "localhost"
    assert kwargs_insecure["port"] == 50051
    to_wnua = WNUAOptions(host="localhost", port=50051)
    kwargs_wnua = to_wnua._to_cyberchannel_kwargs()
    assert kwargs_wnua["host"] == "localhost"
    assert kwargs_wnua["port"] == 50051
