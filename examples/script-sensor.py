# # How to create a sensor

# This tutorial demonstrates how to create a sensor in script layer.

# There are different type of sensors available: irradiance sensor, radiance sensor, camera sensor.

# +
import os

import ansys.speos.core as core
import ansys.speos.core as script

# If using docker container
tests_data_path = os.path.join("/app", "assets")
# If using local server
# tests_data_path = os.path.join(os.path.abspath(""), os.path.pardir, os.path.pardir, os.path.pardir, "tests", "assets")
# -

# ## Create connection with speos rpc server

# +
speos = core.Speos(host="localhost", port=50098)
# -

# ## Create a new project

# The only way to create a sensor, is to create it from a project.

# +
p = script.Project(speos=speos)
print(p)
# -

# ## Create

# Create locally.

# The mention "local: " is added when printing the sensor

# +
distortion_file_path = os.path.join(
    tests_data_path, "CameraInputFiles", "CameraDistortion_130deg.OPTDistortion"
)
transmittance_file_path = os.path.join(
    tests_data_path, "CameraInputFiles", "CameraTransmittance.spectrum"
)
blue_spectrum_path = os.path.join(
    tests_data_path, "CameraInputFiles", "CameraSensitivityBlue.spectrum"
)
green_spectrum_path = os.path.join(
    tests_data_path, "CameraInputFiles", "CameraSensitivityGreen.spectrum"
)
red_spectrum_path = os.path.join(
    tests_data_path, "CameraInputFiles", "CameraSensitivityRed.spectrum"
)

sensor1 = p.create_sensor(name="Camera.1", feature_type=script.sensor.Camera)
sensor1.set_distortion_file_uri(uri=distortion_file_path)
# Choose photometric mode
sensor1.set_mode_photometric().set_transmittance_file_uri(uri=transmittance_file_path)
# Choose color mode (will imply to give spectrum file for blue, green and red)
sensor1.set_mode_photometric().set_mode_color().set_blue_spectrum_file_uri(uri=blue_spectrum_path)
sensor1.set_mode_photometric().set_mode_color().set_green_spectrum_file_uri(uri=green_spectrum_path)
sensor1.set_mode_photometric().set_mode_color().set_red_spectrum_file_uri(uri=red_spectrum_path)
print(sensor1)
# -

# ## Push it to the server.

# Now that it is committed to the server, the mention "local: " is no more present when printing the sensor.

# +
sensor1.commit()
print(sensor1)
# -

# ## Another example
#
# Set more characteristics.

# Camera feature is created with the same default values as the GUI speos.

# If the user would like to modify the camera characteristics,
# it is possible to do so as below.

# +
distortion_file_path = os.path.join(
    tests_data_path, "CameraInputFiles", "CameraDistortion_130deg.OPTDistortion"
)
transmittance_file_path = os.path.join(
    tests_data_path, "CameraInputFiles", "CameraTransmittance.spectrum"
)
blue_spectrum_path = os.path.join(
    tests_data_path, "CameraInputFiles", "CameraSensitivityBlue.spectrum"
)
green_spectrum_path = os.path.join(
    tests_data_path, "CameraInputFiles", "CameraSensitivityGreen.spectrum"
)
red_spectrum_path = os.path.join(
    tests_data_path, "CameraInputFiles", "CameraSensitivityRed.spectrum"
)

sensor2 = p.create_sensor(name="Camera.2", feature_type=script.sensor.Camera)
sensor2.set_distortion_file_uri(uri=distortion_file_path)
sensor2.set_mode_photometric().set_transmittance_file_uri(uri=transmittance_file_path)
sensor2.set_mode_photometric().set_layer_type_source()
sensor2.set_mode_photometric().set_mode_color().set_blue_spectrum_file_uri(uri=blue_spectrum_path)
sensor2.set_mode_photometric().set_mode_color().set_green_spectrum_file_uri(uri=green_spectrum_path)
sensor2.set_mode_photometric().set_mode_color().set_red_spectrum_file_uri(uri=red_spectrum_path)
sensor2.set_focal_length(5.5)
sensor2.set_height(value=6).set_width(value=6)  # dimensions
sensor2.set_axis_system(
    [20, 10, 40, 1, 0, 0, 0, 1, 0, 0, 0, 1]
)  # camera location [Origin, Xvector, Yvector, Zvector]
sensor2.commit()

print(sensor2)
# -


# ## Read

# ### Sensor Instance

# A mention "local: " is added if it is not yet committed to the server

# +
print(sensor1)
# -

# ### Project

# Committed feature will appear in the project.

# +
print(p)
# -

# ## Update

# Tipp: if you are manipulating a source already committed, don't forget to commit your changes.

# If you don't, you will still only watch what is committed on the server.

# +
# modify f number and axis system
sensor1.set_f_number(value=11).set_axis_system([17, 10, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
sensor1.commit()
print(sensor1)
# -

# ## Reset

# Possibility to reset local values from the one available in the server.

# +
sensor1.set_mode_geometric()  # set camera in geometric mode but no commit
sensor1.reset()  # reset -> this will apply the server value (photometric mode) to the local value
sensor1.delete()  # delete (to display the local value with the below print)
print(sensor1._sensor_template)
# -

# ## Delete

# Once the data is deleted from the server, you can still work with local data and maybe commit later.

# +
sensor2.delete()
print(sensor2)
# -

# +
sensor1.delete()
# -

# ## Other sensors

# ### Irradiance sensor

# +
sensor3 = p.create_sensor(name="Irradiance.1", feature_type=script.sensor.Irradiance)
sensor3.commit()
print(sensor3)
# -

# +
sensor3.set_type_colorimetric()
sensor3.set_layer_type_polarization()
sensor3.commit()
print(sensor3)
# -

# +
sensor3.delete()
# -

# ### radiance sensor

# +
sensor4 = p.create_sensor(name="Radiance.1", feature_type=script.sensor.Radiance)
sensor4.commit()
print(sensor4)
# -

# +
sensor4.set_focal(value=200).set_type_spectral()
sensor4.set_layer_type_source()
sensor4.commit()
print(sensor4)
# -

# +
sensor4.delete()
print(sensor4)
# -
