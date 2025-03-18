# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Test basic vop template database connection."""

import json
from pathlib import Path

import grpc
import pytest

from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
from ansys.speos.core.speos import Speos
from tests.conftest import test_path


def test_vop_template(speos: Speos):
    """Test the vop template creation."""
    assert speos.client.healthy is True
    # Get DB
    vop_t_db = speos.client.vop_templates()  # Create spectrum stub from client channel

    # Opaque
    vop_t_opaque = vop_t_db.create(
        ProtoVOPTemplate(
            name="opaque_0",
            description="Opaque vop template",
            opaque=ProtoVOPTemplate.Opaque(),
        )
    )
    assert vop_t_opaque.key != ""

    # Optic without constringence
    vop_t_optic0 = vop_t_db.create(
        ProtoVOPTemplate(
            name="optic_0",
            description="Optic vop template without constringence",
            optic=ProtoVOPTemplate.Optic(index=1.5, absorption=0.0),
        )
    )
    assert vop_t_optic0.key != ""

    # Optic with constringence
    vop_t_optic1 = vop_t_db.create(
        ProtoVOPTemplate(
            name="optic_1",
            description="Optic vop template with constringence",
            optic=ProtoVOPTemplate.Optic(index=1.5, absorption=0.0, constringence=60.0),
        )
    )
    assert vop_t_optic1.key != ""

    # Library
    vop_t_lib = vop_t_db.create(
        ProtoVOPTemplate(
            name="library_0",
            description="Library vop template",
            library=ProtoVOPTemplate.Library(
                material_file_uri=str(Path(test_path) / "AIR.material")
            ),
        )
    )
    assert vop_t_lib.key != ""

    # NonHomogeneous
    vop_t_non_hom = vop_t_db.create(
        ProtoVOPTemplate(
            name="non_homogeneous_0",
            description="Non Homogeneous vop template",
            non_homogeneous=ProtoVOPTemplate.NonHomogeneous(
                gradedmaterial_file_uri=str(
                    Path(test_path) / "Index_1.5_Gradient_0.499_Abs_0.gradedmaterial"
                )
            ),
        )
    )
    assert vop_t_non_hom.key != ""

    # Example of wrong vop template creation : negative absorption
    with pytest.raises(grpc.RpcError) as exc_info:
        vop_t_db.create(
            ProtoVOPTemplate(
                name="optic_2",
                description="Optic vop template with negative absorption",
                optic=ProtoVOPTemplate.Optic(index=1.5, absorption=-50.0),
            )
        )
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "OPTUserMaterialBasicHasNegativeAbsorptionValues"

    # constringence < 20
    with pytest.raises(grpc.RpcError) as exc_info:
        vop_t_db.create(
            ProtoVOPTemplate(
                name="optic_3",
                description="Optic vop template with constringence < 20",
                optic=ProtoVOPTemplate.Optic(index=1.5, absorption=0.0, constringence=10.0),
            )
        )
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "OPTOutOfRangeValueForFeature"

    vop_t_opaque.delete()
    vop_t_optic0.delete()
    vop_t_optic1.delete()
    vop_t_lib.delete()
    vop_t_non_hom.delete()
