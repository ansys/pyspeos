"""
Test job.
"""
import time

from test_scene import create_basic_scene

from ansys.speos.core import LOG  # Global logger
from ansys.speos.core.job import JobFactory
from ansys.speos.core.job import messages as job_messages
from ansys.speos.core.proto_message_utils import protobuf_message_to_str
from ansys.speos.core.speos import Speos
from helper import clean_all_dbs, run_job_and_check_state


def test_job_factory(speos: Speos):
    """Test the job factory."""
    assert speos.client.healthy is True

    scene = create_basic_scene(speos)
    assert scene.key != ""
    assert len(scene.get().simulations) == 4

    job_dir = speos.client.jobs().create(
        message=JobFactory.new(
            name="job_dir", scene=scene, simulation_path=scene.get().simulations[0].name, properties=JobFactory.direct_mc_props()
        )
    )
    assert job_dir.key != ""

    job_inv = speos.client.jobs().create(
        message=JobFactory.new(
            name="job_inv", scene=scene, simulation_path=scene.get().simulations[2].name, properties=JobFactory.inverse_mc_props()
        )
    )
    assert job_inv.key != ""

    job_int = speos.client.jobs().create(
        message=JobFactory.new(
            name="job_int", scene=scene, simulation_path=scene.get().simulations[3].name, properties=JobFactory.interactive_props()
        )
    )
    assert job_int.key != ""

    # job_int.run()

    clean_all_dbs(speos.client)


def test_job_actions(speos: Speos):
    """Test the job actions."""
    assert speos.client.healthy is True

    # Create basic scene
    scene = create_basic_scene(speos)
    assert scene.key != ""
    assert len(scene.get().simulations) == 4

    # Create CPU job for direct simu
    job_dir = speos.client.jobs().create(
        message=JobFactory.new(
            name="job_dir", scene=scene, simulation_path=scene.get().simulations[1].name, properties=JobFactory.direct_mc_props()
        )
    )
    assert job_dir.key != ""

    # Start job and check its state regularly
    job_dir.start()
    job_state_res = job_dir.get_state()
    while (
        job_state_res.state != job_messages.Job.State.FINISHED
        and job_state_res.state != job_messages.Job.State.STOPPED
        and job_state_res.state != job_messages.Job.State.IN_ERROR
    ):
        time.sleep(2)
        job_state_res = job_dir.get_state()
        LOG.info(protobuf_message_to_str(job_state_res))
        if job_state_res.state == job_messages.Job.State.IN_ERROR:
            LOG.error(protobuf_message_to_str(job_dir.get_error()))
            assert False

    # Verify that results are generated
    assert len(job_dir.get_results().results) == 3

    # Create CPU job for inverse simu + run via helper method
    job_inv = speos.client.jobs().create(
        message=JobFactory.new(
            name="job_inv",
            scene=scene,
            simulation_path=scene.get().simulations[2].name,
            properties=JobFactory.inverse_mc_props(stop_condition_passes_number=200),
        )
    )
    assert job_inv.key != ""
    run_job_and_check_state(job_inv)

    clean_all_dbs(speos.client)
