# # How to create a part

# This tutorial demonstrates how to create a part.

# ## What is a part?

# A part is either a volume or a face type bodies that are defined by a number of mesh triangles.

# Then a material optical property can be then applied to a part (like bodies, faces).

# +
import os

from ansys.speos.core import Body, Face, Part, Project, Speos

# If using docker container
tests_data_path = os.path.join("/app", "assets")
# If using local server
# tests_data_path = os.path.join(os.path.abspath(""), os.path.pardir, os.path.pardir, "tests", "assets")
# -

# ## Create connection with speos rpc server

# +
speos = Speos(host="localhost", port=50098)
# -

# ## New Project

# The only way to create an optical property, is to create it from a project.

# +
p = Project(speos=speos)
print(p)
# -

# ## Create

# Before creating a body, a Root part needs to be created and committed.

# +
root_part = p.create_root_part().commit()
print(root_part)
# -

# ### Create bodies in root part.
# A body can either a volume or face type. Both use the method named "create_body".

# +
body_b1 = root_part.create_body(name="TheBodyB1").commit()
body_b2 = root_part.create_body(name="TheBodyB2").commit()
print(root_part)
# -

# ### Create faces inside a body.
# A body can have one (example, surface/open-volume type of body) or multiple faces (close-volume type of body).

# Each face is then defined by a number of triangles/facets.

# Each triangle/facet is defined by vertices and vertice normals.

# +
face_b1_f1 = (
    body_b1.create_face(name="TheFaceF1")
    .set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0])
    .set_facets([0, 1, 2])
    .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
    .commit()
)
print(root_part)
# -

# ### Create bodies in sub part.

# Part can also be created under a sub-part.

# The location sub-part can be defined using set_axis_system method.

# +
sub_part1 = (
    root_part.create_sub_part(name="TheSubPartSP1")
    .set_axis_system(axis_system=[5, 5, 5, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    .commit()
)
print(root_part)
# -

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
# -

# ### Create sub parts in sub part

# +
sub_part11 = (
    sub_part1.create_sub_part(name="TheSubPartSP11")
    .set_axis_system([1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1])
    .commit()
)
print(root_part)
# -

# ## Read

# ### Find with exact name

# Find the root part

# +
features = p.find(name="", feature_type=Part)
print(features[0])
# -

# Find a specific body in root part

# +
features = p.find(name="TheBodyB1", feature_type=Body)
print(features[0])
# -

# Find a specific face of a body in root part

# +
features = p.find(name="TheBodyB1/TheFaceF1", feature_type=Face)
print(features[0])
# -

# Find a sub part

# +
features = p.find(name="TheSubPartSP1", feature_type=Part.SubPart)
print(features[0])
# -


# Find a specific body in sub part

# +
features = p.find(name="TheSubPartSP1/TheBodySP1_B1", feature_type=Body)
print(features[0])
# -

# Find a specific face of a body in sub part

# +
features = p.find(name="TheSubPartSP1/TheBodySP1_B1/TheFaceSP1_B1_F1", feature_type=Face)
print(features[0])
# -

# ### Find with approximation name

# Find all bodies in root part

# +
features = p.find(name=".*", name_regex=True, feature_type=Body)
for feat in features:
    print(feat._name)
# -

# Find all faces inside body called "TheBodyB1"

# +
features = p.find(name="TheBodyB1/.*", name_regex=True, feature_type=Face)
for feat in features:
    print(feat._name)
# -


# If you want to retrieve several kind of geometry features at a certain level, give feature_type=Part

# all the geometry features at root part level:

# +
features = p.find(name=".*", name_regex=True, feature_type=Part)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)
# -

# all the geometry features at second level: e.g.:
# - TheBodyB1's all faces
# - TheSubPartSP1's all bodies
# - TheSubPartSP1's all sub part


# +
features = p.find(name=".*/.*", name_regex=True, feature_type=Part)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)
# -

# all the geometry features at the third level:
# e.g. TheSubPartSP1's all bodies' faces
features = p.find(name=".*/.*/.*", name_regex=True, feature_type=Part)
for feat in features:
    print(str(type(feat)) + " : name=" + feat._name)
# -

# ## Delete

# +
root_part.delete()
print(root_part)
# -
