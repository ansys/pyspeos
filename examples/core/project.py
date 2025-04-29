# # How to create a project
#
# This tutorial demonstrates how to create a project.
#
# ## What is a project?
#
# A project is a speos simulation container that includes parts, material properties, sensor,
# sources and simulations.
#
# In this tutorial you will learn how to create a project from scratch or from a pre-defined .speos
# file.
#
# ## Prerequisites
#
# ### Perform imports
# +
import os
from pathlib import Path

from ansys.speos.core import Project, Speos
from ansys.speos.core.launcher import launch_local_speos_rpc_server
from ansys.speos.core.sensor import SensorIrradiance
from ansys.speos.core.simulation import SimulationDirect
from ansys.speos.core.source import SourceLuminaire, SourceSurface

# -

# ### Define constants
#
# The constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.


# ## Model Setup
#
# ### Load assets
# The assets used to run this example are available in the
# [PySpeos repository](https://github.com/ansys/pyspeos/) on GitHub.
#
# > **Note:** Make sure you
# > have downloaded simulation assets and set ``assets_data_path``
# > to point to the assets folder.
USE_DOCKER = False
if USE_DOCKER:  # Running on the remote server.
    assets_data_path = Path("/app") / "assets"
else:
    assets_data_path = Path("/path/to/your/download/assets/directory")

# ### Start/Connect to Speos RPC Server
# This Python client connects to a server where the Speos engine
# is running as a service. In this example, the server and
# client are the same machine. the launch_local_speos_rpc_method can
# be used to start a local instance of the service.

if USE_DOCKER:
    speos = Speos(host=HOSTNAME, port=GRPC_PORT)
else:
    speos = launch_local_speos_rpc_server(port=GRPC_PORT)

# ## New empty project
#
# An empty project can be created by only passing speos rpc server to
# the Project class.


p = Project(speos=speos)
print(p)


# ### Create features
# The Project class has a multitude of method to create Speos features.
# each create methedo takes the name and the Feature type as arguments
# and returns the created Feature
# #### Source

source1 = p.create_source(name="Source.1", feature_type=SourceLuminaire)
source1.set_intensity_file_uri(uri=str(assets_data_path / "IES_C_DETECTOR.ies"))
source1.commit()


# #### Sensor

sensor1 = p.create_sensor(name="Sensor.1")
sensor1.commit()

# #### Optical property

opt_prop1 = p.create_optical_property(name="Material.1")
opt_prop1.commit()

# ## Read Project
#
# User can read the content of a project via simply printing the project

print(p)

# Or, user can use the find_key method to read a specific feature:

for it in p.find_key(key="monochromatic"):
    print(it)

# ## Find a feature inside a project
#
# ### Use find method with an exact name
#
# If no feature is found, an empty list is returned.

# +
features = p.find(name="UnexistingName")
print(features)
# -

# +
features = p.find(name="Sensor.1")
print(features[0])
# -

# ### Use find method with feature type
#
# Here a wrong type is given: no source is called Sensor.1 in the project

# +
features = p.find(name="Sensor.1", feature_type=SourceLuminaire)
print(features)
# -

# +
features = p.find(name="Sensor.1", feature_type=SensorIrradiance)
print(features[0])
# -

# ### Use find method with approximation name with regex
#
# find a feature with name starting with Mat

features = p.find(name="Mat.*", name_regex=True)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)

# find all features without defining any name

features = p.find(name=".*", name_regex=True)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)

# ## Delete
#
# This erases the scene content in server database.
#
# This deletes also each feature of the project

p.delete()
print(p)

# As the features were deleted just above -> this returns an empty vector

print(p.find(name="Sensor.1"))

# ## Create project from pre-defined speos project
#
# Via passing the .speos/.sv5 file path to the Project class.

p2 = Project(
    speos=speos,
    path=str(assets_data_path / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"),
)
print(p2)

# ## Preview the part information
#
# User can check the project part using preview method.

p2.preview()

# use find_key method to find specific information

for it in p2.find_key(key="surface"):
    print(it)

# Use find method to retrieve feature:
#
# e.g. surface source

features = p2.find(name=".*", name_regex=True, feature_type=SourceSurface)
print(features)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)
src = features[1]

# modify the surface source, e.g. surface source wavelength:

src.set_spectrum().set_monochromatic(wavelength=550)
src.commit()


# Retrieve a simulation feature:

# +
features = p2.find(name=".*", name_regex=True, feature_type=SimulationDirect)
sim_feat = features[0]
print(sim_feat)
# -

# +
sim_feat.compute_CPU()
# -

# Preview simulation result (only windows)

if os.name == "nt":
    from ansys.speos.core.workflow.open_result import open_result_image

    open_result_image(
        simulation_feature=sim_feat,
        result_name="ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp",
    )
