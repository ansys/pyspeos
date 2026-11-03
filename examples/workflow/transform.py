# # Move and copy features with workflow transforms
#
# This tutorial demonstrates how to translate, rotate, and position bodies, parts,
# lightboxes, and sources using the PySpeos workflow helpers.
#
# Each helper modifies the input feature by default. Set ``copy=True`` to create a
# transformed duplicate while leaving the input unchanged. The helpers return the
# transformed feature and commit their changes to the server automatically.

# ## Prerequisites
#
# Use a running Speos RPC server with Speos 2026 R1 or later for this complete example,
# including lightbox transforms. Install PySpeos with the ``graphics`` extra to use
# the previews.
#
# ### Perform imports

# +
from pathlib import Path

from ansys.speos.core import Project, Speos, launcher
from ansys.speos.core.component import LightBoxFileInstance
from ansys.speos.core.kernel.client import default_docker_channel
from ansys.speos.core.source import SourceLuminaire
from ansys.speos.core.workflow import axis_to_axis_feature, move_feature, rotate_feature

# -

# ### Define constants
#
# Distances and positions are expressed in millimeters, and rotation angles in degrees.
# Direction vectors are normalized by the helpers, so their magnitude does not change
# the requested distance.

GRPC_PORT = 50055
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.

# ## Model setup
#
# ### Load assets
#
# The assets used in this example are available in ``tests/assets`` in the
# [PySpeos repository](https://github.com/ansys/pyspeos/).
#
# > **Note:** Download ``IES_C_DETECTOR.ies`` and the ``lightbox`` folder, including
# > its dependencies. Set ``assets_data_path`` to their location on the server.

if USE_DOCKER:  # Running on the remote server.
    assets_data_path = Path("/app") / "assets"
else:
    assets_data_path = Path(r"D:\path\to\your\download\assets\directory")

# ### Connect to the Speos RPC server
#
# Connect to the Docker server or launch a local server.

if USE_DOCKER:
    speos = Speos(channel=default_docker_channel(port=GRPC_PORT))
else:
    speos = launcher.launch_local_speos_rpc_server(port=GRPC_PORT)

# ### Create a project and geometry
#
# Create a triangular body directly under the root part.

# +
p = Project(speos=speos)
root_part = p.create_root_part().commit()

body = root_part.create_body(name="Triangle")
face = body.create_face(name="Triangle face")
face.vertices = [0, 0, 0, 20, 0, 0, 0, 20, 0]
face.facets = [0, 1, 2]
face.normals = [0, 0, 1, 0, 0, 1, 0, 0, 1]
body.commit()
# -

# Create another triangle inside a subpart. Transform a ``Part.SubPart`` to place an
# entire group of bodies or nested parts. The project root ``Part`` and standalone
# ``Face`` objects cannot be passed to the transform helpers.

# +
sub_part = root_part.create_sub_part(name="Triangle assembly")
sub_part.axis_system = [0, 50, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
part_body = sub_part.create_body(name="Assembly triangle")
part_face = part_body.create_face(name="Assembly face")
part_face.vertices = list(face.vertices)
part_face.facets = list(face.facets)
part_face.normals = list(face.normals)
sub_part.commit()
# -

# ### Import a lightbox and create a source
#
# A lightbox transform positions the whole imported scene, including its geometry
# and sources. A luminaire transform changes the source position and orientation.

# +
lightbox = p.create_lightbox(
    name="Lightbox",
    lightbox=LightBoxFileInstance(
        file=assets_data_path / "lightbox" / "Light Box Export.2.SPEOSLightBox",
        password="",
    ),
)
lightbox.axis_system = [0, 100, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
lightbox.commit()

luminaire = p.create_source(name="Luminaire", feature_type=SourceLuminaire)
luminaire.intensity_file_uri = assets_data_path / "IES_C_DETECTOR.ies"
luminaire.spectrum.set_daylightfluorescent()
luminaire.axis_system = [0, 150, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
luminaire.commit()
# -

# Preview the initial project before applying transforms.

p.preview()

# ## Move and copy a body
#
# Move the triangle 25 mm along Y. Body transforms update mesh vertices directly
# and rotate normals when needed; bodies do not have an ``axis_system`` property.
# For a body inside a subpart, these mesh coordinates are local to its parent part.

print("First vertex before move:", list(body.faces[0].vertices[:3]))
move_feature(body, direction=[0, 1, 0], distance=25)
print("First vertex after move:", list(body.faces[0].vertices[:3]))

# Copy the moved body 50 mm along X. The original stays at its current position.
# A body copy duplicates its mesh, so subsequent mesh changes are independent.
# The optional ``name`` must be unique among siblings and is only valid with
# ``copy=True``. Without it, a unique name such as ``Triangle_copy`` is generated.

# +
body_copy = move_feature(
    body, direction=[1, 0, 0], distance=50, copy=True, name="Triangle translated copy"
)
print("Original first vertex:", list(body.faces[0].vertices[:3]))
print("Copied first vertex:", list(body_copy.faces[0].vertices[:3]))
# -

# ## Move and copy a part
#
# Moving a subpart changes its instance coordinate system, positioning all its
# contents together. Its pose is expressed in its parent part's coordinates.
#
# A copied subpart shares the original part definition and its contents, but has an
# independent pose. Changing the shared geometry later can affect both instances.

# +
print("Part origin before move:", sub_part.axis_system[:3])
move_feature(sub_part, direction=[0, 1, 0], distance=25)
sub_part_copy = move_feature(
    sub_part, direction=[1, 0, 0], distance=50, copy=True, name="Assembly translated copy"
)
print("Original part origin:", sub_part.axis_system[:3])
print("Copied part origin:", sub_part_copy.axis_system[:3])
# -

# ## Move and copy a lightbox
#
# Lightbox poses are expressed in scene coordinates. Copying a lightbox creates
# another instance of the same imported scene, not an independent copy of its
# contents. Moving the duplicate does not move the original.

# +
print("Lightbox origin before move:", lightbox.axis_system[:3])
move_feature(lightbox, direction=[0, 1, 0], distance=25)
lightbox_copy = move_feature(
    lightbox, direction=[1, 0, 0], distance=50, copy=True, name="Lightbox translated copy"
)
print("Original lightbox origin:", lightbox.axis_system[:3])
print("Copied lightbox origin:", lightbox_copy.axis_system[:3])
# -

# ## Move and copy a source
#
# The luminaire's pose is expressed in scene coordinates. Its copy has an independent
# pose but shares the source template, including its spectrum and intensity settings.
# Add copied sources explicitly to a simulation's ``source_paths`` when needed;
# creating a copy does not add it to existing simulations.

# +
print("Source origin before move:", luminaire.axis_system[:3])
move_feature(luminaire, direction=[0, 1, 0], distance=25)
luminaire_copy = move_feature(
    luminaire, direction=[1, 0, 0], distance=50, copy=True, name="Luminaire translated copy"
)
print("Original source origin:", luminaire.axis_system[:3])
print("Copied source origin:", luminaire_copy.axis_system[:3])
# -

# > **Note:** Surface sources are handled differently from luminaires. For constant
# > exitance, the referenced body is transformed, and ``copy=True`` also duplicates
# > that body. The geometry must resolve to exactly one body. Moving it in place
# > also moves the geometry used by other features. For variable exitance, the XMP
# > map plane is transformed instead.

# ## Rotate a feature
#
# The same move/copy options are available for rotation. Rotate the copied assembly
# 45 degrees around a Z axis through its own origin. To orbit a feature around
# another point instead, change ``point``. Set ``copy=True`` to keep the input pose
# and create another rotated instance.

# +
rotate_feature(
    sub_part_copy,
    point=sub_part_copy.axis_system[:3],
    axis=[0, 0, 1],
    angle=45,
)
print("Rotated assembly coordinate system:", sub_part_copy.axis_system)
# -

# ## Position a feature from one coordinate system to another
#
# ``axis_to_axis_feature`` combines translation and rotation by mapping a reference
# frame onto a target frame. Each frame contains twelve values:
# ``[origin_x, origin_y, origin_z, Xx, Xy, Xz, Yx, Yy, Yz, Zx, Zy, Zz]``.
# The basis vectors must form an orthonormal, right-handed coordinate system.
#
# Use the copied luminaire's current frame as the reference to place its origin at
# (100, 175, 0) and rotate its orientation 90 degrees around Z. Like the other helpers,
# this operation also accepts ``copy=True`` and an optional duplicate ``name``.

# +
target_axis = [100, 175, 0, 0, 1, 0, -1, 0, 0, 0, 0, 1]
axis_to_axis_feature(
    luminaire_copy,
    reference_axis=luminaire_copy.axis_system,
    target_axis=target_axis,
)
print("Positioned source coordinate system:", luminaire_copy.axis_system)
print("Unchanged original source coordinate system:", luminaire.axis_system)
# -

# ## Review the transformed project
#
# Preview the moved originals and their copies. No extra ``commit()`` is required
# after any of the transform calls.

p.preview()

# ## Close the connection

speos.close()
