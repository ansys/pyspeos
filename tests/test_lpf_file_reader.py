"""This module allows pytest to perform unit testing.

Usage:
.. code::
   $ pytest
   $ pytest -vx

With coverage.
.. code::
   $ pytest --cov ansys.pyoptics.speos

"""
import os

import ansys.api.speos.lpf.v1.lpf_file_reader_pb2 as lpf_file_reader__v1__pb2
import ansys.api.speos.lpf.v1.lpf_file_reader_pb2_grpc as lpf_file_reader__v1__pb2_grpc
from google.protobuf.empty_pb2 import Empty

from ansys.pyoptics.speos import grpc_stub
from conftest import config, test_path


def test_lpf_file_reader_mono_v1_DirectSimu():
    # Lpf file reader creation
    stub = grpc_stub.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=lpf_file_reader__v1__pb2_grpc.LpfFileReader_MonoStub
    )

    # Init with file path
    path = os.path.join(test_path, "basic_DirectSimu.lpf")
    stub.InitLpfFileName(lpf_file_reader__v1__pb2.InitLpfFileNameRequest_Mono(lpf_file_path=path))

    # GetInformation
    res_information = stub.GetInformation(lpf_file_reader__v1__pb2.GetInformationRequest_Mono())
    nb_of_traces = res_information.nb_of_traces
    assert nb_of_traces == 24817
    assert res_information.nb_of_xmps == 3
    assert res_information.has_sensor_contributions == False  # No contributions stored in Direct simu
    assert len(res_information.sensor_names) == 3
    assert res_information.sensor_names[0] == "Irradiance Sensor (0)"
    assert res_information.sensor_names[2] == "Irradiance Sensor (2)"

    # Read
    raypaths = []
    for rp in stub.Read(lpf_file_reader__v1__pb2.ReadRequest_Mono()):
        raypaths.append(rp)
    assert len(raypaths) == nb_of_traces

    # Check result (first entry)
    expected_nb_of_impact = 5
    assert len(raypaths[0].impacts) == expected_nb_of_impact
    assert raypaths[0].impacts[1] == lpf_file_reader__v1__pb2.TripletFloat(x=3.19368935, y=14.999999, z=-3.94779062)
    assert len(raypaths[0].wavelengths) == expected_nb_of_impact
    assert raypaths[0].wavelengths[1] == 691.44708251953125
    assert len(raypaths[0].body_context_ids) == expected_nb_of_impact
    assert raypaths[0].body_context_ids[1] == 2001802324
    assert len(raypaths[0].unique_face_ids) == expected_nb_of_impact
    assert raypaths[0].unique_face_ids[1] == 1815582994
    assert raypaths[0].lastDirection == lpf_file_reader__v1__pb2.TripletFloat(
        x=0.0606396869, y=0.995341122, z=-0.0749590397
    )
    assert len(raypaths[0].interaction_statuses) == expected_nb_of_impact
    assert raypaths[0].interaction_statuses[0] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusJustEmitted
    assert (
        raypaths[0].interaction_statuses[1] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusSpecularTransmitted
    )
    assert len(raypaths[0].sensor_contributions) == 0

    # Close
    stub.CloseLpfFileName(Empty())


def test_lpf_file_reader_mono_v1_InverseSimu():
    # Lpf file reader creation
    stub = grpc_stub.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=lpf_file_reader__v1__pb2_grpc.LpfFileReader_MonoStub
    )

    # Init with file path
    path = os.path.join(test_path, "basic_InverseSimu.lpf")
    stub.InitLpfFileName(lpf_file_reader__v1__pb2.InitLpfFileNameRequest_Mono(lpf_file_path=path))

    # GetInformation
    res_information = stub.GetInformation(lpf_file_reader__v1__pb2.GetInformationRequest_Mono())
    nb_of_traces = res_information.nb_of_traces
    assert nb_of_traces == 21044
    assert res_information.nb_of_xmps == 1
    assert res_information.has_sensor_contributions == True  # contributions stored in Inverse simu
    assert len(res_information.sensor_names) == 1
    assert res_information.sensor_names[0] == "Camera_Perfect_Lens_System_V2:3"

    # Read
    raypaths = []
    for rp in stub.Read(lpf_file_reader__v1__pb2.ReadRequest_Mono()):
        raypaths.append(rp)
    assert len(raypaths) == nb_of_traces

    # Check sensor_contributions in first raypath
    assert len(raypaths[0].sensor_contributions) == 1
    assert raypaths[0].sensor_contributions[0].sensor_id == 0
    assert raypaths[0].sensor_contributions[0].coordinates == lpf_file_reader__v1__pb2.DoubletDouble(
        x=-0.20848463202592682, y=0.1897648665199252
    )

    # Close
    stub.CloseLpfFileName(Empty())


def test_lpf_file_reader_multi_v1():
    # Lpf file reader multi creation
    stub = grpc_stub.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=lpf_file_reader__v1__pb2_grpc.LpfFileReader_MultiStub
    )

    # Create a reader and retrieve its associated guid
    guid = stub.Create(Empty())

    # Init with file path
    path = os.path.join(test_path, "basic_DirectSimu.lpf")
    stub.InitLpfFileName(lpf_file_reader__v1__pb2.InitLpfFileNameRequest_Multi(id=guid, lpf_file_path=path))

    # GetInformation
    res_information = stub.GetInformation(lpf_file_reader__v1__pb2.GetInformationRequest_Multi(id=guid))
    nb_of_traces = res_information.nb_of_traces
    assert nb_of_traces == 24817
    assert res_information.nb_of_xmps == 3

    # Create a second reader
    guid2 = stub.Create(Empty())
    # Init second reader
    path2 = os.path.join(test_path, "basic_InverseSimu.lpf")
    stub.InitLpfFileName(lpf_file_reader__v1__pb2.InitLpfFileNameRequest_Multi(id=guid2, lpf_file_path=path2))

    # GetInformation and read second
    res_information = stub.GetInformation(lpf_file_reader__v1__pb2.GetInformationRequest_Multi(id=guid2))
    nb_of_traces2 = res_information.nb_of_traces
    assert nb_of_traces2 == 21044
    raypaths2 = []
    for rp in stub.Read(lpf_file_reader__v1__pb2.ReadRequest_Multi(id=guid2)):
        raypaths2.append(rp)
    assert len(raypaths2) == nb_of_traces2

    # Check sensor_contributions in first raypath
    assert len(raypaths2[0].sensor_contributions) == 1
    assert raypaths2[0].sensor_contributions[0].sensor_id == 0
    assert raypaths2[0].sensor_contributions[0].coordinates == lpf_file_reader__v1__pb2.DoubletDouble(
        x=-0.20848463202592682, y=0.1897648665199252
    )

    # Delete the second reader
    stub.Delete(guid2)

    # Read the first
    raypaths = []
    for rp in stub.Read(lpf_file_reader__v1__pb2.ReadRequest_Multi(id=guid)):
        raypaths.append(rp)
    assert len(raypaths) == nb_of_traces

    # Check some result (first entry)
    expected_nb_of_impact = 5
    assert len(raypaths[0].impacts) == expected_nb_of_impact
    assert raypaths[0].impacts[1] == lpf_file_reader__v1__pb2.TripletFloat(x=3.19368935, y=14.999999, z=-3.94779062)
    assert len(raypaths[0].interaction_statuses) == expected_nb_of_impact
    assert (
        raypaths[0].interaction_statuses[1] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusSpecularTransmitted
    )
    assert len(raypaths[0].sensor_contributions) == 0

    # Close and Delete the first
    stub.CloseLpfFileName(guid)
    stub.Delete(guid)
