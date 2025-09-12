# # How to create a sensor
#
# This tutorial demonstrates how to create a sensor.
#
# There are different type of sensors available: irradiance sensor, radiance sensor, camera sensor.

# ## Prerequisites
#
# ### Perform imports

from pathlib import Path

from ansys.speos.core import GeoRef, Project, Speos, launcher
from ansys.speos.core.sensor import (
    Sensor3DIrradiance,
    SensorCamera,
    SensorIrradiance,
    SensorRadiance,
)

# ### Define constants
#
# The constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.
FILES = "CameraInputFiles"

# ### Define helper functions


def create_helper_geometries(project: Project):
    """Create bodies and faces."""

    def create_face(body):
        (
            body.create_face(name="TheFaceF")
            .set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0])
            .set_facets([0, 1, 2])
            .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
            .commit()
        )

    root_part = project.create_root_part().commit()
    body_b1 = root_part.create_body(name="TheBodyB").commit()
    body_b2 = root_part.create_body(name="TheBodyC").commit()
    body_b3 = root_part.create_body(name="TheBodyD").commit()
    body_b4 = root_part.create_body(name="TheBodyE").commit()
    for b in [body_b1, body_b2, body_b3, body_b4]:
        create_face(b)


# ## Model Setup
#
# ### Load assets
# The assets used to run this example are available in the
# [PySpeos repository](https://github.com/ansys/pyspeos/) on GitHub.
#
# > **Note:** Make sure you
# > have downloaded simulation assets and set ``assets_data_path``
# > to point to the assets folder.

if USE_DOCKER:  # Running on the remote server.
    assets_data_path = Path("/app") / "assets"
else:
    assets_data_path = Path("/path/to/your/download/assets/directory")

# ### Connect to the RPC Server
# This Python client connects to a server where the Speos engine
# is running as a service. In this example, the server and
# client are the same machine. The launch_local_speos_rpc_method can
# be used to start a local instance of the service.

if USE_DOCKER:
    speos = Speos(host=HOSTNAME, port=GRPC_PORT)
else:
    speos = launcher.launch_local_speos_rpc_server(port=GRPC_PORT)

# ## Create a new project
#
# The only way to create a sensor, is to create it from a project.

p = Project(speos=speos)
print(p)

# ## Create
#
# Create locally.

# The mention "local: " is added when printing the sensor

# +

distortion_file_path = str(assets_data_path / FILES / "CameraDistortion_130deg.OPTDistortion")
transmittance_file_path = str(assets_data_path / FILES / "CameraTransmittance.spectrum")
blue_spectrum_path = str(assets_data_path / FILES / "CameraSensitivityBlue.spectrum")
green_spectrum_path = str(assets_data_path / FILES / "CameraSensitivityGreen.spectrum")
red_spectrum_path = str(assets_data_path / FILES / "CameraSensitivityRed.spectrum")

sensor1 = p.create_sensor(name="Camera.1", feature_type=SensorCamera)
sensor1.distortion_file_uri = distortion_file_path
# Choose photometric mode
sensor1.set_mode_photometric().transmittance_file_uri = transmittance_file_path
# Choose color mode (will imply to give spectrum file for blue, green and red)
mode_color = sensor1.photometric.set_mode_color()
mode_color.blue_spectrum_file_uri = blue_spectrum_path
mode_color.green_spectrum_file_uri = green_spectrum_path
mode_color.red_spectrum_file_uri = red_spectrum_path
print(sensor1)
# -

# ## Push it to the server.
#
# Now that it is committed to the server, the mention "local: " is no more present when printing the
# sensor.

sensor1.commit()
print(sensor1)

# ## Another example
#
# Set more characteristics.
#
# Camera feature is created with the same default values as the GUI speos.
#
# If the user would like to modify the camera characteristics,
# it is possible to do so as below.

# +
distortion_file_path = str(assets_data_path / FILES / "CameraDistortion_130deg.OPTDistortion")
transmittance_file_path = str(assets_data_path / FILES / "CameraTransmittance.spectrum")
blue_spectrum_path = str(assets_data_path / FILES / "CameraSensitivityBlue.spectrum")
green_spectrum_path = str(assets_data_path / FILES / "CameraSensitivityGreen.spectrum")
red_spectrum_path = str(assets_data_path / FILES / "CameraSensitivityRed.spectrum")

sensor2 = p.create_sensor(name="Camera.2", feature_type=SensorCamera)
sensor2.distortion_file_uri = distortion_file_path
photometric = sensor2.set_mode_photometric()
photometric.transmittance_file_uri = transmittance_file_path
photometric.set_layer_type_source()
color = photometric.set_mode_color()
color.blue_spectrum_file_uri = blue_spectrum_path
color.green_spectrum_file_uri = green_spectrum_path
color.red_spectrum_file_uri = red_spectrum_path
sensor2.focal_length = 5.5
sensor2.height = 6
sensor2.width = 6  # dimensions
sensor2.axis_system = [20, 10, 40, 1, 0, 0, 0, 1, 0, 0, 0, 1]
# camera location [Origin, Xvector, Yvector, Zvector]
sensor2.commit()

print(sensor2)
# -


# ## Read
#
# ### Sensor Instance
#
# A mention "local: " is added if it is not yet committed to the server

print(sensor1)

# ### Project

# Committed feature will appear in the project.

print(p)

# ## Update
#
# Tipp: if you are manipulating a sensor already committed, don't forget to commit your changes.
#
# If you don't, you will still only watch what is committed on the server.

# modify f number and axis system
sensor1.f_number = 11
sensor1.axis_system = [17, 10, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
sensor1.commit()
print(sensor1)

# ## Reset
#
# Possibility to reset local values from the one available in the server.

sensor1.set_mode_geometric()  # set camera in geometric mode but no commit
sensor1.reset()  # reset -> this will apply the server value (photometric mode) to the local value
sensor1.delete()  # delete (to display the local value with the below print)
print(sensor1._sensor_template)

# ## Delete
#
# Once the data is deleted from the server, you can still work with local data and maybe commit
# later.

sensor2.delete()
print(sensor2)

sensor1.delete()


# ## Other sensors
#
# ### Irradiance sensor

sensor3 = p.create_sensor(name="Irradiance.1", feature_type=SensorIrradiance)
sensor3.commit()
print(sensor3)

sensor3.set_type_radiometric()
sensor3.set_layer_type_polarization()
sensor3.commit()
print(sensor3)

sensor3.delete()

# ### radiance sensor

sensor4 = p.create_sensor(name="Radiance.1", feature_type=SensorRadiance)
sensor4.commit()
print(sensor4)

sensor4.focal = 200
sensor4.set_type_spectral()
sensor4.set_layer_type_source()
sensor4.commit()
print(sensor4)

sensor4.delete()
print(sensor4)

# ### 3D irradiance sensor

create_helper_geometries(p)
sensor5 = p.create_sensor(name="3D_Irradiance.2", feature_type=Sensor3DIrradiance)
sensor5.geometries = [GeoRef.from_native_link("TheBodyB/TheFaceF")]
sensor5.commit()
print(sensor5)

speos.close()
