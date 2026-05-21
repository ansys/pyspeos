import os
import time
import shutil
import datetime
import progressbar
from pathlib import Path


from ansys.speos.core import project, launcher, simulation, sensor
from ansys.speos.core.kernel.job import ProtoJob
from ansys.speos.core.workflow import SpeosFileInstance, combine_speos


def launch_sim(p, sim, out_folder, outname):
    ### LAUNCH SIMULATION#1 AS PROTOJOB ###
    sim._job.job_type = ProtoJob.Type.GPU
    sim.job_link = p.client.jobs().create(message=sim._job)
    sim.job_link.start()

    ### MONITOR STATUS ###
    #bar = progressbar.ProgressBar(maxval=100, widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
    #bar.start()
    job_state_res = sim.job_link.get_state()

    while (
        job_state_res.state != ProtoJob.State.FINISHED
        and job_state_res.state != ProtoJob.State.STOPPED
        and job_state_res.state != ProtoJob.State.IN_ERROR
    ):
        time.sleep(1) # status update interval
        job_state_res = sim.job_link.get_state() # check simulation status
        #bar.update(100*sim.job_link.get_progress_status().progress)
        print(sim.job_link.get_progress_status().infos) # simuation progress, estimated time remaining

    try:
        sim_result = sim.job_link.get_results()
    except:
        time.sleep(1)
        sim_result = sim.job_link.get_results()

    ### retrieve the results 
    xmp_path = sim_result.results[0].path


    # add simulation name to out path
    sim_name = sim._name
    out_folder = out_folder / f"{sim_name}_{outname}"
    if not os.path.isdir(out_folder):
        # create the output folder
        os.mkdir(out_folder)

    # Move all data files from xmp_path to out_folder, overwriting existing files
    for filename in os.listdir(os.path.dirname(xmp_path)):
        full_file_name = os.path.join(os.path.dirname(xmp_path), filename)
        if os.path.isfile(full_file_name):
            shutil.copy2(full_file_name, out_folder)  # overwrite existing files
    shutil.rmtree(os.path.dirname(xmp_path))


print("Launching SPEOS RPC server...")
speos = launcher.launch_local_speos_rpc_server(version="261", port=50098) 
print("Speos RPC server connection established")

cwd = Path.cwd()
#speos_file = "Inverse_wfov_timelineoff.speos"
speos_file = "Inverse_wfov.speos"
model_data_path = cwd / "development-testing" / "feat-implement-timeline" / "SPEOS output files" / f"{speos_file}" / f"{speos_file}" 
out_folder = cwd / "development-testing" / "feat-implement-timeline" / "#PySpeos_Simulation_Results"
if not model_data_path.is_file():
    print("\nerror: invalid .speos file path\n")

p = project.Project(speos=speos, path=model_data_path)
root_part = p.create_root_part()
root_part.commit()


### Retrieve the simulation
sim = p.find(name=".*", name_regex=True, feature_type=simulation.SimulationInverse)[0]

### test results organization
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# test config1: no change to settings
test1 = timestamp + "_nominal"
#sim.stop_condition_passes_number = 25 ##### IN THIS CASE, THE STOP_CONDITION_PASSES_NUMBER SETTING FROM .SPEOS FILE SIMULATION IS CORRECTLY USED WITHOUT INTERVENTION
launch_sim(p, sim, out_folder, test1) 

# test config 2
test2 = timestamp + "_timeline-false"
sim.timeline = False
sim.stop_condition_passes_number = 25 ##### WITHOUT THIS, STOP CONDITION GETS REMOVED; WHY IS THIS NECESSARY?
sim.commit()
launch_sim(p, sim, out_folder, test2)

# test config 3
test3 = timestamp + "_timeline-true"
sim.timeline = True
sim.commit()
launch_sim(p, sim, out_folder, test3)


# test config 4
test4 = timestamp + "_adjust-start-time-0p9"
sim.start_time = 0.9
sim.commit()
launch_sim(p, sim, out_folder, test4)


# test config 5
test5 = timestamp + "_timeline-false-reset"
sim.timeline = False
sim.commit()
launch_sim(p, sim, out_folder, test5)