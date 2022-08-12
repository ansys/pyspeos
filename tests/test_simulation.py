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
    SimulationManagerStub = speos.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=simulation__v1__pb2_grpc.SpeosSimulationsManagerStub
    )

    # Stub on simulation
    SimulationStub = speos.get_stub_insecure_channel(
        port=config.get("SpeosServerPort"), stub_type=simulation__v1__pb2_grpc.SpeosSimulationStub
    )

    # Create a new simulation on the server
    guidSimu = SimulationManagerStub.Create(simulation__v1__pb2.Create_Request())

    # Get input file path and load it
    SpeosSimulationName = "LG_50M_Colorimetric_short.sv5"
    Folderpath = os.path.join(test_path, SpeosSimulationName)
    SpeosSimulationFullPath = os.path.join(Folderpath, SpeosSimulationName)
    print("path = " + str(Folderpath))

    Load_Request = simulation__v1__pb2.Load_Request()
    Load_Request.guid = guidSimu.guid
    Load_Request.input_file_path = SpeosSimulationFullPath

    SimulationStub.Load(Load_Request)

    # GetName
    GetName_Request = simulation__v1__pb2.GetName_Request()
    GetName_Request.guid = guidSimu.guid
    GetName_Response = SimulationStub.GetName(GetName_Request)

    print("Simulation name : " + GetName_Response.name)
    assert GetName_Response.name == "ASSEMBLY1.DS (0)"

    # Get Results list
    GetResults_Request = simulation__v1__pb2.GetResults_Request()
    GetResults_Request.guid = guidSimu.guid
    # GetResults_Response = simulation__v1__pb2.GetResults_Response()

    GetResults_Response = SimulationStub.GetResults(GetResults_Request)
    print("RESULTS = " + str(GetResults_Response))

    # Run the simulation
    Run_Request = simulation__v1__pb2.Run_Request()
    Run_Request.guid = guidSimu.guid
    SimulationStub.Run(Run_Request)

    # Check results has been pushed
    for result in GetResults_Response.results_paths:
        assert does_file_exist(result)
        remove_file(result)
        assert not does_file_exist(result)

    Delete_Request = simulation__v1__pb2.Delete_Request()
    Delete_Request.guid = guidSimu.guid
    SimulationManagerStub.Delete(Delete_Request)
