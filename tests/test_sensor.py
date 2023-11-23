"""This module allows pytest to perform unit testing.
Usage:
.. code::
   $ pytest
   $ pytest -vx
With coverage.
.. code::
   $ pytest --cov ansys.speos.core
"""
import os
import time

from ansys.api.speos.job.v1 import job_pb2, job_pb2_grpc
from ansys.api.speos.simulation.v1 import sensor_properties_pb2, simulation_pb2, simulation_pb2_grpc

from ansys.speos.core.sensor_template import SensorTemplateHelper, SensorTemplateLink
from ansys.speos.core.speos import Speos
from conftest import test_path


def test_create_camera_sensor(speos: Speos):
    # Create spectrum stub from client channel
    ssr_db = speos.client.sensor_templates()

    # Create empty Simulation
    simu_manager_stub = simulation_pb2_grpc.SimulationsManagerStub(speos.client.channel)
    simu_create_res = simu_manager_stub.Create(simulation_pb2.Create_Request())

    # Load speos file into allocated simulation
    sv5_path = os.path.join(test_path, "Inverse_simu.speos")
    simu_stub = simulation_pb2_grpc.SpeosSimulationStub(speos.client.channel)
    simu_load_req = simulation_pb2.Load_Request(guid=simu_create_res.guid, input_file_path=sv5_path)
    simu_load_res = simu_stub.Load(simu_load_req)

    # Read simu dm
    simu_read_req = simulation_pb2.Read_Request(guid=simu_create_res.guid)
    simu_read_res = simu_manager_stub.Read(simu_read_req)
    assert len(simu_read_res.simulation.sensors) == 1

    # Read first sensor template dm
    irr = speos.client.get_item(key=simu_read_res.simulation.sensors[0].guid)
    assert isinstance(irr, SensorTemplateLink)
    assert irr.get().HasField("irradiance_sensor_template")

    # Create a camera sensor template dm
    camera_input_files_path = os.path.join(test_path, "CameraInputFiles")
    red_spectrum = os.path.join(camera_input_files_path, "CameraSensitivityRed.spectrum")
    green_spectrum = os.path.join(camera_input_files_path, "CameraSensitivityGreen.spectrum")
    blue_spectrum = os.path.join(camera_input_files_path, "CameraSensitivityBlue.spectrum")
    transmittance = os.path.join(camera_input_files_path, "CameraTransmittance.spectrum")
    distortion = os.path.join(camera_input_files_path, "CameraDistortion.OPTDistortion")

    camera_t = SensorTemplateHelper.create_camera(
        sensor_template_stub=ssr_db,
        name="CameraSensorPhotometric",
        description=".",
        settings=SensorTemplateHelper.CameraSettings(
            gamma_correction=2.2, focal_length=4, imager_distance=10, f_number=30
        ),
        dimensions=SensorTemplateHelper.CameraDimensions(horz_pixel=640, vert_pixel=480, width=5, height=5),
        distorsion_file_uri=distortion,
        transmittance_file_uri=transmittance,
        spectrum_file_uris=[red_spectrum, green_spectrum, blue_spectrum],
        wavelengths_range=SensorTemplateHelper.WavelengthsRange(start=400, end=800, sampling=10),
    )

    # Create a camera sensor using template + properties
    camera_sensor = simulation_pb2.Sensor()
    camera_sensor.name = camera_t.get().name + "_1"
    camera_sensor.guid = camera_t.key

    camera_sensor.camera_sensor_properties.sensor_position.origin[:] = [25.0, 0.0, 0.0]
    camera_sensor.camera_sensor_properties.sensor_position.x_vector[:] = [0.0, 0.0, -1.0]
    camera_sensor.camera_sensor_properties.sensor_position.y_vector[:] = [0.0, 1.0, 0.0]
    camera_sensor.camera_sensor_properties.sensor_position.z_vector[:] = [1.0, 0.0, 0.0]
    camera_sensor.camera_sensor_properties.layer_type_source.CopyFrom(sensor_properties_pb2.LayerTypeSource())

    # Add this camera to the simulation - To do so, use simu_read_res
    simu_read_res.simulation.sensors.append(camera_sensor)

    simu_update_req = simulation_pb2.Update_Request(guid=simu_create_res.guid, simulation=simu_read_res.simulation)
    simu_update_res = simu_manager_stub.Update(simu_update_req)

    # Create Job from simu guid + choose type + simu properties
    job_manager_stub = job_pb2_grpc.SpeosJobsManagerStub(speos.client.channel)
    j = job_pb2.Job()
    j.simu_guid = simu_create_res.guid
    j.job_type = job_pb2.Job_Type.CPU
    j.inverse_mc_simulation_properties.optimized_propagation_none.stop_condition_passes_number = 5
    j.inverse_mc_simulation_properties.automatic_save_frequency = 1800
    job_create_res = job_manager_stub.Create(job_pb2.Create_Request(job=j))

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
    assert len(get_results_res.results) == 6

    # Delete job
    delete_res = job_manager_stub.Delete(job_pb2.Delete_Request(guid=job_create_res.guid))

    # Delete simu
    delete_res = simu_manager_stub.Delete(simulation_pb2.Delete_Request(guid=simu_create_res.guid))

    # Delete all sensor templates
    for ssr in ssr_db.list():
        ssr.delete()
