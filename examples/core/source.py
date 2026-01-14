# # How to create a source

# This tutorial demonstrates how to create a source.
#
# There are different type of sources available: luminaire source, surface source, ray file source.
#
# ## Prerequisites
#
# ### Perform imports

# +
from pathlib import Path

from ansys.speos.core import GeoRef, Project, Speos, launcher
from ansys.speos.core.kernel.client import (
    default_docker_channel,
)
from ansys.speos.core.source import (
    SourceAmbientEnvironment,
    SourceAmbientNaturalLight,
    SourceLuminaire,
    SourceRayFile,
    SourceSurface,
)

# -

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.
IES = "IES_C_DETECTOR.ies"

# ### Define helper functions


def create_helper_geometries(project: Project):
    """Create bodies and faces."""

    def create_face(body):
        (
            body.create_face(name="TheFaceF")
            .set_vertices([0, 0, 0, 1, 0, 0, 0, 1, 0])
            .set_facets([0, 1, 2])
            .set_normals([0, 0, 1, 0, 0, 1, 0, 0, 1])
            .commit()
        )

    root_part = project.create_root_part().commit()
    body_b1 = root_part.create_body(name="TheBodyB").commit()
    body_b2 = root_part.create_body(name="TheBodyC").commit()
    body_b3 = root_part.create_body(name="TheBodyD").commit()
    body_b4 = root_part.create_body(name="TheBodyE").commit()
    for b in [body_b1, body_b2, body_b3, body_b4]:
        create_face(b)


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
# The only way to create a source using the core layer, is to create it from a project.
# The ``Project`` class is instantiated by passing a ``Speos`` instance

p = Project(speos=speos)
print(p)


# ### Source Creation
#
# **Create locally:**
# The mention "local: " is added when printing the source data and information is not yet
# pushed to the RPC server

intensity_file_path = str(assets_data_path / IES)
source1 = p.create_source(name="Luminaire.1", feature_type=SourceLuminaire)  # type luminaire
source1.set_intensity_file_uri(uri=intensity_file_path)
print(source1)

# **Push it to the server.**
#
# After it is committed to the server, the mention "local: " is no more present when printing the
# source.

source1.commit()
print(source1)

# **Changing additional Source Properties**
#
# Setting several more characteristics.


intensity_file_path = str(assets_data_path / IES)
source2 = p.create_source(name="Luminaire.2", feature_type=SourceLuminaire)
source2.set_intensity_file_uri(uri=intensity_file_path)
source2.set_flux_radiant()  # select flux radiant with default value
# choose the source location [Origin, Xvector, Yvector, Zvector]
source2.set_axis_system(axis_system=[20, 50, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])
source2.set_spectrum().set_blackbody()  # choose blackbody with default value for the spectrum
source2.commit()  # Push to the server
print(source2)

# **Source Instance**
#
# As mention "local: " is added if it is not yet committed to the server.

print(source1)

# **Project:**
#
# Committed feature will appear inside the project information.

print(p)

# **Update:**
#
# > **Note:** If you are manipulating a source already committed, don't forget to commit your
# > changes.
# > If you don't, you will still only watch what is committed on the server.

source1.set_flux_radiant(value=1.2)  # modify radiant flux value
source1.set_axis_system(axis_system=[17, 10, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1])  # modify axis system
source1.set_spectrum().set_halogen()  # modify spectrum by choosing halogen
source1.commit()  # Push changes to the server
print(source1)

# **Reset**
#
# Possibility to reset local values from the one available in the server.

source1.set_flux_luminous()  # modify to luminous flux BUT no commit
source1.reset()
# reset -> this will apply the server value to the local value the local value will be back to
# halogen
source1.delete()  # delete (to display the local value with the below print)
print(source1)


# **Delete**
#
# Once the data is deleted from the server, you can still work with local data and maybe commit
# later.

# +
source2.delete()
print(source2)
source1.delete()
print(p)
# -

# ## Other Sources Examples

# ### Ray-file source

# +
ray_file_path = str(assets_data_path / "Rays.ray")

source3 = p.create_source(name="Ray-file.1", feature_type=SourceRayFile)  # type ray file
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

# ### Surface source

# +
create_helper_geometries(p)
source4 = p.create_source(name="Surface.1", feature_type=SourceSurface)
source4.set_exitance_constant(
    geometries=[
        (GeoRef.from_native_link("TheBodyB/TheFaceF"), False),
        (GeoRef.from_native_link("TheBodyC/TheFaceF"), True),
    ]
)
source4.commit()
print(source4)
# -

# +
source4.set_flux_luminous_intensity()
source4.set_intensity().set_gaussian().set_axis_system(
    axis_system=[10, 50, 20, 1, 0, 0, 0, 1, 0, 0, 0, 1]
)
source4.commit()
print(source4)
# -

# +
source4.delete()
print(source4)
# -

# ### Ambient natural light source

# +
source5 = p.create_source(name="NaturalLight.1", feature_type=SourceAmbientNaturalLight)
source5.turbidity = 4
source5.with_sky = True
print(source5.zenith_direction)  # default zenith direction
print(source5.north_direction)  # default north direction
source5.reverse_north_direction = True
print(source5)

source5.commit()
print(source5)
# -

# +
source5.set_sun_automatic().year = 2026
source5.set_sun_automatic().month = 12
source5.set_sun_automatic().day = 31
source5.set_sun_automatic().hour = 12
source5.set_sun_automatic().minute = 23
source5.set_sun_automatic().longitude = 10
source5.set_sun_automatic().latitude = 45
source5.set_sun_automatic().time_zone = "CST"
source5.commit()
print(source5)
# -

# +
source5.delete()
# -

# ### Ambient environment light source

# +
source6 = p.create_source(name="Environment.1", feature_type=SourceAmbientEnvironment)
print(source6.zenith_direction)  # default zenith direction
print(source6.north_direction)  # default north direction
source6.reverse_north_direction = True
print(source6.luminance)  # default luminance value
source6.set_predefined_color_space().set_color_space_adobergb()
source6.set_predefined_color_space().set_color_space_srgb()
print(source6.color_space)
source6.set_userdefined_color_space().set_white_point_type_d50()
print(source6.source6.set_userdefined_color_space().white_point_type)
print(source6)

source5.commit()
print(source5)
# -

# +
source5.set_sun_automatic().year = 2026
source5.set_sun_automatic().month = 12
source5.set_sun_automatic().day = 31
source5.set_sun_automatic().hour = 12
source5.set_sun_automatic().minute = 23
source5.set_sun_automatic().longitude = 10
source5.set_sun_automatic().latitude = 45
source5.set_sun_automatic().time_zone = "CST"
source5.commit()
print(source5)
# -

# +
source5.delete()
# -

# When creating sources, this creates some intermediate objects (spectrums, intensity templates).
#
# Deleting a source does not delete in cascade those objects
# because they could be used by some other entities from core layer.
#
# Then at the end of the example, we just clean all databases

# +
for item in speos.client.intensity_templates().list() + speos.client.spectrums().list():
    item.delete()

speos.close()
