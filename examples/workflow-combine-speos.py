# # Moving car workflow example using script layer

# This tutorial demonstrates how to run moving car workflow use case using script layer.

# +
import os

import ansys.speos.core as core
import ansys.speos.script as script

tests_data_path = os.path.join("/app", "assets")
# -

# Create connection with speos rpc server
# +
speos = core.Speos(host="localhost", port=50098)
# -

# ## Combine several speos file into one project feature

# Here we are building a project with:
# - An environment which is a road
# - A blue car
# - A red car
# +
from ansys.speos.workflow.combine_speos import SpeosFileInstance, combine_speos

p = combine_speos(
    speos=speos,
    speos_to_combine=[
        SpeosFileInstance(
            speos_file=os.path.join(tests_data_path, "Env_Simplified.speos", "Env_Simplified.speos"),
            axis_system=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        ),
        SpeosFileInstance(
            speos_file=os.path.join(tests_data_path, "BlueCar.speos", "BlueCar.speos"),
            axis_system=[2000, 0, 35000, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        ),
        SpeosFileInstance(
            speos_file=os.path.join(tests_data_path, "RedCar.speos", "RedCar.speos"),
            axis_system=[-4000, 0, 48000, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0],
        ),
    ],
)
print(p)
# -


# ## Preview the project
# +
p.preview()
# -

# ## Complete the project with source/sensor/simulation

# We are adding a camera sensor to have output results, a luminaire to have a light source.
# And we gather the sensor and the camera into a simulation. (we will compute it just after)
# +
ssr = p.create_sensor(name="Camera.1", feature_type=script.sensor.Camera)
ssr.set_distortion_file_uri(
    uri=os.path.join(tests_data_path, "CameraInputFiles", "CameraDistortion_190deg.OPTDistortion")
).set_mode_photometric().set_transmittance_file_uri(
    uri=os.path.join(tests_data_path, "CameraInputFiles", "CameraTransmittance.spectrum")
).set_mode_color().set_red_spectrum_file_uri(
    uri=os.path.join(tests_data_path, "CameraInputFiles", "CameraSensitivityRed.spectrum")
).set_blue_spectrum_file_uri(
    uri=os.path.join(tests_data_path, "CameraInputFiles", "CameraSensitivityBlue.spectrum")
).set_green_spectrum_file_uri(
    uri=os.path.join(tests_data_path, "CameraInputFiles", "CameraSensitivityGreen.spectrum")
)
ssr.set_axis_system([-2000, 1500, 11000, -1, 0, 0, 0, 1, 0, 0, 0, -1])
ssr.commit()
# -

# Create a source
# +
src = p.create_source(name="Luminaire.1", feature_type=script.source.Luminaire)
src.set_intensity_file_uri(uri=os.path.join(tests_data_path, "IES_C_DETECTOR.ies")).set_spectrum().set_daylightfluorescent()
src.set_axis_system([0, 10000, 50000, 1, 0, 0, 0, 1, 0, 0, 0, 1])
src.commit()
# -

# Create a simulation
# +
sim = p.create_simulation(name="Inverse.1", feature_type=script.simulation.Inverse)
sim.set_sensor_paths(["Camera.1"]).set_source_paths(["Luminaire.1"])
sim.commit()
# -


# Run the simulation
# +
sim.compute_CPU()
# -

# ## Check Result
# open result (only windows)
# +
if os.name == "nt":
    from ansys.speos.workflow.open_result import open_result_image

    open_result_image(simulation_feature=sim, result_name="Camera.1.png")
# -


# ## Modify project
# Modify part
# +
blue_car_sub_part = p.find(name="BlueCar", feature_type=script.Part.SubPart)[0]
blue_car_sub_part.set_axis_system([2000, 0.0, 20000, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
blue_car_sub_part.commit()
# -

# Run simulation with new part position
# +
sim.compute_CPU()
# -

# Review result:
# +
if os.name == "nt":
    open_result_image(simulation_feature=sim, result_name="Camera.1.png")
# -

# Modify camera property
# +
cam1 = p.find(name="Camera.1", feature_type=script.sensor.Camera)[0]
cam1.set_focal_length(value=10)
cam1.commit()
# -

# Run the simulation and review result
# +
sim.compute_CPU()
if os.name == "nt":
    open_result_image(simulation_feature=sim, result_name="Camera.1.png")
# -
