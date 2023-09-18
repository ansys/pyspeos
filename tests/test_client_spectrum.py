"""
Test basic spectrum database connection.
"""
import pytest

from ansys.speos.core.client import SpeosClient
from ansys.speos.core.spectrum import Spectrum
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
    sDB = client.get_spectrum_db()  # Create spectrum stub from client channel
    # Create new blackbody spectrum
    sBB5321 = sDB.NewBlackbody(temperature=5321)
    assert sBB5321.key() != ""
    assert sBB5321.database() is not None
    # Get data
    sBB5321data = sBB5321.read_content()
    assert sBB5321data.blackbody.temperature == 5321
    # Update data
    sBB5321data.blackbody.temperature = 5326
    sBB5321.update_content(sBB5321data)
    sBB5321data = sBB5321.read_content()
    assert sBB5321data.blackbody.temperature == 5326
    # New from scratch spectrum
    sM659data = Spectrum.Content()
    sM659data.name = "blipo"
    sM659data.description = "tion"
    sM659data.monochromatic.wavelength = 659
    SM659 = sDB.New(sM659data)
    # Duplicate
    SM659_bis = sDB.New(SM659.read_content())
    SM659_bisdata = SM659_bis.read_content()
    assert SM659_bis.key() != SM659.key()
    assert SM659_bisdata == sM659data
    # Delete
    SM659_bis.delete()
