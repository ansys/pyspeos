# # How to use scene and job

# This tutorial demonstrates how to create a scene, and fill it from a speos file.
# Then this demonstrates how to create a job from the scene, and run it.

# +
import os
import time

from ansys.speos.core.kernel.job import Job
from ansys.speos.core.speos import Speos

# If using docker container
tests_data_path = os.path.join("/app", "assets")
# If using local server
# tests_data_path = os.path.join(os.path.abspath(""), os.path.pardir, os.path.pardir, os.path.pardir, "tests", "assets")
# -

# Create connection with speos rpc server

# +
speos = Speos(host="localhost", port=50098)
# -

# ## Scene

# Create an empty scene

# +
my_scene = speos.client.scenes().create()
# -

# Load a file to fill the scene

# +
speos_file = os.path.join(
    tests_data_path, "LG_50M_Colorimetric_short.sv5", "LG_50M_Colorimetric_short.sv5"
)
my_scene.load_file(file_uri=speos_file)
# -

# Print scene data model

# Here it is possible to see that the scene contains two surface sources, one irradiance sensor.

# +
print(my_scene)
# -

# ## Job

# Create a job for the first simulation. When loaded from a speos file, there is always only one simulation in the scene.

# +
# First create the protobuf message
job_message = Job(name="my_job")
job_message.scene_guid = my_scene.key  # The job needs a scene guid
job_message.simulation_path = (
    my_scene.get().simulations[0].name
)  # And needs to know which simulation in the scene is involved.
job_message.job_type = Job.Type.CPU  # Choose type of job, can also be GPU.
job_message.direct_mc_simulation_properties.automatic_save_frequency = 1800
job_message.direct_mc_simulation_properties.stop_condition_rays_number = (
    200000  # Stop condition, here 200000 rays will be sent.
)

# Create the JobLink
job_link = speos.client.jobs().create(message=job_message)
# -

# Start the job

# +
job_link.start()
# -

# Verify state of the job

# +
job_link.get_state()
# -

# Wait that the job is finished

# +
job_state_res = job_link.get_state()
while (
    job_state_res.state != Job.State.FINISHED
    and job_state_res.state != Job.State.STOPPED
    and job_state_res.state != Job.State.IN_ERROR
):
    time.sleep(2)

    job_state_res = job_link.get_state()
# -

# Retrieve results of the job

# Two results are generated : the result of irradiance sensor: ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp
# and the simulation report in html

# +
results = job_link.get_results().results
print(results)
# -

# Once no more needed: delete the job

# +
job_link.delete()
# -


# When loading a speos file into a scene, this creates many objects (source templates, sensor templates, vop template, sop templates).
# Then at the end of the example, we just clean all databases

# +
for item in (
    speos.client.scenes().list()
    + speos.client.simulation_templates().list()
    + speos.client.sensor_templates().list()
    + speos.client.source_templates().list()
    + speos.client.intensity_templates().list()
    + speos.client.spectrums().list()
    + speos.client.vop_templates().list()
    + speos.client.sop_templates().list()
    + speos.client.parts().list()
    + speos.client.bodies().list()
    + speos.client.faces().list()
):
    item.delete()
# -
