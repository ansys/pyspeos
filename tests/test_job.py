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
import time

from ansys.api.speos import grpc_stub
import ansys.api.speos.job.v1.job_pb2 as job__v1__pb2
import ansys.api.speos.job.v1.job_pb2_grpc as job__v1__pb2_grpc
import ansys.api.speos.simulation.v1.simulation_pb2 as simulation__v1__pb2
import ansys.api.speos.simulation.v1.simulation_pb2_grpc as simulation__v1__pb2_grpc

from conftest import config, test_path


def test_job():
    # Stubs creations for Simulations
    simu_manager_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=simulation__v1__pb2_grpc.SimulationsManagerStub,
    )
    simu_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=simulation__v1__pb2_grpc.SpeosSimulationStub,
    )
    # Stubs creations for Jobs
    job_manager_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=job__v1__pb2_grpc.SpeosJobsManagerStub,
    )
    job_stub = grpc_stub.get_stub_insecure_channel(
        target="localhost:" + str(config.get("SpeosServerPort")),
        stub_type=job__v1__pb2_grpc.SpeosJobStub,
    )

    speos_simulation_name = "LG_50M_Colorimetric_short.sv5"
    folder_path = os.path.join(test_path, speos_simulation_name)
    speos_simulation_full_path = os.path.join(folder_path, speos_simulation_name)

    # Allocate simulation
    simu_create_res = simu_manager_stub.Create(simulation__v1__pb2.Create_Request())

    # Load sv5 into allocated simulation
    simu_stub.Load(
        simulation__v1__pb2.Load_Request(guid=simu_create_res.guid, input_file_path=speos_simulation_full_path)
    )

    # Allocate job from simu guid, job type and simu properties
    j = job__v1__pb2.Job()
    j.simu_guid = simu_create_res.guid
    j.job_type = job__v1__pb2.Job_Type.CPU
    j.direct_mc_simulation_properties.stop_condition_rays_number = 500000
    j.direct_mc_simulation_properties.automatic_save_frequency = 60
    job_create_res = job_manager_stub.Create(job__v1__pb2.Create_Request(job=j))

    # Start the job
    job_stub.Start(job__v1__pb2.Start_Request(guid=job_create_res.guid))

    count = 0
    # Check job state every second
    get_state_req = job__v1__pb2.GetState_Request(guid=job_create_res.guid)
    job_state = job_stub.GetState(get_state_req).state
    while job_state != job__v1__pb2.Job_State.FINISHED and job_state != job__v1__pb2.Job_State.STOPPED:
        time.sleep(1)

        job_state = job_stub.GetState(get_state_req).state
        assert job_state != job__v1__pb2.Job_State.IN_ERROR

        # Stop the job after few seconds
        if count == 2:
            job_stub.Stop(job__v1__pb2.Stop_Request(guid=job_create_res.guid))

        count = count + 1

    # Check that the job is in STOPPED state
    assert job_state == job__v1__pb2.Job_State.STOPPED

    # Get information about the job
    job_information = job_stub.GetInformation(job__v1__pb2.GetInformation_Request(guid=job_create_res.guid))
    assert job_information.title == "Direct Simulation Processing"
    assert job_information.name == "ASSEMBLY1.DS (0)"

    # Get the results
    get_results_res = job_stub.GetResults(job__v1__pb2.GetResults_Request(guid=job_create_res.guid))
    assert len(get_results_res.results) == 2
    for result in get_results_res.results:
        if config.get("SpeosServerOnDocker"):
            # When user is in another machine as the server : result files are uploaded in server file system
            # And user has access to the Upload_Response (containing FileSystemItemInformation as info)
            # For more information about those messages grammar check file_transfer.proto
            # result.upload_response.info.uri to have the file uri and be able to download it
            # result.upload_response.info.file_name to know its name
            # result.upload_response.info.file_size to know its size
            assert result.HasField("upload_response")
            assert not result.HasField("path")
        else:
            # When user is in same machine as the server : retrieve directly the files path
            assert result.HasField("path")
            assert not result.HasField("upload_response")

    # Delete job
    job_manager_stub.Delete(job__v1__pb2.Delete_Request(guid=job_create_res.guid))
