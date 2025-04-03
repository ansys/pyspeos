# # How to open result (windows os)

# This tutorial demonstrates how to open and review results using workflow method.

# ## Prerequisites
#
# ### Perform imports
import os
from pathlib import Path

from ansys.speos.core import Project, Speos
from ansys.speos.core.simulation import SimulationDirect

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
FILE_NAME = "LG_50M_Colorimetric_short.sv5"
RESULT_NAME = "ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp"
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.
USE_GPU = False

# ## Load assets
# The assets are used to run this example are available in the
# [PySpeos repository](https://github.com/ansys/pyspeos/) on GitHub.
#
# > **Note:** Make sure you
# > have downloaded simulation assets and set ``assets_data_path``
# > to point to the assets folder.

if USE_DOCKER:  # Running on the remote server.
    assets_data_path = Path("/app") / "assets"
else:
    assets_data_path = Path("/path/to/your/download/assets/directory")

# ## Create connection with speos rpc server

speos = Speos(host=HOSTNAME, port=GRPC_PORT)

# ## Create project from speos file

p = Project(
    speos=speos,
    path=str(assets_data_path / FILE_NAME / FILE_NAME),
)
print(p)

# ## Retrieve the simulation feature
#
# Use find method from project class to retrieve the simulation feature.

sim = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]

# ## Run simulation
#
# The simulation can be run using CPU via compute_CPU method or using GPU via compute_GPU method.

run_sim = sim.compute_GPU if USE_GPU else sim.compute_CPU
results = run_sim()  # run the simulation
print(results)


# ## Open result (only windows):
#
# Display one result as image.
#
# A full path can be given, or the name of the result.

if os.name == "nt":
    from ansys.speos.core.workflow.open_result import open_result_image

    open_result_image(simulation_feature=sim, result_name=RESULT_NAME)

# ## Display result in viewer (only windows).
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
