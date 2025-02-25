# # How to create a project

# This tutorial demonstrates how to create a project.

# ## What is a project?

# A project is a speos simulation container that includes parts, material properties, sensor, sources and simulations.

# In this tutorial you will learn how to create a project from scratch or from a pre-defined .speos file.

# +
import os
from pathlib import Path

from ansys.speos.core import Project, Speos
from ansys.speos.core.sensor import SensorIrradiance
from ansys.speos.core.simulation import SimulationDirect
from ansys.speos.core.source import SourceSurface

# If using docker container
tests_data_path = Path("/app") / "assets"
# If using local server
# tests_data_path = os.path.join(os.path.abspath(""), os.path.pardir, os.path.pardir, "tests", "assets")
# -

# ## Create connection with speos rpc server

# +
speos = Speos(host="localhost", port=50098)
# -

# ## New empty project

# An empty project can be created by only passing speos rpc server to the Project class.

# +
p = Project(speos=speos)
print(p)
# -

# create feature - e.g. source

# +
source1 = p.create_source(name="Source.1", feature_type=SourceSurface)
source1.commit()
# -

# create feature - e.g. sensor

# +
sensor1 = p.create_sensor(name="Sensor.1")
sensor1.commit()
# -

# create feature - e.g. optical property

# +
opt_prop1 = p.create_optical_property(name="Material.1")
opt_prop1.commit()
# -

# ## Read Project

# User can read the content of a project via simplily printing the project

# +
print(p)
# -

# Or, user can use the find_key method to read a specific feature:

# +
for it in p.find_key(key="monochromatic"):
    print(it)
# -

# ## Find a feature inside a project

# ### Use find method with an exact name

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

# Here a wrong type is given: no source is called Sensor.1 in the project

# +
features = p.find(name="Sensor.1", feature_type=SourceSurface)
print(features)
# -

# +
features = p.find(name="Sensor.1", feature_type=SensorIrradiance)
print(features[0])
# -

# ### Use find method with approximation name with regex

# find a feature with name starting with Mat

# +
features = p.find(name="Mat.*", name_regex=True)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)
# -

# find all features without defining any name

# +
features = p.find(name=".*", name_regex=True)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)
# -

# ## Delete

# This erases the scene content in server database.

# This deletes also each feature of the project

# +
p.delete()
print(p)
# -

# As the features were deleted just above -> this returns an empty vector

# +
print(p.find(name="Sensor.1"))
# -

# ## Create project from pre-defined speos project

# Via passing the .speos/.sv5 file path to the Project class.

# +
p2 = Project(
    speos=speos,
    path=str(
        tests_data_path / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"
    ),
)
print(p2)
# -

# ## Preview the part information

# User can check the project part using preview method.

# +
p2.preview()
# -


# use find_key method to find specific information

# +
for it in p2.find_key(key="surface"):
    print(it)
# -

# Use find method to retrieve feature:

# e.g. surface source

# +
features = p2.find(name=".*", name_regex=True, feature_type=SourceSurface)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)
src = features[1]
# -

# modify the surface source, e.g. surface source wavelength:

# +
src.set_spectrum().set_monochromatic(wavelength=550)
src.commit()
# -


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

# +
if os.name == "nt":
    from ansys.speos.core.workflow.open_result import open_result_image

    open_result_image(
        simulation_feature=sim_feat, result_name="ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp"
    )
# -
