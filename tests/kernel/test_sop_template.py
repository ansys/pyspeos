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

"""
Test basic sop template database connection.
"""

import json
import os

import grpc
import pytest

from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
from ansys.speos.core.speos import Speos
from tests.conftest import test_path


def test_sop_template(speos: Speos):
    """Test the sop template creation."""
    assert speos.client.healthy is True
    # Get DB
    sop_t_db = speos.client.sop_templates()  # Create sop_template stub from client channel

    # Mirror
    sop_t_mirror = sop_t_db.create(
        message=ProtoSOPTemplate(
            name="mirror_0",
            description="Mirror sop template",
            mirror=ProtoSOPTemplate.Mirror(reflectance=100.0),
        )
    )
    assert sop_t_mirror.key != ""

    # OpticalPolished
    sop_t_optical_polished = sop_t_db.create(
        message=ProtoSOPTemplate(
            name="optical_polished_0",
            description="Optical polished sop template",
            optical_polished=ProtoSOPTemplate.OpticalPolished(),
        )
    )
    assert sop_t_optical_polished.key != ""

    # Library
    sop_t_lib = sop_t_db.create(
        message=ProtoSOPTemplate(
            name="library_0",
            description="library sop template",
            library=ProtoSOPTemplate.Library(
                sop_file_uri=os.path.join(test_path, "Gaussian Fresnel 10 deg.anisotropicbsdf")
            ),
        )
    )
    assert sop_t_lib.key != ""

    # Example of wrong sop template

    with pytest.raises(grpc.RpcError) as exc_info:
        sop_t_db.create(
            message=ProtoSOPTemplate(
                name="mirror_0",
                description="Mirror sop template",
                mirror=ProtoSOPTemplate.Mirror(reflectance=150.0),
            )
        )
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "OPTSOPReflectionOutOfBound"

    sop_t_mirror.delete()
    sop_t_optical_polished.delete()
    sop_t_lib.delete()
