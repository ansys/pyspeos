# # How to create an optical property

# This tutorial demonstrates how to create an optical property.

# ## What is an optical property?

# An optical property (also named material), gathers two notions:
# the surface optical property (SOP) and the volume optical property (VOP).

# The property is then applied to a geometry (like bodies, faces).
#
# ## Prerequisites
#
# ### Perform imports

# +
from pathlib import Path

from ansys.speos.core import Project, Speos, launcher
from ansys.speos.core.kernel.client import (
    default_docker_channel,
)

# -

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.

# ### Define helper functions


def create_helper_geometries(project: Project):
    """Create bodies and faces."""

    def create_face(body):
        face = (
            body.create_face(name="TheFaceF")
            .set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0])
            .set_facets([0, 1, 2])
            .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
            .commit()
        )
        return face

    data = {"bodies": [], "faces": []}
    root_part = project.create_root_part().commit()
    data["bodies"].append(root_part.create_body(name="TheBodyB").commit())
    data["bodies"].append(root_part.create_body(name="TheBodyC").commit())
    data["bodies"].append(root_part.create_body(name="TheBodyD").commit())
    data["bodies"].append(root_part.create_body(name="TheBodyE").commit())
    for b in data["bodies"]:
        data["faces"].append(create_face(b))
    return data


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
# client are the same machine. The launch_local_speos_rpc_method can
# be used to start a local instance of the service.

if USE_DOCKER:
    speos = Speos(channel=default_docker_channel())
else:
    speos = launcher.launch_local_speos_rpc_server(port=GRPC_PORT)

# ### Create a new project
#
# The only way to create an optical property using the core layer, is to create it from a project.
# The ``Project`` class is instantiated by passing a ``Speos`` instance

p = Project(speos=speos)
print(p)
data = create_helper_geometries(p)
bodies = data["bodies"]
faces = data["faces"]

# ## Create VOP (volume optical property)
#
# Create locally.
# The mention "local: " is added when printing the optical property.

op1 = p.create_optical_property(name="Material.1")
op1.set_surface_mirror(reflectance=80)  # SOP : mirror
op1.set_volume_opaque()  # VOP : opaque
# This optical property will be applied to two bodies named : "TheBodyB" and "TheBodyC".
op1.set_geometries(
    geometries=[
        bodies[0],
        bodies[1],
    ]
)
print(op1)


# ### Push it to the server.
#
# Now that it is committed to the server,
# the mention "local: " is no more present when printing the optical property.

op1.commit()
print(op1)

# ## Another example.
#
# Setting several more characteristics.

op2 = p.create_optical_property(name="Material.2")
op2.set_surface_opticalpolished()  # SOP : optical polished
op2.set_volume_library(
    path=str(assets_data_path / "AIR.material")
)  # VOP : selected library via a file .material
# This optical property will be applied to two bodies named : "TheBodyD" and "TheBodyE".
op2.set_geometries(
    geometries=[
        bodies[2],
        bodies[3],
    ]
)
op2.commit()
print(op2)


# ## Create FOP (face optical property)
#
# Sometimes it is needed to create property but only for surface.
#
# In this case, no call for set_volume_xxx function is needed, and we will select a face for the
# geometries.

op3 = p.create_optical_property(name="Material.FOP")
op3.set_surface_mirror(reflectance=90)  # SOP : mirror
# This optical property will be applied a face from TheBodyD named : "TheFaceF".
op3.set_geometries(geometries=[faces[2]])
op3.commit()
print(op3)

# ### Default values
#
# Some default values are available when applicable in every methods and class.

op4 = p.create_optical_property(name="Material.3").commit()
print(op4)

# ## Read
# ### Material Instance Information
#
# A mention "local: " is added if it is not yet committed to the server.

print(op1)

# The get methods allows you to get some properties of your feature

# +
print("op1 name: {}".format(op1.get(key="name")))
print("geometries linked to op1: {}".format(op1.get(key="geo_paths")))
print("op1 surface optical properties info: {}".format(op1.get(key="sops")))
print("op1 volume optical property info: {}".format(op1.get(key="vop")))
# user can use get with vop type as key word to check volume property type
print(
    "op1 {} opaque type volume optical property".format(
        "is" if op1.get(key="opaque") is not None else "is not"
    )
)

print(op2)
print("op2 name: {}".format(op2.get(key="name")))
print(
    "op2 {} optical polished type surface property".format(
        ("is" if "optical_polished" in op2.get(key="sops")[0] else "is not")
    )
)
# an alternative way to check the type of optical property
print(
    "op2 {} library type volume optical property".format(
        "is" if "library" in op2.get(key="vop") is not None else "is not"
    )
)

print(op3)
print("op3 name: {}".format(op3.get(key="name")))
print("op3 has reflectance value of {}".format(op3.get(key="sops")[0]["mirror"]["reflectance"]))
# -

# ### Project Information
# Committed feature information will appear inside a project information.

print(p)

# ## Update
#
# Tipp: if you are manipulating an optical property already committed, don't forget to commit your
# changes.
#
# If you don't, you will still only watch what is committed on the server.


print("op1 surface type before update: {}".format(op1.get(key="sops")[0]))
op1.set_volume_optic().set_surface_opticalpolished().commit()
print(op1)
print("op1 surface type after update: {}".format(op1.get(key="sops")[0]))


# ## Reset
#
# Possibility to reset local values from the one available in the server.

op1.set_surface_mirror()  # set surface as a mirror but no commit
op1.reset()  # reset -> this will apply the server value to the local value
op1.delete()  # delete (to display the local value with the below print)
print(op1)


# ## Delete
#
# Once the data is deleted from the server, you can still work with local data and maybe commit
# later.


op2.delete()
print(op2)

# Clean up all Optical properties

op1.delete()
op3.delete()
op4.delete()

speos.close()
