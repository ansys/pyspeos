"""
Test job.
"""
from ansys.speos.core.job import JobFactory
from ansys.speos.core.speos import Speos
from helper import clean_all_dbs
from test_client_scene import create_basic_scene


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

    clean_all_dbs(speos.client)
