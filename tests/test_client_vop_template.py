"""
Test basic spectrum database connection.
"""
import json
import os

import grpc
import pytest

from ansys.speos.core.speos import Speos
from ansys.speos.core.vop_template import VOPTemplateFactory
from conftest import test_path


def test_vop_template_factory(speos: Speos):
    """Test the instantiation of a client from the default constructor."""
    assert speos.client.healthy is True
    # Get DB
    vop_t_db = speos.client.vop_templates()  # Create spectrum stub from client channel

    # Opaque
    vop_t_opaque = vop_t_db.create(VOPTemplateFactory.opaque(name="opaque_0", description="Opaque vop template"))
    assert vop_t_opaque.key != ""

    # Optic without constringence
    vop_t_optic0 = vop_t_db.create(
        VOPTemplateFactory.optic(
            name="optic_0", description="Optic vop template without constringence", index=1.5, absorption=0.0
        )
    )
    assert vop_t_optic0.key != ""

    # Optic with constringence
    vop_t_optic1 = vop_t_db.create(
        VOPTemplateFactory.optic(
            name="optic_1",
            description="Optic vop template with constringence",
            index=1.5,
            absorption=0.0,
            constringence=60.0,
        )
    )
    assert vop_t_optic1.key != ""

    # Library
    vop_t_lib = vop_t_db.create(
        VOPTemplateFactory.library(
            name="library_0",
            description="Library vop template",
            material_file_uri=os.path.join(test_path, "AIR.material"),
        )
    )
    assert vop_t_lib.key != ""

    # NonHomogeneous
    vop_t_non_hom = vop_t_db.create(
        VOPTemplateFactory.non_homogeneous(
            name="non_homogeneous_0",
            description="Non Homogeneous vop template",
            gradedmaterial_file_uri=os.path.join(test_path, "Index_1.5_Gradient_0.499_Abs_0.gradedmaterial"),
        )
    )
    assert vop_t_non_hom.key != ""

    # Example of wrong vop template creation : negative absorption
    with pytest.raises(grpc.RpcError) as exc_info:
        vop_t_db.create(
            VOPTemplateFactory.optic(
                name="optic_2", description="Optic vop template with negative absorption", index=1.5, absorption=-50.0
            )
        )
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "OPTUserMaterialBasicHasNegativeAbsorptionValues"

    # constringence < 20
    with pytest.raises(grpc.RpcError) as exc_info:
        vop_t_db.create(
            VOPTemplateFactory.optic(
                name="optic_3",
                description="Optic vop template with constringence < 20",
                index=1.5,
                absorption=0.0,
                constringence=10.0,
            )
        )
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "OPTOutOfRangeValueForFeature"
