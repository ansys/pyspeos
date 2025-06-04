# # How to use scene and job

# This tutorial demonstrates how to create a scene, and fill it from a speos file.
# Then this demonstrates how to create a job from the scene, and run it.

# ## Prerequisites
#
# ### Perform imports

# +
from pathlib import Path
import time

from ansys.speos.core import launcher
from ansys.speos.core.kernel.job import ProtoJob
from ansys.speos.core.speos import Speos

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.

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

# ## Scene

# Create an empty scene

# +
my_scene = speos.client.scenes().create()
# -

# Load a file to fill the scene

# +
speos_file = str(
    assets_data_path / "LG_50M_Colorimetric_short.sv5" / "LG_50M_Colorimetric_short.sv5"
)
my_scene.load_file(file_uri=speos_file)
# -

# Print scene data model

# Here it is possible to see that the scene contains two surface sources, one irradiance sensor.

print(my_scene)

# ## Job

# Create a job for the first simulation. When loaded from a speos file, there is always only one
# simulation in the scene.

# +
# First create the protobuf message
job_message = ProtoJob(name="my_job")
job_message.scene_guid = my_scene.key  # The job needs a scene guid
job_message.simulation_path = (
    my_scene.get().simulations[0].name
)  # And needs to know which simulation in the scene is involved.
job_message.job_type = ProtoJob.Type.CPU  # Choose type of job, can also be GPU.
job_message.direct_mc_simulation_properties.automatic_save_frequency = 1800
job_message.direct_mc_simulation_properties.stop_condition_rays_number = (
    200000  # Stop condition, here 200000 rays will be sent.
)

# Create the JobLink
job_link = speos.client.jobs().create(message=job_message)
# -

# Start the job

job_link.start()

# Verify state of the job

job_link.get_state()

# Wait that the job is finished

# +
job_state_res = job_link.get_state()
while (
    job_state_res.state != ProtoJob.State.FINISHED
    and job_state_res.state != ProtoJob.State.STOPPED
    and job_state_res.state != ProtoJob.State.IN_ERROR
):
    time.sleep(2)

    job_state_res = job_link.get_state()
# -

# Retrieve results of the job

# Two results are generated : the result of irradiance sensor:
# "ASSEMBLY1.DS (0).Dom Irradiance Sensor (0).xmp" and the simulation report in html

results = job_link.get_results().results
print(results)

# Once no more needed: delete the job


job_link.delete()


# When loading a speos file into a scene, this creates many objects
# (source templates, sensor templates, vop template, sop templates).
# Then at the end of the example, we just clean all databases


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

speos.close()
