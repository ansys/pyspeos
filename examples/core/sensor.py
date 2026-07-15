# # How to create a sensor
#
# This tutorial demonstrates how to create a sensor.
#
# There are different type of sensors available: irradiance sensor, radiance sensor, camera sensor.

# ## Prerequisites
#
# ### Perform imports

from pathlib import Path

from ansys.speos.core import Face, Project, Speos, launcher
from ansys.speos.core.generic.parameters import (
    CameraSensorParameters,
    ColorParameters,
    ObserverSensorParameters,
    PhotometricCameraParameters,
    PolarIntensityDimensionsParameters,
    PolarIntensityFormatTypes,
    PolarIntensitySensorParameters,
)
from ansys.speos.core.kernel.client import (
    default_docker_channel,
)
from ansys.speos.core.sensor import (
    Sensor3DIrradiance,
    SensorCamera,
    SensorImmersive,
    SensorIrradiance,
    SensorObserver,
    SensorPolarIntensity,
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
        f = body.create_face(name="TheFaceF")
        f.vertices = [0, 0, 0, 1, 0, 0, 0, 1, 0]
        f.facets = [0, 1, 2]
        f.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
        f.commit()

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
    speos = Speos(channel=default_docker_channel())
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
# Set more characteristics, and use parameters classes.
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

color_params = ColorParameters(
    blue_spectrum_file_uri=blue_spectrum_path,
    green_spectrum_file_uri=green_spectrum_path,
    red_spectrum_file_uri=red_spectrum_path,
)
photo_params = PhotometricCameraParameters(
    color_mode=color_params, layer_type="by_source", transmittance_file_uri=transmittance_file_path
)
param = CameraSensorParameters(
    sensor_type_parameters=photo_params,
    distortion_file_uri=distortion_file_path,
    axis_system=[20, 10, 40, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    # camera location [Origin, Xvector, Yvector, Zvector]
    focal_length=5.5,
    height=6,  # dimensions
    width=6,
)

sensor2 = p.create_sensor("Camera_Parameter", feature_type=SensorCamera, parameters=param)
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
face = p.find(name="TheBodyB/TheFaceF", feature_type=Face)[0]
sensor5.geometries = [face]
sensor5.commit()
print(sensor5)

# ### Immersive sensor
#
# An immersive sensor wraps the observer in a virtual cube and records light arriving from all
# six directions (front, back, left, right, top, bottom).  It can be used with both direct and
# inverse simulations.
#

# Create an immersive sensor and commit it to show its default settings.

sensor6 = p.create_sensor(name="Immersive.1", feature_type=SensorImmersive)
print(sensor6)  # local: not yet on server

sensor6.commit()
print(sensor6)  # now on server

# **Customise the sensor**
#
# The sampling controls the pixel count per cube face, the integration angle is used for
# direct simulations, and the wavelengths range selects the spectral window.

sensor6.sampling = 256
sensor6.integration_angle = 10.0
sensor6.stereo_interocular_distance = 50

wl = sensor6.set_wavelengths_range()
wl.start = 380.0
wl.end = 780.0
wl.sampling = 20

# Exclude the bottom face so rays from below are not recorded.
sensor6.exclude_bottom = True

# Separate results by light source.
sensor6.set_layer_type_source()

# Reposition the sensor (Origin, X-axis, Y-axis, Z-axis).
sensor6.axis_system = [5, 0, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]

sensor6.commit()
print(sensor6)

# **Reset and delete**

sensor6.sampling = 512  # local modification — not yet committed
sensor6.reset()  # restores the last committed value (256)
print(sensor6)

sensor6.delete()
print(sensor6)

# ### Observer sensor
#
# An observer sensor places multiple virtual viewpoints on a sphere around the scene.
# It is useful when you want to sample a setup from several directions with one feature.
#
# **Default values**

sensor7 = p.create_sensor(name="Observer.1", feature_type=SensorObserver)
print(sensor7)  # local: not yet on server

sensor7.commit()
print(sensor7)  # now on server

# **Customise the sensor**
#
# The focal distance defines the observer plane, ``distance`` controls the radius of the
# sampling sphere, and the angular range controls how many viewpoints are created.

sensor7.focal = 320.0
sensor7.integration_angle = 7.5
sensor7.distance = 130.0
sensor7.stereo_interocular_distance = 63.0

observer_wl = sensor7.set_wavelengths_range()
observer_wl.start = 430.0
observer_wl.end = 670.0
observer_wl.sampling = 18

observer_dims = sensor7.set_dimensions()
observer_dims.x_start = -90.0
observer_dims.x_end = 90.0
observer_dims.x_sampling = 110
observer_dims.y_start = -70.0
observer_dims.y_end = 70.0
observer_dims.y_sampling = 75

observer_angles = sensor7.set_angular_range()
observer_angles.x_start = -55.0
observer_angles.x_end = 55.0
observer_angles.x_sampling = 9
observer_angles.y_start = -42.0
observer_angles.y_end = 42.0
observer_angles.y_sampling = 6

# Separate the recorded results by source and move the sensor frame.
sensor7.set_layer_type_source()
sensor7.axis_system = [10, 0, 15, 1, 0, 0, 0, 1, 0, 0, 0, 1]

sensor7.commit()
print(sensor7)

# **Create from parameter dataclass**
#
# Observer sensors can also be configured in one shot with a parameter dataclass.

observer_params = ObserverSensorParameters(
    focal=280.0,
    integration_angle=6.0,
    distance=110.0,
    interocular_distance=66.0,
    axis_system=[5, 10, 15, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    layer_type="by_source",
)
sensor8 = p.create_sensor(
    name="Observer.Parameters",
    feature_type=SensorObserver,
    parameters=observer_params,
)
sensor8.commit()
print(sensor8)

# **Reset and delete**

sensor7.distance = 300.0  # local modification — not yet committed
sensor7.stereo_interocular_distance = None
sensor7.reset()  # restores the last committed values from the server
print(sensor7)

sensor8.delete()
print(sensor8)

sensor7.delete()
print(sensor7)

# ### Polar intensity sensor
#
# A polar intensity sensor generates an IES/Eulumdat photometric file from the simulation.
# It supports format selection, explicit angular sampling, and far-field or near-field setup.

sensor_polar = p.create_sensor(name="PolarIntensity.1", feature_type=SensorPolarIntensity)
print(sensor_polar)  # local: not yet on server

sensor_polar.commit()
print(sensor_polar)  # now on server

# Customise format, sampling and field configuration.
assert isinstance(sensor_polar, SensorPolarIntensity)
sensor_polar.set_format_eulumdat()
sensor_polar.set_constant_sampling()
sensor_polar.horizontal_sampling = 180
sensor_polar.vertical_sampling = 90
sensor_polar.set_far_field()
sensor_polar.integration_angle = 1
sensor_polar.axis_system = [0, 0, 25, 1, 0, 0, 0, 1, 0, 0, 0, 1]

sensor_polar.commit()
print(sensor_polar)

# The same sensor can be created directly from parameter dataclasses.
polar_param = PolarIntensitySensorParameters(
    format=PolarIntensityFormatTypes.iesna_b,
    dimensions=PolarIntensityDimensionsParameters(horizontal_sampling=37, vertical_sampling=37),
    integration_angle=1.0,
    axis_system=[10, 0, 30, 1, 0, 0, 0, 1, 0, 0, 0, 1],
)

sensor_polar_param = p.create_sensor(
    name="PolarIntensity.Parameters",
    feature_type=SensorPolarIntensity,
    parameters=polar_param,
)
sensor_polar_param.commit()
print(sensor_polar_param)

sensor_polar_param.delete()
sensor_polar.delete()

speos.close()
