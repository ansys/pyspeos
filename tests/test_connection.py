import json
import os

import grpc
import pytest

from ansys.pyoptics.speos.client import SpeosClient, wait_until_healthy

local_path = os.path.dirname(os.path.realpath(__file__))

# Load the local config file
local_config_file = os.path.join(local_path, "local_config.json")
if os.path.exists(local_config_file):
    with open(local_config_file) as f:
        config = json.load(f)
else:
    raise ValueError("Missing local_config.json file")


@pytest.fixture(scope="function")
def client():
    return SpeosClient(port=(config.get("SpeosServerPort")))


def test_wait_until_healthy():
    # create a bogus channel
    channel = grpc.insecure_channel("9.0.0.1:80")
    with pytest.raises(TimeoutError):
        wait_until_healthy(channel, timeout=1.0)


def test_client_init(client: SpeosClient):
    assert client.healthy is True
    client_repr = repr(client)
    assert "Target" in client_repr


def test_client_close(client: SpeosClient):
    client.close()
    assert client._closed
    assert "Closed" in str(client)
