# # How to create a component
#
# This tutorial demonstrates how to create a component feature.
#
# Component feature includes: lightbox import.

# ## Prerequisites
#
# ### Perform imports

from pathlib import Path

from ansys.speos.core import Project, Speos, launcher
from ansys.speos.core.component import LightBox, LightBoxFileInstance
from ansys.speos.core.generic.parameters import LightBoxParameters
from ansys.speos.core.kernel.client import (
    default_docker_channel,
)
from ansys.speos.core.simulation import SimulationDirect

# ### Define constants
#
# The constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.
FILES = "CameraInputFiles"


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

# ## Create a new project
#
# The only way to create a lightbox import, is to create it from a project.

p = Project(speos=speos)
print(p)

# ## Create
#
# Create locally.

# The mention "local: " is added when printing the lightbox

# +

lightbox = p.create_lightbox_import(name="Light Box Import.1", parameters=LightBoxParameters())
lightbox.set_speos_light_box(
    lightbox=LightBoxFileInstance(
        file=assets_data_path / "lightbox" / "Light Box Export.2.SPEOSLightBox", password=""
    )
)
print(lightbox)
# -

# ## Push it to the server.
#
# Now that it is committed to the server, the mention "local: " is no more present when printing the
# lightbox.

# +

lightbox.commit()
print(lightbox)
# -

# ## Read
#
# ### Lightbox Instance
#
# Properties methods provided are used to retrieve or modify the information of lightbox.

# +

print(lightbox.name)
print(lightbox.axis_system)
print(lightbox.source_paths)
lightbox.axis_system = [100, 50, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
print(lightbox)

# commit the modification to server

lightbox.commit()
print(lightbox)
# -

# ## Lightbox
#
# ### Lightbox sources in simulation
#
# A project contains 2 lightbox features


p2 = Project(
    speos=speos,
    path=assets_data_path / "lightbox" / "Direct.1.speos",
)
lightboxes = p2.find(name=".*", name_regex=True, feature_type=LightBox)
lightbox_1 = lightboxes[0]
lightbox_2 = lightboxes[1]
print(lightbox_1.source_paths)
print(lightbox_2.source_paths)

# The simulation contains sources from 2 lightbox features

simulation = p2.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
print(simulation.get(key="source_paths"))

# Modify the second lightbox feature with a new lightbox file

lightbox_2.set_speos_light_box(
    lightbox=LightBoxFileInstance(
        file=assets_data_path / "lightbox" / "Light Box Export.2.SPEOSLightBox", password=""
    )
)
print(lightbox_2.source_paths)
lightbox_2.commit()

# The new lightbox feature share 1 light source compared to the previous lightbox feature,
# so the un-matched old light source is removed from the simulation while keeping the matched
# light source.
# Any completely new light source will not be added to simulation by default, User need to decide
# if adding the new light source into simulation to simulation.

print(simulation.get(key="source_paths"))
