# # How to create a simulation

# This tutorial demonstrates how to create a simulation in script layer.

# ## What is a simulation?

# A simulation contains selected sensors, sources to model ray-trace in space.

# +
import os

import ansys.speos.core as core
import ansys.speos.script as script

# If using docker container
tests_data_path = os.path.join("/app", "assets")
# If using local server
# tests_data_path = os.path.join(os.path.abspath(""), os.path.pardir, os.path.pardir, os.path.pardir, "tests", "assets")
# -

# ## Create connection with speos rpc server

# +
speos = core.Speos(host="localhost", port=50098)
# -

# ## Create Project

# Create a new project first.

# The only way to create a simulation is to create it from a project.

# +
p = script.Project(speos=speos)
print(p)
# -

## Prerequisites

# Create the necessary elements for a simulation: Sensor, source, root part are prerequisites.

# ### Prepare the root part

# +
root_part = p.create_root_part()
root_part.create_body(name="Body.1").create_face(name="Face.1").set_vertices([0, 1, 2, 0, 2, 2, 1, 2, 2]).set_facets([0, 1, 2]).set_normals(
    [0, 0, 1, 0, 0, 1, 0, 0, 1]
)
root_part.commit()
# -

# ### Prepare an irradiance sensor

# +
sensor1 = p.create_sensor(name="Irradiance.1")
sensor1.set_type_colorimetric()  # colorimetric or spectral so that the sensor can be used both in direct and inverse simulation
sensor1.commit()
# -

# ### Prepare a surface source

# +
source1 = p.create_source(name="Surface.1")
source1.set_exitance_constant(geometries=[(script.GeoRef.from_native_link(geopath="Body.1/Face.1"), True)])
source1.set_spectrum().set_blackbody()  # blackbody so that the source can be used both in direct and inverse simulation
source1.commit()
# -

# ## Create a simulation

# +
simulation1 = p.create_simulation(name="Simulation.1")
simulation1.set_sensor_paths(["Irradiance.1"]).set_source_paths(["Surface.1"])
print(simulation1)

simulation1.commit()
print(simulation1)
# -

# ## Set simulation characteristics

# Simulation is defined with the same default values as the GUI speos.

# If the user would like to modify the simulation characteristics,
# it is possible to do so by setting the simulation characteristics as below.

# +
simulation2_direct = p.create_simulation(name="Simulation.2")

simulation2_direct.set_ambient_material_file_uri(
    uri=os.path.join(tests_data_path, "AIR.material")
).set_colorimetric_standard_CIE_1964().set_weight_none().set_geom_distance_tolerance(0.01).set_max_impact(200).set_dispersion(False)
simulation2_direct.set_sensor_paths(["Irradiance.1"]).set_source_paths(["Surface.1"]).commit()
print(simulation2_direct)
# -

# ## Read information

# Read simulation information

# +
print(simulation1)
# -

# Read project information

# +
print(p)
# -

# ## Update simulation settings

# If you are manipulating a simulation already committed, remember to commit your changes.

# If you don't, you will still only watch what is committed on the server.

# +
simulation1.set_ambient_material_file_uri(uri=os.path.join(tests_data_path, "AIR.material"))
simulation1.commit()
print(simulation1)
# -

# ## Reset

# Possibility to reset local values from the one available in the server.

# +
simulation1.set_max_impact(1000)  # adjust max impact but no commit
simulation1.reset()  # reset -> this will apply the server value to the local value
simulation1.delete()  # delete (to display the local value with the below print)
print(simulation1)
# -

# ## Other simulation examples

# ### Inverse simulation

# +
simulation3 = p.create_simulation(name="Simulation.3", feature_type=script.simulation.Inverse)
simulation3.set_sensor_paths(sensor_paths=["Irradiance.1"]).set_source_paths(source_paths=["Surface.1"]).commit()
print(simulation3)
# -

# ### Interactive simulation

# +
simulation4 = p.create_simulation(name="Simulation.4", feature_type=script.simulation.Interactive)
simulation4.set_source_paths(source_paths=["Surface.1"]).commit()
print(simulation4)
# -
