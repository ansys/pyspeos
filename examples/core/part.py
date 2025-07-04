# # How to create a part
#
# This tutorial demonstrates how to create a part.
#
# ## What is a part?
#
# A part is either a volume or a face type bodies that are defined by a number of mesh triangles.
#
# Then a material optical property can be then applied to a part (like bodies, faces).

# ## Prerequisites
#
# ### Perform imports

# +
from pathlib import Path

from ansys.speos.core import Body, Face, Part, Project, Speos
from ansys.speos.core.launcher import launch_local_speos_rpc_server

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
# > **Note:** Make sure you have downloaded the simulation assets
# > and set ``assets_data_path`` to point to the assets folder.

if USE_DOCKER:  # Running on the remote server.
    assets_data_path = Path("/app") / "assets"
else:
    assets_data_path = Path("/path/to/your/download/assets/directory")


# ### Start/Connect to Speos RPC Server
# This Python client connects to a server where the Speos engine
# is running as a service. In this example, the server and
# client are the same machine. The launch_local_speos_rpc_method can
# be used to start a local instance of the service.

if USE_DOCKER:
    speos = Speos(host=HOSTNAME, port=GRPC_PORT)
else:
    speos = launch_local_speos_rpc_server(port=GRPC_PORT)


# ## New Project
#
# The only way to create parts, bodies and faces is from a project.

p = Project(speos=speos)
print(p)

# ## Create
#
# Before creating a body, a Root part needs to be created and committed.

root_part = p.create_root_part().commit()
print(root_part)

# ### Create bodies in root part.
# A body can either a volume or face type. Both use the method named "create_body".

body_b1 = root_part.create_body(name="TheBodyB1").commit()
body_b2 = root_part.create_body(name="TheBodyB2").commit()
print(root_part)

# ### Create faces inside a body.
# A body can have one (example, surface/open-volume type of body) or multiple faces
# (close-volume type of body).
#
# Each face is then defined by a number of triangles/facets.
#
# Each triangle/facet is defined by vertices and vertice normals.

face_b1_f1 = (
    body_b1.create_face(name="TheFaceF1")
    .set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0])
    .set_facets([0, 1, 2])
    .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    .commit()
)
print(root_part)

# ### Create bodies in sub part.
#
# Part can also be created under a sub-part.
#
# The location sub-part can be defined using set_axis_system method.

sub_part1 = (
    root_part.create_sub_part(name="TheSubPartSP1")
    .set_axis_system(axis_system=[5, 5, 5, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    .commit()
)
print(root_part)

# ### Create body and faces in sub part body

body_sp1_b1 = sub_part1.create_body(name="TheBodySP1_B1").commit()
print(root_part)
face_sp1_b1_f1 = (
    body_sp1_b1.create_face(name="TheFaceSP1_B1_F1")
    .set_vertices([0, 1, 0, 0, 2, 0, 1, 2, 0])
    .set_facets([0, 1, 2])
    .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    .commit()
)
print(root_part)

# ### Create sub parts in sub part

sub_part11 = (
    sub_part1.create_sub_part(name="TheSubPartSP11")
    .set_axis_system([1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    .commit()
)
print(root_part)

# ## Read
#
# ### Find with exact name
#
# Find the root part

features = p.find(name="", feature_type=Part)
print(features[0])

# Find a specific body in root part

features = p.find(name="TheBodyB1", feature_type=Body)
print(features[0])

# Find a specific face of a body in root part

features = p.find(name="TheBodyB1/TheFaceF1", feature_type=Face)
print(features[0])

# Find a sub part

features = p.find(name="TheSubPartSP1", feature_type=Part.SubPart)
print(features[0])


# Find a specific body in sub part

features = p.find(name="TheSubPartSP1/TheBodySP1_B1", feature_type=Body)
print(features[0])

# Find a specific face of a body in sub part

features = p.find(name="TheSubPartSP1/TheBodySP1_B1/TheFaceSP1_B1_F1", feature_type=Face)
print(features[0])

# ### Find with approximation name

# Find all bodies in root part

features = p.find(name=".*", name_regex=True, feature_type=Body)
for feat in features:
    print(feat._name)

# Find all faces inside body called "TheBodyB1"

features = p.find(name="TheBodyB1/.*", name_regex=True, feature_type=Face)
for feat in features:
    print(feat._name)


# If you want to retrieve several kind of geometry features at a certain level, give
# feature_type=Part

# All the geometry features at root part level:

features = p.find(name=".*", name_regex=True, feature_type=Part)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)

# All the geometry features at second level: e.g.:
# - TheBodyB1's all faces
# - TheSubPartSP1's all bodies
# - TheSubPartSP1's all sub part

features = p.find(name=".*/.*", name_regex=True, feature_type=Part)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)

# All the geometry features at the third level:
# e.g. TheSubPartSP1's all bodies' faces

features = p.find(name=".*/.*/.*", name_regex=True, feature_type=Part)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)


# ## Delete

root_part.delete()
print(root_part)

speos.close()
