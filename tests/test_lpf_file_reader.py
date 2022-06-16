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
from conftest import config, test_path
from google.protobuf.empty_pb2 import Empty

from ansys.pyoptics import speos


def test_lpf_file_reader_mono_v1():
    # Lpf file reader creation
    stub = speos.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=lpf_file_reader__v1__pb2_grpc.LpfFileReader_MonoStub
    )

    # Init with file path
    path = os.path.join(test_path, "basic_1.lpf")
    stub.InitLpfFileName(lpf_file_reader__v1__pb2.InitLpfFileNameRequest_Mono(lpf_file_path=path))

    # Check Nb XMPs
    assert stub.GetNbOfXMPs(Empty()).nb_of_xmps == 3

    # Check Nb Traces
    nb_of_traces = stub.GetNbOfTraces(Empty()).nb_of_traces
    assert nb_of_traces == 10

    # Read
    raypaths = []
    for rp in stub.Read(lpf_file_reader__v1__pb2.ReadRequest_Mono()):
        raypaths.append(rp)
    assert len(raypaths) == nb_of_traces

    # Check result (first and last entry)
    expectedNbOfImpactOnFaces0 = 4
    assert len(raypaths[0].impacts) == expectedNbOfImpactOnFaces0
    assert raypaths[0].impacts[1] == lpf_file_reader__v1__pb2.TripletFloat(
        x=4.4084320068359375, y=14.999999046325684, z=2.4493408203125
    )
    assert len(raypaths[0].wavelengths) == expectedNbOfImpactOnFaces0
    assert raypaths[0].wavelengths[1] == 678.1803588867188
    assert len(raypaths[0].body_context_ids) == expectedNbOfImpactOnFaces0
    assert raypaths[0].body_context_ids[1] == 2001802324
    assert len(raypaths[0].unique_face_ids) == expectedNbOfImpactOnFaces0
    assert raypaths[0].unique_face_ids[1] == 1815582994
    assert raypaths[0].lastDirection == lpf_file_reader__v1__pb2.TripletFloat(
        x=0.2041478008031845, y=-0.9723469614982605, z=0.11342425644397736
    )
    assert len(raypaths[0].interaction_statuses) == expectedNbOfImpactOnFaces0
    assert raypaths[0].interaction_statuses[0] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusJustEmitted
    assert (
        raypaths[0].interaction_statuses[1] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusSpecularTransmitted
    )
    assert raypaths[0].interaction_statuses[3] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusSpecularReflected

    expectedNbOfImpactOnFaces9 = 6
    assert len(raypaths[9].impacts) == expectedNbOfImpactOnFaces9
    assert raypaths[9].impacts[1] == lpf_file_reader__v1__pb2.TripletFloat(
        x=-1.8186546564102173, y=15.0, z=-6.767658233642578
    )
    assert len(raypaths[9].wavelengths) == expectedNbOfImpactOnFaces9
    assert raypaths[9].wavelengths[1] == 743.3338623046875
    assert len(raypaths[9].body_context_ids) == expectedNbOfImpactOnFaces9
    assert raypaths[9].body_context_ids[1] == 2001802324
    assert len(raypaths[9].unique_face_ids) == expectedNbOfImpactOnFaces9
    assert raypaths[9].unique_face_ids[1] == 1815582994
    assert raypaths[9].lastDirection == lpf_file_reader__v1__pb2.TripletFloat(
        x=0.14110437035560608, y=0.8392737507820129, z=0.5250800848007202
    )
    assert len(raypaths[9].interaction_statuses) == expectedNbOfImpactOnFaces9
    assert raypaths[9].interaction_statuses[0] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusJustEmitted
    assert raypaths[9].interaction_statuses[4] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusSpecularReflected
    assert (
        raypaths[9].interaction_statuses[5] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusSpecularTransmitted
    )

    # Close
    stub.CloseLpfFileName(Empty())


def test_lpf_file_reader_multi_v1():
    # Lpf file reader multi creation
    stub = speos.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=lpf_file_reader__v1__pb2_grpc.LpfFileReader_MultiStub
    )

    # Create a reader and retrieve its associated guid
    guid = stub.Create(Empty())

    # Init with file path
    path = os.path.join(test_path, "basic_1.lpf")
    stub.InitLpfFileName(lpf_file_reader__v1__pb2.InitLpfFileNameRequest_Multi(id=guid, lpf_file_path=path))

    # Check Nb Traces
    nb_of_traces = stub.GetNbOfTraces(guid).nb_of_traces
    assert nb_of_traces == 10

    # Create a second reader
    guid2 = stub.Create(Empty())

    # Get Nb XMPs for first reader
    assert stub.GetNbOfXMPs(guid).nb_of_xmps == 3

    # Init second reader
    path2 = os.path.join(test_path, "basic_2.lpf")
    stub.InitLpfFileName(lpf_file_reader__v1__pb2.InitLpfFileNameRequest_Multi(id=guid2, lpf_file_path=path2))

    # Check Nb Traces and read second
    nb_of_traces2 = stub.GetNbOfTraces(guid2).nb_of_traces
    assert nb_of_traces2 == 5
    raypaths2 = []
    for rp in stub.Read(lpf_file_reader__v1__pb2.ReadRequest_Multi(id=guid2)):
        raypaths2.append(rp)
    assert len(raypaths2) == nb_of_traces2

    # Check result (fourth entry)
    expectedNbOfImpactOnFaces3 = 5
    assert len(raypaths2[3].impacts) == expectedNbOfImpactOnFaces3
    assert raypaths2[3].impacts[1] == lpf_file_reader__v1__pb2.TripletFloat(
        x=5.026374340057373, y=15.000000953674316, z=0.7341787815093994
    )
    assert len(raypaths2[3].wavelengths) == expectedNbOfImpactOnFaces3
    assert raypaths2[3].wavelengths[1] == 652.2732543945312
    assert len(raypaths2[3].body_context_ids) == expectedNbOfImpactOnFaces3
    assert raypaths2[3].body_context_ids[1] == 2001802324
    assert len(raypaths2[3].unique_face_ids) == expectedNbOfImpactOnFaces3
    assert raypaths2[3].unique_face_ids[1] == 1815582994
    assert raypaths2[3].lastDirection == lpf_file_reader__v1__pb2.TripletFloat(
        x=0.09542781859636307, y=0.9953387975692749, z=0.013935667462646961
    )
    assert len(raypaths2[3].interaction_statuses) == expectedNbOfImpactOnFaces3
    assert raypaths2[3].interaction_statuses[0] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusJustEmitted
    assert (
        raypaths2[3].interaction_statuses[1] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusSpecularTransmitted
    )

    # Delete the second reader
    stub.Delete(guid2)

    # Read the first
    raypaths = []
    for rp in stub.Read(lpf_file_reader__v1__pb2.ReadRequest_Multi(id=guid)):
        raypaths.append(rp)
    assert len(raypaths) == nb_of_traces

    # Check result (first entry)
    expectedNbOfImpactOnFaces0 = 4
    assert len(raypaths[0].impacts) == expectedNbOfImpactOnFaces0
    assert raypaths[0].impacts[1] == lpf_file_reader__v1__pb2.TripletFloat(
        x=4.4084320068359375, y=14.999999046325684, z=2.4493408203125
    )
    assert len(raypaths[0].wavelengths) == expectedNbOfImpactOnFaces0
    assert raypaths[0].wavelengths[1] == 678.1803588867188
    assert len(raypaths[0].body_context_ids) == expectedNbOfImpactOnFaces0
    assert raypaths[0].body_context_ids[1] == 2001802324
    assert len(raypaths[0].unique_face_ids) == expectedNbOfImpactOnFaces0
    assert raypaths[0].unique_face_ids[1] == 1815582994
    assert raypaths[0].lastDirection == lpf_file_reader__v1__pb2.TripletFloat(
        x=0.2041478008031845, y=-0.9723469614982605, z=0.11342425644397736
    )
    assert len(raypaths[0].interaction_statuses) == expectedNbOfImpactOnFaces0
    assert raypaths[0].interaction_statuses[0] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusJustEmitted
    assert (
        raypaths[0].interaction_statuses[1] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusSpecularTransmitted
    )
    assert (
        raypaths[0].interaction_statuses[2] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusSpecularTransmitted
    )
    assert raypaths[0].interaction_statuses[3] == lpf_file_reader__v1__pb2.RayPath.PhotonStatus.StatusSpecularReflected

    # Close and Delete the first
    stub.CloseLpfFileName(guid)
    stub.Delete(guid)
