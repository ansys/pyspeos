"""
Test basic spectrum database connection.
"""
from os import path

from ansys.speos.core.spectrum import Spectrum, SpectrumFactory
from ansys.speos.core.speos import Speos
from conftest import test_path


def test_client_spectrum_init(speos: Speos):
    """Test the instantiation of a client from the default constructor."""
    assert speos.client.healthy is True
    # Get DB
    spec_db = speos.client.spectrums()  # Create spectrum stub from client channel

    # Create SpectrumLink from data:
    s_ph_data = Spectrum()
    s_ph_data.name = "predefined_halogen_0"
    s_ph_data.description = "Predefined spectrum"
    s_ph_data.predefined.halogen.SetInParent()
    s_ph = spec_db.create(message=s_ph_data)  # at this step the spectrum is stored in DB
    assert s_ph.key != ""
    assert s_ph.stub is not None

    # Create SpectrumLink and use factory to get message data
    s_bb_5321 = spec_db.create(
        message=SpectrumFactory.blackbody(name="blackbody_0", description="Blackbody spectrum", temperature=5321.0)
    )  # the spectrum created is stored in DB
    # Get data
    s_bb_5321_data = s_bb_5321.get()
    assert s_bb_5321_data.blackbody.temperature == 5321
    # Update data
    s_bb_5321_data.blackbody.temperature = 5326  # data modified only locally, not in DB
    s_bb_5321.set(s_bb_5321_data)  # data modified in DB thanks to set method
    s_bb_5321_data = s_bb_5321.get()  # retrieve value from DB to verify that it is correctly updated
    assert s_bb_5321_data.blackbody.temperature == 5326
    # Delete
    s_bb_5321.delete()  # Delete from DB

    # Create SpectrumLink
    s_m_659 = spec_db.create(
        SpectrumFactory.monochromatic(name="monochr_0", description="Monochromatic spectrum", wavelength=659.0)
    )
    # Duplicate = same data but different keys
    s_m_659_bis = spec_db.create(s_m_659.get())
    assert s_m_659_bis.stub == s_m_659.stub
    assert s_m_659_bis.key != s_m_659.key
    assert s_m_659_bis.get() == s_m_659.get()

    # Delete all spectrums from DB
    for spec in spec_db.list():
        spec.delete()


def test_spectrum_factory(speos: Speos):
    """Test the instantiation of a client from the default constructor."""
    assert speos.client.healthy is True
    # Get DB
    spec_db = speos.client.spectrums()  # Create spectrum stub from client channel

    # Monochromatic
    spec_mono = spec_db.create(
        SpectrumFactory.monochromatic(name="monochr_1", description="Monochromatic spectrum", wavelength=659.0)
    )
    assert spec_mono.key != ""

    # Blackbody
    spec_blackbody = spec_db.create(
        message=SpectrumFactory.blackbody(name="blackbody_1", description="Blackbody spectrum", temperature=5321.0)
    )
    assert spec_blackbody.key != ""

    # Sampled
    s_sampled = spec_db.create(
        message=SpectrumFactory.sampled(
            name="sampled_1",
            description="Sampled spectrum",
            wavelengths=[500.0, 550.0, 600.0],
            values=[20.5, 100.0, 15.6],
        )
    )
    assert s_sampled.key != ""

    # Library
    spectrum_path = path.join(test_path, path.join("CameraInputFiles", "CameraSensitivityBlue.spectrum"))
    s_lib = spec_db.create(
        message=SpectrumFactory.library(name="library_1", description="Library spectrum", file_uri=spectrum_path)
    )
    assert s_lib.key != ""

    # Predefined
    s_predefined_incandescent = spec_db.create(
        SpectrumFactory.predefined(
            name="predefined_1",
            description="Predefined incandescent spectrum",
            type=SpectrumFactory.PredefinedType.Incandescent,
        )
    )
    assert s_predefined_incandescent.key != ""

    # Delete all spectrums from DB
    for spec in spec_db.list():
        spec.delete()
