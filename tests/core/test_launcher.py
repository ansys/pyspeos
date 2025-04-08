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

"""Test launcher."""

import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

import psutil
import pytest

from ansys.speos.core.kernel.client import LATEST_VERSION
from ansys.speos.core.launcher import launch_local_speos_rpc_server
from tests.conftest import IS_WINDOWS, config

IS_DOCKER = config.get("SpeosServerOnDocker")


@pytest.mark.skipif(IS_DOCKER, reason="launcher only works without Docker image")
def test_local_session(*args):
    """Test local session launch and close."""
    port = config.get("SpeosServerPort") + 1
    if IS_WINDOWS:
        speos_loc = None
        name = "SpeosRPC_Server.exe"
    else:
        speos_loc = None
        name = "SpeosRPC_Server.x"
    p_list = [p.name() for p in psutil.process_iter()]
    nb_process = p_list.count(name)
    test_speos = launch_local_speos_rpc_server(port=port, speos_rpc_loc=speos_loc)
    p_list = [p.name() for p in psutil.process_iter()]
    running = p_list.count(name) > nb_process
    assert running is test_speos.client.healthy
    closed = test_speos.close()
    p_list = [p.name() for p in psutil.process_iter()]
    running = p_list.count(name) > nb_process
    assert running is not closed


@patch.object(subprocess, "Popen")
def test_coverage_launcher_speosdocker(*args):
    """Test local session launch on remote server to improve coverage."""
    port = config.get("SpeosServerPort")
    tmp_file = tempfile.gettempdir()
    if IS_WINDOWS:
        name = "SpeosRPC_Server.exe"
    else:
        name = "SpeosRPC_Server.x"
    speos_loc = Path(tmp_file) / "Optical Products" / "SPEOS_RPC" / name
    speos_loc.parent.parent.mkdir(exist_ok=True)
    speos_loc.parent.mkdir(exist_ok=True)
    if not speos_loc.exists():
        f = speos_loc.open("w")
        f.write("speos_test_file")
        f.close()
    os.environ["AWP_ROOT{}".format(LATEST_VERSION)] = tmp_file
    test_speos = launch_local_speos_rpc_server(port=port)
    assert True is test_speos.client.healthy
    assert True is test_speos.close()
    assert False is test_speos.client.healthy
    test_speos = launch_local_speos_rpc_server(port=port, speos_rpc_loc=speos_loc)
    assert True is test_speos.client.healthy
    assert True is test_speos.close()
    assert False is test_speos.client.healthy
    speos_loc.unlink()
    speos_loc.parent.rmdir()
    speos_loc.parent.parent.rmdir()
