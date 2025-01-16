# # How to preview light expert result

# This tutorial demonstrates how to review the light expert simulation result.

# +
import os

from ansys.speos.core import Speos
import ansys.speos.script as script

# If using docker container
tests_data_path = os.path.join("/app", "assets")
# If using local server
# tests_data_path = os.path.join(os.path.abspath(""), os.path.pardir, os.path.pardir, os.path.pardir, "tests", "assets")
# -

# ## Create connection with speos rpc server

# +
speos = Speos(host="localhost", port=50098)
# -

# ## New Project and Run Simulation

# In this example, a project is created via reading a pre-defined .speos file.

# +
p = script.Project(speos=speos, path=os.path.join(tests_data_path, "error_data.speos", "error_data.speos"))
# -

# User can preview the part and mesh information.

# +
p.preview()
# -

# Retrieve the simulation feature and run

# +
sim = p.find("Direct.1")[0]
sim.compute_CPU()
# -

from IPython.display import HTML, display

# ## Methods from workflow class

# workflow class is collection of useful workflow methods

# example, open_result check the result with given result file type:

# If we have a look to the simulation report we will find that we have 40% simulation error


data = ORF._find_correct_result(sim, "Direct.1.html")
display(HTML(data, metadata=dict(isolated=True)))
# -

# ## Create an interactive simulation with light expert

# We will define an interactive simulation to have a look at the rays in error

# +
interactive_sim = p.create_simulation("error", feature_type=script.simulation.Interactive)
interactive_sim.set_light_expert(True)
interactive_sim.set_sensor_paths(["Irradiance.1:70"])
interactive_sim.set_source_paths(["Surface.1:4830"])
interactive_sim.commit()
results = interactive_sim.compute_CPU()
# -

# ## Retrieve the light expert file

# Create a light expert from script.LightPathFinder

# by default, the light expert will display all the rays collected.

# +
path = ORF._find_correct_result(interactive_sim, "error.lpf", download_if_distant=False)
lxp = script.LightPathFinder(speos, path)
lxp.preview(project=p)
# -

# ## Filter error rays

# We can directly see a volume conflict between two solids.

# Let's filter the rays to see only rays in error

# +
lxp.filter_error_rays()
lxp.preview(project=p, ray_filter=True)
# -
