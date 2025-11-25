# # How to open result (MS Windows OS only)

# This tutorial demonstrates how to open and review results using workflow method.

# ## Prerequisites
#
# ### Perform imports

# +
import os
from pathlib import Path

from ansys.speos.core import Project, Speos
from ansys.speos.core.kernel.client import (
    default_docker_channel,
)
from ansys.speos.core.simulation import SimulationDirect

# -

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
FILE_NAME = "LG_50M_Colorimetric_short.sv5"
RESULT_NAME = "ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp"
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.
USE_GPU = False

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
# client are the same
# machine.

if USE_DOCKER:
    speos = Speos(channel=default_docker_channel())
else:
    speos = launcher.launch_local_speos_rpc_server(port=GRPC_PORT)

# ### Create project from a Speos file
#
# The ``Project`` class is instantiated by passing a ``Speos`` instance and the name of the Speos
# project file.

p = Project(
    speos=speos,
    path=str(assets_data_path / FILE_NAME / FILE_NAME),
)
print(p)

# ### Retrieve the simulation feature
#
# Use the method ``Project.find()`` to retrieve an instance
# of the ``SimulationDirect`` feature.

sim = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]

# ## Run simulation
#
# The simulation can be run using either the CPU or with GPU acceleration. The following cell shows
# how Python is used to assign the appropriate method to ``run_sim``.

run_sim = sim.compute_GPU if USE_GPU else sim.compute_CPU
results = run_sim()  # run the simulation
print(results)


# ## Postprocessing
# ### Open the results (MS Windows OS only):
#
# Display one result as image.
#
# A full path can be given, or the name of the result.

if os.name == "nt":  # Are we running on Windows OS?
    from ansys.speos.core.workflow.open_result import open_result_image

    open_result_image(simulation_feature=sim, result_name=RESULT_NAME)

# ### Display the image
#
# Display one result in a result viewer.
#
# A full path can be given, or the name of the result.

if os.name == "nt":
    from ansys.speos.core.workflow.open_result import open_result_in_viewer

    open_result_in_viewer(
        simulation_feature=sim,
        result_name=RESULT_NAME,
    )
speos.close()
