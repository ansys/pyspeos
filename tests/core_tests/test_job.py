# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
    assert len(scene.get().simulations) == 4

    job_dir = speos.client.jobs().create(
        message=JobFactory.new(
            name="job_dir", scene=scene, simulation_path=scene.get().simulations[0].name, properties=JobFactory.direct_mc_props()
        )
    )

    job_inv = speos.client.jobs().create(
        message=JobFactory.new(
            name="job_inv", scene=scene, simulation_path=scene.get().simulations[2].name, properties=JobFactory.inverse_mc_props()
        )
    )

    job_int = speos.client.jobs().create(
        message=JobFactory.new(
            name="job_int", scene=scene, simulation_path=scene.get().simulations[3].name, properties=JobFactory.interactive_props()
        )
    )

    clean_all_dbs(speos.client)


def test_job_actions(speos: Speos):
    """Test the job actions."""
    assert speos.client.healthy is True

    # Create basic scene
    scene = create_basic_scene(speos)
    assert len(scene.get().simulations) == 4

    # Create CPU job for direct simu
    job_dir = speos.client.jobs().create(
        message=JobFactory.new(
            name="job_dir", scene=scene, simulation_path=scene.get().simulations[1].name, properties=JobFactory.direct_mc_props()
        )
    )

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

    clean_all_dbs(speos.client)


def test_job_actions_interactive_simu(speos: Speos):
    """Test the job actions with interactive simulation."""
    assert speos.client.healthy is True

    # Create basic scene
    scene = create_basic_scene(speos)
    assert len(scene.get().simulations) == 4

    # Create CPU job for interactive simu
    job_int = speos.client.jobs().create(
        message=JobFactory.new(
            name="job_int", scene=scene, simulation_path=scene.get().simulations[3].name, properties=JobFactory.interactive_props()
        )
    )
    run_job_and_check_state(job_int)
    assert len(job_int.get_results().results) == 1

    ray_paths = []
    for ray_path in job_int.get_ray_paths():
        ray_paths.append(ray_path)
    assert len(ray_paths) == 3 * 100  # 100 rays per source and three sources are referenced in this simulation

    clean_all_dbs(speos.client)
