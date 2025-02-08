# # How to use an ObjectLink

# This tutorial demonstrates how to use speos objects in layer core.

# ## What is an ObjectLink?

# The ObjectLink is an object that is created from a protobuf message and then stored in the server database.

# ## Which speos objects are used via ObjectLink?

# Almost all speos objects are used via ObjectLink: like sources, sensors, simulations and more.
# For this tutorial we will use as example the surface optical property (sop)

# +
from ansys.speos.core.kernel.sop_template import SOPTemplate
from ansys.speos.core.speos import Speos

# -

# Create connection with speos rpc server

# +
speos = Speos(host="localhost", port=50098)
# -

# ## Create an ObjectLink

# Retrieve the access to the database.

# +
sop_t_db = speos.client.sop_templates()
# -

# Create the protobuf message.

# +
sop_t = SOPTemplate()
sop_t.name = "Mirror_90"
sop_t.mirror.reflectance = 90.0
# -

# Create the ObjectLink (here a SOPTemplateLink).

# +
mirror_90_link = sop_t_db.create(message=sop_t)
print(mirror_90_link)
# -

# Create another ObjectLink from another protobuf message.

# +
sop_t = SOPTemplate()
sop_t.name = "Mirror_100"
sop_t.mirror.reflectance = 100.0

mirror_100_link = sop_t_db.create(message=sop_t)
# -

# ## Modify an ObjectLink

# Retrieve the protobuf message corresponding to the ObjectLink.

# +
mirror_data = mirror_90_link.get()
# -

# Modify data locally

# +
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
