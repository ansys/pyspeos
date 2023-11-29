"""
Test basic sop template database connection.
"""
import json
import os

import grpc
import pytest

from ansys.speos.core.sop_template import SOPTemplateFactory
from ansys.speos.core.speos import Speos
from conftest import test_path


def test_sop_template_factory(speos: Speos):
    """Test the sop template factory."""
    assert speos.client.healthy is True
    # Get DB
    sop_t_db = speos.client.sop_templates()  # Create sop_template stub from client channel

    # Mirror
    sop_t_mirror = sop_t_db.create(
        message=SOPTemplateFactory.mirror(name="mirror_0", description="Mirror sop template", reflectance=100.0)
    )
    assert sop_t_mirror.key != ""

    # OpticalPolished
    sop_t_optical_polished = sop_t_db.create(
        message=SOPTemplateFactory.optical_polished(name="optical_polished_0", description="Optical polished sop template")
    )
    assert sop_t_optical_polished.key != ""

    # Library
    sop_t_lib = sop_t_db.create(
        message=SOPTemplateFactory.library(
            name="library_0",
            description="library sop template",
            sop_file_uri=os.path.join(test_path, "Gaussian Fresnel 10 deg.anisotropicbsdf"),
        )
    )
    assert sop_t_lib.key != ""

    # Example of wrong sop template
    with pytest.raises(grpc.RpcError) as exc_info:
        sop_t_db.create(message=SOPTemplateFactory.mirror(name="mirror_0", description="Mirror sop template", reflectance=150.0))
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "OPTSOPReflectionOutOfBound"

    sop_t_mirror.delete()
    sop_t_optical_polished.delete()
    sop_t_lib.delete()
