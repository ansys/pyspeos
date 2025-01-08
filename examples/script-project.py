# # How to create a project

# This tutorial demonstrates how to create a project in script layer.

## What is a project?

# A project is a speos simulation container that includes parts, material properties, sensor, sources and simulations.
# In this tutorial you will learn how to create a project from scratch or from a pre-defined .speos file.

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

# ## New empty Project
# An empty project can be created by only passing speos rpc server to the script.Project class.

# +
p = script.Project(speos=speos)
print(p)
# -

# create feature - e.g. source
# +
source1 = p.create_source(name="Source.1", feature_type=script.source.Surface)
source1.commit()
# -
# create feature - e.g. sensor
# +
sensor1 = p.create_sensor(name="Sensor.1")
sensor1.commit()
# -

# create feature - e.g. optical property
# etc.
# +
opt_prop1 = p.create_optical_property(name="Material.1")
opt_prop1.commit()
# -

# ## Read Project
# User can read the content of a project via simplily printing the project
# +
print(p)
# -

# Or, user can use the find_key method to read a specific feature, e.g.:
# +
for it in p.find_key(key="monochromatic"):
    print(it)
# -

# ## Find a feature inside a project
# Use find method with an exact name
# If no feature is found, an empty list is returned.
# +
features = p.find(name="UnexistingName")
print(features)
# -

# +
features = p.find(name="Sensor.1")
print(features[0])
# -

# Use find method with feature type
# Here wrong type is given: no source is called Sensor.1 in the project
# +
features = p.find(name="Sensor.1", feature_type=script.source.Surface)
print(features)
# -

# +
features = p.find(name="Sensor.1", feature_type=script.sensor.Irradiance)
print(features[0])
# -

# Use find method with approximation name with regex
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
# Via passing the .speos/.sv5 file path to the script.Project class.
# +
p2 = script.Project(speos=speos, path=os.path.join(tests_data_path, "LG_50M_Colorimetric_short.sv5", "LG_50M_Colorimetric_short.sv5"))
print(p2)
# -

# User can preview the part information
# +
p2.preview()
# -

# use find_key method to find specific information
for it in p2.find_key(key="surface"):
    print(it)

# Use find method to retrieve feature:
# e.g. surface source
# +
features = p2.find(name=".*", name_regex=True, feature_type=script.source.Surface)
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
features = p2.find(name=".*", name_regex=True, feature_type=script.simulation.Direct)
sim_feat = features[0]
print(sim_feat)
# -

# +
sim_feat.compute_CPU()
# -

# review simulation result
# +
from ansys.speos.workflow.open_result import open_result_image

open_result_image(simulation_feature=sim_feat, result_name="ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp")
# -
