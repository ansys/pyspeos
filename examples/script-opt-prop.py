# # How to create an optical property.

# This tutorial demonstrates how to create an optical property in script layer.

# ## What is an optical property?

# An optical property (also named material), gathers two notions: the surface optical property (SOP) and the volume optical property (VOP).
# The property is then applied to a geometry (like bodies, faces).

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

# The only way to create an optical property, is to create it from a project.

# +
p = script.Project(speos=speos)
print(p)
# -

# ## Create

# Create locally.
# The mention "local: " is added when printing the optical property.

# +
op1 = p.create_optical_property(name="Material.1")
op1.set_surface_mirror(reflectance=80)  # SOP : mirror
op1.set_volume_opaque()  # VOP : opaque
# This optical property will be applied to two bodies named : "TheBodyB" and "TheBodyC".
op1.set_geometries(geometries=[script.GeoRef.from_native_link(geopath="TheBodyB"), script.GeoRef.from_native_link(geopath="TheBodyC")])
print(op1)
# -

# Push it to the server.
# Now that it is committed to the server, the mention "local: " is no more present when printing the optical property.

# +
op1.commit()
print(op1)
# -

# Another example.

# +
op2 = p.create_optical_property(name="Material.2")
op2.set_surface_opticalpolished()  # SOP : optical polished
op2.set_volume_library(path=os.path.join(tests_data_path, "AIR.material"))  # VOP : selected library via a file .material
# This optical property will be applied to two bodies named : "TheBodyD" and "TheBodyE".
op2.set_geometries(geometries=[script.GeoRef.from_native_link(geopath="TheBodyD"), script.GeoRef.from_native_link(geopath="TheBodyE")])
op2.commit()
print(op2)
# -

# ### FOP (face optical property)

# Sometimes it is needed to create property but only for surface.
# In this case, no call for set_volume_xxx function is needed, and we will select a face for the geometries.

# +
op3 = p.create_optical_property(name="Material.FOP")
op3.set_surface_mirror(reflectance=90)  # SOP : mirror
# This optical property will be applied a face from TheBodyD named : "TheFaceF".
op3.set_geometries(geometries=[script.GeoRef.from_native_link(geopath="TheBodyD/TheFaceF")])
op3.commit()
print(op3)
# -

# ### Default values
# Some default values are available when applicable in every methods and class.

# +
op4 = p.create_optical_property(name="Material.3").commit()
print(op4)
# -

# ## Read
# ### Material Instance
# A mention "local: " is added if it is not yet committed to the server

# +
print(op1)
# -

# ### Project

# +
print(p)
# -

# ## Update
# Tipp: if you are manipulating an optical property already committed, don't forget to commit your changes.
# If you don't, you will still only watch what is committed on the server.

# +
op1.set_volume_optic().set_surface_opticalpolished().commit()
print(op1)
# -

# ## Reset
# Possibility to reset local values from the one available in the server.

# +
op1.set_surface_mirror()  # set surface as a mirror but no commit
op1.reset()  # reset -> this will apply the server value to the local value
op1.delete()  # delete (to display the local value with the below print)
print(op1)
# -

# ## Delete
# Once the data is deleted from the server, you can still work with local data and maybe commit later.

# +
op2.delete()
print(op2)
# -

# +
op1.delete()
op3.delete()
op4.delete()
# -
