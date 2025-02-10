# # How to modify scene elements

# This tutorial demonstrates how to modify a scene. For example how to modify an existing sensor, how to add a new sensor.
# The logic is the same to modify sources, simulations, materials.

# ## Template vs Instance

# When applicable, the speos objects are separated in two different notions: template and instance.
# The template represents the feature with its inherent characteristics.
# The instance represents the completion of a template by adding properties such as spatial position, link to geometry, etc.

# ### Template

# The template objects are handled by a manager.
# It was explained how to interact with them in the kernel-object-link example ("How to use an ObjectLink").
# The interesting thing about the template notion is that the same template can be used several times with different properties.

# ### Instance

# The template objects are instantiated in the Scene object, with properties needed to place them at the wanted position,
# or attached to the wanted geometry.
# The Scene object will gather all features that you need to run a job (compute a simulation).

# +
import os

from ansys.api.speos.sensor.v1 import camera_sensor_pb2
from ansys.speos.core import Speos
from ansys.speos.core.kernel import SensorTemplateLink
from ansys.speos.core.kernel.scene import Scene
from ansys.speos.core.kernel.sensor_template import SensorTemplate

# If using docker container
tests_data_path = os.path.join("/app", "assets")
# If using local server
# tests_data_path = os.path.join(os.path.abspath(""), os.path.pardir, os.path.pardir, os.path.pardir, "tests", "assets")
# -

# Create connection with speos rpc server

# +
speos = Speos(host="localhost", port=50098)
# -

# Create an empty scene and load speos file to fill it.

# +
my_scene = speos.client.scenes().create()

speos_file = os.path.join(
    tests_data_path, "Inverse_SeveralSensors.speos", "Inverse_SeveralSensors.speos"
)
my_scene.load_file(file_uri=speos_file)
# -

# ## Print data models

# ### Whole scene

# +
print(my_scene)
# -

# ### Sensors (instance + template) in this scene

# +
for sensor_i in my_scene.get().sensors:
    print(sensor_i)  # Print instance data model
    print(speos.client.get_item(key=sensor_i.sensor_guid))  # Print template data model
    print("\n")
# -

# ### Camera sensors in this scene

# +
for sensor_i in my_scene.get().sensors:
    if sensor_i.HasField("camera_properties"):
        print(sensor_i)  # Print instance data model
        print(speos.client.get_item(key=sensor_i.sensor_guid))  # Print template data model
        print("\n")
# -

# ## Modify existing data

# ### Modify a camera instance

# +
my_scene_data = my_scene.get()  # get() = retrieve datamodel corresponding to my_scene
camera_i_0 = my_scene_data.sensors[
    0
]  # retrieve the specific part of the message corresponding to the first sensor
assert camera_i_0.HasField("camera_properties")  # verify that it is a camera

# Modification on protobuf message : axis system + layer type
camera_i_0.camera_properties.ClearField("axis_system")
camera_i_0.camera_properties.axis_system.extend(
    [17.0, 10.0, 15.0] + [0.0, 0.0, -1.0] + [0.0, 1.0, 0.0] + [1.0, 0.0, 0.0]
)  # Origin + Xvector + Yvector + Zvector
camera_i_0.camera_properties.layer_type_none.SetInParent()

# Until now, we only modified the data locally. We need to push the changes to the server:
my_scene.set(my_scene_data)  # set = Update using modified datamodel

print(my_scene.get().sensors[0])  # Do another get() to check new value on database
# -

# ### Modify a camera template

# +
new_distortion_file = os.path.join(
    tests_data_path, os.path.join("CameraInputFiles", "CameraDistortion_150deg.OPTDistortion")
)

# Retrieve SensorTemplateLink corresponding to camera_i_0.sensor_guid
camera_t_0 = speos.client.get_item(camera_i_0.sensor_guid)
assert isinstance(camera_t_0, SensorTemplateLink)

# get() = retrieve datamodel corresponding to camera_t_0 from database
camera_t_0_data = camera_t_0.get()

# Modification on protobuf message : distortion_file_uri + focal_length
assert camera_t_0_data.HasField("camera_sensor_template")
camera_t_0_data.camera_sensor_template.distortion_file_uri = new_distortion_file
camera_t_0_data.camera_sensor_template.focal_length = 4.5

# set = Update using modified datamodel (push modified data to the server)
camera_t_0.set(camera_t_0_data)

print(camera_t_0)  # Print ObjectLink to see its datamodel in database
# -

# ## Add new data (like a new sensor)

# ### Create a camera template

# +
sensor_t_db = speos.client.sensor_templates()  # Retrieve access to sensor templates db

# Create protobuf message SensorTemplate
sensor_t_data = SensorTemplate(name="CameraFromScratch")
sensor_t_data.camera_sensor_template.sensor_mode_photometric.acquisition_integration = 0.01
sensor_t_data.camera_sensor_template.sensor_mode_photometric.acquisition_lag_time = 0
sensor_t_data.camera_sensor_template.sensor_mode_photometric.transmittance_file_uri = os.path.join(
    tests_data_path, os.path.join("CameraInputFiles", "CameraTransmittance.spectrum")
)
sensor_t_data.camera_sensor_template.sensor_mode_photometric.gamma_correction = 2.2
sensor_t_data.camera_sensor_template.sensor_mode_photometric.png_bits = (
    camera_sensor_pb2.EnumSensorCameraPNGBits.PNG_16
)
sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.red_spectrum_file_uri = os.path.join(
    tests_data_path, os.path.join("CameraInputFiles", "CameraSensitivityRed.spectrum")
)
sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.green_spectrum_file_uri = os.path.join(
    tests_data_path, os.path.join("CameraInputFiles", "CameraSensitivityGreen.spectrum")
)
sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.blue_spectrum_file_uri = os.path.join(
    tests_data_path, os.path.join("CameraInputFiles", "CameraSensitivityBlue.spectrum")
)
sensor_t_data.camera_sensor_template.sensor_mode_photometric.color_mode_color.balance_mode_none.SetInParent()
sensor_t_data.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_start = 400
sensor_t_data.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_end = 700
sensor_t_data.camera_sensor_template.sensor_mode_photometric.wavelengths_range.w_sampling = 13
sensor_t_data.camera_sensor_template.focal_length = 5
sensor_t_data.camera_sensor_template.imager_distance = 10
sensor_t_data.camera_sensor_template.f_number = 20
sensor_t_data.camera_sensor_template.distortion_file_uri = os.path.join(
    tests_data_path, os.path.join("CameraInputFiles", "CameraDistortion_130deg.OPTDistortion")
)
sensor_t_data.camera_sensor_template.horz_pixel = 640
sensor_t_data.camera_sensor_template.vert_pixel = 480
sensor_t_data.camera_sensor_template.width = 5
sensor_t_data.camera_sensor_template.height = 5

# Store it in db and retrieve SensorTemplateLink
sensor_t_new = sensor_t_db.create(message=sensor_t_data)
print(sensor_t_new)
# -

# ### Create a camera instance

# +
camera_i_2 = Scene.SensorInstance(name=sensor_t_new.get().name + ".1")
camera_i_2.sensor_guid = sensor_t_new.key  # An instance has to reference a template - here we use the SensorTemplateLink's key that we got just above.
camera_i_2.camera_properties.axis_system.extend(
    [50, 50, 50, 1, 0, 0, 0, 1, 0, 0, 0, 1]
)  # Choose axis system
camera_i_2.camera_properties.layer_type_source.SetInParent()  # choose separation by source
# -

# ### Add this instance in our scene

# +
my_scene_data = my_scene.get()  # Retrieve scene datamodel

# Modify scene datamodel to add our camera instance
my_scene_data.sensors.append(camera_i_2)

# We can also reference it in the first simulation, so that it will be taken into account by this simulation
my_scene_data.simulations[0].sensor_paths.append(camera_i_2.name)  # We reference by name

# Update value in db
my_scene.set(my_scene_data)

# Check scene data after update
print(my_scene)
# -

# When loading a speos file into a scene, this creates many objects (source templates, sensor templates, vop template, sop templates).
# Then at the end of the example, we just clean all databases

# +
for item in (
    speos.client.scenes().list()
    + speos.client.simulation_templates().list()
    + speos.client.sensor_templates().list()
    + speos.client.source_templates().list()
    + speos.client.intensity_templates().list()
    + speos.client.spectrums().list()
    + speos.client.vop_templates().list()
    + speos.client.sop_templates().list()
    + speos.client.parts().list()
    + speos.client.bodies().list()
    + speos.client.faces().list()
):
    item.delete()
# -
