"""
Test source template.
"""
from os import path

from ansys.speos.core.source_template import SourceTemplateHelper
from ansys.speos.core.spectrum import SpectrumHelper
from ansys.speos.core.speos import Speos
from conftest import test_path


def test_client_source_template(speos: Speos):
    """Test the instantiation of a client from the default constructor."""
    assert speos.client.healthy is True

    # Get DB
    source_t_db = speos.client.source_templates()  # Create source_templates stub from client channel

    # Create SourceTemplateLink by using helper method - this way, no need to write data
    # The source template created is stored in DB
    src_t_luminaire = SourceTemplateHelper.create_luminaire(
        source_template_stub=source_t_db,
        name="luminaire_0",
        description="Luminaire source",
        intensity_file_uri=path.join(test_path, "IES_C_DETECTOR.ies"),
        spectrum=SpectrumHelper.create_blackbody(
            spectrum_stub=speos.client.spectrums(),
            name="blackbody_2500",
            description="blackbody spectrum - T 2500K",
            temperature=2500.0,
        ),
    )
    assert src_t_luminaire.key != ""
    assert src_t_luminaire.stub is not None
