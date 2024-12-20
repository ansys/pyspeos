# # How to create a source.

# This tutorial demonstrates how to create a source in script layer.
# There are different type of sources available: luminaire source, surface source, ray file source.

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

# ## New Project

# The only way to create a source, is to create it from a project.

# +
p = script.Project(speos=speos)
print(p)
# -

# ## Create
# Create locally
# The mention "local: " is added when printing the source.

# +
intensity_file_path = os.path.join(tests_data_path, "IES_C_DETECTOR.ies")

source1 = p.create_source(name="Luminaire.1", feature_type=script.source.Luminaire)  # type luminaire
source1.set_intensity_file_uri(uri=intensity_file_path)
print(source1)
# -

# Push it to the server.
# Now that it is committed to the server, the mention "local: " is no more present when printing the source.

# +
source1.commit()
print(source1)
# -

# Another example by setting several characteristics

# +
intensity_file_path = os.path.join(tests_data_path, "IES_C_DETECTOR.ies")

source2 = p.create_source(name="Luminaire.2", feature_type=script.source.Luminaire)
source2.set_intensity_file_uri(uri=intensity_file_path)
source2.set_flux_radiant()  # select flux radiant with default value
# choose the source location [Origin, Xvector, Yvector, Zvector]
source2.set_axis_system(axis_system=[20, 50, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
source2.set_spectrum().set_blackbody()  # choose blacbody with default value for the source spectrum
source2.commit()  # Push to the server
print(source2)
# -

# ### Default values
# Some default values are available when applicable in every methods and class.

# ## Read
# ### Source Instance
# A mention "local: " is added if it is not yet committed to the server

# +
print(source1)
# -

# ### Project

# +
print(p)
# -

# ## Update
# Tipp: if you are manipulating a source already committed, don't forget to commit your changes.
# If you don't, you will still only watch what is committed on the server.

# +
source1.set_flux_radiant(value=1.2)  # modify radiant flux value
source1.set_axis_system(axis_system=[17, 10, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])  # modify axis system
source1.set_spectrum().set_halogen()  # modify spectrum by choosing halogen
source1.commit()  # Push changes to the server
print(source1)
# -

# ## Reset
# Possibility to reset local values from the one available in the server.

# +
source1.set_flux_luminous()  # modify to luminous flux BUT no commit
source1.reset()  # reset -> this will apply the server value to the local value (then local value will be back to halogen)
source1.delete()  # delete (to display the local value with the below print)
print(source1)
# -

# ## Delete
# Once the data is deleted from the server, you can still work with local data and maybe commit later.

# +
source2.delete()
print(source2)
# -

# +
source1.delete()
# -

# ## More content
# ### ray-file source

# +
ray_file_path = os.path.join(tests_data_path, "Rays.ray")

source3 = p.create_source(name="Ray-file.1", feature_type=script.source.RayFile)  # type ray file
source3.set_ray_file_uri(uri=ray_file_path)
source3.commit()
print(source3)
# -

# +
source3.set_flux_luminous()
source3.commit()
print(source3)
# -

# +
source3.delete()
# -

# ### surface source

# +
source4 = p.create_source(name="Surface.1", feature_type=script.source.Surface)
source4.set_exitance_constant(
    geometries=[(script.GeoRef.from_native_link("TheBodyB/TheFaceF"), False), (script.GeoRef.from_native_link("TheBodyB/TheFaceG"), True)]
)
source4.commit()
print(source4)
# -

# +
source4.set_flux_luminous_intensity()
source4.set_intensity().set_gaussian().set_axis_system(axis_system=[10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1])
source4.commit()
print(source4)
# -

# +
source4.delete()
print(source4)
# -

# When creating sources, this creates some intermediate objects (spectrums, intensity templates).
# Deleting a source does not delete in cascade those objects because they could be used by some other entities from core layer.
# Then at the end of the example, we just clean all databases

# +
for item in speos.client.intensity_templates().list() + speos.client.spectrums().list():
    item.delete()
