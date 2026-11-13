# # How to get vtp export from xmp or xm3 results (Windows only)

# This tutorial demonstrates how to get vtp export when computing a simulation.
# It also demonstrates how to get vtp export from an existing xmp or xm3 result
# generated for example by Speos HPC computation.

# ## Prerequisites
#
# ### Perform imports

# +
import os
from pathlib import Path

from ansys.speos.core import Project, Speos, launcher
from ansys.speos.core.kernel.client import (
    default_docker_channel,
)
from ansys.speos.core.sensor import SensorIrradiance
from ansys.speos.core.simulation import SimulationDirect

# -

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
FILE_NAME = "LG_50M_Colorimetric_short.sv5"
RESULT_NAME = "ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp"
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

# ### Connect to the RPC Server
# This Python client connects to a server where the Speos engine
# is running as a service. In this example, the server and
# client are the same machine.

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

# ### Retrieve the simulation feature
#
# Use the method ``Project.find()`` to retrieve an instance
# of the ``SimulationDirect`` feature.

sim = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]

# ## Run simulation
#
# When running the simulation, the ``export_vtp`` argument can be set to True to get vtp export
# of the compatible results.

if os.name == "nt":
    speos_results, vtp_results = sim.compute_CPU(export_vtp=True)  # run the simulation
    print(speos_results, vtp_results)


# ## vtp export from an existing xmp or xm3 result
# ### Create a project
#
# The project needs to be created from the same Speos file used to generate the xmp or xm3 result.

p2 = Project(
    speos=speos,
    path=str(assets_data_path / FILE_NAME / FILE_NAME),
)

# ### Retrieve needed features
#
# The simulation is here retrieved, but won't be computed.
# The vtp export will be done from the existing xmp or xm3 result.

# The sensor feature is also retrieved.

sim2 = p2.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
ssr = p2.find(name=".*", name_regex=True, feature_type=SensorIrradiance)[0]

# ### Export xmp result to vtp
#
# simulation feature and sensor feature are needed to export the xmp result to vtp.
# As well as the path of the existing xmp result.

if os.name == "nt":
    from ansys.speos.core.workflow.open_result import export_xmp_vtp

    vtp_path = export_xmp_vtp(
        simulation_feature=sim2,
        xmp_feature=ssr,
        result_name=assets_data_path / "mimic_extern_results" / RESULT_NAME,
    )


speos.close()
