import os

import ansys.speos.core as core
from ansys.speos.core.launcher import launch_local_speos_rpc_server
import ansys.speos.core.source as source

speos = launch_local_speos_rpc_server(version="252")
speos_file = os.path.join(os.getcwd(), "Speos Bench", "Inverse.1.1.speos", "Inverse.1.1.speos")
project = core.Project(speos=speos, path=speos_file)
mysource = project.find(name=".*", name_regex=True, feature_type=source.SourceThermic)
mysource[0].set_emissive_faces_temp(value=100)
mysource[0].commit()
mysimu = project.find(name=".*", name_regex=True, feature_type=core.simulation.SimulationInverse)
mysimu = mysimu[0]
new_source = project.create_source(name="test", feature_type=source.SourceThermic)
new_source.commit()
print(project)

# mysimu.compute_CPU()
# print(mysimu.result_list)
