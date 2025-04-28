# # How to create a simulation

# This tutorial demonstrates how to create a simulation.
#
# ## What is a simulation?
#
# A simulation contains selected sensors, sources to model ray-trace in space.
#
# ## Prerequisites
#
# ### Perform imports

# +
from pathlib import Path

from ansys.speos.core import Project, Speos
from ansys.speos.core.simulation import SimulationInteractive, SimulationInverse

# -

# ### Define constants
#
# The constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.
SOURCE_NAME = "Surface.1"
SENSOR_NAME = "Irradiance.1"

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
# client are the same machine.

speos = Speos(host=HOSTNAME, port=GRPC_PORT)

# ### Create a new project
#
# The only way to create a simulation using the core layer, is to create it from a
# project. The ``Project`` class is instantiated by passing a ``Speos`` instance.

p = Project(speos=speos)
print(p)

# ### Prepare prerequisites
#
# Create the necessary elements for a simulation: Sensor, source, root part, optical property are
# prerequisites.

# ### Prepare the root part

root_part = p.create_root_part()
body_1 = root_part.create_body(name="Body.1")
face_1 = (
    body_1.create_face(name="Face.1")
    .set_vertices([0, 1, 2, 0, 2, 2, 1, 2, 2])
    .set_facets([0, 1, 2])
    .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
)
root_part.commit()

# ### Prepare an optical property
# Create Optical Property

opt_prop = p.create_optical_property("Material.1")
opt_prop.set_volume_opaque().set_surface_mirror()

# Choose the geometry for this optical property : Body.1

opt_prop.set_geometries(geometries=[body_1.geo_path])
opt_prop.commit()


# ### Prepare an irradiance sensor


sensor1 = p.create_sensor(name=SENSOR_NAME)
# set type to colorimetric or spectral so that the sensor can be used both in
# direct and inverse simulation
sensor1.set_type_colorimetric()
sensor1.commit()

# ### Prepare a surface source

source1 = p.create_source(name=SOURCE_NAME)
source1.set_exitance_constant(geometries=[(face_1.geo_path, True)])
# define a spectrum which is not monochromatic so it can be used in both direct and inverse
# simulation
source1.set_spectrum().set_blackbody()
source1.commit()

# ## Create a simulation

simulation1 = p.create_simulation(name="Simulation.1")
simulation1.set_sensor_paths([SENSOR_NAME]).set_source_paths([SOURCE_NAME])
print(simulation1)
simulation1.commit()
print(simulation1)


# ### Set simulation characteristics
#
# Simulation is defined with the same default values as the GUI speos.
#
# If the user would like to modify the simulation characteristics,
# it is possible to do so by setting the simulation characteristics as below.


simulation2_direct = p.create_simulation(name="Simulation.2")
simulation2_direct.set_ambient_material_file_uri(
    uri=str(assets_data_path / "AIR.material")
).set_colorimetric_standard_CIE_1964().set_weight_none().set_geom_distance_tolerance(
    0.01
).set_max_impact(200).set_dispersion(False)
simulation2_direct.set_sensor_paths([SENSOR_NAME]).set_source_paths([SOURCE_NAME]).commit()
print(simulation2_direct)


# ### Read information
#
# Read simulation information

print(simulation1)

# Read project information

print(p)

# ## Update simulation settings
#
# If you are manipulating a simulation already committed, remember to commit your changes.
#
# If you don't, you will still only watch what is committed on the server.

simulation1.set_ambient_material_file_uri(uri=str(assets_data_path / "AIR.material"))
simulation1.commit()
print(simulation1)


# ## Reset
#
# Possibility to reset local values from the one available in the server.

simulation1.set_max_impact(1000)  # adjust max impact but no commit
simulation1.reset()  # reset -> this will apply the server value to the local value
simulation1.delete()  # delete (to display the local value with the below print)
print(simulation1)


# ## Other simulation examples
#
# ### Inverse simulation

simulation3 = p.create_simulation(name="Simulation.3", feature_type=SimulationInverse)
simulation3.set_sensor_paths(sensor_paths=[SENSOR_NAME]).set_source_paths(
    source_paths=[SOURCE_NAME]
).commit()
print(simulation3)

# ### Interactive simulation

simulation4 = p.create_simulation(name="Simulation.4", feature_type=SimulationInteractive)
simulation4.set_source_paths(source_paths=[SOURCE_NAME]).commit()
print(simulation4)
