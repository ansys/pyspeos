"""
Test basic spectrum database connection.
"""
from ansys.speos.core.spectrum import Spectrum
from ansys.speos.core.speos import Speos


def test_client_spectrum_init(speos: Speos):
    """Test the instantiation of a client from the default constructor."""
    assert speos.client.healthy is True
    # Get DB
    sDB = speos.client.spectrums()  # Create spectrum stub from client channel

    # Create new blackbody spectrum
    sBB5321 = Spectrum()
    sBB5321.name = "myspectrm"
    sBB5321.description = "tion"
    sBB5321.blackbody.temperature = 5321
    sBB5321 = sDB.Create(sBB5321)
    assert sBB5321.key != ""
    assert sBB5321.stub is not None
    # Get data
    sBB5321data = sBB5321.get()
    assert sBB5321data.blackbody.temperature == 5321
    # Update data
    sBB5321data.blackbody.temperature = 5326
    sBB5321.set(sBB5321data)
    sBB5321data = sBB5321.get()
    assert sBB5321data.blackbody.temperature == 5326
    # New from scratch spectrum
    sM659data = Spectrum()
    sM659data.name = "blipo"
    sM659data.description = "tion"
    sM659data.monochromatic.wavelength = 659
    SM659 = sDB.Create(sM659data)
    # Duplicate
    SM659_bis = sDB.Create(SM659.get())
    assert SM659_bis.stub == SM659.stub
    assert SM659_bis.key != SM659.key
    assert SM659_bis.get() == SM659.get()
    # Delete
    SM659_bis.delete()
