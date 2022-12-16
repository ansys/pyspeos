"""
Unit Test Configuration Module
-------------------------------

Description
===========
This module loads the configuration for pyoptics unit tests.
The configuration can be changed by modifying a file called local_config.json in the same
directory as this module.
"""
import json
import os

import grpc


def grpc_server_on(config) -> bool:
    TIMEOUT_SEC = 60
    try:
        with grpc.insecure_channel(f"localhost:" + str(config.get("SpeosServerPort"))) as channel:
            grpc.channel_ready_future(channel).result(timeout=TIMEOUT_SEC)
            return True
    except:
        return False


local_path = os.path.dirname(os.path.realpath(__file__))

# Load the local config file
local_config_file = os.path.join(local_path, "local_config.json")
if os.path.exists(local_config_file):
    with open(local_config_file) as f:
        config = json.load(f)
else:
    raise ValueError("Missing local_config.json file")


# set test_path var depending on if we are using the servers in a docker container or not
local_test_path = os.path.join(local_path, "assets/")
if config.get("SpeosServerOnDocker"):
    test_path = "/app/assets/"
else:
    test_path = local_test_path

# Wait for the grpc server - in case the timeout is reached raise an error
if not grpc_server_on(config):
    raise ValueError("Start SpeosRPC_Server - Timeout reached.")

import logging as deflogging  # Default logging

import pytest

# Define default pytest logging level to DEBUG and stdout
from ansys.pyoptics.speos import LOG

LOG.setLevel(level="DEBUG")
LOG.log_to_stdout()


@pytest.fixture
def fake_record():
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
        Function to fake log records using the format from the logger handler.

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
