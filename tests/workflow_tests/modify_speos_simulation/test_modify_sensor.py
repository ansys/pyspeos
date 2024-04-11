# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

import os

import ansys.speos.core as core
from ansys.speos.core.speos import Speos
from ansys.speos.workflow.modify_speos_simulation import modify_sensor
from conftest import test_path


def test_modify_camera(speos: Speos):
    # Speos simulation to load
    simu_name = "Inverse_SeveralSensors.speos"
    speos_file = os.path.join(test_path, os.path.join(simu_name, simu_name))
    camera_input_path = os.path.join(test_path, "CameraInputFiles")

    new_sim = modify_sensor.SpeosSimulationUpdate(speos, speos_file)

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
        new_sim.add_camera_sensor(camera_sensor, camera_properties)

    camera_sensor_update = camera_sensor.copy()
    camera_sensor_update.name = "FOV_150deg.1"

    camera_properties_update = modify_sensor.CameraSensorProperties()
    camera_properties_update.origin = [20, 10, 15]
    camera_properties_update.x_vector = [0.0, 0.0, -1.0]
    camera_properties_update.y_vector = [0.0, 1.0, 0.0]
    camera_properties_update.z_vector = [1.0, 0.0, 0.0]
    new_sim.update_sensor(camera_sensor_update, camera_properties_update)

    job_link = new_sim.compute(stop_condition_duration=8)
    assert job_link.key != ""

    job_link.delete()
    new_sim.close()


def test_modify_irradiance(speos: Speos):
    # Speos simulation to load
    simu_name = "LG_50M_Colorimetric_short.sv5"
    speos_file = os.path.join(test_path, os.path.join(simu_name, simu_name))

    new_sim = modify_sensor.SpeosSimulationUpdate(speos, speos_file)

    irradiance_sensor_list = []

    irradiance_sensor = modify_sensor.IrradianceSensorParameters()
    irradiance_sensor.name = "Dom Irradiance Sensor New"
    irradiance_sensor.integration_type = core.SensorTemplateFactory.IlluminanceType.Planar
    irradiance_sensor.type = core.SensorTemplateFactory.Type.Spectral
    irradiance_sensor.wavelengths_start = 400
    irradiance_sensor.wavelengths_end = 700
    irradiance_sensor.wavelengths_sampling = 25
    irradiance_sensor.x_range_start = -20
    irradiance_sensor.x_range_end = 20
    irradiance_sensor.x_range_sampling = 500
    irradiance_sensor.y_range_start = -20
    irradiance_sensor.y_range_end = 20
    irradiance_sensor.y_range_sampling = 500
    irradiance_sensor_list.append(irradiance_sensor)

    irradiance_sensor = irradiance_sensor.copy()
    irradiance_sensor.name = "Dom Irradiance Sensor Update"
    irradiance_sensor_list.append(irradiance_sensor)

    irradiance_properties = modify_sensor.IrradianceSensorProperties()
    irradiance_properties.origin = [-42, 5, 5]
    irradiance_properties.x_vector = [0.0, 1.0, 0.0]
    irradiance_properties.y_vector = [0.0, 0.0, -1.0]
    irradiance_properties.z_vector = [1.0, 0.0, 0.0]

    for sensor in irradiance_sensor_list:
        new_sim.add_camera_sensor(sensor, irradiance_properties)

    irradiance_sensor_update = irradiance_sensor.copy()
    irradiance_sensor_update.name = "Dom Irradiance Sensor Update.1"

    irradiance_properties_update = modify_sensor.IrradianceSensorProperties()
    irradiance_properties_update.origin = [-45, 5, 5]
    irradiance_properties_update.x_vector = [0.0, 1.0, 0.0]
    irradiance_properties_update.y_vector = [0.0, 0.0, -1.0]
    irradiance_properties_update.z_vector = [1.0, 0.0, 0.0]
    new_sim.update_sensor(irradiance_sensor_update, irradiance_properties_update)

    job_link = new_sim.compute(stop_condition_duration=8)
    assert job_link.key != ""

    job_link.delete()
    new_sim.close()


def test_modify_scene(speos: Speos):
    # Speos simulation to load
    simu_name_1 = "Inverse_SeveralSensors.speos"
    speos_file_1 = os.path.join(test_path, os.path.join(simu_name_1, simu_name_1))
    simu_name_2 = "LG_50M_Colorimetric_short.sv5"
    speos_file_2 = os.path.join(test_path, os.path.join(simu_name_2, simu_name_2))

    sim_1 = modify_sensor.SpeosSimulationUpdate(speos, speos_file_1, clean_dbs=False)
    sim_2 = modify_sensor.SpeosSimulationUpdate(speos, speos_file_2, clean_dbs=False)

    sim_2_position = modify_sensor.PositionProperties()
    sim_2_position.origin = [0.0, 0.0, 0.0]
    sim_2_position.x_vector = [1.0, 0.0, 0.0]
    sim_2_position.y_vector = [0.0, 1.0, 0.0]
    sim_2_position.z_vector = [0.0, 0.0, 1.0]

    sim_1.add_scene(sim_2, sim_2_position)
    job_link = sim_1.compute(stop_condition_duration=8)
    assert job_link.key != ""

    sim_2_position_update = sim_2_position.copy()
    sim_2_position_update.origin = [1.0, 0.0, 0.0]
    sim_2_position_update.x_vector = [1.0, 0.0, 0.0]
    sim_2_position_update.y_vector = [0.0, 1.0, 0.0]
    sim_2_position_update.z_vector = [0.0, 0.0, 1.0]

    sim_1.add_scene(sim_2, sim_2_position)
    new_body_positions = {
        "LG_50M_Colorimetric_short": sim_2_position_update,
    }
    sim_1.update_scene_part_position(new_part_positions=new_body_positions)
    job_link = sim_1.compute(stop_condition_duration=8)
    assert job_link.key != ""

    job_link.delete()
    sim_1.close()
    sim_2.close()
