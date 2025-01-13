# # prism example using script layer

# This tutorial demonstrates how to run a prism use case using layer.

# +
import os

import ansys.speos.core as core
import ansys.speos.script as script

tests_data_path = os.path.join("/app", "assets")
# -

# Create connection with speos rpc server
# +
speos = core.Speos(host="localhost", port=50098)
# -


# ## Create simulation
# load a simulation from .speos file
# +
p = script.Project(speos=speos, path=os.path.join(tests_data_path, "Prism.speos", "Prism.speos"))
print(p)
# -

# preview simulation's part
# +
p.preview()
# -

# retrieve the simulation feature
# +
sim_features = p.find(name="Prism", feature_type=script.simulation.Direct)
sim = sim_features[0]
sim.compute_CPU()
# -

# Use the open_result_image method to review the result
# +
if os.name == "nt":
    from ansys.speos.workflow.open_result import open_result_image

    open_result_image(simulation_feature=sim, result_name="Prism.Irradiance.1.xmp")
# -

# Retrieve the sensor feature and modify sensor definition
# +
irr_features = p.find(name=".*", name_regex=True, feature_type=script.sensor.Irradiance)
irr = irr_features[0]
irr.set_type_spectral().set_wavelengths_range().set_start(500).set_end(600).set_sampling(11)
irr.commit()
# -

# re-run the simulation with new sensor definition
# +
sim.compute_CPU()
if os.name == "nt":
    open_result_image(simulation_feature=sim, result_name="Prism.Irradiance.1.xmp")
# -
