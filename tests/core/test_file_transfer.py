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

"""Unit test for file transfer service and helper."""

from pathlib import Path

from ansys.speos.core.generic.file_transfer import FileTransfer
from ansys.speos.core.speos import Speos
from tests.conftest import local_test_path


def test_transfer_file(speos: Speos):
    """Test to check file transfer."""
    file_transfer = FileTransfer(speos_client=speos.client)

    # local file upload to the server
    brdf_path = Path(local_test_path) / "Test_not_interpolated.brdf"
    upload_response = file_transfer.upload_file(brdf_path)
    file_uri0 = upload_response.info.uri
    assert upload_response.info.uri != ""
    assert upload_response.info.file_name == "Test_not_interpolated.brdf"
    assert upload_response.info.file_size == brdf_path.stat().st_size

    # Upload but to a reserved file item
    reserved_uri1 = file_transfer.reserve()
    upload_response = file_transfer.upload_file(brdf_path, reserved_uri1)
    assert upload_response.info.uri == reserved_uri1
    assert upload_response.info.file_name == "Test_not_interpolated.brdf"
    assert upload_response.info.file_size == brdf_path.stat().st_size

    # Download
    download_location = Path(local_test_path) / "file_transfer_tests_download"
    download_location.mkdir(exist_ok=True)
    download_response = file_transfer.download_file(file_uri0, download_location)
    assert download_response.info.uri == file_uri0
    assert download_response.info.file_name == "Test_not_interpolated.brdf"
    downloaded_file = download_location / download_response.info.file_name
    assert downloaded_file.exists()
    assert downloaded_file.is_file()
    assert brdf_path.stat().st_size == downloaded_file.stat().st_size
    downloaded_file.unlink()

    # Delete files on server
    file_transfer.delete(file_uri=file_uri0)
    file_transfer.delete(file_uri=reserved_uri1)
    # Delete new folder created for this test
    download_location.rmdir()


def _check_uploaded_files(
    upload_responses, expected_file_names, speos_file_name, reserved_file_uri=""
):
    assert len(upload_responses) == 3
    speos_file_upload_res = None
    for upload_response in upload_responses:
        assert upload_response.info.uri != ""

        assert upload_response.info.file_name in expected_file_names
        expected_file_names.remove(upload_response.info.file_name)

        if upload_response.info.file_name == speos_file_name:
            speos_file_upload_res = upload_response
            if reserved_file_uri != "":
                assert upload_response.info.uri == reserved_file_uri

    assert len(expected_file_names) == 0
    return speos_file_upload_res


def _check_downloaded_files(download_responses, expected_file_names, download_location):
    assert len(download_responses) == 3
    for download_response in download_responses:
        assert download_response.info.uri != ""
        assert download_response.info.file_name in expected_file_names
        expected_file_names.remove(download_response.info.file_name)
        downloaded_file = download_location / download_response.info.file_name
        assert downloaded_file.exists()
        assert downloaded_file.is_file()
        downloaded_file.unlink()
    assert len(expected_file_names) == 0


def test_transfer_folder(speos: Speos):
    """Test to check folder transfer."""
    file_transfer = FileTransfer(speos_client=speos.client)

    # local file upload to the server
    speos_folder_path = Path(local_test_path) / "LG_50M_Colorimetric_short.sv5"
    speos_file_path = speos_folder_path / "LG_50M_Colorimetric_short.sv5"
    upload_responses = file_transfer.upload_folder(
        speos_folder_path, "LG_50M_Colorimetric_short.sv5"
    )

    expected_file_names = [
        "LG_50M_Colorimetric_short.sv5",
        "Blue Spectrum.spectrum",
        "Red Spectrum.spectrum",
    ]
    speos_file_upload_res = _check_uploaded_files(
        upload_responses, expected_file_names, speos_file_path.name
    )

    # Upload but to a reserved file item
    reserved_uri1 = file_transfer.reserve()
    upload_responses = file_transfer.upload_folder(
        speos_folder_path, "LG_50M_Colorimetric_short.sv5", reserved_uri1
    )

    expected_file_names = [
        "LG_50M_Colorimetric_short.sv5",
        "Blue Spectrum.spectrum",
        "Red Spectrum.spectrum",
    ]
    _check_uploaded_files(
        upload_responses, expected_file_names, speos_file_path.name, reserved_uri1
    )

    # Download
    download_location = Path(local_test_path) / "file_transfer_tests_download2"
    download_location.mkdir(exist_ok=True)
    download_responses = file_transfer.download_folder(
        speos_file_upload_res.info.uri, download_location
    )

    expected_file_names = [
        "LG_50M_Colorimetric_short.sv5",
        "Blue Spectrum.spectrum",
        "Red Spectrum.spectrum",
    ]
    _check_downloaded_files(download_responses, expected_file_names, download_location)

    # Delete speos files and all their dependencies
    file_transfer.delete(file_uri=speos_file_upload_res.info.uri)
    file_transfer.delete(file_uri=reserved_uri1)
    # Delete new folder created for this test
    download_location.rmdir()
