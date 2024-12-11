# # Object Link usage in PySpeos core layer

# This tutorial demonstrates how to use speos objects in layer core.

# ## What is an ObjectLink?

# The ObjectLink is an object that is created from a protobuf message and then stored in the server database.

# ## Which speos objects are used via ObjectLink?

# Almost all speos objects are used via ObjectLink: like sources, sensors, simulations and more.

# +
import ansys.speos.core as core

# -

# ## Create connection with speos rpc server

# +
speos = core.Speos(host="localhost", port=50098)
# -

# ## Create an ObjectLink

# +
sop_t_db = speos.client.sop_templates()
# -

# +
sop_t = core.SOPTemplate()
sop_t.name = "Mirror_90"
sop_t.mirror.reflectance = 90.0

mirror_90_link = sop_t_db.create(message=sop_t)
print(mirror_90_link)
# -

# +
sop_t = core.SOPTemplate()
sop_t.name = "Mirror_100"
sop_t.mirror.reflectance = 100.0

mirror_100_link = sop_t_db.create(message=sop_t)
# -

# ## Modify an ObjectLink

# Modify data locally

# +
mirror_data = mirror_90_link.get()
mirror_data.name = "Mirror_50"
mirror_data.mirror.reflectance = 50
# -

# Update on db

# +
mirror_90_link.set(data=mirror_data)
print(mirror_90_link)
# -

# ## Delete an ObjectLink

# This means deleting data in db

# +
mirror_100_link.delete()
mirror_90_link.delete()
sop_t_db.list()
# -
