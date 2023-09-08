"""
Test basic spectrum database connection.
"""
import pytest

from ansys.speos.core.client import SpeosClient
from conftest import config


@pytest.fixture(scope="function")
def client(speos):
    # this uses DEFAULT_HOST and DEFAULT_PORT which are set by environment
    # variables in the workflow
    return SpeosClient(port=str(config.get("SpeosServerPort")))


def test_client_spectrum_init(client: SpeosClient):
    """Test the instantiation of a client from the default constructor."""
    assert client.healthy is True
    # Get DB
    sDB = client.getSpectrumDB()  # Create spectrum stub from client channel
    # Create new blackbody spectrum
    sBB5321 = sDB.NewBlackbody(temperature=5321)
    assert sBB5321.key() != ""
    assert sBB5321.database() is not None
    # Get spectrum data
    sBB5321data = sBB5321.getContent()
    assert sBB5321data.blackbody.temperature == 5321
    # Set data
    sBB5321data.blackbody.temperature = 5326
    sBB5321.setContent(sBB5321data)
    # Duplicate spectrum
    # SBB5321_2 = sBB5321.Clone()

    sBB5321data.blackbody.temperature = 5326
    # Create a new spectrum
    # sp = sDB.CreateBlackbody(temperature = 5000)
    # sp.Delete()
