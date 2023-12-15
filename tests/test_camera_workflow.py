import os

from ansys.speos.workflow.modify_speos_simulation import modify_sensor

# Speos simulation to load
tests_data_path = r"C:\MyEbooks\Product management\PO_AUTOMATION\2024 R2 pySpeos"
simu_name = "Rearview.NHTSA.Day-time.speos"
speos_file = os.path.join(tests_data_path, os.path.join(simu_name, simu_name))

new_sim = modify_sensor.speos_simulation_update(speos_file)

# Create camera database

camera_input_path = r"C:\MyEbooks\Product management\PO_AUTOMATION\2024 R2 pySpeos\Cameras\SPEOS input files"

camera_sensor_db = []

camera_sensor = modify_sensor.photometric_camera_sensor_parameters()
camera_sensor.name = "FOV_190deg"
camera_sensor.transmittance_file = os.path.join(camera_input_path, "OPTIS_Transmittance.spectrum")
camera_sensor.distorsion_file = os.path.join(camera_input_path, "OPTIS_Distortion_190deg.OPTDistortion")
camera_sensor.color_mode_red_spectrum_file = os.path.join(camera_input_path, "OPTIS_Sensitivity_Red.spectrum")
camera_sensor.color_mode_green_spectrum_file = os.path.join(camera_input_path, "OPTIS_Sensitivity_Green.spectrum")
camera_sensor.color_mode_blue_spectrum_file = os.path.join(camera_input_path, "OPTIS_Sensitivity_Blue.spectrum")
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

camera_sensor_db.append(camera_sensor)

camera_sensor = camera_sensor.copy()
camera_sensor.name = "FOV_150deg"
camera_sensor.distorsion_file = os.path.join(camera_input_path, "OPTIS_Distortion_150deg.OPTDistortion")

camera_sensor_db.append(camera_sensor)

camera_properties = modify_sensor.camera_sensor_properties()
camera_properties.origin = [12750, 21416.5446481695, 573.389073289149]
camera_properties.x_vector = [-1.0, 0.0, 0.0]
camera_properties.y_vector = [-0.0002, 0.5706, 0.8212]
camera_properties.z_vector = [0.0, 0.8212, -0.5706]

for camera_sensor in camera_sensor_db:
    new_sim.add_camera_sensor(camera_sensor.create_template(), camera_properties.create_properties())

new_sim.compute()
new_sim.close()
