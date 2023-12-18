import os

from ansys.speos.core.speos import Speos
from ansys.speos.workflow.modify_speos_simulation import modify_sensor
from conftest import test_path


def test_modify_camera(speos: Speos):
    # Speos simulation to load
    simu_name = "Inverse_SeveralSensors.speos"
    speos_file = os.path.join(test_path, os.path.join(simu_name, simu_name))

    new_sim = modify_sensor.SpeosSimulationUpdate(speos, speos_file)

    # Create camera database
    camera_input_path = os.path.join(test_path, "CameraInputFiles")

    camera_sensor_list = []

    camera_sensor = modify_sensor.PhotometricCameraSensorParameters()
    camera_sensor.name = "FOV_190deg"
    camera_sensor.transmittance_file = os.path.join(camera_input_path, "CameraTransmittance.spectrum")
    camera_sensor.distorsion_file = os.path.join(camera_input_path, "CameraDistortion_190deg.OPTDistortion")
    camera_sensor.color_mode_red_spectrum_file = os.path.join(camera_input_path, "CameraSensitivityRed.spectrum")
    camera_sensor.color_mode_green_spectrum_file = os.path.join(camera_input_path, "CameraSensitivityGreen.spectrum")
    camera_sensor.color_mode_blue_spectrum_file = os.path.join(camera_input_path, "CameraSensitivityBlue.spectrum")
    camera_sensor.wavelengths_start = 380
    camera_sensor.wavelengths_end = 780
    camera_sensor.wavelengths_sampling = 21
    camera_sensor.focal_length = 0.9
    camera_sensor.imager_distance = 19.1
    camera_sensor.f_number = 2
    camera_sensor.horizontal_pixel = 640
    camera_sensor.vertical_pixel = 480
    camera_sensor.width = 3.6
    camera_sensor.height = 2.7

    camera_sensor_list.append(camera_sensor)

    camera_sensor = camera_sensor.copy()
    camera_sensor.name = "FOV_150deg"
    camera_sensor.distorsion_file = os.path.join(camera_input_path, "CameraDistortion_150deg.OPTDistortion")

    camera_sensor_list.append(camera_sensor)

    camera_properties = modify_sensor.CameraSensorProperties()
    camera_properties.origin = [17, 10, 15]
    camera_properties.x_vector = [0.0, 0.0, -1.0]
    camera_properties.y_vector = [0.0, 1.0, 0.0]
    camera_properties.z_vector = [1.0, 0.0, 0.0]

    for camera_sensor in camera_sensor_list:
        new_sim.add_camera_sensor(camera_sensor.create_template(), camera_properties.create_properties())

    results = new_sim.compute(stop_condition_duration=8)
    assert len(results) == 17
    new_sim.close()
