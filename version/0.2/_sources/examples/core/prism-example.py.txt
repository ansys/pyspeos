# # Prism example

# This tutorial demonstrates how to run a prism use case.

# +
import os
from pathlib import Path

from ansys.speos.core import Project, Speos
from ansys.speos.core.sensor import SensorIrradiance
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


# ## Create project

# Load a project from .speos file.

# +
p = Project(speos=speos, path=str(tests_data_path / "Prism.speos" / "Prism.speos"))
print(p)
# -

# ## Preview.

# +
p.preview()
# -

# ## Retrieve the simulation feature and open result

# Run the simulation

# +
sim_features = p.find(name="Prism", feature_type=SimulationDirect)
sim = sim_features[0]
sim.compute_CPU()
# -

# Use the open_result_image method to review the result

# +
if os.name == "nt":
    from ansys.speos.core.workflow.open_result import open_result_image

    open_result_image(simulation_feature=sim, result_name="Prism.Irradiance.1.xmp")
# -

# ## Work with sensor

# Retrieve the sensor feature.

# Modify the sensor setting, e.g. set the spectral type, etc.

# +
irr_features = p.find(name=".*", name_regex=True, feature_type=SensorIrradiance)
irr = irr_features[0]
irr.set_type_spectral().set_wavelengths_range().set_start(500).set_end(600).set_sampling(11)
irr.commit()
# -

# ## Re-run the simulation with new sensor definition

# +
sim.compute_CPU()
if os.name == "nt":
    open_result_image(simulation_feature=sim, result_name="Prism.Irradiance.1.xmp")
# -
