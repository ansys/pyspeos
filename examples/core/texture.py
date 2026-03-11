# # How to create an texture property
import os

# This tutorial demonstrates how to create an texture property.
# ## What is an textur property?
# An texture property (also named material), gathers 3 notions:
# the surface optical property (SOP), the texture and the volume optical property (VOP).
# The property is then applied to a geometry (like bodies, faces).
#
# ## Prerequisites
#
# ### Perform imports
# +
from pathlib import Path

import matplotlib.pyplot as plt

from ansys.speos.core import Face, Project, Speos, launcher
from ansys.speos.core.generic.parameters import MappingOperator, MeshData, TextureNormalizationTypes
from ansys.speos.core.kernel.client import (
    default_docker_channel,
)
from ansys.speos.core.opt_prop import MappingByData, TextureLayer
from ansys.speos.core.sensor import SensorRadiance
from ansys.speos.core.simulation import SimulationInverse
from ansys.speos.core.source import SourceAmbientEnvironment

# -

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.

# ### Define helper functions


def create_helper_geometries(project: Project):
    """Create bodies and faces."""

    def create_rect_face(my_body, name, pos, x, y) -> Face:
        face = my_body.create_face(name=name)
        face.set_vertices(
            [
                pos[0],
                pos[1],
                pos[2],
                pos[0],
                pos[1] + y,
                pos[2],
                pos[0] + x,
                pos[1],
                pos[2],
                pos[0] + x,
                pos[1] + y,
                pos[2],
            ]
        )
        face.set_facets([0, 1, 2, 1, 2, 3])
        face.set_normals([0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0])
        return face

    data = {"bodies": [], "faces": []}
    root_part = project.create_root_part().commit()
    data = {"bodies": [], "faces": [], "rp": root_part}
    data["bodies"].append(root_part.create_body(name="TheBody0").commit())
    data["bodies"].append(root_part.create_body(name="TheBody1").commit())
    data["bodies"].append(root_part.create_body(name="TheBody2").commit())
    data["bodies"].append(root_part.create_body(name="TheBody3").commit())
    data["bodies"].append(root_part.create_body(name="TheBody4").commit())
    data["bodies"].append(root_part.create_body(name="TheBody5").commit())
    data["faces"].append(create_rect_face(data["bodies"][0], "face0_0", [0, 0, 0], 5, 5))
    data["faces"].append(create_rect_face(data["bodies"][1], "Face1_0", [6, 0, 0], 5, 10))
    data["faces"].append(create_rect_face(data["bodies"][2], "Face2_0", [12, 0, 0], 10, 5))
    data["faces"].append(create_rect_face(data["bodies"][3], "Face3_0", [0, -6, 0], 5, 5))
    data["faces"].append(create_rect_face(data["bodies"][4], "Face4_0", [6, -6, 0], 5, 5))
    data["faces"].append(create_rect_face(data["bodies"][5], "Face5_0", [12, -6, 0], 5, 5))
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


# ### Apply vertices data for all faces except the first
#
# we create image locations for each vertices and provide these to each face to position the texture
# on the Geometry. we give for each vertices the u,v location of the image

face1_0 = faces[1]
face1_0.vertices_data = [
    MeshData(name="uv_0", data=[0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0])  # full picture
]

face2_0 = faces[2]
face2_0.vertices_data = [
    MeshData(name="uv_0", data=[0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0])  # full picture
]

# Here we play with the u: from 0.0 to 0.5

face3_0 = faces[3]
face3_0.vertices_data = [
    MeshData(name="uv_0", data=[0.0, 1.0, 0.0, 0.0, 0.5, 1.0, 0.5, 0.0])
]  # first half of the picture

# Here we play with the u: from 0.5 to 1.0

face4_0 = faces[4]
face4_0.vertices_data = [
    MeshData(name="uv_0", data=[0.5, 1.0, 0.5, 0.0, 1.0, 1.0, 1.0, 0.0])
]  # second half of the picture

# Here we play with the u: from 4/6 to 5/6

face5_0 = faces[5]
face5_0.vertices_data = [
    MeshData(name="uv_0", data=[4 / 6, 1.0, 4 / 6, 0.0, 5 / 6, 1.0, 5 / 6, 0.0])
]

# As the used image has strips there is no interest in playing with v
# . ----> u
# |
# | picture
# v
data["rp"].commit()

# ### Create Ambient source

src = p.create_source(name="Ambient", feature_type=SourceAmbientEnvironment)
src.luminance = 1000
src.image_file_uri = Path(assets_data_path) / "uffizi_cross.hdr"
src.set_predefined_color_space().set_color_space_srgb()
src.zenith_direction = [0.0, 0.0, 1.0]
src.north_direction = [1.0, 0.0, 0.0]
src.commit()

# ### Create Radiance Sensor

ssr = p.create_sensor(name="Radiance", feature_type=SensorRadiance)
ssr.axis_system = [11, 0, 10, 1, 0, 0, 0, 1, 0, 0, 0, 1]
ssr.integration_angle = 5
ssr.dimensions.x_start = -8
ssr.dimensions.x_end = 8
ssr.dimensions.x_sampling = 200
ssr.dimensions.y_start = -8
ssr.dimensions.y_end = 8
ssr.dimensions.y_sampling = 200
ssr.focal = 10
wv = ssr.set_type_spectral().set_wavelengths_range()
wv.start = 400
wv.end = 800
wv.sampling = 13
ssr.commit()


# ### Create Texture Property by data

opt_prop = p.create_optical_property(name="OptProp.1")
opt_prop.set_volume_none()
opt_prop.geometries = [
    face1_0.geo_path,
    face2_0.geo_path,
    face3_0.geo_path,
    face4_0.geo_path,
    face5_0.geo_path,
]

layer_1 = TextureLayer(opt_prop, "Layer.1")
layer_1.set_surface_library().sop_library = Path(assets_data_path) / "L100 2.simplescattering"
layer_1.image_texture_file_uri = Path(assets_data_path) / "textureColors.jpg"
layer_1.image_property = MappingByData(vertices_data_index=0, repeat_u=False, repeat_v=False)
layer_1.commit()

opt_prop.texture = [layer_1]
opt_prop.commit()

# ### Create Texture Property by mapping operator
# as alternative to mapping by data you can create some simple Mappings using planar,
# cubic, spherical or cylindrical mapping operator
face0_0 = faces[0]
opt_prop1 = p.create_optical_property(name="OptProp.2")
opt_prop1.set_volume_none()
opt_prop1.geometries = [face0_0.geo_path]

layer_2 = TextureLayer(opt_prop, "Layer.2")
layer_2.set_surface_library().sop_library = Path(assets_data_path) / "L100 2.simplescattering"
layer_2.image_texture_file_uri = Path(assets_data_path) / "textureColors.jpg"
layer_2.image_property = MappingOperator(
    mapping_type="planar",
    u_length=2.5,
    v_length=2.5,
    repeat_u=True,
    repeat_v=True,
    axis_system=[2.5, 2.5, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0],
)
layer_2.commit()

opt_prop1.texture = [layer_2]
opt_prop1.commit()

# ### Create Inverse Simulation with define Texture normalization

sim = p.create_simulation(name="Inverse", feature_type=SimulationInverse)
sim.set_sensor_paths(sensor_paths=["Radiance"])
sim.set_source_paths(source_paths=["Ambient"])
sim.texture_normalization = TextureNormalizationTypes.none
sim.commit()

# ### Run Simulation and open result
results = sim.compute_CPU()

if os.name == "nt":
    from ansys.speos.core.workflow.open_result import open_result_image

    open_result_image(simulation_feature=sim, result_name="Radiance.xmp")
else:
    # plot expected results from image export
    plt.imshow(Path(assets_data_path) / "texture_sim.png")
