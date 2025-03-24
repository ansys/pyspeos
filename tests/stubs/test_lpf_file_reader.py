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

"""Unit test for LPF reader service."""

from pathlib import Path

import ansys.api.speos.file.v1.file_transfer as file_transfer_helper__v1
import ansys.api.speos.file.v1.file_transfer_pb2 as file_transfer__v1__pb2
import ansys.api.speos.file.v1.file_transfer_pb2_grpc as file_transfer__v1__pb2_grpc
import ansys.api.speos.lpf.v2.lpf_file_reader_pb2 as lpf_file_reader__v2__pb2
import ansys.api.speos.lpf.v2.lpf_file_reader_pb2_grpc as lpf_file_reader__v2__pb2_grpc
from ansys.speos.core.speos import Speos
from tests.conftest import local_test_path, test_path


def test_lpf_file_reader_mono_v2_direct_simu(speos: Speos):
    """Test to check lpf reader for direct simulation."""
    # Lpf file reader creation
    stub = lpf_file_reader__v2__pb2_grpc.LpfFileReader_MonoStub(speos.client.channel)

    # Init with file local path
    path = str(Path(test_path) / "basic_DirectSimu.lpf")
    stub.InitLpfFileName(lpf_file_reader__v2__pb2.InitLpfFileName_Request_Mono(lpf_file_uri=path))

    # GetInformation
    res_information = stub.GetInformation(lpf_file_reader__v2__pb2.GetInformation_Request_Mono())
    nb_of_traces = res_information.nb_of_traces
    assert nb_of_traces == 24817
    assert res_information.nb_of_xmps == 3
    assert (
        res_information.has_sensor_contributions is False
    )  # No contributions stored in Direct simu
    assert len(res_information.sensor_names) == 3
    assert res_information.sensor_names[0] == "Irradiance Sensor (0)"
    assert res_information.sensor_names[2] == "Irradiance Sensor (2)"

    # Read
    raypaths = []
    for rp in stub.Read(lpf_file_reader__v2__pb2.Read_Request_Mono()):
        raypaths.append(rp)
    assert len(raypaths) == nb_of_traces

    # Check result (first entry)
    expected_nb_of_impact = 5
    assert len(raypaths[0].impacts) == expected_nb_of_impact
    assert raypaths[0].impacts[1] == lpf_file_reader__v2__pb2.TripletFloat(
        x=3.19368935, y=14.999999, z=-3.94779062
    )
    assert len(raypaths[0].wavelengths) == expected_nb_of_impact
    assert raypaths[0].wavelengths[1] == 691.44708251953125
    assert len(raypaths[0].body_context_ids) == expected_nb_of_impact
    assert raypaths[0].body_context_ids[1] == 2001802324
    assert len(raypaths[0].unique_face_ids) == expected_nb_of_impact
    assert raypaths[0].unique_face_ids[1] == 1815582994
    assert raypaths[0].lastDirection == lpf_file_reader__v2__pb2.TripletFloat(
        x=0.0606396869, y=0.995341122, z=-0.0749590397
    )
    assert len(raypaths[0].interaction_statuses) == expected_nb_of_impact
    assert (
        raypaths[0].interaction_statuses[0]
        == lpf_file_reader__v2__pb2.RayPath.PhotonStatus.StatusJustEmitted
    )
    assert (
        raypaths[0].interaction_statuses[1]
        == lpf_file_reader__v2__pb2.RayPath.PhotonStatus.StatusSpecularTransmitted
    )
    assert len(raypaths[0].sensor_contributions) == 0

    # Close
    stub.CloseLpfFileName(lpf_file_reader__v2__pb2.CloseLpfFileName_Request_Mono())


def test_lpf_file_reader_mono_v2_inverse_simu(speos: Speos):
    """Test to check lpf service for inverse simulation."""
    # Lpf file reader creation
    stub = lpf_file_reader__v2__pb2_grpc.LpfFileReader_MonoStub(speos.client.channel)

    # Init with file local path
    path = str(Path(test_path) / "basic_InverseSimu.lpf")
    stub.InitLpfFileName(lpf_file_reader__v2__pb2.InitLpfFileName_Request_Mono(lpf_file_uri=path))

    # GetInformation
    res_information = stub.GetInformation(lpf_file_reader__v2__pb2.GetInformation_Request_Mono())
    nb_of_traces = res_information.nb_of_traces
    assert nb_of_traces == 21044
    assert res_information.nb_of_xmps == 1
    assert res_information.has_sensor_contributions is True  # contributions stored in Inverse simu
    assert len(res_information.sensor_names) == 1
    assert res_information.sensor_names[0] == "Camera_Perfect_Lens_System_V2:3"

    # Read
    raypaths = []
    for rp in stub.Read(lpf_file_reader__v2__pb2.Read_Request_Mono()):
        raypaths.append(rp)
    assert len(raypaths) == nb_of_traces

    # Check sensor_contributions in first raypath
    assert len(raypaths[0].sensor_contributions) == 1
    assert raypaths[0].sensor_contributions[0].sensor_id == 0
    assert raypaths[0].sensor_contributions[
        0
    ].coordinates == lpf_file_reader__v2__pb2.DoubletDouble(
        x=-0.20848463202592682, y=0.1897648665199252
    )

    # Close
    stub.CloseLpfFileName(lpf_file_reader__v2__pb2.CloseLpfFileName_Request_Mono())


def test_lpf_file_reader_multi_v2(speos: Speos):
    """Test to check multifile lpf service."""
    # Lpf file reader multi creation
    stub = lpf_file_reader__v2__pb2_grpc.LpfFileReader_MultiStub(speos.client.channel)

    # Create a reader and retrieve its associated guid
    create_lpf_reader_response = stub.Create(lpf_file_reader__v2__pb2.Create_Request_Multi())
    guid = create_lpf_reader_response.lpf_reader_guid

    # Init with file local path
    path = str(Path(test_path) / "basic_DirectSimu.lpf")
    stub.InitLpfFileName(
        lpf_file_reader__v2__pb2.InitLpfFileName_Request_Multi(
            lpf_reader_guid=guid, lpf_file_uri=path
        )
    )

    # GetInformation
    res_information = stub.GetInformation(
        lpf_file_reader__v2__pb2.GetInformation_Request_Multi(lpf_reader_guid=guid)
    )
    nb_of_traces = res_information.nb_of_traces
    assert nb_of_traces == 24817
    assert res_information.nb_of_xmps == 3

    # Create a second reader
    guid2 = stub.Create(lpf_file_reader__v2__pb2.Create_Request_Multi()).lpf_reader_guid
    # Init second reader
    path2 = str(Path(test_path) / "basic_InverseSimu.lpf")
    stub.InitLpfFileName(
        lpf_file_reader__v2__pb2.InitLpfFileName_Request_Multi(
            lpf_reader_guid=guid2, lpf_file_uri=path2
        )
    )

    # GetInformation and read second
    res_information = stub.GetInformation(
        lpf_file_reader__v2__pb2.GetInformation_Request_Multi(lpf_reader_guid=guid2)
    )
    nb_of_traces2 = res_information.nb_of_traces
    assert nb_of_traces2 == 21044
    raypaths2 = []
    for rp in stub.Read(lpf_file_reader__v2__pb2.Read_Request_Multi(lpf_reader_guid=guid2)):
        raypaths2.append(rp)
    assert len(raypaths2) == nb_of_traces2

    # Check sensor_contributions in first raypath
    assert len(raypaths2[0].sensor_contributions) == 1
    assert raypaths2[0].sensor_contributions[0].sensor_id == 0
    assert raypaths2[0].sensor_contributions[
        0
    ].coordinates == lpf_file_reader__v2__pb2.DoubletDouble(
        x=-0.20848463202592682, y=0.1897648665199252
    )

    # Delete the second reader
    stub.Delete(lpf_file_reader__v2__pb2.Delete_Request_Multi(lpf_reader_guid=guid2))

    # Read the first
    raypaths = []
    for rp in stub.Read(lpf_file_reader__v2__pb2.Read_Request_Multi(lpf_reader_guid=guid)):
        raypaths.append(rp)
    assert len(raypaths) == nb_of_traces

    # Check some result (first entry)
    expected_nb_of_impact = 5
    assert len(raypaths[0].impacts) == expected_nb_of_impact
    assert raypaths[0].impacts[1] == lpf_file_reader__v2__pb2.TripletFloat(
        x=3.19368935, y=14.999999, z=-3.94779062
    )
    assert len(raypaths[0].interaction_statuses) == expected_nb_of_impact
    assert (
        raypaths[0].interaction_statuses[1]
        == lpf_file_reader__v2__pb2.RayPath.PhotonStatus.StatusSpecularTransmitted
    )
    assert len(raypaths[0].sensor_contributions) == 0

    # Close and Delete the first
    stub.CloseLpfFileName(
        lpf_file_reader__v2__pb2.CloseLpfFileName_Request_Multi(lpf_reader_guid=guid)
    )
    stub.Delete(lpf_file_reader__v2__pb2.Delete_Request_Multi(lpf_reader_guid=guid))


def test_lpf_file_reader_mono_v2_direct_simu_with_file_transfer(speos: Speos):
    """Test to check lpf service with file transfer service."""
    # local file upload to the server
    path = str(Path(local_test_path) / "basic_DirectSimu.lpf")
    file_transfer_stub = file_transfer__v1__pb2_grpc.FileTransferServiceStub(speos.client.channel)
    upload_response = file_transfer_helper__v1.upload_file(file_transfer_stub, path)

    # Lpf file reader creation
    stub = lpf_file_reader__v2__pb2_grpc.LpfFileReader_MonoStub(speos.client.channel)

    # Init with uri from file transfer
    stub.InitLpfFileName(
        lpf_file_reader__v2__pb2.InitLpfFileName_Request_Mono(lpf_file_uri=upload_response.info.uri)
    )

    # GetInformation
    res_information = stub.GetInformation(lpf_file_reader__v2__pb2.GetInformation_Request_Mono())
    nb_of_traces = res_information.nb_of_traces
    assert nb_of_traces == 24817
    assert res_information.nb_of_xmps == 3
    assert (
        res_information.has_sensor_contributions is False
    )  # No contributions stored in Direct simu
    assert len(res_information.sensor_names) == 3
    assert res_information.sensor_names[0] == "Irradiance Sensor (0)"
    assert res_information.sensor_names[2] == "Irradiance Sensor (2)"

    # Read
    raypaths = []
    for rp in stub.Read(lpf_file_reader__v2__pb2.Read_Request_Mono()):
        raypaths.append(rp)
    assert len(raypaths) == nb_of_traces

    # Check result (first entry)
    expected_nb_of_impact = 5
    assert len(raypaths[0].impacts) == expected_nb_of_impact
    assert raypaths[0].impacts[1] == lpf_file_reader__v2__pb2.TripletFloat(
        x=3.19368935, y=14.999999, z=-3.94779062
    )
    assert len(raypaths[0].wavelengths) == expected_nb_of_impact
    assert raypaths[0].wavelengths[1] == 691.44708251953125
    assert len(raypaths[0].body_context_ids) == expected_nb_of_impact
    assert raypaths[0].body_context_ids[1] == 2001802324
    assert len(raypaths[0].unique_face_ids) == expected_nb_of_impact
    assert raypaths[0].unique_face_ids[1] == 1815582994
    assert raypaths[0].lastDirection == lpf_file_reader__v2__pb2.TripletFloat(
        x=0.0606396869, y=0.995341122, z=-0.0749590397
    )
    assert len(raypaths[0].interaction_statuses) == expected_nb_of_impact
    assert (
        raypaths[0].interaction_statuses[0]
        == lpf_file_reader__v2__pb2.RayPath.PhotonStatus.StatusJustEmitted
    )
    assert (
        raypaths[0].interaction_statuses[1]
        == lpf_file_reader__v2__pb2.RayPath.PhotonStatus.StatusSpecularTransmitted
    )
    assert len(raypaths[0].sensor_contributions) == 0

    # Close
    stub.CloseLpfFileName(lpf_file_reader__v2__pb2.CloseLpfFileName_Request_Mono())

    # Delete the file previously uploaded to the server - it is no more needed
    file_transfer_stub.Delete(file_transfer__v1__pb2.Delete_Request(uri=upload_response.info.uri))
