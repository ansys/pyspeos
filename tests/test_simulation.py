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
import shutil

from ansys.api.speos import grpc_stub
from ansys.api.speos.file.v1 import file_transfer
import ansys.api.speos.file.v1.file_transfer_pb2 as file_transfer__v1__pb2
import ansys.api.speos.file.v1.file_transfer_pb2_grpc as file_transfer__v1__pb2_grpc
import ansys.api.speos.simulation.v1.simulation_pb2 as simulation__v1__pb2
import ansys.api.speos.simulation.v1.simulation_pb2_grpc as simulation__v1__pb2_grpc

from conftest import config, local_test_path, test_path


def test_simulation():
    # Stub on simulation manager
    simulation_manager_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=simulation__v1__pb2_grpc.SimulationsManagerStub,
    )

    # Stub on simulation
    simulation_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=simulation__v1__pb2_grpc.SpeosSimulationStub,
    )

    # Create a new simulation on the server
    guid_simu = simulation_manager_stub.Create(simulation__v1__pb2.Create_Request())

    # Get input file path and load it
    speos_simulation_name = "LG_50M_Colorimetric_short.sv5"
    folder_path = os.path.join(test_path, speos_simulation_name)
    speos_simulation_full_path = os.path.join(folder_path, speos_simulation_name)

    load_request = simulation__v1__pb2.Load_Request()
    load_request.guid = guid_simu.guid
    load_request.input_file_path = speos_simulation_full_path

    simulation_stub.Load(load_request)

    # Delete simulation
    delete_request = simulation__v1__pb2.Delete_Request()
    delete_request.guid = guid_simu.guid
    simulation_manager_stub.Delete(delete_request)


def test_simu_allocateSyst_load_run_with_file_transfer():
    # Stubs creations
    file_transfer_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=file_transfer__v1__pb2_grpc.FileTransferServiceStub,
    )
    simu_manager_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=simulation__v1__pb2_grpc.SimulationsManagerStub,
    )
    simu_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=simulation__v1__pb2_grpc.SpeosSimulationStub,
    )

    # Use upload_folder helper provided within ansys.api.speos.file.v1
    sv5_name = "LG_50M_Colorimetric_short.sv5"
    upload_responses = file_transfer.upload_folder(
        file_transfer_service_stub=file_transfer_stub,
        folder_path=os.path.join(local_test_path, sv5_name),
        main_file_name=sv5_name,
    )
    sv5_res_uri = [upload_res.info.uri for upload_res in upload_responses if upload_res.info.file_name == sv5_name][0]

    # Allocate simulation
    create_res = simu_manager_stub.Create(simulation__v1__pb2.Create_Request())

    # Load sv5 into allocated simulation
    simu_stub.Load(simulation__v1__pb2.Load_Request(guid=create_res.guid, input_file_path=sv5_res_uri))

    # Delete files on Server
    # Files uploaded
    file_transfer_stub.Delete(file_transfer__v1__pb2.Delete_Request(uri=sv5_res_uri))


def test_simu_allocateSyst_load_save_with_file_transfer():
    # Stubs creations
    file_transfer_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=file_transfer__v1__pb2_grpc.FileTransferServiceStub,
    )
    simu_manager_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=simulation__v1__pb2_grpc.SimulationsManagerStub,
    )
    simu_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=simulation__v1__pb2_grpc.SpeosSimulationStub,
    )
    sv5_name = "LG_50M_Colorimetric_short.sv5"
    blue_spectrum = "Blue Spectrum.spectrum"
    red_spectrum = "Red Spectrum.spectrum"

    # Use upload_folder helper provided within ansys.api.speos.file.v1
    upload_responses = file_transfer.upload_folder(
        file_transfer_service_stub=file_transfer_stub,
        folder_path=os.path.join(local_test_path, sv5_name),
        main_file_name=sv5_name,
    )
    sv5_res_uri = [upload_res.info.uri for upload_res in upload_responses if upload_res.info.file_name == sv5_name][0]

    # Allocate simulation
    create_res = simu_manager_stub.Create(simulation__v1__pb2.Create_Request())

    # Load sv5 into allocated simulation
    simu_stub.Load(simulation__v1__pb2.Load_Request(guid=create_res.guid, input_file_path=sv5_res_uri))

    # Reserve an item in file system in order to perform a Save
    reserve_res = file_transfer_stub.Reserve(file_transfer__v1__pb2.Reserve_Request())
    # And Save
    simu_stub.Save(simulation__v1__pb2.Save_Request(guid=create_res.guid, input_folder_path=reserve_res.uri))

    # Download locally the simu saved - using download_folder helper provided within ansys.api.speos.file.v1
    download_loc = os.path.join(local_test_path, "download_simu")
    os.mkdir(download_loc)
    download_responses = file_transfer.download_folder(
        file_transfer_service_stub=file_transfer_stub, main_file_uri=reserve_res.uri, download_location=download_loc
    )

    # Check that file are well downloaded
    for res in download_responses:
        downloaded_file = os.path.join(download_loc, res.info.file_name)
        assert os.path.exists(downloaded_file)
        assert os.path.getsize(downloaded_file) == res.info.file_size
    shutil.rmtree(download_loc)

    # Delete files on Server
    # Files uploaded
    file_transfer_stub.Delete(file_transfer__v1__pb2.Delete_Request(uri=sv5_res_uri))
    # Files saved
    file_transfer_stub.Delete(file_transfer__v1__pb2.Delete_Request(uri=reserve_res.uri))
