# # How to preview a light expert result

# This tutorial demonstrates how to review the light expert simulation result.

# +
import os

from ansys.speos.core import LightPathFinder, Project, Speos
from ansys.speos.core.simulation import Interactive

# If using docker container
tests_data_path = os.path.join("/app", "assets")
# If using local server
# tests_data_path = os.path.join(os.path.abspath(""), os.path.pardir, os.path.pardir, "tests", "assets")

# -

# ## Create connection with speos rpc server

# +
speos = Speos(host="localhost", port=50098)
# -

# ## Create a new project

# In this example, a project is created via reading a pre-defined .speos file.

# User can preview the part and mesh information.

# By providing viz_args to the preview function, project part can be viewed in a semi-transparent way.

# It can be found there is volume conflict in this project.

# +
p = Project(speos=speos, path=os.path.join(tests_data_path, "error_data.speos", "error_data.speos"))
p.preview(viz_args={"opacity": 0.7})
# -

# ## Retrieve the simulation feature and run

# +
sim = p.find("Direct.1")[0]
sim.compute_CPU()
# -

# If looking to the simulation report, we will find that we have 40% simulation error

# +
import ansys.speos.core.workflow.open_result as ORF

# Methods from workflow class provide a way to find the correct result file.
# Detailed information can be found in the workflow_open_result example.
data = ORF._find_correct_result(sim, "Direct.1.html")
# -

# ## Create a simulation with light expert

# We will define an interactive simulation to have a look at the rays in error

# +
interactive_sim = p.create_simulation("error", feature_type=Interactive)
interactive_sim.set_light_expert(True)
interactive_sim.set_sensor_paths(["Irradiance.1:70"])
interactive_sim.set_source_paths(["Surface.1:4830"])
interactive_sim.commit()
# -

# ## Preview the light expert result

# Here, we will run the simulation and preview the result via LightPathFinder class.

# By default, the LightPathFinder class will preview all the rays collected in the simulation.

# +
results = interactive_sim.compute_CPU()
path = ORF._find_correct_result(interactive_sim, "error.lpf", download_if_distant=False)
lxp = LightPathFinder(speos, path)
lxp.preview(project=p)
# -

# ## Preview the light expert result with error filter

# ray_filter option is provided in the preview function that user can filter the rays to see only rays in error.

# In this example, error rays are generated due to a volume conflict between two solids.

# +
lxp.filter_error_rays()
lxp.preview(project=p, ray_filter=True)
# -
