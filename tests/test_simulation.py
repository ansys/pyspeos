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

import ansys.api.speos.simulation.v1.simulation_pb2 as simulation__v1__pb2
import ansys.api.speos.simulation.v1.simulation_pb2_grpc as simulation__v1__pb2_grpc

from ansys.pyoptics import speos
from conftest import config, test_path
from helper import does_file_exist, remove_file


def test_simulation():
    # Stub on simulation manager
    simulation_manager_stub = speos.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=simulation__v1__pb2_grpc.SpeosSimulationsManagerStub
    )

    # Stub on simulation
    simulation_stub = speos.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=simulation__v1__pb2_grpc.SpeosSimulationStub
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

    # GetName
    get_name_request = simulation__v1__pb2.GetName_Request()
    get_name_request.guid = guid_simu.guid
    get_name_response = simulation_stub.GetName(get_name_request)

    assert get_name_response.name == "ASSEMBLY1.DS (0)"

    # Get Results list
    get_results_request = simulation__v1__pb2.GetResults_Request()
    get_results_request.guid = guid_simu.guid

    get_results_response = simulation_stub.GetResults(get_results_request)

    # Run the simulation
    run_request = simulation__v1__pb2.Run_Request()
    run_request.guid = guid_simu.guid
    simulation_stub.Run(run_request)

    # Check results has been pushed
    for result in get_results_response.results_paths:
        assert does_file_exist(result)
        remove_file(result)
        assert not does_file_exist(result)

    delete_request = simulation__v1__pb2.Delete_Request()
    delete_request.guid = guid_simu.guid
    simulation_manager_stub.Delete(delete_request)
