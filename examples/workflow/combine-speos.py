# # Moving car example by combining Speos files
#
# This tutorial demonstrates how to run moving car workflow use case.
# ## Prerequisites
#
# ### Perform imports

# +
import os
from pathlib import Path

from ansys.speos.core import Part, Speos
from ansys.speos.core.sensor import SensorCamera
from ansys.speos.core.simulation import SimulationInverse
from ansys.speos.core.source import SourceLuminaire
from ansys.speos.core.workflow.combine_speos import SpeosFileInstance, combine_speos

# -

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
car_names = ["BlueCar", "RedCar"]
environment_name = "Env_Simplified"
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.
USE_GPU = False

# ## Coordinate systems
#
# Define the global coordinate systems for each of the assets.

global_cs = [
    0,
    0,
    0,  # Origin
    1,
    0,
    0,  # x-direction
    0,
    1,
    0,  # y-direction
    0,
    0,
    1,
]
car_cs = {}
car_cs["red"] = [
    2000,
    0,
    35000,  # Origin of red car
    0.0,
    0.0,
    -1.0,  # x-direction
    -1.0,
    0.0,
    0.0,  # y-direction
    0.0,
    1.0,
    0.0,  # z-direction
]
car_cs["blue"] = [2000, 0, 35000, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0]


# ## Load assets
# Assets used to run this example are available in the
# [PySpeos repository](https://github.com/ansys/pyspeos/) on GitHub.
#
# > **Note:** Make sure you
# > have downloaded simulation assets and set ``test_data_path``
# > to point to the assets folder.

if USE_DOCKER:  # Running on the remote server.
    tests_data_path = Path("/app") / "assets"
else:
    tests_data_path = Path().resolve().parent.parent / "tests" / "assets"

# ## Create connection with speos rpc server

speos = Speos(host=HOSTNAME, port=GRPC_PORT)

# ## Combine several speos files into one project
#
# Here we are building a project with:
# - An environment which is a road
# - A blue car
# - A red car

full_env_path = tests_data_path / f"{environment_name}.speos" / f"{environment_name}.speos"
car_paths = [tests_data_path / f"{car}.speos" / f"{car}.speos" for car in car_names]
assets = [
    SpeosFileInstance(
        speos_file=str(full_env_path),
        axis_system=global_cs,
    ),
    SpeosFileInstance(
        speos_file=str(car_paths[0]),
        axis_system=car_cs["red"],
    ),
    SpeosFileInstance(
        speos_file=str(car_paths[1]),
        axis_system=car_cs["blue"],
    ),
]
p = combine_speos(
    speos=speos,
    speos_to_combine=assets,
)

print(p)

# ## Preview the project
#
# User can review the created/loaded project using preview method.

p.preview()

# ## Complete the project with sensor/source/simulation
#
# We are adding a camera sensor to have output results, a luminaire to have a light source.
#
# And, we gather the source and the sensor into a simulation (we will compute it just after).
#
# ### Create a sensor

ssr = p.create_sensor(name="Camera.1", feature_type=SensorCamera)
ssr.set_distortion_file_uri(
    uri=str(tests_data_path / "CameraInputFiles" / "CameraDistortion_190deg.OPTDistortion")
).set_mode_photometric().set_transmittance_file_uri(
    uri=str(tests_data_path / "CameraInputFiles" / "CameraTransmittance.spectrum")
).set_mode_color().set_red_spectrum_file_uri(
    uri=str(tests_data_path / "CameraInputFiles" / "CameraSensitivityRed.spectrum")
).set_blue_spectrum_file_uri(
    uri=str(tests_data_path / "CameraInputFiles" / "CameraSensitivityBlue.spectrum")
).set_green_spectrum_file_uri(
    uri=str(tests_data_path / "CameraInputFiles" / "CameraSensitivityGreen.spectrum")
)
ssr.set_axis_system([-2000, 1500, 11000, -1, 0, 0, 0, 1, 0, 0, 0, -1])
ssr.commit()

# ### Create a source
#
# In this example, a luminaire source is created with an IES file.
#
# More details on creating/editing source examples can be found in core examples.

# +
src = p.create_source(name="Luminaire.1", feature_type=SourceLuminaire)
src.set_intensity_file_uri(
    uri=str(tests_data_path / "IES_C_DETECTOR.ies")
).set_spectrum().set_daylightfluorescent()
src.set_axis_system([0, 10000, 50000, 1, 0, 0, 0, 1, 0, 0, 0, 1])

src.commit()
# -

# ### Create a simulation
#
# More details on creating/editing simulation examples can be found in core examples.

sim = p.create_simulation(name="Inverse.1", feature_type=SimulationInverse)
sim.set_sensor_paths(["Camera.1"]).set_source_paths(["Luminaire.1"])
sim.commit()

# ## Run the simulation
#
# Simulation can be run using CPU via compute_CPU method or using GPU via compute_GPU method.

run_sim = sim.compute_GPU if USE_GPU else sim.compute_CPU
run_sim()  # Run the simulation

# ## Check and review result
#
# Open result (only windows)

if os.name == "nt":
    from ansys.speos.core.workflow.open_result import open_result_image

    open_result_image(simulation_feature=sim, result_name="Camera.1.png")

# ## Modify part
#
# Move the part via changing the axis_system of a part.
#
# axis_system is a list of 12 float values:
# x, y, z,
# x_vect_x, x_vect_y, x_vect_z,
# y_vect_x, y_vect_y, y_vect_z,
# z_vect_x, z_vect_y, z_vect_z.

blue_car_sub_part = p.find(name="BlueCar", feature_type=Part.SubPart)[0]
blue_car_sub_part.set_axis_system([2000, 0.0, 20000, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
blue_car_sub_part.commit()

# ## Re-run simulation with the modified part position

run_sim()

# Review result:

if os.name == "nt":
    open_result_image(simulation_feature=sim, result_name="Camera.1.png")

# ## Modify camera property
#
# Modify the camera, e.g. focal length to 10

cam1 = p.find(name="Camera.1", feature_type=SensorCamera)[0]
cam1.set_focal_length(value=10)
cam1.commit()

# Re-run the simulation and review result

run_sim()
if os.name == "nt":
    open_result_image(simulation_feature=sim, result_name="Camera.1.png")
