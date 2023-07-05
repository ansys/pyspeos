"""This module allows pytest to perform unit testing.
Usage:
.. code::
   $ pytest
   $ pytest -vx
With coverage.
.. code::
   $ pytest --cov ansys.speos.core
"""
import json
import os
import shutil
import time

from ansys.api.speos.file.v1 import file_transfer, file_transfer_pb2, file_transfer_pb2_grpc
from ansys.api.speos.job.v1 import job_pb2, job_pb2_grpc
from ansys.api.speos.simulation.v1 import (
    simulation_pb2,
    simulation_pb2_grpc,
    simulation_template_pb2,
    simulation_template_pb2_grpc,
)
import grpc
import pytest

from ansys.speos.core.speos import Speos
from conftest import local_test_path, test_path
import helper


def test_simulation(speos: Speos):
    # Stub on simulation manager
    simulation_manager_stub = simulation_pb2_grpc.SimulationsManagerStub(speos.client.channel)

    # Stub on simulation
    simulation_stub = simulation_pb2_grpc.SpeosSimulationStub(speos.client.channel)

    # Create a new simulation on the server
    guid_simu = simulation_manager_stub.Create(simulation_pb2.Create_Request())

    # Get input file path and load it
    speos_simulation_name = "LG_50M_Colorimetric_short.sv5"
    folder_path = os.path.join(test_path, speos_simulation_name)
    speos_simulation_full_path = os.path.join(folder_path, speos_simulation_name)

    load_request = simulation_pb2.Load_Request()
    load_request.guid = guid_simu.guid
    load_request.input_file_path = speos_simulation_full_path

    simulation_stub.Load(load_request)

    # Delete simulation
    delete_request = simulation_pb2.Delete_Request()
    delete_request.guid = guid_simu.guid
    simulation_manager_stub.Delete(delete_request)


def test_simu_allocateSyst_load_with_file_transfer(speos: Speos):
    # Stubs creations
    file_transfer_stub = file_transfer_pb2_grpc.FileTransferServiceStub(speos.client.channel)
    simu_manager_stub = simulation_pb2_grpc.SimulationsManagerStub(speos.client.channel)
    simu_stub = simulation_pb2_grpc.SpeosSimulationStub(speos.client.channel)

    # Use upload_folder helper provided within ansys.api.speos.file.v1
    sv5_name = "LG_50M_Colorimetric_short.sv5"
    upload_responses = file_transfer.upload_folder(
        file_transfer_service_stub=file_transfer_stub,
        folder_path=os.path.join(local_test_path, sv5_name),
        main_file_name=sv5_name,
    )
    sv5_res_uri = [upload_res.info.uri for upload_res in upload_responses if upload_res.info.file_name == sv5_name][0]

    # Allocate simulation
    create_res = simu_manager_stub.Create(simulation_pb2.Create_Request())

    # Load sv5 into allocated simulation
    simu_stub.Load(simulation_pb2.Load_Request(guid=create_res.guid, input_file_path=sv5_res_uri))

    # Delete files on Server
    # Files uploaded
    file_transfer_stub.Delete(file_transfer_pb2.Delete_Request(uri=sv5_res_uri))


def test_simu_allocateSyst_load_save_with_file_transfer(speos: Speos):
    # Stubs creations
    file_transfer_stub = file_transfer_pb2_grpc.FileTransferServiceStub(speos.client.channel)
    simu_manager_stub = simulation_pb2_grpc.SimulationsManagerStub(speos.client.channel)
    simu_stub = simulation_pb2_grpc.SpeosSimulationStub(speos.client.channel)
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
    create_res = simu_manager_stub.Create(simulation_pb2.Create_Request())

    # Load sv5 into allocated simulation
    simu_stub.Load(simulation_pb2.Load_Request(guid=create_res.guid, input_file_path=sv5_res_uri))

    # Reserve an item in file system in order to perform a Save
    reserve_res = file_transfer_stub.Reserve(file_transfer_pb2.Reserve_Request())
    # And Save
    simu_stub.Save(simulation_pb2.Save_Request(guid=create_res.guid, input_folder_path=reserve_res.uri))

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
    file_transfer_stub.Delete(file_transfer_pb2.Delete_Request(uri=sv5_res_uri))
    # Files saved
    file_transfer_stub.Delete(file_transfer_pb2.Delete_Request(uri=reserve_res.uri))


def test_simu_load_read_update(speos: Speos):
    # Create empty Simulation
    simu_manager_stub = simulation_pb2_grpc.SimulationsManagerStub(speos.client.channel)
    simu_create_res = simu_manager_stub.Create(simulation_pb2.Create_Request())

    # Load speos file into allocated simulation
    sv5_path = os.path.join(test_path, "Inverse_SeveralSensors.speos")

    simu_stub = simulation_pb2_grpc.SpeosSimulationStub(speos.client.channel)
    simu_load_req = simulation_pb2.Load_Request(guid=simu_create_res.guid, input_file_path=sv5_path)
    simu_load_res = simu_stub.Load(simu_load_req)

    # Read simulation dm
    simu_read_req = simulation_pb2.Read_Request(guid=simu_create_res.guid)
    simu_read_res = simu_manager_stub.Read(simu_read_req)
    assert len(simu_read_res.simulation.sensors) == 2
    assert simu_read_res.simulation.name == "Inverse.1"

    # Read simu template dm
    simulation_templates_manager_stub = simulation_template_pb2_grpc.SimulationTemplatesManagerStub(
        speos.client.channel
    )
    simu_template_read_req = simulation_template_pb2.Read_Request(guid=simu_read_res.simulation.guid)
    simu_template_read_res = simulation_templates_manager_stub.Read(simu_template_read_req)
    assert simu_template_read_res.simulation_template.HasField("inverse_mc_simulation_template")
    assert simu_template_read_res.simulation_template.inverse_mc_simulation_template.splitting == False

    # Duplicate the simulation template to have same but with splitting activated
    simu_template_read_res.simulation_template.inverse_mc_simulation_template.splitting = True
    simu_template_read_res.simulation_template.name = "Inverse.2"
    simu_template_read_res.simulation_template.description = "Inverse simu with splitting"

    simu_template_create_req = simulation_template_pb2.Create_Request(
        simulation_template=simu_template_read_res.simulation_template
    )
    simu_template_create_res = simulation_templates_manager_stub.Create(simu_template_create_req)

    # Update the simulation to use new template (with splitting) -> ERROR
    simu_read_res.simulation.guid = simu_template_create_res.guid
    simu_update_req = simulation_pb2.Update_Request(guid=simu_create_res.guid, simulation=simu_read_res.simulation)
    with pytest.raises(grpc.RpcError) as exc_info:
        simu_update_res = simu_manager_stub.Update(simu_update_req)
    error_details = json.loads(exc_info.value.details())
    assert error_details["ErrorName"] == "OPTCAALPAWithSplitting"

    # Create Job from simu guid + choose type + simu properties
    job_manager_stub = job_pb2_grpc.SpeosJobsManagerStub(speos.client.channel)

    j = job_pb2.Job()
    j.simu_guid = simu_create_res.guid
    j.job_type = job_pb2.Job_Type.CPU
    # No optimized propagation and set related stop condition
    j.inverse_mc_simulation_properties.optimized_propagation_none.stop_condition_passes_number = 3
    j.inverse_mc_simulation_properties.stop_condition_duration = 6  # Set stop condition on duration also
    j.inverse_mc_simulation_properties.automatic_save_frequency = 600  # Set automatic save frequency

    job_create_req = job_pb2.Create_Request(job=j)
    job_create_res = job_manager_stub.Create(job_create_req)

    # Start the job
    job_stub = job_pb2_grpc.SpeosJobStub(speos.client.channel)
    job_start_req = job_pb2.Start_Request(guid=job_create_res.guid)
    job_start_res = job_stub.Start(job_start_req)

    # Check job state every second
    get_state_req = job_pb2.GetState_Request(guid=job_create_res.guid)
    job_state_res = job_stub.GetState(get_state_req)
    while (
        job_state_res.state != job_pb2.Job_State.FINISHED
        and job_state_res.state != job_pb2.Job_State.STOPPED
        and job_state_res.state != job_pb2.Job_State.IN_ERROR
    ):
        time.sleep(2)

        job_state_res = job_stub.GetState(get_state_req)

    # Get results
    get_results_req = job_pb2.GetResults_Request(guid=job_create_res.guid)
    get_results_res = job_stub.GetResults(get_results_req)
    assert len(get_results_res.results) == 9

    # Delete job
    delete_res = job_manager_stub.Delete(job_pb2.Delete_Request(guid=job_create_res.guid))

    # Delete simu
    helper.remove_file(os.path.join(sv5_path, "CameraSensitivityBlue_1044-9741-9c42-85c2.spectrum"))
    helper.remove_file(os.path.join(sv5_path, "CameraSensitivityGreen_b5d3-6c51-134d-a5d6.spectrum"))
    helper.remove_file(os.path.join(sv5_path, "CameraSensitivityRed_9433-b5a9-12ab-7c7f.spectrum"))
    helper.remove_file(os.path.join(sv5_path, "CameraTransmittance_7345-0c60-5ae6-d225.spectrum"))
    delete_res = simu_manager_stub.Delete(simulation_pb2.Delete_Request(guid=simu_create_res.guid))

    # Delete all simu templates
    simu_templates_list_res = simulation_templates_manager_stub.List(simulation_template_pb2.List_Request())
    for simu_template_guid in simu_templates_list_res.guids:
        delete_res = simulation_templates_manager_stub.Delete(
            simulation_template_pb2.Delete_Request(guid=simu_template_guid)
        )

    # Delete all sensor templates
    import ansys.api.speos.sensor.v1.sensor_pb2 as sensor_v1
    import ansys.api.speos.sensor.v1.sensor_pb2_grpc

    sensor_templates_manager_stub = ansys.api.speos.sensor.v1.sensor_pb2_grpc.SensorTemplatesManagerStub(
        speos.client.channel
    )
    sensor_templates_list_res = sensor_templates_manager_stub.List(sensor_v1.List_Request())
    for sensor_template_guid in sensor_templates_list_res.guids:
        delete_res = sensor_templates_manager_stub.Delete(sensor_v1.Delete_Request(guid=sensor_template_guid))
