# # How to open result using workflow method

# This tutorial demonstrates how to open and review results using workflow method

# +
import os

from ansys.speos.core import Speos
import ansys.speos.script as script

tests_data_path = os.path.join("/app", "assets")
# -

# Create connection with speos rpc server
# +
speos = Speos(host="localhost", port=50098)
# -

# ## Create project from speos file
# +
p = script.Project(speos=speos, path=os.path.join(tests_data_path, "LG_50M_Colorimetric_short.sv5", "LG_50M_Colorimetric_short.sv5"))
print(p)
# -

# ## Retrieve the simulation feature

# +
sim = p.find(name=".*", name_regex=True, feature_type=script.simulation.Direct)[0]
# -

# ## Run simulation

# +
results = sim.compute_CPU()
print(results)
# -

# ## Open result:
# Display one result as image
# A full path can be given, or the name of the result.

# +
from ansys.speos.workflow.open_result import open_result_image

open_result_image(simulation_feature=sim, result_name=results[0].path)
# -

# Display one result in the appropriate viewer
# A full path can be given, or the name of the result.

# +
from ansys.speos.workflow.open_result import open_result_in_viewer

open_result_in_viewer(simulation_feature=sim, result_name="ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp")
# -
