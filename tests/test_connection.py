import grpc
import pytest

from ansys.pyoptics.speos.client import SpeosClient, wait_until_healthy


def test_wait_until_healthy():
    # create a bogus channel
    channel = grpc.insecure_channel("9.0.0.1:80")
    with pytest.raises(TimeoutError):
        wait_until_healthy(channel, timeout=1.0)


@pytest.fixture()
def client(speos):
    # this uses DEFAULT_HOST and DEFAULT_PORT which are set by environment
    # variables in the workflow
    return SpeosClient()


def test_client_init(client):
    assert client.healthy is True
    client_repr = repr(client)
    assert "Target" in client_repr
    assert "Connection" in client_repr


def test_client_close(client):
    client.close()
    assert client._closed
    assert "Closed" in str(client)
