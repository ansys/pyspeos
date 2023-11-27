"""
Test basic spectrum database connection.
"""
from ansys.speos.core.spectrum import Spectrum, SpectrumHelper
from ansys.speos.core.speos import Speos


def test_client_spectrum_init(speos: Speos):
    """Test the instantiation of a client from the default constructor."""
    assert speos.client.healthy is True
    # Get DB
    sDB = speos.client.spectrums()  # Create spectrum stub from client channel

    # Create SpectrumLink from data:
    sPHdata = Spectrum()
    sPHdata.name = "predefined_halogen_0"
    sPHdata.description = "Predefined spectrum"
    sPHdata.predefined.halogen.SetInParent()
    sPH = sDB.create(message=sPHdata)  # at this step the spectrum is stored in DB
    assert sPH.key != ""
    assert sPH.stub is not None

    # Create SpectrumLink by using helper method - this way, no need to write data
    sBB5321 = SpectrumHelper.create_blackbody(
        spectrum_stub=sDB, name="blackbody_0", description="Blackbody spectrum", temperature=5321.0
    )  # the spectrum created is stored in DB
    # Get data
    sBB5321data = sBB5321.get()
    assert sBB5321data.blackbody.temperature == 5321
    # Update data
    sBB5321data.blackbody.temperature = 5326  # data modified only locally, not in DB
    sBB5321.set(sBB5321data)  # data modified in DB thanks to set method
    sBB5321data = sBB5321.get()  # retrieve value from DB to verify that it is correctly updated
    assert sBB5321data.blackbody.temperature == 5326
    # Delete
    sBB5321.delete()  # Delete from DB

    # Create SpectrumLink by using helper method
    sM659 = SpectrumHelper.create_monochromatic(
        spectrum_stub=sDB, name="monochr_0", description="Monochromatic spectrum", wavelength=659.0
    )
    # Duplicate = same data but different keys
    sM659_bis = sDB.create(sM659.get())
    assert sM659_bis.stub == sM659.stub
    assert sM659_bis.key != sM659.key
    assert sM659_bis.get() == sM659.get()

    # Delete all spectrums from DB
    for spec in sDB.list():
        spec.delete()
