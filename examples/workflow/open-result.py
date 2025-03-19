# # How to open result (windows os)

# This tutorial demonstrates how to open and review results using workflow method.

# +
import os
from pathlib import Path

from ansys.speos.core import Project, Speos
from ansys.speos.core.simulation import SimulationDirect

# If using docker container
tests_data_path = Path("/app") / "assets"
# If using local server
# tests_data_path = Path().resolve().parent.parent / "tests" / "assets"
# -

# ## Create connection with speos rpc server

# +
speos = Speos(host="localhost", port=50098)
# -

# ## Create project from speos file

# +
p = Project(
    speos=speos,
    path=str(tests_data_path / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"),
)
print(p)
# -

# ## Retrieve the simulation feature

# Use find method from project class to retrieve the simulation feature.

# +
sim = p.find(name=".*", name_regex=True, feature_type=SimulationDirect)[0]
# -

# ## Run simulation

# simulation can be run using CPU via compute_CPU method or using GPU via compute_GPU method.

# +
results = sim.compute_cpu()  # run in CPU
print(results)
# -

# ## Open result (only windows):

# Display one result as image.

# A full path can be given, or the name of the result.

# +
if os.name == "nt":
    from ansys.speos.core.workflow.open_result import open_result_image

    open_result_image(
        simulation_feature=sim,
        result_name="ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp",
    )
# -

# ## Display result in viewer (only windows).

# Display one result in a result viewer.

# A full path can be given, or the name of the result.

# +
if os.name == "nt":
    from ansys.speos.core.workflow.open_result import open_result_in_viewer

    open_result_in_viewer(
        simulation_feature=sim,
        result_name="ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp",
    )
# -
