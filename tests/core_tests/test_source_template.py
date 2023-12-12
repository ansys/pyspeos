"""
Test source template.
"""
import json
import os

import grpc
import pytest

from ansys.speos.core.intensity_template import IntensityTemplateFactory
from ansys.speos.core.source_template import SourceTemplateFactory
from ansys.speos.core.spectrum import SpectrumFactory
from ansys.speos.core.speos import Speos
from conftest import test_path


def test_source_template_factory(speos: Speos):
    """Test the source template factory."""
    assert speos.client.healthy is True

    # Get DB
    source_t_db = speos.client.source_templates()  # Create source_templates stub from client channel
    spec_db = speos.client.spectrums()  # Create spectrums stub from client channel
    intens_t_db = speos.client.intensity_templates()  # Create intensity_templates stub from client channel

    # This spectrum will be used by both src_t_luminaire and src_t_surface
    spec_bb_2500 = spec_db.create(
        SpectrumFactory.blackbody(
            name="blackbody_2500",
            description="blackbody spectrum - T 2500K",
            temperature=2500.0,
        )
    )

    # This intensity template will be used in several luminaire source template
    intens_t_lamb = intens_t_db.create(
        message=IntensityTemplateFactory.lambertian(
            name="lambertian_180", description="lambertian intensity template 180", total_angle=180.0
        )
    )

    # Luminaire source template with flux from intensity file
    src_t_luminaire = source_t_db.create(
        message=SourceTemplateFactory.luminaire(
            name="luminaire_0",
            description="Luminaire source template",
            intensity_file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies"),
            spectrum=spec_bb_2500,
        ),
    )
    assert src_t_luminaire.key != ""

    # Surface with luminous flux, exitance constant
    src_t_surface = source_t_db.create(
        message=SourceTemplateFactory.surface(
            name="surface_0",
            description="Surface source template",
            intensity_template=intens_t_lamb,
            flux=SourceTemplateFactory.Flux(unit=SourceTemplateFactory.Flux.Unit.Lumen, value=683.0),
            spectrum=spec_bb_2500,
        )
    )
    assert src_t_surface.key != ""

    # Some parameters are not compatible
    # For example a Surface source template with flux from intensity file AND
    # no intensity file provided (instead lambertian intensity template)
    with pytest.raises(grpc.RpcError) as exc_info:
        source_t_db.create(
            message=SourceTemplateFactory.surface(
                name="surface_err0",
                description="Surface source template in error",
                intensity_template=intens_t_lamb,
                flux=None,
                spectrum=spec_bb_2500,
            )
        )
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "FluxFromIntensityWithoutFile"

    # Another incompatibility
    # Surface source template with spectrum from xmp file AND no xmp file provided
    with pytest.raises(grpc.RpcError) as exc_info:
        source_t_db.create(
            message=SourceTemplateFactory.surface(
                name="surface_err1",
                description="Surface source template in error",
                intensity_template=intens_t_lamb,
                flux=SourceTemplateFactory.Flux(unit=SourceTemplateFactory.Flux.Unit.Lumen, value=683.0),
            )
        )
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "OPTNullSpectrum"

    src_t_luminaire.delete()
    src_t_surface.delete()
    spec_bb_2500.delete()
    intens_t_lamb.delete()
