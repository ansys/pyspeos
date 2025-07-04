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

"""Unit Test Configuration Module.

This module loads the configuration for PySpeos unit tests.
The configuration can be changed by modifying a file called local_config.json in the same
directory as this module.
"""

import json
import logging
import logging as deflogging  # Default logging
import os
from pathlib import Path

import pytest

from ansys.speos.core import LOG
from ansys.speos.core.generic.constants import MAX_CLIENT_MESSAGE_SIZE
from ansys.speos.core.speos import Speos

try:
    import pyvista as pv

    pv.OFF_SCREEN = True
    pv.global_theme.window_size = [500, 500]
except ImportError:
    pass

IMAGE_RESULTS_DIR = Path(Path(__file__).parent, "image_results")
IS_WINDOWS = os.name == "nt"


@pytest.fixture(scope="session")
def speos():
    """Pytest ficture to create Speos objects for all unit, integration and workflow tests.

    Yields
    ------
    ansys.speos.cor.speos.Speos
        Speos Class instance

    Returns
    -------
    None
    """
    # Log to file - accepts str or Path objects, Path is passed for testing/coverage purposes.
    log_file_path = Path(__file__).absolute().parent / "logs" / "integration_tests_logs.txt"
    Path(log_file_path).unlink(missing_ok=True)

    speos = Speos(
        logging_level=logging.DEBUG,
        logging_file=log_file_path,
        port=str(config.get("SpeosServerPort")),
        message_size=MAX_CLIENT_MESSAGE_SIZE * 128,
    )

    yield speos


local_path = Path(os.path.realpath(__file__)).parent

# Load the local config file
local_config_file = local_path / "local_config.json"
if local_config_file.exists():
    with local_config_file.open() as f:
        config = json.load(f)
else:
    raise ValueError("Missing local_config.json file")


# set test_path var depending on if we are using the servers in a docker container or not
local_test_path = local_path / "assets"
if config.get("SpeosServerOnDocker"):
    test_path = "/app/assets/"
else:
    test_path = local_test_path


# Define default pytest logging level to DEBUG and stdout

LOG.setLevel(level="DEBUG")
LOG.log_to_stdout()


@pytest.fixture
def fake_record():
    """Emulate logger.

    Returns
    -------
    logger :
        fake logger

    """

    def inner_fake_record(
        logger,
        msg="This is a message",
        instance_name="172.1.1.1:52000",
        handler_index=0,
        name_logger=None,
        level=deflogging.DEBUG,
        filename="fn",
        lno=0,
        args=(),
        exc_info=None,
        extra={},
    ):
        """
        Fake log records using the format from the logger handler.

        Parameters
        ----------
        logger : logging.Logger
            A logger object with at least a handler.
        msg : str, default: "This is a message"
            Message to include in the log record.
        instance_name : str, default: "172.1.1.1:52000"
            Name of the instance.
        handler_index : int, default: 0
            Index of the selected handler in case you want to test a handler different than
            the first one.
        level : int, default: deflogging.DEBUG
            Logging level.
        filename : str, default: fn
            Name of the file name. [FAKE].
        lno : int, default: 0
            Line where the fake log is recorded [FAKE].
        args : tuple, default: ()
            Other arguments.
        exc_info : [type], default: None
            Exception information.
        extra : dict, default: {}
            Extra arguments, one of them should be 'instance_name'.

        Returns
        -------
        str
            The formatted message according to the handler.
        """
        sinfo = None
        if not name_logger:
            name_logger = logger.name

        if "instance_name" not in extra.keys():
            extra["instance_name"] = instance_name

        record = logger.makeRecord(
            name_logger,
            level,
            filename,
            lno,
            msg,
            args=args,
            exc_info=exc_info,
            extra=extra,
            sinfo=sinfo,
        )
        handler = logger.handlers[handler_index]
        return handler.format(record)

    return inner_fake_record
