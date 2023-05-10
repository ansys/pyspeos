"""
Test basic client connection.
"""
from grpc import insecure_channel
import pytest

from ansys.pyoptics.speos.client import SpeosClient
from conftest import config


@pytest.fixture(scope="function")
def client(speos):
    # this uses DEFAULT_HOST and DEFAULT_PORT which are set by environment
    # variables in the workflow
    return SpeosClient(port=str(config.get("SpeosServerPort")))


def test_client_init(client: SpeosClient):
    """Test the instantiation of a client from the default ctor."""
    assert client.healthy is True


def test_client_through_channel():
    """Test the instantiation of a client from a gRPC channel."""
    target = "localhost:" + str(config.get("SpeosServerPort"))
    channel = insecure_channel(target)
    client = SpeosClient(channel=channel)
    client_repr = repr(client)
    assert "Target" in client_repr
    assert "Connection" in client_repr
    assert client.healthy is True
    assert client.target() == target
    assert client.channel
