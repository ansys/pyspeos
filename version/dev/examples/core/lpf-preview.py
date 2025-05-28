# # How to preview a light expert result
#
# This tutorial demonstrates how to review the light expert simulation result.
#
# ## Prerequisites
#
# ### Perform imports

# +
from pathlib import Path

from ansys.speos.core import LightPathFinder, Project, Speos, launcher
from ansys.speos.core.simulation import SimulationInteractive

# -

# ### Define constants
#
# The constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.
RESULT_NAME = "Direct.1.Irradiance.1.lpf"

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

# ### Start/Connect to Speos RPC Server
# This Python client connects to a server where the Speos engine
# is running as a service. In this example, the server and
# client are the same machine. The launch_local_speos_rpc_method can
# be used to start a local instance of the service.

if USE_DOCKER:
    speos = Speos(host=HOSTNAME, port=GRPC_PORT)
else:
    speos = launcher.launch_local_speos_rpc_server(port=GRPC_PORT)

# ## Create a new project
#
# In this example, a project is created via reading a pre-defined .speos file.
# It can be found there is volume conflict in this project.

# +
p = Project(
    speos=speos,
    path=str(assets_data_path / "error_data.speos" / "error_data.speos"),
)
p.preview(viz_args={"opacity": 0.7})
# -

# ## Retrieve the simulation feature, add light expert and run

sim = p.find("Direct.1")[0]
sim.set_light_expert(True)
sim.commit()
sim.compute_CPU()

# If looking to the simulation report, we will find that we have 40% simulation error

# +
import ansys.speos.core.workflow.open_result as orf

# Methods from workflow class provide a way to find the correct result file.
# Detailed information can be found in the workflow_open_result example.
data = orf._find_correct_result(sim, "Direct.1.html")
# -

# when reviewing The ray data using LightPathFinder class. We can see a lot of rays missing

path = orf._find_correct_result(sim, RESULT_NAME, download_if_distant=False)
lxp = LightPathFinder(speos, path)
lxp.preview(project=p)

# ## Create an Interactive simulation with light expert
#
# We will define an interactive simulation to have a look at the rays in error as a direct
# simulation will only show the rays hitting the sensor not the rays in error.


interactive_sim = p.create_simulation("error", feature_type=SimulationInteractive)
interactive_sim.set_light_expert(True)
interactive_sim.set_sensor_paths(["Irradiance.1:70"])
interactive_sim.set_source_paths(["Surface.1:4830"])
interactive_sim.commit()

# ## Preview the light expert result
#
# Here, we will run the simulation and preview the result via LightPathFinder class.
# By default, the LightPathFinder class will preview the first 100 rays stored in the lpf-file.


results = interactive_sim.compute_CPU()
path = orf._find_correct_result(interactive_sim, "error.lpf", download_if_distant=False)
lxp = LightPathFinder(speos, path)
lxp.preview(project=p)


# ## Preview the light expert result with error filter
#
# ray_filter option is provided in the preview function that user can filter the rays to see only
# rays in error.
# In this example, error rays are generated due to a volume conflict between two solids.

lxp.filter_error_rays()
lxp.preview(project=p, ray_filter=True)
