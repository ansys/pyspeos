# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
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

"""Test using combine_speos module in workflow layer."""

from pathlib import Path

import pytest

from ansys.speos.core.generic.file_transfer import FileTransfer
from ansys.speos.core.project import Project
from ansys.speos.core.simulation import SimulationDirect
from ansys.speos.core.speos import Speos
from ansys.speos.core.workflow.open_result import export_xmp_to_image
from tests.conftest import local_test_path, test_path


@pytest.mark.supported_speos_versions(min=261)
def test_export_xmp_to_image(speos: Speos):
    """Test exporting XMP file to image."""
    p = Project(
        speos=speos,
        path=test_path / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5",
    )
    sim_feat: SimulationDirect = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)[
        0
    ]
    results = sim_feat.compute_CPU()
    print(results)

    # Look for the first XMP file encountered.
    xmp_name_to_export = Path()
    for result in results:
        if result.HasField("path") and result.path.endswith(".xmp"):
            xmp_name_to_export = Path(result.path).name
            break
        elif result.HasField("upload_response") and result.upload_response.info.file_name.endswith(
            ".xmp"
        ):
            xmp_name_to_export = result.upload_response.info.file_name
            break

    image_exported = export_xmp_to_image(
        simulation_feature=sim_feat, result_name=xmp_name_to_export
    )
    if image_exported.HasField("path"):
        downloaded_image = Path(image_exported.path)
        assert downloaded_image.is_file() is True
        downloaded_image.unlink()
    elif image_exported.HasField("upload_response"):
        file_transfer = FileTransfer(speos.client)
        file_transfer.download_file(
            file_uri=image_exported.upload_response.info.uri, download_location=local_test_path
        )
        downloaded_image = local_test_path / image_exported.upload_response.info.file_name
        assert downloaded_image.is_file() is True
        downloaded_image.unlink()
