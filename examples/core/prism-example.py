# # Prism example
#
# This tutorial demonstrates how to open an existing Speos file, run
# the simulation and open the result. After that it explains how to
# edit the File and adjust Parameters of the sensor.
#
# ## Prerequisites
#
# ### Perform imports

# +
import os
from pathlib import Path

from ansys.speos.core import Project, Speos
from ansys.speos.core.launcher import launch_local_speos_rpc_server
from ansys.speos.core.sensor import SensorIrradiance
from ansys.speos.core.simulation import SimulationDirect

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
# client are the same machine. the launch_local_speos_rpc_method can
# be used to start a local instance of the service.

if USE_DOCKER:
    speos = Speos(host=HOSTNAME, port=GRPC_PORT)
else:
    speos = launch_local_speos_rpc_server(port=GRPC_PORT)


# ## Create project
#
# Load a project from .speos file.

p = Project(speos=speos, path=str(assets_data_path / "Prism.speos" / "Prism.speos"))
print(p)

# ## Preview
# This preview method allows you to preview the content of the Speos solver
# file.

p.preview()


# ## Retrieve the simulation feature and open result
#
# Run the simulation

sim_features = p.find(name="Prism", feature_type=SimulationDirect)
sim = sim_features[0]
sim.compute_CPU()

# Use the open_result_image method to review the result


if os.name == "nt":
    from ansys.speos.core.workflow.open_result import open_result_image

    open_result_image(simulation_feature=sim, result_name="Prism.Irradiance.1.xmp")

# ## Work with sensor
#
# Retrieve the sensor feature.
#
# Modify the sensor setting, e.g. set the spectral type, etc.

irr_features = p.find(name=".*", name_regex=True, feature_type=SensorIrradiance)
irr = irr_features[0]
irr.set_type_spectral().set_wavelengths_range().set_start(500).set_end(600).set_sampling(11)
irr.commit()

# ## Re-run the simulation with new sensor definition

sim.compute_CPU()
if os.name == "nt":
    open_result_image(simulation_feature=sim, result_name="Prism.Irradiance.1.xmp")
