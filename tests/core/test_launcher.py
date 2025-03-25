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

import time

import psutil

from ansys.speos.core.launcher import launch_local_speos_rpc_server
from tests.conftest import config


def test_local_session():
    """Test local session launch and close."""
    port = config.get("SpeosServerPort") + 1
    if config.get("SpeosServerOnDocker"):
        speos_loc = config.get("SpeosDockerLocation")
        name = "SpeosRPC_Server.x"
    else:
        speos_loc = None
        name = "SpeosRPC_Server.exe"
    test_speos = launch_local_speos_rpc_server(port=port, speos_rpc_loc=speos_loc)
    running = name in (p.name() for p in psutil.process_iter())
    assert running
    test_speos.close()
    time.sleep(5)
    running = name in (p.name() for p in psutil.process_iter())
    assert not running
